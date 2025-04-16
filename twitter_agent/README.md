# Kieren Twitter Agent

An intelligent Twitter agent that authentically represents Kieren's voice and thinking style to grow his audience and influence through strategic engagement.

## Overview

This project creates an autonomous Twitter agent that:
- Finds relevant conversations in your domain
- Responds in your authentic voice and thought patterns
- Posts original insights on your behalf
- Strategically grows your audience and influence

## Key Features

- **Authentic Voice Replication**: Uses advanced LLM prompting to genuinely capture your unique perspective and communication style
- **Intelligent Filtering**: Multi-tiered system to find high-value engagement opportunities while minimizing API costs
- **Strategic Growth**: Targets influential accounts and conversations for maximum impact
- **Performance Analytics**: Tracks effectiveness and continuously improves targeting
- **Economic Operation**: Optimizes API usage through intelligent filtering and caching

## Project Structure

- `src/`: Core modules for the Twitter agent
  - `config.py`: Configuration management
  - `twitter_client.py`: Twitter API interactions
  - `ai_client.py`: OpenAI API interactions
  - `bot.py`: Main bot logic
  - `filters/`: Tweet filtering system
  - `analytics/`: Performance tracking
- `scripts/`: Executable scripts
  - `run_bot.py`: Runs the bot continuously or once
  - `test_bot.py`: Tests AI response generation
- `config/`: Configuration files
  - `.env`: Environment variables and API keys
- `data/`: Training data and examples
  - `tweets/`: Example tweets and responses
  - `style_guide.md`: Kieren's voice and thinking patterns

## Approach

Our implementation follows a phased approach:

1. **Foundation Phase**: Collect examples of your writing, develop filtering system, implement basic functionality
2. **Training Phase**: Build a comprehensive model of your thinking and communication style 
3. **Supervised Operation**: Begin engagement with high oversight, gather performance data
4. **Optimization**: Refine targeting and prompting based on real-world results

For full details, see [APPROACH.md](APPROACH.md) and [BENEFITS.md](BENEFITS.md).

## Setup

### Prerequisites

- Python 3.8+
- Twitter Developer Account with API access
- OpenAI API key

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy the example environment file:
   ```
   cp config/.env.example config/.env
   ```
4. Edit the `.env` file with your API keys and configuration

## Usage

### Run Once

To run the bot once and exit:

```
python scripts/run_bot.py --run-once
```

### Run Continuously

To run the bot on a scheduled interval:

```
python scripts/run_bot.py --interval 60
```

### Test Without Posting

To test how the bot would respond to a tweet without posting:

```
python scripts/test_bot.py --reply "DeFi still feels too complicated for the average user. Thoughts?"
```

## Configuration

Edit the values in your `.env` file to customize the bot behavior:

- `SEARCH_QUERY`: The Twitter search query for finding relevant tweets
- `MAX_TWEETS_PER_SEARCH`: Maximum number of tweets to retrieve per search
- `REPLY_PROBABILITY`: Probability (0-1) of replying to a relevant tweet
- `POST_ORIGINAL_PROBABILITY`: Probability (0-1) of posting an original tweet per cycle
- `SCHEDULE_INTERVAL_MINUTES`: How often to run the bot (in minutes)

## License

MIT 