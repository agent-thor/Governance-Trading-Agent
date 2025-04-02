import numpy as np
import pandas as pd
import time
import json
import os
import firebase_admin
from datetime import datetime
import logging

# Use direct imports instead of relative imports
import sys
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import ProposalScanner
from models.summarization import Summarization
from utils import format_time_utc, btc_price_check, get_config
from utils.logging_utils import get_logger
from exchange import BinanceAPI
from services import SlackBot, post_to_slack, post_error_to_slack
from models.bullish_price import RobertaForRegressionBullish
from models.bearish_price import RobertaForRegressionBearish
from utils.text_verification import classify_text
from utils.clean_html import remove_html_tags
from utils.save_trades import Save

# Initialize logger
logger = get_logger(__name__)

class TradeLogic:
    """
    Class to handle trading logic for governance proposals.
    """
    
    # Constants
    PRICE_DICT = {
        "verySmall": 0.20,  # (0.15 + 0.25) / 2
        "small": 0.325,     # (0.25 + 0.40) / 2
        "medium": 0.50,     # (0.40 + 0.60) / 2
        "high": 0.80,       # (0.60 + 1) / 2
        "nn": 0             # Default to 0 for 'nn'
    }
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the TradeLogic with configuration.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load configuration using environment variables with fallback to config.json
        self.config = get_config().config
        
        # Initialize proposal scanner
        self.proposal_scanner = ProposalScanner(config_path)
        
        # Initialize SlackBot
        self.slack_bot = SlackBot(config_path)
        
        # Initialize BinanceAPI
        self.binance_api = BinanceAPI(config_path)
    
    def store_data(self, db):
        """
        Store initial data into database.
        
        Args:
            db: Firestore database client
        """
        print("Initating first DB creation")
        proposal_dict = self.proposal_scanner.download_and_save_proposal(db, False)
        start_time = self.proposal_scanner.store_into_db(proposal_dict)
        print("Key DB created successfully")
        
        proposal_post_all = pd.DataFrame(columns=["timestamp", "post_id", "coin", "description", "summary", "sentiment", "sentiment_score", "text_verify"])    
        proposal_post_all.to_csv(self.config['data_dir'] + '/proposal_post_all.csv')
        print("Proposal_post_all DB created successfully")
        
        empty_data = {}
        with open(self.config['data_dir'] + '/proposal_post_live.json', 'w') as json_file:
            json.dump(empty_data, json_file, indent=4)
            
        print("Proposal_post_live DB created successfully")
        
        price_check_file_path = self.config['data_dir'] + '/price_check.json'
        if not os.path.exists(price_check_file_path):
            data = []
            # Create new file with empty list
            with open(price_check_file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        print("price_check_json created into DB")
        
        return start_time
    
    def store_into_live(self, coin, post_id, trade_id, description, buying_price, buying_time, 
                        stop_loss_price, trade_type, stop_loss_orderID, proposal_post_live, 
                        target_orderId, targetPrice):
        """
        Store trade information into live trades database.
        
        Args:
            coin (str): Coin symbol
            post_id (str): Post ID
            trade_id (str): Trade ID
            description (str): Trade description
            buying_price (float): Buying price
            buying_time (str): Buying time
            stop_loss_price (float): Stop loss price
            trade_type (str): Trade type (long/short)
            stop_loss_orderID (str): Stop loss order ID
            proposal_post_live (dict): Live proposals dictionary
            target_orderId (str): Target order ID
            targetPrice (float): Target price
        """
        new_data = {
            "coin": coin,
            "post_id": post_id,
            "description": description,
            "buying_price": buying_price,
            "buying_time": buying_time,
            "stop_loss_price": stop_loss_price,
            "type": trade_type,
            "stop_loss_id": stop_loss_orderID,
            "target_order_id": target_orderId,
            "target_price": targetPrice,
            "status": "unsold"
        }
        
        proposal_post_live[trade_id] = new_data
        
        with open(self.config['data_dir'] + '/proposal_post_live.json', 'w') as json_file:
            json.dump(proposal_post_live, json_file, indent=4)
    
    def check_trade_limit(self, coin):
        """
        Check if trade limit is reached or coin already exists in live trades.
        
        Args:
            coin (str): Coin symbol
            
        Returns:
            bool: True if trade is allowed, False otherwise
        """
        with open(self.config['data_dir'] + '/proposal_post_live.json', 'r') as json_file:
            proposal_post_live = json.load(json_file)
        
        if len(proposal_post_live) >= 4:
            return False
        
        if len(proposal_post_live) == 0:
            return True
       
        for key, value in proposal_post_live.items():
            if proposal_post_live[key]['coin'] == coin:
                return False
            else:
                return True
    
    def send_new_post_slack(self, coin, post_id, discussion_link, sentiment, sentiment_score, target_price, summary, slack_bot=None):
        """
        Send notification about new post to Slack.
        
        Args:
            coin (str): Coin symbol
            post_id (str): Post ID
            discussion_link (str): Link to discussion
            sentiment (str): Sentiment (positive/negative)
            sentiment_score (float): Sentiment score
            target_price (float): Target price
            summary (str): Summary text
            slack_bot (SlackBot, optional): SlackBot instance for notifications
        """
        slack_bot = slack_bot or self.slack_bot
        
        if discussion_link == '' or discussion_link is None:
            discussion_link = summary
            
        message = {
            "discussion_link": discussion_link,
            "coin": coin,
            "post_id": post_id,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "target_percent": target_price
        }
        
        post_to_slack(message)
        print("Posted to slack", message)
    
    def send_trade_info_slack(self, coin, trade_type, buying_price, stop_loss_price, targetPrice, 
                              trade_id, stop_loss_orderID, target_orderId, quantity, slack_bot=None):
        """
        Send trade information to Slack.
        
        Args:
            coin (str): Coin symbol
            trade_type (str): Trade type (Long/Short)
            buying_price (float): Buying price
            stop_loss_price (float): Stop loss price
            targetPrice (float): Target price
            trade_id (str): Trade ID
            stop_loss_orderID (str): Stop loss order ID
            target_orderId (str): Target order ID
            quantity (float): Quantity
            slack_bot (SlackBot, optional): SlackBot instance for notifications
        """
        slack_bot = slack_bot or self.slack_bot
        
        message = {
            "coin": coin,
            "trade_type": trade_type,
            "buying_price": buying_price,
            "stop_loss_price": stop_loss_price,
            "target_price": targetPrice,
            "trade_id": trade_id,
            "stop_loss_orderID": stop_loss_orderID,
            "target_orderId": target_orderId,
            "quantity": quantity
        }
        
        post_to_slack(message)
        print("Posted to slack", message)
    
    def predict_final_sentiment(self, sentiment, sentiment_score, sentiment_crypto, crypto_score):
        """
        Predict final sentiment by combining two sentiment analyses.
        
        Args:
            sentiment (str): Sentiment from main analysis
            sentiment_score (float): Score from main analysis
            sentiment_crypto (str): Sentiment from crypto-specific analysis
            crypto_score (float): Score from crypto-specific analysis
            
        Returns:
            tuple: Combined sentiment and score
        """
        if sentiment != sentiment_crypto:
            return sentiment, sentiment_score
        
        else:
            sentiment_score = (sentiment_score + crypto_score) / 2
            return sentiment, sentiment_score
    
    def trigger_trade(self, new_row_df, summary_obj, sentiment_analyzer, reasoning, dynamo, slack_bot=None):
        """
        Trigger trades based on new proposals.
        
        Args:
            new_row_df (DataFrame): DataFrame with new proposals
            summary_obj: Summarization object
            sentiment_analyzer: Sentiment analyzer object
            reasoning: Reasoning object
            dynamo: DynamoDB client
            slack_bot (SlackBot, optional): SlackBot instance for notifications
        """
        # Use provided SlackBot if available
        slack_bot = slack_bot or self.slack_bot
        
        if len(new_row_df) == 0:
            return
            
        proposal_post_all = pd.read_csv(self.config['data_dir'] + '/proposal_post_all.csv', index_col=0)
        proposal_post_id = pd.read_csv(self.config['data_dir'] + '/proposal_post_id.csv', index_col=0)
        
        with open(self.config['data_dir'] + '/proposal_post_live.json', 'r') as json_file:
            proposal_post_live = json.load(json_file)
        
        live_post_ids = []
        for key, live_trade in proposal_post_live.items():
            live_post_ids.append(proposal_post_live[key]['post_id'])

        for index, row in new_row_df.iterrows():
            coin = row['coin']
            post_id = row['post_id']
            slack_bot.post_error_to_slack(str(post_id))
            description = row['description']
            description = self.proposal_scanner.clean_content(description)
            timestamp = row['timestamp']
            discussion_link = row['discussion_link']
            
            text_verify = classify_text(description)
            summary = summary_obj.summarize_text(description)
            sentiment, sentiment_score = sentiment_analyzer.predict(summary)
            
            # Calculating deepseek and openAI sentiment
            sentiment, sentiment_score = reasoning.predict_sentiment(summary, sentiment_score)
                        
            # Saving into DB
            new_row = {
                "post_id": post_id,
                "coin": coin,
                "description": description,
                "summary": summary,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "text_verify": text_verify
            }
            if post_id not in list(proposal_post_all['post_id']):
                proposal_post_all = pd.concat([proposal_post_all, pd.DataFrame([new_row])], ignore_index=True) 
        
            proposal_post_all.to_csv(self.config['data_dir'] + '/proposal_post_all.csv')
            
            # Store into proposal_post_id 
            new_row1 = {
                "post_id": post_id
            }
            if post_id not in list(proposal_post_id['post_id']):
                proposal_post_id = pd.concat([proposal_post_id, pd.DataFrame([new_row1])], ignore_index=True)
            
            proposal_post_id.to_csv(self.config['data_dir'] + '/proposal_post_id.csv')  
                        
            # Get sentiment thresholds from environment variables, defaulting to 0.80 if not set
            sentiment_score_bullish = self.config.get('sentiment_score_bullish', 0.80)
            sentiment_score_bearish = self.config.get('sentiment_score_bearish', 0.80)
            # Taking trade from here
            if sentiment == 'positive' and sentiment_score >= sentiment_score_bullish and text_verify == 'genuine' and not btc_price_check(self.config): 
                # Making an object for bullish price prediction
                bullish_predictor = RobertaForRegressionBullish(self.config['bullish_dir'])
                target_price = bullish_predictor.predict(summary)[0]
                
                if post_id not in live_post_ids:
                    self.send_new_post_slack(coin, post_id, discussion_link, sentiment, sentiment_score, target_price, summary, slack_bot)
                
                check_status = self.check_trade_limit(coin)
                if check_status:
                    # Divide by 100 because target profit is in number ex 5 bringing it to 0.05
                    buying_price, trade_id, stop_loss_price, stop_loss_orderID, target_orderId, targetPrice, quantity = self.binance_api.create_buy_order_long(coin, target_price/100)
                    buying_time = format_time_utc()
                    print("---------------TRADE BOUGHT---------------------")
                    
                    self.store_into_live(coin, post_id, trade_id, description, buying_price, buying_time, 
                                        stop_loss_price, "long", stop_loss_orderID, proposal_post_live, 
                                        target_orderId, targetPrice)
                                        
                    self.send_trade_info_slack(coin, "Long", buying_price, stop_loss_price, targetPrice, 
                                              trade_id, stop_loss_orderID, target_orderId, quantity, slack_bot)
                    
                    # Saving info to dynamoDB
                    try:
                        save_object = Save(dynamo, 'trade_table')
                        save_object.save_to_dynamo(coin, description, sentiment_score, post_id)
                        print("--saved to dynamoDB--")
                    except Exception as e:
                        print(f"Error saving to DynamoDB: {e}")
                        slack_bot.post_error_to_slack(f"Error saving to DynamoDB: {e}")
                        print("Continuing with remaining operations...")
                    
            if sentiment == 'negative' and sentiment_score >= sentiment_score_bearish and text_verify == 'genuine' and not btc_price_check(self.config):
                # Making an object for bearish price prediction
                bearish_predictor = RobertaForRegressionBearish(model_path=self.config['bearish_dir'])
                target_price = bearish_predictor.predict(summary)[0]
                
                if post_id not in live_post_ids:
                    self.send_new_post_slack(coin, post_id, description, sentiment, sentiment_score, target_price, summary, slack_bot)

                check_status = self.check_trade_limit(coin)
                if check_status:
                    # Divide by 100 because target profit is in number ex 5 bringing it to 0.05
                    buying_price, trade_id, stop_loss_price, stop_loss_orderID, target_orderId, targetPrice, quantity = self.binance_api.create_buy_order_short(coin, target_price/100)
                    buying_time = format_time_utc()
                    print("---------------TRADE BOUGHT---------------------")
                    
                    self.store_into_live(coin, post_id, trade_id, description, buying_price, buying_time, 
                                        stop_loss_price, "short", stop_loss_orderID, proposal_post_live, 
                                        target_orderId, targetPrice)
                                        
                    self.send_trade_info_slack(coin, "Short", buying_price, stop_loss_price, targetPrice, 
                                              trade_id, stop_loss_orderID, target_orderId, quantity, slack_bot)
                    
                    # Saving info to dynamoDB
                    try:
                        save_object = Save(dynamo, 'trade_table')
                        save_object.save_to_dynamo(coin, description, sentiment_score, post_id)
                        print("--saved to dynamoDB--")
                    except Exception as e:
                        print(f"Error saving to DynamoDB: {e}")
                        slack_bot.post_error_to_slack(f"Error saving to DynamoDB: {e}")
                        print("Continuing with remaining operations...")
    
    def close_firebase_client(self, app):
        """
        Close Firebase client.
        
        Args:
            app: Firebase app instance
        """
        firebase_admin.delete_app(app)
        print("Firebase client closed successfully.")


# Create global instance for backward compatibility
# _trade_logic = None

# def get_trade_logic():
#     """Get a global instance of the TradeLogic."""
#     global _trade_logic
#     if _trade_logic is None:
#         _trade_logic = TradeLogic()
#     return _trade_logic

# # Backward compatibility functions
# def store_data(db):
#     """Backward compatibility function for store_data."""
#     return get_trade_logic().store_data(db)

# def store_into_live(coin, post_id, trade_id, description, buying_price, buying_time, 
#                   stop_loss_price, trade_type, stop_loss_orderID, proposal_post_live, 
#                   target_orderId, targetPrice):
#     """Backward compatibility function for store_into_live."""
#     return get_trade_logic().store_into_live(coin, post_id, trade_id, description, buying_price, buying_time, 
#                                            stop_loss_price, trade_type, stop_loss_orderID, proposal_post_live, 
#                                            target_orderId, targetPrice)

# def check_trade_limit(coin):
#     """Backward compatibility function for check_trade_limit."""
#     return get_trade_logic().check_trade_limit(coin)

# def send_new_post_slack(coin, post_id, discussion_link, sentiment, sentiment_score, target_price, summary):
#     """Backward compatibility function for send_new_post_slack."""
#     return get_trade_logic().send_new_post_slack(coin, post_id, discussion_link, sentiment, sentiment_score, target_price, summary)

# def send_trade_info_slack(coin, trade_type, buying_price, stop_loss_price, targetPrice, trade_id, stop_loss_orderID, target_orderId, quantity):
#     """Backward compatibility function for send_trade_info_slack."""
#     return get_trade_logic().send_trade_info_slack(coin, trade_type, buying_price, stop_loss_price, targetPrice, trade_id, stop_loss_orderID, target_orderId, quantity)

# def predict_final_sentiment(sentiment, sentiment_score, sentiment_crypto, crypto_score):
#     """Backward compatibility function for predict_final_sentiment."""
#     return get_trade_logic().predict_final_sentiment(sentiment, sentiment_score, sentiment_crypto, crypto_score)

# def trigger_trade(new_row_df, summary_obj, sentiment_analyzer, reasoning, dynamo, slack_bot=None):
#     """Backward compatibility function for trigger_trade."""
#     return get_trade_logic().trigger_trade(new_row_df, summary_obj, sentiment_analyzer, reasoning, dynamo, slack_bot)

# def close_firebase_client(app):
#     """Backward compatibility function for close_firebase_client."""
#     return get_trade_logic().close_firebase_client(app)




        
