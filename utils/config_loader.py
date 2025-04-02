#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config loader module for loading configuration from environment variables.

This module provides functionality to load configuration from:
1. Environment variables (.env file)
2. Legacy config.json file (fallback)

It provides a unified interface to access configuration parameters regardless of source.
"""

import os
import json
from dotenv import load_dotenv

class ConfigLoader:
    """
    ConfigLoader handles loading and centralizing configuration from environment 
    variables or a legacy config.json file.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the ConfigLoader.
        
        Args:
            config_path (str): Path to the fallback config.json file
        """
        # Load environment variables first
        load_dotenv()
        
        # Initialize configuration dict
        self.config = {}
        
        # Load configuration from env vars
        self._load_from_env()
        
        # If any essential configs are missing, try loading from legacy config file
        if not self._check_essential_configs():
            self._load_from_json(config_path)
    
    def _check_essential_configs(self):
        """
        Check if all essential configurations are present.
        
        Returns:
            bool: True if all essential configs are present, False otherwise
        """
        essential_keys = ['data_dir', 'binance_api_key', 'binance_api_secret']
        return all(key in self.config for key in essential_keys)
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Paths and directories
        self.config['data_dir'] = os.getenv('DATA_DIR')
        self.config['firebase_cred'] = os.getenv('FIREBASE_CRED')
        self.config['bullish_dir'] = os.getenv('BULLISH_DIR')
        self.config['bearish_dir'] = os.getenv('BEARISH_DIR')
        self.config['sentiment_dir'] = os.getenv('SENTIMENT_DIR')
        
        # Binance API credentials
        self.config['binance_api_key'] = os.getenv('BINANCE_API_KEY')
        self.config['binance_api_secret'] = os.getenv('BINANCE_API_SECRET')
        
        # Slack integration
        self.config['slack_webhook_url'] = os.getenv('SLACK_WEBHOOK_URL')
        
        # Trading parameters
        if os.getenv('COUNTDOWN_TIME'):
            self.config['countdown_time'] = int(os.getenv('COUNTDOWN_TIME'))
        else:
            self.config['countdown_time'] = 60
            
        if os.getenv('SENTIMENT_SCORE_BULLISH'):
            self.config['sentiment_score_bullish'] = float(os.getenv('SENTIMENT_SCORE_BULLISH'))
        else:
            self.config['sentiment_score_bullish'] = 0.80
            
        if os.getenv('SENTIMENT_SCORE_BEARISH'):
            self.config['sentiment_score_bearish'] = float(os.getenv('SENTIMENT_SCORE_BEARISH'))
        else:
            self.config['sentiment_score_bearish'] = 0.80
            
        if os.getenv('TRADE_AMOUNT'):
            self.config['trade_amount'] = float(os.getenv('TRADE_AMOUNT'))
        else:
            self.config['trade_amount'] = 5000
            
        if os.getenv('LEVERAGE'):
            self.config['leverage'] = int(os.getenv('LEVERAGE'))
        else:
            self.config['leverage'] = 3
            
        if os.getenv('STOP_LOSS_PERCENT'):
            self.config['stop_loss_percent'] = float(os.getenv('STOP_LOSS_PERCENT'))
        else:
            self.config['stop_loss_percent'] = 2.0
            
        if os.getenv('MAX_TRADES'):
            self.config['max_trades'] = int(os.getenv('MAX_TRADES'))
        else:
            self.config['max_trades'] = 4
        
        # Clean up None values
        self.config = {k: v for k, v in self.config.items() if v is not None}
    
    def _load_from_json(self, config_path):
        """
        Load configuration from a JSON file.
        
        Args:
            config_path (str): Path to the config.json file
        """
        try:
            # Try finding the config file in various locations
            possible_paths = [
                config_path,  # Original path
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), config_path),  # From project root
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), config_path)  # From parent directory
            ]
            
            # Use the first path that exists
            config_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_file_path = path
                    break
                    
            if not config_file_path:
                print(f"Configuration file not found in any of the possible paths: {possible_paths}")
                return
                
            with open(config_file_path, 'r') as json_file:
                json_config = json.load(json_file)
                
            # Map old config keys to new ones
            key_mapping = {
                'data_dir': 'data_dir',
                'firebase_cred': 'firebase_cred',
                'API_KEY': 'binance_api_key',
                'API_SECRET': 'binance_api_secret',
                'webhook_url': 'slack_webhook_url',
                'bullish_dir': 'bullish_dir',
                'bearish_dir': 'bearish_dir',
                'sentiment_dir': 'sentiment_dir',
                'proposal_check_interval': 'countdown_time'
            }
            
            # Transfer values using the mapping
            for old_key, new_key in key_mapping.items():
                if old_key in json_config and new_key not in self.config:
                    self.config[new_key] = json_config[old_key]
            
            print(f"Loaded legacy configuration from {config_path}")
        except Exception as e:
            print(f"Error loading legacy configuration: {e}")
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): The configuration key
            default: The default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """
        Get a configuration value using dictionary syntax.
        
        Args:
            key (str): The configuration key
            
        Returns:
            The configuration value
            
        Raises:
            KeyError: If the key is not found
        """
        if key in self.config:
            return self.config[key]
        raise KeyError(f"Configuration key '{key}' not found")

# Create a singleton instance that can be imported
config_loader = ConfigLoader()

def get_config():
    """
    Get the global ConfigLoader instance.
    
    Returns:
        ConfigLoader: The singleton ConfigLoader instance
    """
    return config_loader 