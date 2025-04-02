"""
Database functionality for the Governance Trading Bot.

This package contains modules for scanning proposals, storing data,
and interacting with the database systems.
"""

import logging
import sys, os

# Add parent directory to path if running as script
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use absolute import instead of relative import
from utils.logging_utils import get_logger

# Initialize logger
logger = get_logger(__name__)

from .scan_proposal import ProposalScanner, create_firebase_client, close_firebase_client
from .scan_proposal import DataProvider, create_data_provider

# Register MongoDB provider if available
try:
    from .mongo_provider import MongoDataProvider
    
    # Update the create_data_provider function to handle MongoDB
    original_create_provider = create_data_provider
    
    def new_create_provider(provider_type, config):
        provider_type = provider_type.lower()
        if provider_type == 'mongodb':
            logger.info("Using MongoDB provider as specified")
            return MongoDataProvider(config)
        elif provider_type == 'firebase':
            logger.info("Using Firebase provider as specified")
            return original_create_provider(provider_type, config)
        else:
            logger.warning(f"Provider type '{provider_type}' not recognized, using default provider")
            return original_create_provider(provider_type, config)
    
    # Replace the factory function
    create_data_provider = new_create_provider
    
    logger.info("MongoDB provider registered successfully.")
except ImportError:
    # MongoDB provider not available - that's okay
    logger.info("MongoDB provider not available. Using default providers only.")
    pass

# Exports
__all__ = [
    'ProposalScanner',
    'create_firebase_client',
    'close_firebase_client',
    'DataProvider',
    'create_data_provider'
] 