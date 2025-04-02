import pandas as pd 
import numpy as np

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import os
import sys
import pandas as pd
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
from google.api_core.retry import Retry
import logging

# Add the parent directory to sys.path for direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import get_config
from utils.logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

class DataProvider:
    """
    Base class for data providers that supply proposal data.
    
    Implement this class to support different data sources.
    """
    
    def connect(self):
        """Connect to the data source. Return connection object."""
        raise NotImplementedError("Subclasses must implement connect()")
    
    def disconnect(self, connection):
        """Disconnect from the data source."""
        raise NotImplementedError("Subclasses must implement disconnect()")
    
    def download_proposals(self, connection, scan_mode=True):
        """
        Download proposals from the data source.
        
        Args:
            connection: Connection object from connect()
            scan_mode: If True, limit to recent proposals, otherwise get more
            
        Returns:
            dict: Dictionary of proposal data
        """
        raise NotImplementedError("Subclasses must implement download_proposals()")
    
    def check_new_proposals(self, proposals_dict, existing_data_path):
        """
        Check for new proposals not in existing data.
        
        Args:
            proposals_dict: Dictionary of proposal data
            existing_data_path: Path to file with existing data
            
        Returns:
            DataFrame: DataFrame of new proposals
        """
        raise NotImplementedError("Subclasses must implement check_new_proposals()")

