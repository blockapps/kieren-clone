try:
    import tweepy
except ImportError as e:
    if "No module named 'imghdr'" in str(e):
        # In Python 3.13, imghdr was removed
        import sys
        import types
        
        # Create a dummy imghdr module
        imghdr = types.ModuleType('imghdr')
        
        def what(file, h=None):
            return None
        
        imghdr.what = what
        sys.modules['imghdr'] = imghdr
        
        # Now try importing tweepy again
        import tweepy
    else:
        raise

from . import config

def get_twitter_client():
    """
    Create and return a Twitter API v2 client.
    """
    client = tweepy.Client(
        bearer_token=config.TWITTER_BEARER_TOKEN,
        consumer_key=config.TWITTER_API_KEY,
        consumer_secret=config.TWITTER_API_SECRET,
        access_token=config.TWITTER_ACCESS_TOKEN,
        access_token_secret=config.TWITTER_ACCESS_SECRET
    )
    return client

def search_tweets(query=None, max_results=None):
    """
    Search for recent tweets matching the query.
    
    Args:
        query (str): The search query (default: from config)
        max_results (int): Maximum number of results to return (default: from config)
        
    Returns:
        list: List of tweet objects
    """
    client = get_twitter_client()
    
    if query is None:
        query = config.SEARCH_QUERY
    
    if max_results is None:
        max_results = config.MAX_TWEETS_PER_SEARCH
    
    tweets = client.search_recent_tweets(
        query=query,
        max_results=max_results,
        tweet_fields=['author_id', 'created_at', 'public_metrics']
    )
    
    return tweets.data if tweets.data else []

def post_tweet(text, reply_to_id=None):
    """
    Post a new tweet or reply to an existing tweet.
    
    Args:
        text (str): The tweet text
        reply_to_id (str, optional): Tweet ID to reply to
        
    Returns:
        tweepy.Response: The response from the Twitter API
    """
    client = get_twitter_client()
    
    if reply_to_id:
        response = client.create_tweet(
            text=text,
            in_reply_to_tweet_id=reply_to_id
        )
    else:
        response = client.create_tweet(text=text)
    
    return response

def get_tweet_by_id(tweet_id):
    """
    Get a tweet by its ID.
    
    Args:
        tweet_id (str): The tweet ID
        
    Returns:
        dict: The tweet data
    """
    client = get_twitter_client()
    
    response = client.get_tweet(
        tweet_id,
        tweet_fields=['author_id', 'created_at', 'public_metrics', 'text']
    )
    
    return response.data if response.data else None 