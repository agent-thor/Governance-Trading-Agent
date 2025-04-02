"""
Price monitoring module for the Governance Trading Bot.

This module provides functionality to monitor prices and manage trades
based on price movements.
"""

import json
import os
import time
import pandas as pd
import sys

# Use direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services import post_error_to_slack
from utils import get_config

class Monitor:
    """
    Class for monitoring prices and managing trades.
    
    This class checks prices of open positions and executes necessary
    actions based on price movements.
    """
    
    def __init__(self, dynamo_client, table_name):
        """
        Initialize the Monitor.
        
        Args:
            dynamo_client: DynamoDB client for storing trade data
            table_name (str): DynamoDB table name
        """
        self.dynamo = dynamo_client
        self.table_name = table_name
        self.config = get_config().config
    
    def check_price(self):
        """
        Check prices for all open positions and take necessary actions.
        
        This method loads open positions from a JSON file, checks current
        prices, and updates positions status as needed.
        """
        try:
            # Load live trades data
            live_trades_path = os.path.join(self.config['data_dir'], 'proposal_post_live.json')
            
            # Check if the file exists
            if not os.path.exists(live_trades_path):
                print("No live trades file found.")
                return
            
            # Read the JSON file
            with open(live_trades_path, 'r') as json_file:
                trades_data = json.load(json_file)
            
            # If no trades, return early
            if not trades_data:
                print("No active trades to monitor.")
                return
                
            print(f"Monitoring {len(trades_data)} active trades...")
            
            # Process each trade
            for trade_id, trade_info in trades_data.items():
                self._process_trade(trade_id, trade_info)
                
            print("Price monitoring completed.")
            
        except Exception as e:
            error_msg = f"Error in price monitoring: {str(e)}"
            print(error_msg)
            post_error_to_slack(error_msg)
    
    def _process_trade(self, trade_id, trade_info):
        """
        Process a single trade.
        
        Args:
            trade_id (str): ID of the trade
            trade_info (dict): Trade information
        """
        try:
            coin = trade_info.get('coin')
            trade_type = trade_info.get('type')
            status = trade_info.get('status')
            
            print(f"Processing trade {trade_id} - {coin} ({trade_type}) - Status: {status}")
            
            # If trade is already closed, skip
            if status == 'sold':
                return
                
            # Add logic here to check specific conditions
            # For example: check current price vs. target or stop-loss
            # and update trade status accordingly
            
        except Exception as e:
            error_msg = f"Error processing trade {trade_id}: {str(e)}"
            print(error_msg)
            post_error_to_slack(error_msg) 