# Data Provider System

## Overview

The Governance Trading Bot features a modular data provider system that allows you to easily integrate data from different sources. This document explains the architecture and provides detailed instructions for creating custom data providers.

## Model Requirements

Before using data providers, ensure you have the required trained models installed:

1. The bot requires pre-trained models for sentiment analysis and trading decisions
2. Download the models from [Google Drive](https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing)
3. Extract and place them in the `trained_model` directory with the following structure:
   ```
   trained_model/
   ├── bullish/      # Contains models for bullish prediction
   ├── bearish/      # Contains models for bearish prediction
   └── sentiment/    # Contains models for sentiment analysis
   ```

4. Update your `.env` file to point to these directories:
   ```
   BULLISH_DIR=./trained_model/bullish
   BEARISH_DIR=./trained_model/bearish
   SENTIMENT_DIR=./trained_model/sentiment
   ```

The data provider system uses these models to analyze proposals and make trading decisions.

## Architecture

The data provider system consists of:

1. **Abstract Base Class**: `DataProvider` defines the interface that all providers must implement
2. **Factory Function**: `create_data_provider` creates provider instances based on configuration
3. **Concrete Implementations**: Ready-to-use providers (e.g., `FirebaseDataProvider`, `MongoDataProvider`)
4. **Registration System**: Dynamic provider registration mechanism in `__init__.py`

## Built-in Providers

### FirebaseDataProvider

The default provider that fetches governance proposals from Firebase Firestore.

Configuration parameters:
- `firebase_cred`: Path to Firebase credentials JSON file

### MongoDataProvider

An alternative provider that fetches governance proposals from MongoDB.

Configuration parameters:
- `mongo_connection_string`: MongoDB connection string (default: `mongodb://localhost:27017/`)
- `mongo_db_name`: MongoDB database name (default: `governance_data`)

## Creating a Custom Provider

To create a custom data provider, you need to:

1. Create a new class that inherits from `DataProvider`
2. Implement all required methods
3. Register your provider in the factory system

### Required Methods

#### `connect()`
Establishes a connection to your data source.

```python
def connect(self):
    """Connect to your data source and return a connection object."""
    # Your connection code here
    return connection_object
```

#### `disconnect(connection)`
Closes the connection to your data source.

```python
def disconnect(self, connection):
    """Disconnect from your data source."""
    # Your disconnection code here
```

#### `download_proposals(connection, scan_mode=True)`
Fetches proposals from your data source.

```python
def download_proposals(self, connection, scan_mode=True):
    """
    Fetch governance proposals from your data source.
    
    Args:
        connection: Connection object from connect()
        scan_mode: If True, fetch recent proposals (~20)
                   If False, fetch more historical data (~1000)
    
    Returns:
        dict: Dictionary mapping protocol names to DataFrames
    """
    # Your implementation here
```

The returned dictionary should map protocol names (e.g., "uniswap", "aave") to pandas DataFrames with the following columns:
- `protocol`: Protocol name 
- `post_id`: Unique identifier for the proposal
- `timestamp`: Creation timestamp
- `title`: Proposal title
- `description`: Proposal text content
- `discussion_link`: URL to discussion (optional)

#### `check_new_proposals(proposals_dict, existing_data_path)`
Identifies new proposals that haven't been processed before.

```python
def check_new_proposals(self, proposals_dict, existing_data_path):
    """
    Identify new proposals not in existing data.
    
    Args:
        proposals_dict: Dictionary from download_proposals()
        existing_data_path: Path to CSV with existing IDs
    
    Returns:
        DataFrame: DataFrame of new proposals
    """
    # Your implementation here
```

The returned DataFrame must have these columns:
- `post_id`: Unique proposal identifier
- `coin`: Protocol/coin name
- `description`: Proposal content
- `discussion_link`: Link to discussion
- `timestamp`: Creation timestamp

### Example Implementation

Here's a simplified example that pulls data from a REST API:

