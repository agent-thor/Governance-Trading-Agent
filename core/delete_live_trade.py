#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 13:16:26 2024

@author: krishnayadav
"""
import json
import time
import os
import sys
from binance.client import Client

# Add the parent directory to sys.path for direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from exchange import BinanceAPI
from services import SlackBot
from utils import get_config

class LiveTradeManager:
    """
    Class for managing and deleting live trades based on position information.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the LiveTradeManager with configuration.
        
        Args:
            config_path (str): Path to the configuration file (not used if using env vars)
        """
        # Load configuration from environment variables
        self.config = get_config().config
            
        # Initialize SlackBot
        self.slack_bot = SlackBot(config_path)
        
        # Initialize BinanceAPI
        self.binance_api = BinanceAPI(config_path)
        
        # Load coin symbols
        exchange_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exchange')
        with open(os.path.join(exchange_dir, 'coin.json'), 'r') as json_file:
            self.coin_symbol = json.load(json_file)
    
    def delete_live_trade(self, client=None, slack_bot=None):
        """
        Delete trades that are no longer open positions.
        
        Args:
            client: Binance client instance (optional, uses self.binance_api.client if not provided)
            slack_bot (SlackBot, optional): SlackBot instance for notifications
        """
        # Use provided SlackBot if available
        if slack_bot:
            self.slack_bot = slack_bot
        
        # Use provided client or the one from BinanceAPI
        client = client or self.binance_api.client
        
        # Load live trades data
        with open(self.config['data_dir'] + '/proposal_post_live.json', 'r') as json_file:
            proposal_post_live = json.load(json_file)

        # Map trade IDs to coin symbols
        live_coin_symbol = {}
        for key, value in proposal_post_live.items():
            live_coin_symbol[key] = self.coin_symbol[proposal_post_live[key]['coin']]

        # Retry mechanism for fetching positions
        positions = self._fetch_positions(client)
        if positions is None:
            return

        # Filter for only open positions
        open_coin = []
        open_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        for position_dict in open_positions:
            open_coin.append(position_dict['symbol'])

        # Remove closed positions from live trades
        self._update_live_trades(proposal_post_live, live_coin_symbol, open_coin)
    
    def _fetch_positions(self, client):
        """
        Fetch positions with retry mechanism.
        
        Args:
            client: Binance client instance
            
        Returns:
            list: List of positions or None if fetching failed
        """
        max_retries = 5
        retry_count = 0
        positions = None

        while retry_count < max_retries:
            try:
                positions = client.futures_position_information()
                break  # Exit loop if successful
            except Exception as e:
                retry_count += 1
                print(f"Error fetching positions: {e}. Retrying {retry_count}/{max_retries}...")
                time.sleep(2)  # Wait before retrying

        if positions is None:
            error_message = "Failed to fetch positions after 5 retries."
            print(error_message)
            self.slack_bot.post_error_to_slack(error_message)
        
        return positions
    
    def _update_live_trades(self, proposal_post_live, live_coin_symbol, open_coin):
        """
        Update the live trades file by removing closed positions.
        
        Args:
            proposal_post_live (dict): Dictionary of live trades
            live_coin_symbol (dict): Mapping from trade ID to coin symbol
            open_coin (list): List of symbols with open positions
        """
        updated = False
        
        for trade_id, symbol in live_coin_symbol.items():
            if symbol not in open_coin:
                del proposal_post_live[trade_id]
                print(f"{symbol} was deleted from proposal post live")
                sell_string = f"{symbol} WAS SOLD"
                self.slack_bot.post_error_to_slack(sell_string)
                updated = True
        
        # Save updated data if changes were made
        if updated:
            with open(self.config['data_dir'] + '/proposal_post_live.json', 'w') as json_file:
                json.dump(proposal_post_live, json_file, indent=4)
        else:
            print("No trade was deleted from proposal post live")


# Create a function that instantiates the class for backward compatibility
def delete_live_trade(client, slack_bot=None):
    """
    Backward compatibility function for delete_live_trade.
    
    Args:
        client: Binance client instance
        slack_bot (SlackBot, optional): SlackBot instance for notifications
    """
    manager = LiveTradeManager()
    manager.delete_live_trade(client, slack_bot)
    





   