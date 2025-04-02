import os
from datetime import datetime, timedelta
import pytz
import json
import sys

# Add the parent directory to sys.path for direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils.config_loader import ConfigLoader
from utils.time_utils import get_ist_time
from utils.price_utils import get_coin_price

# Get configuration from environment variables
config_loader = ConfigLoader()
config = config_loader.config

class Save:
    def __init__(self, dynamo, table_name):
        self.dynamo = dynamo
        self.table_name = table_name  # Assume table_name is passed to the constructor
        self.config = config  # Use the loaded config

    def save_to_json(self, time_after_5_days_ist, coin_name, current_time, post_id, initial_price):
        data_dir = self.config.get('data_dir')
        if not data_dir:
            print("Error: DATA_DIR not found in configuration")
            return
            
        file_path = os.path.join(data_dir, 'price_check.json')

        # Check if price_check.json exists
        if not os.path.exists(file_path):
            data = []
        else:
            # Load existing JSON
            with open(file_path, 'r') as f:
                data = json.load(f)

        # Append the new record
        data.append({
            "time_after_5_days": time_after_5_days_ist,
            "coin_name": coin_name,
            "initial_time": current_time,
            "trade_id" : post_id,
            "initial_price" : initial_price
        })

        # Write updated list back to JSON
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def save_to_dynamo(self, coin_name, text, score, post_id):
        current_time_ist = get_ist_time().strftime("%Y-%m-%d %H:%M:%S")
        price = get_coin_price(coin_name)
        date_after_5_days = (datetime.strptime(current_time_ist, "%Y-%m-%d %H:%M:%S") + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")

        item = {
            "trade_id": {"S": str(post_id)},
            "coin_name": {"S": str(coin_name)},
            "post": {"S": str(text)},
            "score": {"S": str(score)},
            "current_time": {"S": current_time_ist},
            "current_price": {"S": str(price) if price is not None else "0"},
            "time_after_5_days": {"S": date_after_5_days.split(' ')[0]}
        }

        self.dynamo.add_item(self.table_name, item)
        self.save_to_json(date_after_5_days.split(' ')[0], coin_name, current_time_ist, post_id, price)
        
