import argparse
import sys
import os

from twitter_agent.src import twitter_client, ai_client

def main():
    parser = argparse.ArgumentParser(description="Generate and post a tweet about a given topic using the fine-tuned model.")
    parser.add_argument('--topic', type=str, required=True, help='Topic to tweet about')
    parser.add_argument('--long', action='store_true', help='Generate a long tweet (up to 4000 characters)')
    args = parser.parse_args()

    topic = args.topic.strip()
    if not topic:
        print("Error: You must provide a topic.")
        sys.exit(1)

    feedback = None
    while True:
        print(f"Generating tweet about: {topic}")
        tweet_text = ai_client.generate_topic_tweet(topic, long=args.long, feedback=feedback)
        if not tweet_text:
            print("Failed to generate tweet.")
            sys.exit(1)
        print(f"Generated tweet:\n{tweet_text}")

        user_feedback = input("Feedback for the AI (or press Enter to accept and post, 'r' to regenerate, 'n' to abort): ").strip()
        if user_feedback == 'n':
            print("Aborted by user.")
            sys.exit(0)
        elif user_feedback == 'r':
            print("Regenerating tweet...")
            feedback = None
            continue
        elif user_feedback:
            print("Regenerating tweet with your feedback...")
            feedback = user_feedback
            continue
        else:
            # Accept and post
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

def get_my_username():
    client = twitter_client.get_twitter_client()
    user = client.get_me().data
    return user.username if hasattr(user, 'username') else 'me'

if __name__ == "__main__":
    main() 