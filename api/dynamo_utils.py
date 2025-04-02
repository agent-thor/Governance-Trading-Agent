"""
AWS DynamoDB utilities for the Governance Trading Bot.

This module provides classes and functions for interacting with AWS DynamoDB.
"""

import os
import time
import boto3
import json
from datetime import datetime
import sys

# Add the parent directory to sys.path for direct imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import get_config

class DynamoDBClient:
    """
    Client for interacting with AWS DynamoDB.
    
    This class provides methods for storing and retrieving data from DynamoDB.
    """
    
    def __init__(self):
        """
        Initialize the DynamoDB client.
        
        Loads AWS credentials from environment variables and sets up the client.
        """
        # Load configuration
        self.config = get_config().config
        
        # Get AWS credentials from environment variables
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Initialize DynamoDB resource with credentials if available
        if aws_access_key and aws_secret_key:
            self.dynamo = boto3.resource(
                'dynamodb',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        else:
            # Use default credentials (from ~/.aws/credentials)
            self.dynamo = boto3.resource('dynamodb', region_name=aws_region)
            print("Using default AWS credentials from environment or ~/.aws/credentials")
    
    def get_table(self, table_name):
        """
        Get a DynamoDB table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            Table: DynamoDB table object
        """
        return self.dynamo.Table(table_name)
    
    def put_item(self, table_name, item_data):
        """
        Put an item into a DynamoDB table.
        
        Args:
            table_name (str): Name of the table
            item_data (dict): Item data to put
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            table = self.get_table(table_name)
            table.put_item(Item=item_data)
            print(f"Item added to {table_name}")
            return True
        except Exception as e:
            print(f"Error putting item to DynamoDB: {e}")
            return False
    
    def get_item(self, table_name, key):
        """
        Get an item from a DynamoDB table.
        
        Args:
            table_name (str): Name of the table
            key (dict): Key to retrieve
            
        Returns:
            dict: Item data or None if not found or error occurred
        """
        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            print(f"Error getting item from DynamoDB: {e}")
            return None 