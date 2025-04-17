import os
import sys
import argparse
from dotenv import load_dotenv
import json
from datetime import datetime
import difflib

# Robust import handling for both direct and module execution
try:
    from twitter_agent.src import twitter_client, ai_client
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
    import twitter_client
    import ai_client

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../config/.env'))

def fetch_home_timeline(n=10):
    client = twitter_client.get_twitter_client()
    timeline = client.get_home_timeline(
        max_results=n * 2,  # Fetch more to allow for filtering
        tweet_fields=['created_at', 'public_metrics', 'conversation_id', 'author_id', 'referenced_tweets'],
        expansions=['author_id', 'referenced_tweets.id'],
        user_fields=['username', 'name']
    )
    tweets = []
    users = {}
    referenced_tweets = {}
    # Build user lookup
    if hasattr(timeline, 'includes') and 'users' in timeline.includes:
        for user in timeline.includes['users']:
            users[user.id] = {
                'username': user.username,
                'name': user.name
            }
    # Build referenced tweet lookup (for retweets/quotes)
    if hasattr(timeline, 'includes') and 'tweets' in timeline.includes:
        for ref_tweet in timeline.includes['tweets']:
            referenced_tweets[ref_tweet.id] = ref_tweet.text
    for tweet in timeline.data:
        # Detect tweet type
        tweet_type = 'original'
        full_text = tweet.text
        quoted_text = None
        if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
            for ref in tweet.referenced_tweets:
                if ref.type == 'retweeted':
                    tweet_type = 'retweet'
                    if ref.id in referenced_tweets:
                        full_text = referenced_tweets[ref.id]
                elif ref.type == 'quoted':
                    tweet_type = 'quote'
                    quoted_text = referenced_tweets.get(ref.id)
                elif ref.type == 'replied_to':
                    tweet_type = 'reply'
        author_info = users.get(tweet.author_id, {})
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
        engagement = (
            metrics.get('like_count', 0) +
            metrics.get('reply_count', 0) +
            metrics.get('retweet_count', 0) +
            metrics.get('quote_count', 0)
        )
        tweet_dict = {
            'id': tweet.id,
            'text': full_text,
            'author_username': author_info.get('username', 'unknown'),
            'author_name': author_info.get('name', 'unknown'),
            'created_at': str(tweet.created_at),
            'engagement': engagement,
            'metrics': metrics,
            'type': tweet_type
        }
        if quoted_text:
            tweet_dict['quoted_text'] = quoted_text
        tweets.append(tweet_dict)
    # Sort by engagement, descending
    tweets = sorted(tweets, key=lambda t: t['engagement'], reverse=True)
    # Only return top n
    return tweets[:n]

def post_reply(reply_text, tweet_id):
    disclaimer = "\n\n(This reply was AI generated based on my personality.)"
    reply_text = reply_text.strip() + disclaimer
    try:
        resp = twitter_client.post_tweet(reply_text, reply_to_id=tweet_id)
        new_tweet_id = resp.data['id'] if hasattr(resp, 'data') and 'id' in resp.data else None
        return new_tweet_id
    except Exception as e:
        print(f"Error posting reply: {e}")
        return None

def load_tweet_examples(tweet_file='data/tweets/kjameslubin_all_tweets_20250415_003953.jsonl', n=3):
    examples = []
    try:
        with open(tweet_file, 'r') as f:
            for line in f:
                if len(examples) >= n:
                    break
                data = json.loads(line)
                examples.append(data['text'])
    except Exception:
        pass
    return examples

def load_accepted_replies(reply_file='data/attempted_replies.jsonl', n=3):
    examples = []
    try:
        with open(reply_file, 'r') as f:
            for line in f:
                if len(examples) >= n:
                    break
                data = json.loads(line)
                if data.get('status') == 'accepted':
                    examples.append(data['final_reply'])
    except Exception:
        pass
    return examples

