"""
Tests for the data provider factory functionality.
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from proposal_revamp.database.data_provider_factory import DataProviderFactory
from proposal_revamp.database.data_provider import DataProvider
from proposal_revamp.database.mongo_provider import MongoProvider
from proposal_revamp.database.firebase_provider import FirebaseDataProvider


class TestDataProviderFactory(unittest.TestCase):
    """Test cases for the DataProviderFactory class."""

    def test_get_mongodb_provider(self):
        """Test that the factory returns a MongoDB provider when requested."""
        provider = DataProviderFactory.get_provider("mongodb")
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, DataProvider)
        self.assertIsInstance(provider, MongoProvider)

    def test_get_firebase_provider(self):
        """Test that the factory returns a Firebase provider when requested."""
        provider = DataProviderFactory.get_provider("firebase")
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, DataProvider)
        self.assertIsInstance(provider, FirebaseDataProvider)

    def test_get_default_provider(self):
        """Test that the factory returns the default provider when no type is specified."""
        provider = DataProviderFactory.get_provider()
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, DataProvider)
        # The default provider should be MongoDB
        self.assertIsInstance(provider, MongoProvider)

    def test_get_invalid_provider(self):
        """Test that the factory raises an exception for invalid provider types."""
        with self.assertRaises(ValueError):
            DataProviderFactory.get_provider("invalid_provider_type")

    def test_register_custom_provider(self):
        """Test registering and retrieving a custom provider."""
        # Create a simple test provider
        class TestProvider(DataProvider):
            def get_proposals(self, **kwargs):
                return []
            
            def get_proposal_by_id(self, proposal_id):
                return None
            
            def get_dao_proposals(self, dao_name, **kwargs):
                return []

        # Register the provider with the factory
        DataProviderFactory.register_provider("test_provider", TestProvider)
        
        # Retrieve the provider
        provider = DataProviderFactory.get_provider("test_provider")
        self.assertIsNotNone(provider)
        self.assertIsInstance(provider, DataProvider)
        self.assertIsInstance(provider, TestProvider)


if __name__ == "__main__":
    unittest.main() 