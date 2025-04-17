import json
import openai
import sys
import os
from twitter_agent.src.personality import get_personality_and_style_guide
try:
    from . import config
except ImportError:
    import config

# Set OpenAI API key
openai.api_key = config.OPENAI_API_KEY

def generate_tweet_reply(tweet_text, feedback=None):
    """
    Generate a reply to a tweet using the fine-tuned GPT-4 model.
    
    Args:
        tweet_text (str): The text of the tweet to respond to
        feedback (str): Optional user feedback for improvement
        
    Returns:
        dict: JSON response with 'respond' and possibly 'reply' fields
    """
    try:
        reminder = (
            "\n\nIMPORTANT: Your response MUST be a single line of valid JSON in the format {\"respond\": true/false, \"reply\": \"<text>\"}. "
            "Do NOT retweet, quote tweet, or use 'RT @' or similar. Only mention users if directly replying to them. "
            "Prefer standalone, original replies. Do not copy or repeat exact phrases from past tweets. "
            "Do NOT reply to the wrong person. Do NOT use hashtags, emojis, or reply formatting unless directly replying. "
            "If you would not reply, return {\"respond\": false}. Otherwise, return {\"respond\": true, \"reply\": \"<your reply>\"}. "
            "Never output anything except the JSON object."
        )
        prompt = (
            config.RELEVANCE_PROMPT.format(tweet_text=tweet_text)
            + reminder
        )
        if feedback:
            prompt += f"\n\nUser feedback for improvement: {feedback}"
        response = openai.chat.completions.create(
            model="ft:gpt-4.1-mini-2025-04-14:blockapps::BN4Ftmd0",
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        content = response.choices[0].message.content.strip()
        print("[DEBUG] Raw OpenAI response:", response)
        print("[DEBUG] Parsed content:", content)
        
        # Try to parse JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If not valid JSON, but non-empty, treat as reply
            if content:
                print("[WARNING] AI reply not in expected JSON format. Showing raw reply for approval.")
                return {"respond": True, "reply": content}
            else:
                return {"respond": False}
                
    except Exception as e:
        print(f"Error generating reply: {e}")
        return {"respond": False}

def generate_topic_tweet(topic, long=False, feedback=None):
    """
    Generate an original tweet about a given topic, with no user mentions or reply formatting.
    Args:
        topic (str): The topic to tweet about
        long (bool): If True, generate a longer, more detailed tweet (up to 4000 characters)
        feedback (str): Optional user feedback to guide the tweet
    Returns:
        str: The generated tweet text
    """
    try:
        style_guide = get_personality_and_style_guide()
        if long:
            prompt = (
                f"Write a long, detailed tweet (up to 4000 characters) about {topic}. "
                "Make a clear point, support it with arguments, and include links or citations to relevant sources if possible. "
                "Do not mention or tag any users. Do not use @ or reply formatting. "
                "Do not retweet, quote tweet, or use 'RT @' or similar. "
                "Do not copy or repeat exact phrases from past tweets—generate a fresh, original statement that matches my style. "
                "Make it a standalone statement. Match my style."
            )
            max_tokens = 2000
            char_limit = 4000
        else:
            prompt = (
                f"Write an original tweet about {topic}. "
                "Do not mention or tag any users. Do not use @ or reply formatting. "
                "Do not retweet, quote tweet, or use 'RT @' or similar. "
                "Do not copy or repeat exact phrases from past tweets—generate a fresh, original statement that matches my style. "
                "Make it a standalone statement. Match my style."
            )
            max_tokens = 100
            char_limit = 280
        if feedback:
            prompt += f"\n\nFeedback for improvement: {feedback}"
        response = openai.chat.completions.create(
            model="ft:gpt-4.1-mini-2025-04-14:blockapps::BN4Ftmd0",
            messages=[
                {"role": "system", "content": style_guide},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=max_tokens
        )
        tweet_text = response.choices[0].message.content.strip()
        if len(tweet_text) > char_limit:
            tweet_text = tweet_text[:char_limit-3] + "..."
        return tweet_text
    except Exception as e:
        print(f"Error generating topic tweet: {e}")
        return None

def generate_original_tweet():
    """
    Generate an original tweet about everyone being a bond yield expert, with no user mentions.
    Returns:
        str: The generated tweet text
    """
    return generate_topic_tweet("the fact that everyone is a bond yield expert now") 