# Twitter Agent

This directory contains the core scripts and modules for the AI-powered Twitter reply agent.

## Main Script
- `scripts/reply_to_tweet.py`: The main entry point for fetching tweets from your home timeline and generating AI-powered replies.

## Features
- Fetches and displays tweets with engagement metrics and direct links
- Clearly labels retweets
- Uses OpenAI (fine-tuned) to generate original, on-brand replies
- Interactive feedback loop for refining replies
- Avoids duplicate or near-duplicate tweets
- Logs all attempts and accepted replies for future optimization

## Setup
- See the top-level `README.md` for setup and usage instructions.
- Copy `config/.env.example` to `.env` and fill in your API keys.

## Data
- Only essential data files are tracked: `data/attempted_replies.jsonl` and your main tweet history jsonl.
- All other data (timelines, web corpus, etc.) are ignored by `.gitignore`.

## Documentation
- **All documentation in this directory must be kept up to date with code and workflow changes.**
- This is required by `.cursorrules`.

## License
Specify your license here. 