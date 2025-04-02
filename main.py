import time
import threading
import sys
import traceback
import json
import os 
import signal
import importlib.util
import logging
from dotenv import load_dotenv
from binance.client import Client
from flask import Flask, request, jsonify, current_app

# When running as a script directly, make sure the current directory is in the path
# so Python can find our local modules without needing the 'proposal_revamp' package
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize logging - use absolute imports
from utils.logging_utils import setup_logging, get_logger
# Set up logging with INFO level
logger = setup_logging(level=logging.INFO)
# Get module-specific logger
module_logger = get_logger(__name__)

# Always use direct imports from local directories
from database import ProposalScanner, create_firebase_client, close_firebase_client
from core import TradeLogic, LiveTradeManager
from services import SlackBot
from utils import save_error, get_config
from models.sentiment import SentimentPredictor
from models.reasoning import Reasoning
from models.summarization import Summarization
from api.dynamo_utils import DynamoDBClient
from exchange import BinanceAPI, Monitor
import pandas as pd

# Flask app for API endpoints
app = Flask(__name__)
flask_thread = None
bot_instance = None

class GovernanceTradingBot:
    """
    Main class for the Governance Trading Bot that scans proposals and triggers trades
    based on sentiment analysis.
    
    This bot continually monitors governance proposals, analyzes them for sentiment,
    and triggers trades based on the analysis. It also monitors existing trades and
    updates their status as needed.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the Governance Trading Bot with required configurations and components.
        
        Args:
            config_path (str): Path to the configuration file (default: 'config.json')
        """
        self.logger = get_logger(f"{__name__}.GovernanceTradingBot")
        self.logger.info("Initializing Governance Trading Bot")
        
        load_dotenv()
        self.config_path = config_path
        
        # Use the ConfigLoader instead of direct file loading
        self.config = get_config().config
        
        # Initialize core components
        self.slack_bot = SlackBot(config_path)
        self.trade_manager = LiveTradeManager(config_path)
        self.proposal_scanner = ProposalScanner(config_path)
        self.trade_logic = TradeLogic(config_path)
        self.binance_api = BinanceAPI(config_path)
        
        # Initialize state variables
        self.counter = 0
        self.running = False
        self.last_run_time = None
        
        # Initialize components to None
        self.db = None
        self.app = None
        self.summary_obj = None
        self.sentiment_analyzer = None
        self.client = None
        self.reasoning = None
        self.dynamo = None
        self.monitor = None
        
        self.logger.info("Governance Trading Bot initialized")
    
    def load_config(self):
        """Load configuration from environment variables using ConfigLoader."""
        try:
            # Already loaded in __init__, just return success
            self.logger.info("Configuration already loaded from environment variables")
            return True
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    def check_past_data(self):
        """Check if past data exists in the specified directory."""
        files_data_len = len(os.listdir(self.config['data_dir']))
        self.logger.debug(f"Found {files_data_len} files in data directory")
        return files_data_len >= 3
    
    def initialize_components(self):
        """Initialize all required components for the bot."""
        try:
            self.logger.info("Initializing bot components")
            
            # Create data provider client (Firebase, MongoDB, etc.)
            self.db = self.proposal_scanner.create_firebase_client()
            self.app = None  # Only used for Firebase
            
            # Special handling for Firebase which returns a tuple
            provider_type = self.config.get('data_provider_type', 'firebase').lower()
            if provider_type == 'firebase' and isinstance(self.db, tuple):
                self.db, self.app = self.db
                self.logger.debug("Unpacked Firebase connection tuple")
            
            # Check and create DB if needed
            db_status = self.check_past_data()
            if not db_status:
                self.logger.info("No database found, creating new database")
                self.trade_logic.store_data(self.db)
            
            # Initialize all required components
            self.logger.info("Initializing summarization model")
            self.summary_obj = Summarization("mistral")
            
            self.logger.info("Initializing sentiment analyzer")
            self.sentiment_analyzer = SentimentPredictor(self.config['sentiment_dir'])
            
            self.logger.info("Initializing Binance client")
            self.client = self.binance_api.client
            
            # Initialize reasoning module
            self.logger.info("Initializing reasoning module")
            self.reasoning = Reasoning(
                openai_api_key=os.getenv("OPENAI_KEY")
            )
            
            # Initialize DynamoDB client and price monitor only if AWS credentials are present
            self.dynamo = None
            self.monitor = None
            if all([os.getenv("AWS_ACCESS_KEY_ID"), os.getenv("AWS_SECRET_ACCESS_KEY"), os.getenv("AWS_REGION")]):
                self.logger.info("AWS credentials found, initializing DynamoDB client")
                self.dynamo = DynamoDBClient()
            else:
                self.logger.info("AWS credentials not found, skipping DynamoDB initialization")
            
            # Initialize price monitor (independent of DynamoDB)
            self.logger.info("Initializing price monitor")
            self.monitor = Monitor()
            
            self.logger.info("All components initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}")
            self.logger.error(traceback.format_exc())
            self.slack_bot.post_error_to_slack(str(traceback.format_exc()))
            save_error(str(e))
            return False
    
    def get_status(self):
        """
        Get the current status of the bot.
        
        Returns:
            dict: Status information including components status, scan count, and last run time
        """
        status = {
            "running": self.running,
            "scan_count": self.counter,
            "last_run_time": self.last_run_time,
            "firebase_connected": self.db is not None,
            "components_initialized": all([
                self.summary_obj, 
                self.sentiment_analyzer, 
                self.client, 
                self.reasoning
            ])
        }
        # Only include DynamoDB status if it was initialized
        if self.dynamo is not None:
            status["dynamodb_connected"] = True
        self.logger.debug(f"Bot status: {status}")
        return status
    
    def run_scan_cycle(self):
        """
        Run a single scan cycle to check for new proposals and trigger trades.
        
        Returns:
            bool: True if scan completed successfully, False otherwise
        """
        try:
            # Record the start time
            self.last_run_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.running = True
            self.logger.info(f"Starting scan cycle #{self.counter + 1} at {self.last_run_time}")
            
            # Delete any existing live trades
            self.logger.info("Deleting existing live trades")
            self.trade_manager.delete_live_trade()
            
            # Download and save proposal data #abstract
            self.logger.info("Downloading and saving proposal data")
            proposal_dict = self.proposal_scanner.download_and_save_proposal(self.db, True)
            
            # Check for new posts #abstract
            self.logger.info("Checking for new posts")
            new_row_df = self.proposal_scanner.check_new_post(proposal_dict)
            
            self.logger.info(f"Triggering trades based on {len(new_row_df)} new proposals")
            # Trigger trades based on new proposals
            self.trade_logic.trigger_trade(new_row_df, self.summary_obj, self.sentiment_analyzer, 
                          self.reasoning, self.dynamo, self.slack_bot)
            
            # Check price for existing trades
            self.logger.info("Checking prices for existing trades")
            self.monitor.check_price()
            
            # Increment counter
            self.counter += 1
            
            self.running = False
            self.logger.info(f"Scan cycle #{self.counter} completed successfully")
            return True
        except Exception as e:
            self.running = False
            self.logger.error(f"Error in scan cycle: {e}")
            self.logger.error(traceback.format_exc())
            self.slack_bot.post_error_to_slack(str(traceback.format_exc()))
            save_error(str(e))
            return False
    
    def countdown_timer(self, seconds):
        """Display a countdown timer for the next scan."""
        self.logger.info(f"Waiting {seconds} seconds until next scan")
        for remaining in range(seconds, 0, -1):
            if remaining % 10 == 0:  # Log only every 10 seconds to reduce log noise
                self.logger.debug(f"Next scan in {remaining} seconds")
            sys.stdout.write("\rNext scan in: {:02d}:{:02d}".format(remaining // 60, remaining % 60))
            sys.stdout.flush()
            time.sleep(1)
        print("\n")
    
    def scan_proposals(self):
        """
        Main method to continuously scan proposals and trigger trades.
        This method implements error handling and retry mechanisms.
        """
        self.logger.info("Starting Governance Trading Bot main loop")
        self.slack_bot.post_error_to_slack("Governance Trading Bot started")
        
        shutdown_requested = False
        
        try:
            while not shutdown_requested:  # Outer loop for setup/teardown errors
                try:
                    # Initialize all required components
                    self.logger.info("Initializing bot components...")
                    init_success = self.initialize_components()
                    if not init_success:
                        self.logger.error("Failed to initialize components, retrying after delay")
                        time.sleep(60)
                        continue
                    
                    self.logger.info("Bot initialization complete. Starting scan cycles...")
                    
                    # Main operational loop
                    while not shutdown_requested:
                        # Run a single scan cycle
                        self.logger.info(f"Starting scan cycle #{self.counter + 1}...")
                        scan_success = self.run_scan_cycle()
                        
                        if scan_success:
                            self.logger.info(f"Scan cycle #{self.counter} completed successfully")
                        else:
                            self.logger.warning(f"Scan cycle #{self.counter} completed with errors")
                        
                        # Wait for the next scan cycle
                        countdown_time = 1 * 60  # 1 minute countdown
                        self.countdown_timer(countdown_time)
                    
                except KeyboardInterrupt:
                    shutdown_requested = True
                    self.logger.info("Keyboard interrupt received. Shutting down...")
                    
                except Exception as e:
                    self.logger.error(f"Error in scan proposals loop: {e}")
                    self.logger.error(traceback.format_exc())
                    self.slack_bot.post_error_to_slack(f"Error in scan loop: {str(traceback.format_exc())}")
                    save_error(str(e))
                    self.logger.info("Attempting to restart the setup after a delay...")
                    time.sleep(60)
                    continue
        
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received. Shutting down...")
        
        finally:
            # Clean up resources
            self.stop()
            self.logger.info("Governance Trading Bot shutdown complete")

    def stop(self):
        """
        Stop the bot gracefully by closing connections and cleaning up resources.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            self.logger.info("Stopping the Governance Trading Bot...")
            
            # Close the data provider connection if it exists
            provider_type = self.config.get('data_provider_type', 'firebase').lower()
            
            if provider_type == 'firebase' and self.app:
                # For Firebase, use the close_firebase_client function
                self.logger.info("Closing Firebase connection")
                close_firebase_client(self.app)
                self.app = None
                self.db = None
            elif provider_type == 'mongodb' and self.db:
                # For MongoDB, close the connection directly
                self.logger.info("Closing MongoDB connection")
                self.db.close()
                self.db = None
            elif self.db:
                # For other providers, try to use the data provider's disconnect method
                self.logger.info("Closing data provider connection")
                self.proposal_scanner.close_firebase_client(self.app or self.db)
                self.app = None
                self.db = None
            
            # Reset components
            self.logger.info("Resetting bot components")
            self.summary_obj = None
            self.sentiment_analyzer = None
            self.client = None
            self.reasoning = None
            self.dynamo = None
            self.monitor = None
            
            self.running = False
            self.logger.info("Governance Trading Bot stopped successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error stopping the bot: {e}")
            self.logger.error(traceback.format_exc())
            return False

def main():
    """Main entry point for the application."""
    module_logger.info("Starting application")
    
    # Create bot instance
    bot = GovernanceTradingBot()
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        module_logger.info("Shutdown signal received. Stopping bot gracefully...")
        bot.stop()
        module_logger.info("Bot stopped. Exiting.")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Uncomment to post startup notification
    bot.slack_bot.post_error_to_slack("Governance Trading Bot Started")
    
    # Start scanning proposals
    bot.scan_proposals()

if __name__ == "__main__":
    main()
    

    