class FirebaseDataProvider(DataProvider):
    """
    Firebase implementation of DataProvider for proposal data.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger(f"{__name__}.FirebaseDataProvider")
    
    def connect(self):
        """Connect to Firebase and return the database client and app."""
        cred = credentials.Certificate(self.config["firebase_cred"])
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        self.logger.info("Connected to Firebase successfully")
        return (db, app)
    
    def disconnect(self, connection):
        """Disconnect from Firebase."""
        _, app = connection
        try:
            firebase_admin.delete_app(app)
            self.logger.info("Firebase client closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing Firebase client: {e}")
    
    def _clean_content(self, html_text):
        """Clean HTML content by extracting only the text."""
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text()
    
    def download_proposals(self, connection, scan_mode=True):
        """Download proposals from Firebase."""
        # Handle different connection types
        if isinstance(connection, tuple):
            db, _ = connection
        else:
            # If not a tuple, assume it's already the db object
            db = connection
        
        self.logger.info("Downloading proposals from Firebase")
        retry_strategy = Retry()
        collection_name = 'ai_posts'
        collection_ref = db.collection(collection_name)    
        
        if scan_mode:
            self.logger.debug("Using scan mode: limited to 20 most recent documents")
            docs = collection_ref.order_by('created_at', direction='DESCENDING').limit(20).stream(retry=retry_strategy)
        else:
            self.logger.debug("Using full mode: retrieving up to 1000 documents")
            docs = collection_ref.order_by('created_at', direction='DESCENDING').limit(1000).stream(retry=retry_strategy)

        protocol_list = []
        docs_list = []
        for doc in docs:
            protocol = str(doc.id).split('--')[0]
            if protocol not in protocol_list:
                protocol_list.append(protocol)
            docs_list.append(doc.to_dict())
        
        self.logger.info(f"Found {len(docs_list)} documents across {len(protocol_list)} protocols")
            
        proposal_dict = {}
        for key in protocol_list:
            discourse_df = pd.DataFrame(columns = ['protocol', 'post_id', 'timestamp', 'title', 'description', "discussion_link"])    
            
            for doc in docs_list: 
                try:
                    if doc['post_type'] == 'snapshot_proposal':
                        df_row = []
                        if key in doc['house_id']:
                            post_id = doc['id']
                            protocol = key
                            timestamp = doc['created_at']
                            title = doc['title']
                            description = self._clean_content(doc['description'])
                            
                            try:
                                discussion_link = doc['post_url_link']
                            except Exception as e:
                                discussion_link = ''
                                self.logger.debug(f"No discussion link found for {post_id}")
                            
                            df_row = [protocol, post_id, timestamp, title, description, discussion_link]
                            
                            temp_df = pd.DataFrame([df_row], columns=discourse_df.columns)
                            
                            discourse_df = pd.concat([discourse_df, temp_df], ignore_index=True)
                
                except Exception as e:
                    self.logger.error(f"Error processing document: {e}")
                    continue
                    
            proposal_dict[key] = discourse_df
            self.logger.debug(f"Processed {len(discourse_df)} proposals for protocol {key}")
        
        return proposal_dict
    
    def check_new_proposals(self, proposals_dict, existing_data_path):
        """Check for new proposals not in existing data."""
        try:
            proposal_post_id = list(pd.read_csv(existing_data_path, index_col=0)['post_id'])
            self.logger.info(f"Found {len(proposal_post_id)} existing proposals in {existing_data_path}")
        except Exception as e:
            self.logger.warning(f"Could not read existing proposals: {e}. Treating all as new.")
            proposal_post_id = []
        
        columns = ["post_id", "coin", "description", "discussion_link", "timestamp"]
        new_row_df = pd.DataFrame(columns=columns)
        
        for key, coin_df in proposals_dict.items():
            for index, row in coin_df.iterrows():
                post_id = row['post_id']
                if post_id not in proposal_post_id:
                    coin = post_id.split("--")[0]
                    description = row['description']
                    discussion_link = row['discussion_link']
                    timestamp = row['timestamp']
                    
                    new_row = {
                        "post_id": post_id,
                        "coin": coin,
                        "description": description,
                        "discussion_link": discussion_link,
                        "timestamp": timestamp
                    }
                    new_row_df = pd.concat([new_row_df, pd.DataFrame([new_row])], ignore_index=True)
        
        self.logger.info(f"Found {len(new_row_df)} new proposals")
        return new_row_df

# Factory to create appropriate data provider
def create_data_provider(provider_type, config):
    """
    Factory function to create data provider of appropriate type.
    
    Args:
        provider_type (str): Type of data provider ('firebase', etc.)
        config (dict): Configuration for the provider
        
    Returns:
        DataProvider: DataProvider instance
    """
    if provider_type.lower() == 'firebase':
        return FirebaseDataProvider(config)
    else:
        # Default to Firebase provider for backward compatibility
        logger.warning(f"Unknown provider type '{provider_type}', using Firebase provider")
        return FirebaseDataProvider(config)

# Convenience functions for direct Firebase operations
def create_firebase_client():
    """
    Create Firebase client from configuration.
    
    Returns:
        tuple: Tuple containing (db, app)
    """
    config = get_config().config
    provider = FirebaseDataProvider(config)
    return provider.connect()

def close_firebase_client(app):
    """
    Close Firebase client.
    
    Args:
        app: Firebase app to close
    """
    config = get_config().config
    provider = FirebaseDataProvider(config)
    provider.disconnect((None, app))

# Allow direct execution for testing
if __name__ == "__main__":
    # Setup logging
    from utils.logging_utils import setup_logging
    logger = setup_logging(level=logging.INFO)
    
    print("Initializing ProposalScanner...")
    scanner = ProposalScanner()
    
    print("Creating Firebase client...")
    connection = scanner.create_firebase_client()
    
    print("Downloading proposals...")
    proposal_dict = scanner.download_and_save_proposal(connection, scan_mode=True)
    
    print("Checking new posts...")
    new_proposals = scanner.check_new_post(proposal_dict)
    
    print(f"Found {len(new_proposals)} new proposals.")
    
    print("Closing Firebase client...")
    scanner.close_firebase_client(connection)
    
    print("Done.")

class ProposalScanner:
    """
    A class for scanning, downloading, and processing governance proposals.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the ProposalScanner with configuration.
        
        Args:
            config_path (str): Path to the configuration file (not used if using env vars)
        """
        # Initialize logger
        self.logger = get_logger(f"{__name__}.ProposalScanner")
        
        # Load configuration from environment variables
        self.config = get_config().config
        
        # Create the data provider (default to firebase for backward compatibility)
        provider_type = self.config.get('data_provider_type', 'firebase')
        self.logger.info(f"Initializing ProposalScanner with provider type: {provider_type}")
        
        self.data_provider = create_data_provider(provider_type, self.config)
        self.logger.info(f"Provider class: {self.data_provider.__class__.__name__}")
        
        # Store the connection as None initially
        self.connection = None
    
    def create_firebase_client(self):
        """
        Create and initialize a data provider client.
        
        Returns:
            A connection object appropriate for the data provider type.
            For Firebase: a tuple containing (db, app)
            For MongoDB: a MongoDB client
        """
        self.logger.info("Connecting to data provider")
        self.connection = self.data_provider.connect()
        return self.connection
    
    def download_and_save_proposal(self, connection, scan):
        """
        Download and save proposals from the data source.
        
        Args:
            connection: Connection object appropriate for the provider
            scan (bool): If True, limit to recent proposals, otherwise get more
            
        Returns:
            dict: Dictionary containing proposal data by protocol
        """
        self.logger.info(f"Downloading proposals (scan mode: {scan})")
        return self.data_provider.download_proposals(connection, scan)
    
    def check_new_post(self, proposal_dict):
        """
        Check for new posts that haven't been processed before.
        
        Args:
            proposal_dict (dict): Dictionary of proposals by protocol
            
        Returns:
            DataFrame: DataFrame containing new proposals
        """
        self.logger.info("Checking for new proposals")
        existing_data_path = os.path.join(self.config["data_dir"], 'proposal_post_id.csv')
        return self.data_provider.check_new_proposals(proposal_dict, existing_data_path)
    
    def store_data(self, connection):
        """
        Store initial data into database.
        
        Args:
            connection: Connection object appropriate for the provider
            
        Returns:
            str: Timestamp when the data was stored
        """
        self.logger.info("Storing initial data into database")
        proposal_dict = self.download_and_save_proposal(connection, False)
        return self.store_into_db(proposal_dict)
    
    def store_into_db(self, proposal_dict):
        """
        Store proposal data into database.
        
        Args:
            proposal_dict (dict): Dictionary of proposals by protocol
            
        Returns:
            str: Timestamp when the data was stored
        """
        proposal_csv = pd.DataFrame()
        key_list = []
        
        for coin in proposal_dict:
            temp_key = proposal_dict[coin]['post_id']
            for key in temp_key:
                if key not in key_list:
                    key_list.append(key)
        
        proposal_csv['post_id'] = key_list
        
        output_path = os.path.join(self.config["data_dir"], 'proposal_post_id.csv')
        proposal_csv.to_csv(output_path)
        self.logger.info(f"Saved {len(key_list)} proposal IDs to {output_path}")
        
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"Data stored at {start_time}")
    
        return start_time

    def close_firebase_client(self, app):
        """
        Close the Firebase client connection.
        
        Args:
            app: Firebase app instance to close
        """
        if self.connection:
            self.logger.info("Disconnecting from data provider")
            self.data_provider.disconnect(self.connection)
            self.connection = None
        else:
            self.logger.warning("No active connection to close. Creating temporary connection for disconnection.")
            # Create a temporary connection just to disconnect (for API compatibility)
            connection = self.data_provider.connect()
            self.data_provider.disconnect(connection)

    def clean_content(self, html_text):
        """
        Clean HTML content by extracting only the text.
        
        Args:
            html_text (str): HTML content to clean
            
        Returns:
            str: Cleaned text content
        """
        soup = BeautifulSoup(html_text, 'html.parser')
        return soup.get_text()

    
    
    

    
    
