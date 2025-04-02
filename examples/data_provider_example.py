#!/usr/bin/env python3
"""
Example demonstrating the usage of the DataProvider abstraction layer.
This shows how to fetch and process governance proposals using different data providers.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to allow importing from the proposal_revamp package
parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from proposal_revamp.database.data_provider_factory import DataProviderFactory
from proposal_revamp.database.scan_proposal import ProposalScanner
from proposal_revamp.utils.logging_utils import setup_logging

def main():
    # Set up logging
    setup_logging()
    
    print("Data Provider Abstraction Layer Example")
    print("-" * 50)
    
    # Example 1: Using the default MongoDB provider
    print("\nExample 1: Using MongoDB Provider")
    mongo_provider = DataProviderFactory.get_provider("mongodb")
    print(f"Provider type: {type(mongo_provider).__name__}")
    
    # Initialize the ProposalScanner with the MongoDB provider
    scanner = ProposalScanner(data_provider=mongo_provider)
    
    # Get a sample of proposals
    print("Fetching sample proposals...")
    proposals = scanner.get_proposals(limit=3)
    
    if proposals and len(proposals) > 0:
        print(f"Successfully fetched {len(proposals)} proposals")
        # Display a sample proposal
        sample = proposals[0]
        print("\nSample Proposal:")
        print(f"Title: {sample.get('title', 'N/A')}")
        print(f"DAO: {sample.get('dao_name', 'N/A')}")
        print(f"Status: {sample.get('status', 'N/A')}")
    else:
        print("No proposals found. Ensure your database is properly configured.")
    
    # Example 2: Using Firebase provider (if configured)
    try:
        print("\nExample 2: Using Firebase Provider")
        firebase_provider = DataProviderFactory.get_provider("firebase")
        print(f"Provider type: {type(firebase_provider).__name__}")
        
        # Initialize the ProposalScanner with the Firebase provider
        firebase_scanner = ProposalScanner(data_provider=firebase_provider)
        
        # Get a sample of proposals
        print("Fetching sample proposals from Firebase...")
        firebase_proposals = firebase_scanner.get_proposals(limit=3)
        
        if firebase_proposals and len(firebase_proposals) > 0:
            print(f"Successfully fetched {len(firebase_proposals)} proposals from Firebase")
        else:
            print("No proposals found in Firebase or Firebase not configured.")
    except Exception as e:
        print(f"Firebase provider error: {str(e)}")
        print("Make sure Firebase is properly configured in your .env file.")
    
    print("\nExample 3: Creating a Custom Provider")
    print("See the documentation in README.md for instructions on creating custom data providers.")

if __name__ == "__main__":
    main() 