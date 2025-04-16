import os
import json
from datetime import datetime
import time
import argparse
import requests
from dotenv import load_dotenv

def fetch_all_my_tweets_jsonl(max_per_page=100, sleep_time=1, one_page_only=False):
    from twitter_agent.src import twitter_client
    print("Fetching all tweets from your timeline (including retweets and replies)...")
    client = twitter_client.get_twitter_client()
    user = client.get_me(user_fields=["public_metrics"])
    if not user.data:
        print("Could not determine authenticated user.")
        return
    metrics = getattr(user.data, 'public_metrics', None)
    if metrics:
        print(f"Total tweet count (including retweets and replies): {metrics.get('tweet_count', 'N/A')}")
    user_id = user.data.id
    username = user.data.username
    os.makedirs('data/tweets', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"data/tweets/{username}_all_tweets_{timestamp}.jsonl"
    out_file = open(out_path, 'w')
    next_token = None
    total = 0
    while True:
        try:
            print(f"Requesting page with next_token: {next_token}")
            tweets = client.get_users_tweets(
                id=user_id,
                max_results=max_per_page,
                pagination_token=next_token,
                tweet_fields=['created_at', 'public_metrics', 'referenced_tweets', 'conversation_id'],
                expansions=['referenced_tweets.id']
            )
            if not tweets.data:
                print("No more tweets found.")
                break
            print(f"Fetched {len(tweets.data)} tweets in this page.")
            for tweet in tweets.data:
                tweet_type = "original"
                if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                    for ref in tweet.referenced_tweets:
                        if ref.type == 'retweeted':
                            tweet_type = "retweet"
                        elif ref.type == 'replied_to':
                            tweet_type = "reply"
                        elif ref.type == 'quoted':
                            tweet_type = "quote"
                out_file.write(json.dumps({
                    "id": tweet.id,
                    "created_at": str(tweet.created_at),
                    "text": tweet.text,
                    "type": tweet_type,
                    "metrics": tweet.public_metrics if hasattr(tweet, 'public_metrics') else {},
                    "conversation_id": getattr(tweet, 'conversation_id', None)
                }) + "\n")
                total += 1
            print(f"Fetched {total} tweets so far...")
            if hasattr(tweets.meta, 'next_token') and tweets.meta.next_token:
                print(f"Pagination: next_token for next page is {tweets.meta.next_token}")
                next_token = tweets.meta.next_token
                if one_page_only:
                    print("Stopping after first page for manual pagination test.")
                    break
                time.sleep(sleep_time)
            else:
                print("No next_token found. All tweets fetched.")
                break
            print(f"Raw tweets object: {tweets}")
            if hasattr(tweets, 'meta'):
                print(f"tweets.meta: {tweets.meta}")
            if hasattr(tweets, 'data'):
                print(f"Number of tweets in data: {len(tweets.data)}")
            # Try to print the raw JSON if available
            if hasattr(tweets, 'json'):
                print(f"Raw JSON: {tweets.json}")
        except Exception as e:
            print(f"Error: {e}")
            break
    out_file.close()
    print(f"\nDone! Saved {total} tweets to {out_path}")
    return out_path

def fetch_all_my_tweets_v1(max_per_page=200):
    import tweepy
    from twitter_agent.src import config as local_config
    print("Fetching all tweets from your timeline using v1.1 (user_timeline)...")
    auth = tweepy.OAuth1UserHandler(
        local_config.TWITTER_API_KEY,
        local_config.TWITTER_API_SECRET,
        local_config.TWITTER_ACCESS_TOKEN,
        local_config.TWITTER_ACCESS_SECRET
    )
    api = tweepy.API(auth)
    all_tweets = []
    last_id = None
    while True:
        tweets = api.user_timeline(
            count=max_per_page,
            max_id=last_id,
            tweet_mode='extended',
            include_rts=True
        )
        if not tweets:
            break
        for tweet in tweets:
            all_tweets.append(tweet._json)
        print(f"Fetched {len(all_tweets)} tweets so far...")
        last_id = tweets[-1].id - 1
        if len(tweets) < max_per_page:
            break
    os.makedirs('data/tweets', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"data/tweets/v1_all_tweets_{timestamp}.jsonl"
    with open(out_path, 'w') as out_file:
        for tweet in all_tweets:
            out_file.write(json.dumps(tweet) + "\n")
    print(f"\nDone! Saved {len(all_tweets)} tweets to {out_path}")
    return out_path

def fetch_all_my_tweets_requests(max_per_page=100):
    """
    Fetch all tweets for the authenticated user using direct requests to /2/users/:id/tweets, paginating with next_token.
    Loads credentials from .env automatically.
    Handles rate limits per X API docs.
    """
    # Correct dotenv loading
    dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/.env'))
    print(f"[DEBUG] Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path)
    BEARER = os.getenv("TWITTER_BEARER_TOKEN")
    print(f"[DEBUG] BEARER after dotenv load: {BEARER}")
    USERNAME = os.getenv("TWITTER_USERNAME")
    assert BEARER, "TWITTER_BEARER_TOKEN must be set in environment or .env file"
    assert USERNAME, "TWITTER_USERNAME must be set in environment or .env file"
    headers = {"Authorization": f"Bearer {BEARER}"}
    # Step 1: Get user ID from username
    resp = requests.get(f"https://api.twitter.com/2/users/by/username/{USERNAME}", headers=headers)
    resp.raise_for_status()
    user_id = resp.json()["data"]["id"]
    print(f"Fetched user_id: {user_id}")
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {"max_results": max_per_page, "tweet.fields": "created_at,public_metrics,referenced_tweets,conversation_id"}
    tweets = []
    page = 1
    while True:
        print(f"Requesting page {page} with params: {params}")
        try:
            r = requests.get(url, headers=headers, params=params)
            # Print rate limit info
            remaining = r.headers.get('x-rate-limit-remaining')
            reset = r.headers.get('x-rate-limit-reset')
            print(f"x-rate-limit-remaining: {remaining}, x-rate-limit-reset: {reset}")
            if r.status_code == 429:
                print("Rate limit hit (HTTP 429).")
                if reset:
                    reset_time = int(reset)
                    now = int(time.time())
                    sleep_for = max(reset_time - now, 1)
                    print(f"Sleeping until reset ({sleep_for} seconds)...")
                    time.sleep(sleep_for)
                else:
                    print("No reset header found, sleeping for 2 minutes by default...")
                    time.sleep(120)
                continue  # Retry the same request
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
            if r.status_code == 429:
                print("Rate limit hit (HTTP 429).")
                reset = r.headers.get('x-rate-limit-reset')
                if reset:
                    reset_time = int(reset)
                    now = int(time.time())
                    sleep_for = max(reset_time - now, 1)
                    print(f"Sleeping until reset ({sleep_for} seconds)...")
                    time.sleep(sleep_for)
                else:
                    print("No reset header found, sleeping for 2 minutes by default...")
                    time.sleep(120)
                continue  # Retry the same request
            else:
                raise
        data = r.json()
        print(f"meta: {data.get('meta')}")
        tweets.extend(data.get("data", []))
        meta = data.get("meta", {})
        token = meta.get("next_token")
        if not token:
            break
        params["pagination_token"] = token
        page += 1
        time.sleep(1)  # Minimal sleep for politeness
    print(f"Total tweets fetched: {len(tweets)}")
    # Save to JSONL
    out_path = f"data/tweets/{USERNAME}_all_tweets_requests.jsonl"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        for tweet in tweets:
            f.write(json.dumps(tweet) + "\n")
    print(f"Saved all tweets to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch all tweets from your timeline and save as JSONL.")
    parser.add_argument('--max-per-page', type=int, default=100, help='Number of tweets to fetch per page (max_results)')
    parser.add_argument('--one-page-only', action='store_true', help='Only fetch one page for pagination testing')
    parser.add_argument('--use-v1', action='store_true', help='Use Twitter API v1.1 (user_timeline) for up to 3200 tweets')
    parser.add_argument('--use-requests', action='store_true', help='Use direct requests to /2/users/:id/tweets endpoint')
    args = parser.parse_args()
    if args.use_requests:
        fetch_all_my_tweets_requests(max_per_page=args.max_per_page)
    elif args.use_v1:
        fetch_all_my_tweets_v1(max_per_page=args.max_per_page)
    else:
        fetch_all_my_tweets_jsonl(max_per_page=args.max_per_page, one_page_only=args.one_page_only) 