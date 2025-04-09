# Governance Trading Bot

An automated trading system that monitors cryptocurrency governance proposals, analyzes their sentiment, and executes trades based on the predicted market impact.

## Documentation

For detailed information about specific aspects of the bot, please refer to these documentation files:

- [Data Providers Documentation](docs/data_providers.md) - How to create and use custom data sources
- [Trade Flow Documentation](docs/trade_flow.md) - Complete trading workflow and sentiment analysis process

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Ollama Installation for Text Summarization

The governance bot uses Ollama with Mistral 7B for text summarization of governance proposals. Follow these steps to install Ollama:

1. Install Ollama on your system:
   - **macOS/Linux/Windows**: Download from [Ollama's official website](https://ollama.com/download)

2. After installation, pull the Mistral 7B model:
   ```bash
   ollama pull mistral:7b
   ```

3. Verify the installation by running:
   ```bash
   ollama list
   ```
   You should see `mistral:7b` in the list of available models.

4. Ensure Ollama is running when you start the bot. You can run it in the background with:
   ```bash
   ollama serve
   ```

For more information, visit the [Ollama documentation](https://github.com/ollama/ollama).

### Video Tutorial for Next Steps After Ollama Installation

After you have installed Ollama, this video tutorial will guide you through the next steps which are described in the Manual Setup section below:

[Manual Setup](https://drive.google.com/file/d/1kxwfw4dTZgtsJcjvL0yZmiGX4cMvjcdK/view?usp=sharing)

The video provides a visual walkthrough of the manual setup process, making it easier to follow the installation steps.

### Manual Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/governance_trade.git
   cd governance_trade
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies (choose one of the following options):

   **Option 1: Using requirements.txt** (recommended)
   ```
   pip install -r requirements.txt
   ```

   **Option 2: Install as a development package**
   ```
   pip install -e .
   ```

4. Create a `.env` file with your configuration (see below)

5. Ensure `coin.json` and `precision.json` are in the root directory

6. Create a data directory:
   ```
   mkdir -p data
   ```

### Dependencies

The project depends on several Python packages. You can view the complete list in the `requirements.txt` file. Key dependencies include:

- **Data handling**: pandas, numpy
- **Database**: firebase-admin, pymongo, boto3 (optional, only for DynamoDB trade history)
- **Trading**: python-binance
- **AI/ML**: torch, transformers, nltk, langchain-community, openai
- **Web services**: flask, requests
- **Text processing**: beautifulsoup4
- **External tool**: Ollama (installed separately)
- **Optional AI Service**: Deepseek (if not provided, the bot will use only OpenAI and trained models)
- **Optional Database**: DynamoDB (only needed if you want to save trade history in AWS)

To install all dependencies at once:
```bash
pip install -r requirements.txt
```

### Environment Variables

A template `.env.example` file is provided with all the required fields. Copy this file to create your own `.env` file:

```bash
cp .env.example .env
```

Then edit the `.env` file with your actual credentials:

```
# Paths and directories
DATA_DIR=./data
FIREBASE_CRED=/path/to/firebase/credentials.json
BULLISH_DIR=./trained_model/bullish
BEARISH_DIR=./trained_model/bearish
SENTIMENT_DIR=./trained_model/sentiment

# Binance API credentials
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Slack integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# AI API keys
OPENAI_KEY=your_openai_api_key
# Optional: Deepseek API credentials (if not provided, the bot will use only OpenAI and trained models)
AGENT_ENDPOINT=https://your-agent-endpoint.com/api/v1/
AGENT_KEY=your_agent_api_key

# Optional: AWS DynamoDB credentials (only needed if you want to save trade history)
# If not provided, trades will only be stored locally in JSON files
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# Trading parameters
COUNTDOWN_TIME=60
SENTIMENT_SCORE_BULLISH=0.80
SENTIMENT_SCORE_BEARISH=0.80
TRADE_AMOUNT=5000
LEVERAGE=3
STOP_LOSS_PERCENT=2
MAX_TRADES=4

# Data Provider Configuration
DATA_PROVIDER_TYPE=firebase
```

### Downloading the Trading Model

The bot requires pre-trained models for sentiment analysis and trading decisions. You can obtain these models in two ways:

#### Option 1: Automatic Download (Recommended)

Run the included download script to automatically download and set up the models:

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Run the download script
python download_models.py
```

This script will:
1. Create the necessary model directories
2. Download the models from Google Drive
3. Extract them to the correct locations
4. Verify the installation

#### Option 2: Manual Download

If the automatic download doesn't work, follow these steps:

1. Create a `trained_model` directory in the project root:
   ```bash
   mkdir -p trained_model/bullish trained_model/bearish trained_model/sentiment
   ```

2. Download the model file from Google Drive:
   [Download Trading Models](https://drive.google.com/file/d/1zjDwBqagqUPZ8H-igv4KlxdyFA8S4pe3/view?usp=sharing)

3. Extract the downloaded zip file:
   ```bash
   unzip trading_model_Dec\ 2.zip -d temp_models/
   ```

4. Move the extracted models to the appropriate directories:
   ```bash
   # Move model files to their respective directories
   cp -r temp_models/bullish/* trained_model/bullish/
   cp -r temp_models/bearish/* trained_model/bearish/
   cp -r temp_models/sentiment/* trained_model/sentiment/
   
   # Clean up temporary directory
   rm -rf temp_models
   ```

5. Verify the models are correctly installed:
   ```bash
   ls -la trained_model/bullish/
   ls -la trained_model/bearish/
   ls -la trained_model/sentiment/
   ```

Make sure the paths in your `.env` file point to these model directories.

## Running the Bot

After installation, you can run the bot using one of the following methods:

### Method 1: Using the Python Module (Recommended)

```
# If using the virtual environment
source venv/bin/activate

# Run as a Python module
python -m main
```

### Method 2: Direct Script Execution

```
# If using the virtual environment
source venv/bin/activate

# Run the main.py file directly
python main.py
```

Any of these methods will start the trading bot, which will:
1. Initialize all components
2. Scan for new governance proposals
3. Analyze sentiment
4. Execute trades based on analysis
5. Monitor existing trades

## API Access

While the bot is running, you can access the API on port 7111:

- `/open_positions` (GET): View currently open positions
- `/stop_trade` (POST): Manually close a trade
- `/status` (GET): Check the bot's current status

## Running API Server Separately

The bot includes a standalone API server (`open_stop.py`) that you can run independently from the main bot. This is useful if you want to monitor and manage trades without starting the full trading bot.

### Starting the API Server

To run the API server separately:

```bash
# If using the virtual environment
source venv/bin/activate

# Run the API server directly
python -m exchange.open_stop
```

This will start a Flask server on port 7111 with the following endpoints:

- `/open_positions` (GET): Get a list of currently open positions
- `/stop_trade` (POST): Manually close a position

### Using the `/stop_trade` Endpoint

To close a position, send a POST request to `/stop_trade` with the following JSON payload:

```json
{
  "symbol": "uniswap",
  "quantity": 10.5,
  "stop_orderid": 12345678,
  "target_orderid": 87654321,
  "type": "long"
}
```

Parameters:
- `symbol`: The coin name (not the trading pair)
- `quantity`: The amount to sell
- `stop_orderid`: The ID of the stop loss order to cancel
- `target_orderid`: The ID of the target price order to cancel
- `type`: Either "long" or "short" (depending on the type of trade you have taken)

The values for these parameters should match the specific trade you want to close. You can get the details of your open positions by calling the `/open_positions` endpoint first.

### Example API Usage

Using curl:

```bash
# Get open positions
curl http://localhost:7111/open_positions

# Close a position
curl -X POST http://localhost:7111/stop_trade \
  -H "Content-Type: application/json" \
  -d '{"symbol":"uniswap","quantity":10.5,"stop_orderid":12345678,"target_orderid":87654321,"type":"long"}'
```

Using Python:

```python
import requests
import json

# Get open positions
response = requests.get('http://localhost:7111/open_positions')
positions = response.json()
print(positions)

# Close a position
data = {
    "symbol": "uniswap",
    "quantity": 10.5,
    "stop_orderid": 12345678,
    "target_orderid": 87654321,
    "type": "long"
}
response = requests.post('http://localhost:7111/stop_trade', json=data)
result = response.json()
print(result)
```

## Custom Data Providers

The bot uses a modular data provider system that allows you to integrate data from different sources. By default, it uses Firebase, but you can implement your own data provider to fetch governance proposals from any platform.

### Using an Existing Data Provider

To use an alternative data provider (e.g., MongoDB), update your `.env` file:

```
# Data Provider Configuration
DATA_PROVIDER_TYPE=mongodb
MONGO_CONNECTION_STRING=mongodb://localhost:27017/
MONGO_DB_NAME=governance_data
```

### Creating a Custom Data Provider

To create your own data provider:

1. Create a new file in the `proposal_revamp/database` directory, e.g., `custom_provider.py`:

```python
import pandas as pd
from typing import Dict, Any

from .scan_proposal import DataProvider

class CustomDataProvider(DataProvider):
    """Your custom data provider implementation."""
    
    def __init__(self, config):
        self.config = config
    
    def connect(self):
        """Connect to your data source."""
        # Implement connection to your data source
        # Return a connection object that will be passed to other methods
        return connection_object
    
    def disconnect(self, connection):
        """Disconnect from your data source."""
        # Close any open connections
        pass
    
    def download_proposals(self, connection, scan_mode=True):
        """
        Download proposals from your data source.
        
        Args:
            connection: The connection object from connect()
            scan_mode: If True, limit to recent proposals (e.g., 20)
                       If False, fetch more historical data (e.g., 1000)
        
        Returns:
            dict: Dictionary mapping protocols to DataFrames containing proposal data
                  Each DataFrame must have columns: protocol, post_id, timestamp, 
                  title, description, discussion_link
        """
        # Implement fetching data from your source
        # Return data in the expected format
        proposal_dict = {}
        # ... your implementation ...
        return proposal_dict
    
    def check_new_proposals(self, proposals_dict, existing_data_path):
        """
        Identify new proposals that haven't been processed before.
        
        Args:
            proposals_dict: The dictionary returned by download_proposals
            existing_data_path: Path to the CSV file with existing proposal IDs
        
        Returns:
            pd.DataFrame: DataFrame with columns: post_id, coin, description,
                          discussion_link, timestamp
        """
        # Identify new proposals and return as DataFrame
        # Must have specific columns for downstream processing
        new_row_df = pd.DataFrame(columns=["post_id", "coin", "description", 
                                          "discussion_link", "timestamp"])
        # ... your implementation ...
        return new_row_df
```

2. Register your provider in `proposal_revamp/database/__init__.py`:

```python
try:
    from .custom_provider import CustomDataProvider
    
    original_create_provider = create_data_provider
    
    def new_create_provider(provider_type, config):
        if provider_type.lower() == 'custom':
            return CustomDataProvider(config)
        return original_create_provider(provider_type, config)
    
    create_data_provider = new_create_provider
except ImportError:
    pass
```

3. Set `DATA_PROVIDER_TYPE=custom` in your `.env` file

### Required Data Format

For your custom data provider to work with the bot, ensure:

1. The `download_proposals` method returns a dictionary of DataFrames with columns:
   - `protocol`: The protocol name (e.g., "uniswap")
   - `post_id`: A unique identifier for the proposal
   - `timestamp`: When the proposal was created
   - `title`: Proposal title
   - `description`: Proposal content
   - `discussion_link`: Link to discussion (optional)

2. The `check_new_proposals` method returns a DataFrame with columns:
   - `post_id`: Unique proposal identifier
   - `coin`: Protocol/coin name
   - `description`: Proposal content
   - `discussion_link`: Link to discussion (optional)
   - `timestamp`: When the proposal was created

This ensures the bot can process the data correctly for sentiment analysis and trading decisions.

## Conclusion

The Governance Trading Bot provides an automated solution for monitoring cryptocurrency governance proposals and executing trades based on sentiment analysis. By following this documentation, you should be able to:

1. Install and configure the bot with your preferred settings
2. Run the bot to monitor proposals and execute trades
3. Use the API to manage trades manually when needed
4. Customize the data provider to fetch proposals from different sources

For additional support or to report issues, please visit the [GitHub repository](https://github.com/yourusername/governance_trade) or contact the development team.

Happy trading!

