import argparse
import sys
import os

from twitter_agent.src import twitter_client, ai_client

def main():
    parser = argparse.ArgumentParser(description="Generate and post a tweet about a given topic using the fine-tuned model.")
    parser.add_argument('--topic', type=str, required=True, help='Topic to tweet about')
    args = parser.parse_args()

    topic = args.topic.strip()
    if not topic:
        print("Error: You must provide a topic.")
        sys.exit(1)

    while True:
        print(f"Generating tweet about: {topic}")
        tweet_text = ai_client.generate_topic_tweet(topic)
        if not tweet_text:
            print("Failed to generate tweet.")
            sys.exit(1)
        print(f"Generated tweet:\n{tweet_text}")

        # Approval flow with regenerate option
        confirm = input(f"\nPost this tweet? (y = post, n = abort, r = regenerate): {tweet_text}\n").strip().lower()
        if confirm == 'y':
            # Add disclaimer
            disclaimer = "\n\n(This tweet was AI generated based on my personality.)"
            tweet_text += disclaimer
            try:
                response = twitter_client.post_tweet(tweet_text)
                tweet_id = response.data['id'] if hasattr(response, 'data') and 'id' in response.data else None
                print(f"Successfully posted tweet! Tweet ID: {tweet_id}")
                print(f"Link: https://twitter.com/{get_my_username()}/status/{tweet_id}")
            except Exception as e:
                print(f"Error posting tweet: {e}")
                sys.exit(1)
            break
        elif confirm == 'n':
            print("Aborted by user.")
            sys.exit(0)
        elif confirm == 'r':
            print("Regenerating tweet...")
            continue
        else:
            print("Invalid input. Please enter 'y', 'n', or 'r'.")
            continue

def get_my_username():
    client = twitter_client.get_twitter_client()
    user = client.get_me().data
    return user.username if hasattr(user, 'username') else 'me'

if __name__ == "__main__":
    main() 