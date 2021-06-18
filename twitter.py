import os
import tweepy
import logging


logger = logging.getLogger('discord.' + __name__)

# Authenticate to Twitter
auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")

# Create API object
api = tweepy.API(auth)


def tweet(message):
    """Create a tweet"""
    return api.update_status(message)