def build_system_prompt(tweet_examples, reply_examples):
    style = (
        "You are replying as Kieren (@kjameslubin).\n"
        "\n"
        "First, generate an interesting, original tweet in response to the context.\n"
        "Then, rewrite it to match Kieren's style and interests as described below.\n"
        "Do NOT copy or repeat exact phrases from past tweets. Synthesize new replies that reflect the user's interests, topics, and style.\n"
        "\n"
        "Topics & Interests:\n"
        "- Crypto, DeFi, blockchain technology, appchains\n"
        "- Market structure, cycles, technical analysis\n"
        "- Regulation, policy, skepticism about hype or authority\n"
        "- AI, automation, and software development\n"
        "- Free speech, censorship, and civil liberties\n"
        "- Economics, business cycles, macro trends\n"
        "- Dry or understated humor\n"
        "- Radio shows, podcasts, live events\n"
        "- Social media, tech, and internet culture\n"
        "- Startups, building, and coding\n"
        "- Commentary on news, politics, and current events\n"
        "- Fitness (especially sprinting and lifting)\n"
        "- General achievement, management, discipline, and personal growth\n"
        "- Music and movies, especially of the 90s era\n"
        "\n"
        "Style Guide:\n"
        "- Concise, direct, and to the point.\n"
        "- Dry, sometimes wry or understated humor.\n"
        "- Skeptical, but not cynical—often reality-checking or qualifying claims.\n"
        "- Analytical, but not verbose; prefers clarity over flourish.\n"
        "- Not afraid to ask questions or challenge assumptions.\n"
        "- Rarely, if ever, uses hashtags, emojis, or exclamation points.\n"
        "- Avoids platitudes, hype, and excessive enthusiasm.\n"
        "- Sometimes uses 'TIL', 'RT', or 'Live now:' for context, but not as a meme.\n"
        "- Will reference data, cycles, or market structure, but not in a 'guru' tone.\n"
        "\n"
        "Content Patterns:\n"
        "- Replies often start with a direct address ('@user') and a short, specific point.\n"
        "- Will admit uncertainty or partial knowledge ('maybe', 'I think', 'worth a shot', 'not sure').\n"
        "- Uses qualifiers ('probably', 'maybe', 'sort of', 'a little bit', 'to some degree').\n"
        "- Will reference personal experience or observation, but not in a self-promotional way.\n"
        "- Will sometimes use dry humor or a rhetorical question to make a point.\n"
        "- Will reference news, market events, or technical details, but not in a 'breaking news' style.\n"
        "- Will sometimes use 'joking', 'just a thought', or 'worth acknowledging' to soften a take.\n"
        "\n"
        "Formatting:\n"
        "- No hashtags.\n"
        "- No emoji (except when quoting others).\n"
        "- No 'thread' or '1/' style tweets.\n"
        "- No 'hot take' or 'bold prediction' language.\n"
        "- No 'inspirational' or 'motivational' tropes.\n"
        "\n"
        "Summary:\n"
        "- Be concise, dry, and reality-checking.\n"
        "- Use direct address and specific points in replies.\n"
        "- Admit uncertainty when appropriate.\n"
        "- Never use hashtags, emojis, or hype language.\n"
        "- Avoid platitudes, excessive enthusiasm, or 'inspirational' tropes.\n"
        "- If in doubt, err on the side of brevity and skepticism.\n"
    )
    prompt = style
    if tweet_examples:
        prompt += "\nHere are some of your real tweets as examples:\n"
        for t in tweet_examples:
            prompt += f"- {t}\n"
    if reply_examples:
        prompt += "\nHere are some of your accepted replies as examples:\n"
        for r in reply_examples:
            prompt += f"- {r}\n"
    return prompt

def generate_ai_reply(tweet_text, feedback=None):
    print("\nGenerating AI reply...")
    try:
        tweet_examples = load_tweet_examples()
        reply_examples = load_accepted_replies()
        system_prompt = build_system_prompt(tweet_examples, reply_examples)
        prompt = system_prompt + "\n\n" + tweet_text
        if feedback:
            prompt += f"\n\nFeedback: {feedback}"
        response = ai_client.generate_tweet_reply(prompt)
        if response and response.get('respond', False):
            return response.get('reply', '').strip()
    except Exception as e:
        print(f"AI error: {e}")
    return ''