```python
import pandas as pd
import requests
from datetime import datetime
from .scan_proposal import DataProvider

class RestApiDataProvider(DataProvider):
    """Provider that fetches data from a REST API."""
    
    def __init__(self, config):
        self.config = config
        self.api_url = config.get('rest_api_url', 'https://api.example.com/proposals')
        self.api_key = config.get('rest_api_key')
    
    def connect(self):
        """Create a session for API requests."""
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        return session
    
    def disconnect(self, connection):
        """Close the session."""
        connection.close()
    
    def download_proposals(self, connection, scan_mode=True):
        """Fetch proposals from the API."""
        limit = 20 if scan_mode else 1000
        response = connection.get(f"{self.api_url}?limit={limit}")
        response.raise_for_status()
        data = response.json()
        
        # Group proposals by protocol
        proposals_by_protocol = {}
        
        for protocol, proposals in data.items():
            df = pd.DataFrame(columns=[
                'protocol', 'post_id', 'timestamp', 'title', 
                'description', 'discussion_link'
            ])
            
            for p in proposals:
                row = [
                    protocol,
                    p['id'],
                    p['created_at'],
                    p['title'],
                    p['body'],
                    p.get('discussion_url', '')
                ]
                
                temp_df = pd.DataFrame([row], columns=df.columns)
                df = pd.concat([df, temp_df], ignore_index=True)
                
            proposals_by_protocol[protocol] = df
            
        return proposals_by_protocol
    
    def check_new_proposals(self, proposals_dict, existing_data_path):
        """Check for new proposals."""
        try:
            existing_ids = list(pd.read_csv(existing_data_path, index_col=0)['post_id'])
        except (FileNotFoundError, pd.errors.EmptyDataError):
            existing_ids = []
        
        new_proposals = pd.DataFrame(columns=[
            "post_id", "coin", "description", "discussion_link", "timestamp"
        ])
        
        for protocol, df in proposals_dict.items():
            for _, row in df.iterrows():
                if row['post_id'] not in existing_ids:
                    new_row = {
                        "post_id": row['post_id'],
                        "coin": protocol,
                        "description": row['description'],
                        "discussion_link": row['discussion_link'],
                        "timestamp": row['timestamp']
                    }
                    new_proposals = pd.concat([
                        new_proposals, pd.DataFrame([new_row])
                    ], ignore_index=True)
                    
        return new_proposals
```

### Registering Your Provider

To register your provider, add this code to `proposal_revamp/database/__init__.py`:

```python
try:
    from .your_provider_module import YourDataProvider
    
    # Store reference to original factory function
    original_create_provider = create_data_provider
    
    # Create a new factory function that handles your provider type
    def new_create_provider(provider_type, config):
        if provider_type.lower() == 'your_type':
            return YourDataProvider(config)
        return original_create_provider(provider_type, config)
    
    # Replace the factory function
    create_data_provider = new_create_provider
except ImportError:
    pass
```

## Configuration

To use your custom data provider, set these in your `.env` file:

```
DATA_PROVIDER_TYPE=your_type
YOUR_CUSTOM_SETTING1=value1
YOUR_CUSTOM_SETTING2=value2
```

## Best Practices

1. **Error Handling**: Include robust error handling in your provider
2. **Logging**: Add appropriate logging for debugging
3. **Type Hints**: Use Python type hints for better code clarity
4. **Documentation**: Document your provider thoroughly
5. **Testing**: Create unit tests for your provider

## Troubleshooting

### Common Issues

1. **Wrong Data Format**: Make sure your returned DataFrames have all required columns
2. **Connection Issues**: Check your connection parameters and implement retry mechanisms
3. **Performance**: For large datasets, implement pagination or more efficient data handling

### Debugging

Set the environment variable `LOG_LEVEL=DEBUG` to enable detailed logging that can help diagnose issues with your data provider.

## Working with the Standalone API Server

The bot includes a standalone API server (`open_stop.py`) that can be run independently to monitor and manage trades. This server also uses the data from your data provider.

### How the API Server Interacts with Data Providers

The API server:
1. Reads the active trades from `proposal_post_live.json` in the data directory
2. Uses the `coin.json` file to map coin names to trading symbols
3. Provides endpoints to view open positions and close trades

If you're using a custom data provider, ensure:
1. Your provider correctly maintains the `proposal_post_live.json` file
2. The file follows the expected schema with fields such as `coin`, `stop_loss_id`, and `target_order_id`

### Running the API Server Separately

To run the API server with your custom data provider:

1. Make sure your environment is configured with the proper `.env` settings:
   ```
   DATA_PROVIDER_TYPE=your_provider_type
   # Your provider specific settings
   ```

2. Run the API server:
   ```bash
   python -m exchange.open_stop
   ```

3. The server will use your configured data provider to access the necessary data

