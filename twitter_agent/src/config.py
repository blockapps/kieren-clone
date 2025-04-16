import os
from dotenv import load_dotenv

# Load environment variables from the config directory
config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
dotenv_path = os.path.join(config_dir, '.env')
load_dotenv(dotenv_path)

# Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# OpenAI API credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Bot configuration
SEARCH_QUERY = os.getenv("SEARCH_QUERY", "(DeFi OR blockchain OR crypto) lang:en -is:retweet")
MAX_TWEETS_PER_SEARCH = int(os.getenv("MAX_TWEETS_PER_SEARCH", 10))
REPLY_PROBABILITY = float(os.getenv("REPLY_PROBABILITY", 0.8))
POST_ORIGINAL_PROBABILITY = float(os.getenv("POST_ORIGINAL_PROBABILITY", 0.2))
SCHEDULE_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", 60))

# System prompts
RELEVANCE_PROMPT = """
You are emulating Kieren's tone and style: analytical, concise, insightful, occasionally humorous.
Given the following tweet, determine if Kieren would reply to it.

If YES:
- Provide a short, engaging reply tweet (280 characters max).
- Label as {{"respond": true, "reply": "<text>"}}

If NO:
- Label as {{"respond": false}}

Tweet: "{tweet_text}"
"""

ORIGINAL_TWEET_PROMPT = """
You're tweeting as Kieren—CEO, blockchain expert, concise, analytical.
Write a standalone insightful tweet about DeFi market trends or blockchain innovations. Max 280 characters.
""" 