def log_attempt(original_tweet, ai_reply, user_feedback, final_reply, status=None):
    os.makedirs('data', exist_ok=True)
    log_path = 'data/attempted_replies.jsonl'
    # If no status is provided, set to 'rejected' if final_reply is empty, else 'accepted'
    if status is None:
        status = 'accepted' if final_reply else 'rejected'
    record = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'original_tweet': original_tweet,
        'ai_reply': ai_reply,
        'user_feedback': user_feedback,
        'final_reply': final_reply,
        'status': status
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(record) + '\n')

def is_near_duplicate(reply, past_tweets, threshold=0.7):
    for past in past_tweets:
        ratio = difflib.SequenceMatcher(None, reply.strip().lower(), past.strip().lower()).ratio()
        if ratio >= threshold:
            return True, past
    return False, None

def handle_manual_reply(tweet, ai_reply, feedback):
    manual_reply = input("Enter your reply: ").strip()
    if manual_reply:
        final_reply = manual_reply  # Do NOT append disclaimer here
        confirm = input(f"\nPost this manual reply? (y/n): {final_reply}\n").strip().lower()
        if confirm == 'y':
            new_tweet_id = post_reply(final_reply, tweet['id'])
            if new_tweet_id:
                print(f"Reply posted: https://twitter.com/{get_my_username()}/status/{new_tweet_id}")
                log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
            else:
                print("Reply posted, but could not retrieve tweet ID.")
                log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
            return True
        else:
            print("Aborted by user.")
            log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'rejected')
            return True
    else:
        print("No manual reply provided. Returning to feedback loop.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Reply to a tweet from your home timeline or a specific tweet by ID.")
    parser.add_argument('--tweet-id', type=str, help='ID of the tweet to reply to (headless or direct mode)')
    parser.add_argument('--tweet-text', type=str, help='Text of the tweet to reply to (optional, for direct mode)')
    parser.add_argument('--reply', type=str, help='Reply text (headless mode)')
    parser.add_argument('--index', type=int, help='Index of tweet in timeline to reply to (headless mode)')
    parser.add_argument('--count', type=int, default=5, help='Number of tweets to show per page from home timeline')
    parser.add_argument('--batch-size', type=int, default=30, help='Total number of tweets to fetch in one batch')
    args = parser.parse_args()

    try:
        if args.tweet_id:
            # Direct mode: reply to a specific tweet by ID
            tweet_id = args.tweet_id
            if args.tweet_text:
                tweet_text = args.tweet_text
            else:
                # Fetch tweet text using Twitter API
                client = twitter_client.get_twitter_client()
                tweet_obj = client.get_tweet(tweet_id, tweet_fields=["text", "author_id", "created_at"])
                tweet_data = tweet_obj.data
                tweet_text = tweet_data.text if hasattr(tweet_data, 'text') else ''
                author_id = tweet_data.author_id if hasattr(tweet_data, 'author_id') else 'unknown'
                created_at = str(tweet_data.created_at) if hasattr(tweet_data, 'created_at') else ''
                print(f"\nSelected tweet (ID: {tweet_id}):\n{tweet_text}\nAuthor ID: {author_id} | Created at: {created_at}")
            # Interactive feedback loop (same as timeline)
            feedback = None
            radical_attempts = 0
            while True:
                ai_reply = generate_ai_reply(tweet_text, feedback)
                if ai_reply:
                    print(f"\nAI-generated reply:\n{ai_reply}")
                else:
                    print("\nAI could not generate a reply. You can enter your own.")
                    log_attempt(tweet_text, ai_reply, feedback, '', 'no_ai_reply')
                    ai_reply = ''
                user_feedback = input("Feedback for the AI (or press Enter to accept and post this reply, or type 'new' for a radically different attempt, or 'manual' to write your own reply): ").strip().lower()
                if user_feedback in ['manual', 'm']:
                    if handle_manual_reply(tweet_text, ai_reply, feedback):
                        return
                    else:
                        continue
                if user_feedback == 'new':
                    feedback = None
                    radical_attempts += 1
                    if radical_attempts > 3:
                        print("Tried 3 radically different replies. Please provide feedback or enter your own reply.")
                        user_feedback = input("Feedback for the AI (or press Enter to accept and post this reply, or 'manual' to write your own reply): ").strip().lower()
                        if user_feedback in ['manual', 'm']:
                            if handle_manual_reply(tweet_text, ai_reply, feedback):
                                return
                            else:
                                continue
                        if not user_feedback:
                            final_reply = ai_reply
                            if not final_reply:
                                print("No reply provided. Exiting.")
                                log_attempt(tweet_text, ai_reply, feedback, '', 'rejected')
                                return
                            confirm = input(f"\nPost this reply? (y/n): {final_reply}\n").strip().lower()
                            if confirm == 'y':
                                new_tweet_id = post_reply(final_reply, tweet_id)
                                if new_tweet_id:
                                    print(f"Reply posted: https://twitter.com/{get_my_username()}/status/{new_tweet_id}")
                                    log_attempt(tweet_text, ai_reply, feedback, final_reply, 'accepted')
                                else:
                                    print("Reply posted, but could not retrieve tweet ID.")
                                    log_attempt(tweet_text, ai_reply, feedback, final_reply, 'accepted')
                                return
                            else:
                                print("Aborted by user.")
                                log_attempt(tweet_text, ai_reply, feedback, final_reply, 'rejected')
                                return
                        else:
                            log_attempt(tweet_text, ai_reply, feedback, '', 'rejected')
                            feedback = user_feedback
                            continue
                    continue
                if not user_feedback:
                    final_reply = ai_reply
                    if not final_reply:
                        print("No reply provided. Exiting.")
                        log_attempt(tweet_text, ai_reply, feedback, '', 'rejected')
                        return
                    confirm = input(f"\nPost this reply? (y/n): {final_reply}\n").strip().lower()
                    if confirm == 'y':
                        new_tweet_id = post_reply(final_reply, tweet_id)
                        if new_tweet_id:
                            print(f"Reply posted: https://twitter.com/{get_my_username()}/status/{new_tweet_id}")
                            log_attempt(tweet_text, ai_reply, feedback, final_reply, 'accepted')
                        else:
                            print("Reply posted, but could not retrieve tweet ID.")
                            log_attempt(tweet_text, ai_reply, feedback, final_reply, 'accepted')
                        return
                    else:
                        print("Aborted by user.")
                        log_attempt(tweet_text, ai_reply, feedback, final_reply, 'rejected')
                        return
                else:
                    log_attempt(tweet_text, ai_reply, feedback, '', 'rejected')
                    feedback = user_feedback
            return

        # Interactive mode with local batch paging
        batch_size = args.batch_size
        page_size = args.count
        all_tweets = fetch_home_timeline(batch_size)
        if not all_tweets:
            print("No tweets found in your home timeline.")
            return
        shown = 0
        total = len(all_tweets)
        while shown < total:
            page = all_tweets[shown:shown+page_size]
            print(f"\nTweets {shown+1}-{min(shown+page_size, total)} of {total} (sorted by engagement):")
            for i, t in enumerate(page):
                idx = shown + i
                tweet_type = t.get('type', '')
                prefix = ''
                if tweet_type == 'retweet':
                    prefix = '[RT] '
                elif tweet_type == 'quote':
                    prefix = '[QT] '
                elif tweet_type == 'reply':
                    prefix = '[RE] '
                tweet_link = f"https://twitter.com/{t['author_username']}/status/{t['id']}" if t.get('author_username') and t.get('id') else ''
                print(f"[{idx}] @{t['author_username']} ({t['author_name']}) at {t['created_at']} | Engagement: {t['engagement']} (Likes: {t['metrics'].get('like_count', 0)}, Replies: {t['metrics'].get('reply_count', 0)}, RTs: {t['metrics'].get('retweet_count', 0)}, Quotes: {t['metrics'].get('quote_count', 0)})\n{prefix}{t['text']}")
                if t.get('quoted_text'):
                    print(f"  [Quoted] {t['quoted_text']}")
                print(f"{tweet_link}\n")
            shown += page_size
            if shown < total:
                more = input(f"Show more tweets? (y/n): ").strip().lower()
                if more == 'y':
                    continue
                else:
                    break
            else:
                break
        idx = args.index if args.index is not None else int(input(f"Select tweet to reply to [0-{total-1}]: "))
        tweet = all_tweets[idx]
        print(f"\nSelected tweet by @{tweet['author_username']}:")
        print(tweet['text'])

        # Interactive feedback loop
        feedback = None
        radical_attempts = 0
        past_tweets = load_tweet_examples(n=100)
        while True:
            ai_reply = generate_ai_reply(tweet['text'], feedback)
            if ai_reply:
                reply_text = ai_reply if isinstance(ai_reply, str) else ai_reply.get('reply', '')
                is_dup, dup_text = is_near_duplicate(reply_text, past_tweets)
                if is_dup:
                    print("[WARNING] AI reply is very similar to a past tweet:")
                    print(f"AI reply: {reply_text}")
                    print(f"Past tweet: {dup_text}")
                print(f"\nAI-generated reply:\n{reply_text}")
            else:
                print("\nAI could not generate a reply. You can enter your own.")
                log_attempt(tweet['text'], ai_reply, feedback, '', 'no_ai_reply')
                reply_text = ''
            print(f"\nAI-generated reply:\n{reply_text}")
            user_feedback = input("Feedback for the AI (or press Enter to accept and post this reply, type 'new' for a radically different attempt, or 'manual' to write your own reply): ").strip().lower()
            if user_feedback in ['manual', 'm']:
                if handle_manual_reply(tweet, ai_reply, feedback):
                    return
                else:
                    continue
            if user_feedback == 'new':
                feedback = None
                radical_attempts += 1
                if radical_attempts > 3:
                    print("Tried 3 radically different replies. Please provide feedback or enter your own reply.")
                    user_feedback = input("Feedback for the AI (or press Enter to accept and post this reply, or 'manual' to write your own reply): ").strip().lower()
                    if user_feedback in ['manual', 'm']:
                        if handle_manual_reply(tweet, ai_reply, feedback):
                            return
                        else:
                            continue
                    if not user_feedback:
                        final_reply = reply_text
                        if not final_reply:
                            print("No reply provided. Exiting.")
                            log_attempt(tweet['text'], ai_reply, feedback, '', 'rejected')
                            return
                        confirm = input(f"\nPost this reply? (y/n): {final_reply}\n").strip().lower()
                        if confirm == 'y':
                            new_tweet_id = post_reply(final_reply, tweet['id'])
                            if new_tweet_id:
                                print(f"Reply posted: https://twitter.com/{get_my_username()}/status/{new_tweet_id}")
                                log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
                            else:
                                print("Reply posted, but could not retrieve tweet ID.")
                                log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
                            return
                        else:
                            print("Aborted by user.")
                            log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'rejected')
                            return
                    else:
                        log_attempt(tweet['text'], ai_reply, feedback, '', 'rejected')
                        feedback = user_feedback
                        continue
                continue
            if not user_feedback:
                final_reply = reply_text
                if not final_reply:
                    print("No reply provided. Exiting.")
                    log_attempt(tweet['text'], ai_reply, feedback, '', 'rejected')
                    return
                confirm = input(f"\nPost this reply? (y/n): {final_reply}\n").strip().lower()
                if confirm == 'y':
                    new_tweet_id = post_reply(final_reply, tweet['id'])
                    if new_tweet_id:
                        print(f"Reply posted: https://twitter.com/{get_my_username()}/status/{new_tweet_id}")
                        log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
                    else:
                        print("Reply posted, but could not retrieve tweet ID.")
                        log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'accepted')
                    return
                else:
                    print("Aborted by user.")
                    log_attempt(tweet['text'], ai_reply, feedback, final_reply, 'rejected')
                    return
            else:
                log_attempt(tweet['text'], ai_reply, feedback, '', 'rejected')
                feedback = user_feedback
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

def get_my_username():
    client = twitter_client.get_twitter_client()
    user = client.get_me().data
    return user.username if hasattr(user, 'username') else 'me'

if __name__ == "__main__":
    main() 