#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys

# Add the parent directory to sys.path for direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import get_config

class SlackBot:
    """
    Class for sending notifications to Slack channels via webhook.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the SlackBot with configuration.
        
        Args:
            config_path (str): Path to the configuration file (not used if using env vars)
        """
        # Load configuration from environment variables
        config = get_config().config
        
        # Extract webhook URL from config
        self.webhook_url = config.get('slack_webhook_url')
    
    def post_to_slack(self, message):
        """
        Post a formatted message to Slack.
        
        Args:
            message (dict): Dictionary containing the message to post
        """
        # Convert message dictionary to a string with each key-value on a new line
        formatted_message = "\n".join([f"{key}: {value}" for key, value in message.items()])
        
        # Create the payload to send to Slack
        payload = {
            "text": formatted_message  # Message to send to Slack
        }
        
        try:
            # Send a POST request to the Slack webhook URL
            response = requests.post(self.webhook_url, json=payload)
        
            # Check if the request was successful
            if response.status_code == 200:
                print("Message posted successfully")
            else:
                print(f"Failed to post message: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"Error posting message: {e}")
    
    def post_error_to_slack(self, error_message):
        """
        Post an error message to Slack.
        
        Args:
            error_message (str): Error message to post
        """
        payload = {
            "text": error_message  # Message to send to Slack
        }
        
        try:
            # Send a POST request to the Slack webhook URL
            response = requests.post(self.webhook_url, json=payload)
        
            # Check if the request was successful
            if response.status_code == 200:
                print("Message posted successfully")
            else:
                print(f"Failed to post message: {response.status_code}, {response.text}")
        
        except Exception as e:
            print(f"Error posting message: {e}")



