"""
Services for the Governance Trading Bot.

This package contains external services integration such as
notifications, messaging, and third-party APIs.
"""

from .slack_bot import SlackBot

# Define standalone functions for backward compatibility
def post_to_slack(message):
    """Post a message to Slack using the SlackBot class."""
    bot = SlackBot()
    return bot.post_to_slack(message)

def post_error_to_slack(error_message):
    """Post an error message to Slack using the SlackBot class."""
    bot = SlackBot()
    return bot.post_error_to_slack(error_message)

__all__ = ['SlackBot', 'post_to_slack', 'post_error_to_slack'] 