import pandas as pd
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, Any, List, Optional
import logging

# Add parent directory to path if running as script
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from .scan_proposal import DataProvider
from utils.logging_utils import get_logger

class MongoDataProvider(DataProvider):
    """
    MongoDB implementation of DataProvider for proposal data.
    
    This provider connects to a MongoDB database and retrieves proposal data.
    """
    
    def __init__(self, config):
        """Initialize the MongoDB provider with configuration."""
        self.config = config
        self.logger = get_logger(f"{__name__}.MongoDataProvider")
    
    def connect(self):
        """Connect to MongoDB and return the client."""
        connection_string = self.config.get('mongo_connection_string', 'mongodb://localhost:27017/')
        db_name = self.config.get('mongo_db_name', 'governance_data')
        
        self.logger.info(f"Connecting to MongoDB database: {db_name}")
        client = MongoClient(connection_string)
        
        self.logger.info(f"Connected to MongoDB database: {db_name}")
        return client
    
    def disconnect(self, connection):
        """Disconnect from MongoDB."""
        if isinstance(connection, tuple):
            client, _ = connection
        else:
            client = connection
        client.close()
        self.logger.info("MongoDB connection closed")
    
    def download_proposals(self, connection, scan_mode=True):
        """
        Download proposals from MongoDB.
        
        Args:
            connection: Either a MongoDB client or a tuple (client, db)
            scan_mode: If True, limit to recent proposals, otherwise get more
            
        Returns:
            dict: Dictionary containing proposal data by protocol
        """
        # Handle connection as either a client object or a tuple
        if isinstance(connection, tuple):
            client, db = connection
        else:
            # If connection is just a MongoDB client directly, use it
            client = connection
            db_name = self.config.get('mongo_db_name', 'governance_data')
            db = client[db_name]
        
        collection = db['proposals']
        
        # Limit the number of documents based on scan_mode
        limit = 20 if scan_mode else 1000
        
        self.logger.info(f"Downloading proposals from MongoDB (limit: {limit})")
        
        # Get documents ordered by timestamp
        cursor = collection.find().sort('created_at', -1).limit(limit)
        
        # Process documents similar to Firebase provider
        protocol_list = []
        docs_list = []
        
        for doc in cursor:
            # Extract protocol from post_id or use a field in your database
            protocol = doc['post_id'].split('--')[0] if 'post_id' in doc else doc.get('protocol', 'unknown')
            if protocol not in protocol_list:
                protocol_list.append(protocol)
            docs_list.append(doc)
        
        self.logger.info(f"Found {len(docs_list)} documents across {len(protocol_list)} protocols")
        
        # Create a dictionary to store DataFrames by protocol
        proposal_dict = {}
        
        for key in protocol_list:
            # Create an empty DataFrame with required columns
            discourse_df = pd.DataFrame(columns=['protocol', 'post_id', 'timestamp', 'title', 'description', 'discussion_link'])
            
            for doc in docs_list:
                try:
                    protocol = doc.get('protocol', doc['post_id'].split('--')[0])
                    
                    if protocol == key:
                        post_id = doc['post_id']
                        timestamp = doc.get('created_at', datetime.now().isoformat())
                        title = doc.get('title', '')
                        description = doc.get('description', '')
                        discussion_link = doc.get('discussion_link', '')
                        
                        df_row = [protocol, post_id, timestamp, title, description, discussion_link]
                        temp_df = pd.DataFrame([df_row], columns=discourse_df.columns)
                        discourse_df = pd.concat([discourse_df, temp_df], ignore_index=True)
                
                except Exception as e:
                    self.logger.error(f"Error processing MongoDB document: {e}")
                    continue
            
            proposal_dict[key] = discourse_df
            self.logger.debug(f"Processed {len(discourse_df)} proposals for protocol {key}")
        
        return proposal_dict
    
    def check_new_proposals(self, proposals_dict, existing_data_path):
        """
        Check for new proposals not in existing data.
        
        This implementation is similar to the Firebase provider since
        the output format requirements are the same.
        """
        try:
            proposal_post_id = list(pd.read_csv(existing_data_path, index_col=0)['post_id'])
            self.logger.info(f"Found {len(proposal_post_id)} existing proposals in {existing_data_path}")
        except (FileNotFoundError, pd.errors.EmptyDataError):
            # If the file doesn't exist or is empty, treat all proposals as new
            self.logger.warning(f"No existing proposals found at {existing_data_path}. Treating all as new.")
            proposal_post_id = []
        
        columns = ["post_id", "coin", "description", "discussion_link", "timestamp"]
        new_row_df = pd.DataFrame(columns=columns)
        
        for key, coin_df in proposals_dict.items():
            for index, row in coin_df.iterrows():
                post_id = row['post_id']
                if post_id not in proposal_post_id:
                    coin = post_id.split("--")[0]  # Extract coin from post_id
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

# Register the provider (uncomment this to register the provider)
# from database.scan_proposal import create_data_provider
# 
# def register_mongo_provider():
#     # This can be imported and called from __init__.py
#     original_create_provider = create_data_provider
#     
#     def new_create_provider(provider_type, config):
#         if provider_type.lower() == 'mongodb':
#             return MongoDataProvider(config)
#         return original_create_provider(provider_type, config)
#     
#     # Replace the factory function
#     globals()['create_data_provider'] = new_create_provider 