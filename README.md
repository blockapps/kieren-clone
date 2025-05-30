# kieren-clone

A Twitter reply agent that uses AI to generate and post replies to tweets from your home timeline, matching your style, interests, and tone.

## Features
- Fetches tweets from your home timeline
- Uses OpenAI (fine-tuned) to generate original, on-brand replies
- Interactive feedback loop for refining replies
- Avoids duplicate or near-duplicate tweets
- Logs all attempts and accepted replies for future optimization
- Only core data files are tracked in version control

## Setup
1. Clone the repository
2. Create and activate a Python virtual environment (`python3 -m venv venv && source venv/bin/activate`)
3. Install dependencies: `pip install -r twitter_agent/requirements.txt`
4. Copy `twitter_agent/config/.env.example` to `.env` and fill in your API keys
5. Run the main script:
   ```
   python3 -m twitter_agent.scripts.reply_to_tweet --count 5 --batch-size 30
   ```

## Usage
- The script will fetch tweets, display them with engagement and links, and let you select one to reply to.
- The AI will generate a reply, and you can accept, reject, or provide feedback for a new attempt.
- Retweets are clearly labeled, and each tweet includes a direct link.

## Data
- Only essential data files are tracked: `data/attempted_replies.jsonl` and your main tweet history jsonl.
- All other data (timelines, web corpus, etc.) are ignored by `.gitignore`.

## Documentation
- All documentation (including this README and the agent's internal README) should be kept up to date with code and workflow changes.
- See `.cursorrules` for documentation and code quality requirements.

## License
Specify your license here.

# How to Run Scripts

All scripts should be run as modules from the project root to ensure imports work correctly.

## Reply to Tweets from Your Timeline

Fetch tweets from your home timeline and interactively generate replies:

```sh
python3 -m twitter_agent.scripts.reply_to_tweet --batch-size 30
```

- Use `--batch-size` to control how many tweets are fetched for reply selection.
- Follow the interactive prompts to select a tweet and generate/post a reply.

## Generate and Post a Tweet About a Topic

Generate a tweet about a specific topic (with approval and regenerate options):

```sh
python3 -m twitter_agent.scripts.tweet_about_topic --topic "the record high gold price"
```

- You will be shown a generated tweet and prompted to approve, abort, or regenerate.
- If you approve, the tweet will be posted with a disclaimer.

---

**Note:**
- Always run scripts with `python3 -m ...` from the project root for reliable import behavior.
- If you encounter import errors, ensure you are in the project root and using the `-m` flag. 