# Governance Trading Bot Documentation

```
                             +------------------+
                             |                  |
                             |    Data Source   |
                             |  (Governance     |
                             |    Proposals)    |
                             |                  |
                             +--------+---------+
                                      |
                                      v
+---------------+           +---------+---------+           +-----------------+
|               |           |                   |           |                 |
|   Firebase    +<--------->+  ProposalScanner  |           |   Sentiment     |
|   Database    |           |                   |           |   Analysis      |
|               |           +---------+---------+           |                 |
+---------------+                     |                     +--------+--------+
                                      v                              |
                             +---------+---------+                   |
                             |                   |                   |
                             |    TradeLogic    +<------------------+
                             |                   |
                             +---------+---------+
                                      |
                                      v
+---------------+           +---------+---------+           +-----------------+
|               |           |                   |           |                 |
|   DynamoDB    +<--------->+   Exchange API   +---------->+   Notifications |
|   Database    |           |   (Binance/Bybit)|           |   (Slack)       |
|               |           |                   |           |                 |
+---------------+           +-------------------+           +-----------------+
```

## Overview

The Governance Trading Bot is an automated trading system that monitors cryptocurrency governance proposals, analyzes their sentiment, and executes trades based on the predicted market impact. The bot continually scans governance forums for new proposals, processes them to determine sentiment, and triggers trades when proposals are likely to positively or negatively affect a cryptocurrency's price.

## Model Training Information

The sentiment analysis and price prediction models used in this system are custom-trained on a comprehensive dataset of **6,500 governance proposals** collected from various cryptocurrency governance forums and platforms. This extensive training dataset has enabled the models to understand the nuanced language of governance proposals and their potential market impact with high accuracy.

- **Sentiment Analysis Model**: Trained on labeled governance proposals to classify sentiment as positive, negative, or neutral.
- **Bullish Price Predictor**: Trained on governance proposals with positive price impact to predict the magnitude of price increases.
- **Bearish Price Predictor**: Trained on governance proposals with negative price impact to predict the magnitude of price decreases.

The custom training on governance-specific data allows these models to perform significantly better than general-purpose sentiment models for this specialized domain.

## System Architecture

The trading bot is organized into several interconnected modules:

- **Database**: Handles data storage and retrieval (Firebase, DynamoDB, local files)
- **Core**: Contains the main trading logic and trade management
- **Services**: Provides notification (Slack) and other services
- **Models**: Contains AI models for sentiment analysis, reasoning, and price prediction
- **Exchange**: Interfaces with the Binance API for executing trades
- **Utils**: Various utility functions for handling text, time, and other functionalities
- **API**: Additional API utilities

## End-to-End Process Flow

### 1. Data Fetching and Processing

The process begins with fetching new governance proposals from sources like forums and official governance platforms:

1. The `ProposalScanner` class initializes and loads the configuration.
2. The bot creates a Firebase client connection.
3. The `download_and_save_proposal` method retrieves new governance proposals from the source.
4. The `clean_content` method uses BeautifulSoup to extract and clean text from HTML content.
5. The `check_new_post` method identifies new proposals not previously processed.
6. New proposals are stored in the database using the `store_data` and `store_into_db` methods.

### 2. Sentiment Analysis

Once new proposals are identified, the sentiment analysis process begins:

1. The proposal text is summarized using the `Summarization` class with models like Mistral.
2. The summary is passed to the `SentimentPredictor` class, which uses a RoBERTa model to determine if the sentiment is positive, negative, or neutral.
3. The sentiment analysis is enhanced using `Reasoning` class, which can use DeepSeek or OpenAI APIs to get additional sentiment insights.
4. The final sentiment is determined by combining the results from both models.
5. The system also verifies if the text is genuine or not using a classifier.

### 3. Trade Decision

Based on the sentiment analysis, the bot decides whether to execute a trade:

1. The `trigger_trade` method in the `TradeLogic` class evaluates the sentiment score.
2. For positive sentiment with a score ≥ 0.80 and verified "genuine" text, a long position is considered.
3. For negative sentiment with a score ≥ 0.80 and verified "genuine" text, a short position is considered.
4. The system also checks BTC price conditions to avoid trading during high market volatility.
5. The system checks the trade limit to ensure that:
   - There are no more than 4 active trades
   - No two trades involve the same cryptocurrency

### 4. Price Prediction and Order Execution

If a trade decision is made, the system predicts price targets and executes the trade:

1. For bullish sentiment, the `RobertaForRegressionBullish` model predicts the target price movement.
2. For bearish sentiment, the `RobertaForRegressionBearish` model predicts the target price movement.
3. The `BinanceAPI` class calculates:
   - The appropriate position size based on account balance
   - The stop loss price (typically 2% from entry)
   - The take profit target based on the predicted price movement
4. The bot then executes the trade on Binance futures, creating:
   - The main position order
   - A stop-loss order to limit potential losses
   - A take-profit order to secure gains

### 5. Trade Monitoring and Management

Once a trade is executed, the system monitors and manages it:

1. The trade details are stored in the local database (`proposal_post_live.json`).
2. The trade is saved to DynamoDB for long-term storage.
3. The `Monitor` class continually checks the status of active trades.
4. If a stop-loss or take-profit is triggered, the system updates the trade status.
5. Notifications are sent via Slack at key points (new proposal, trade entered, trade closed).

### 6. API Endpoints for User Interaction

The bot provides API endpoints to allow users to interact with the system:

1. `/stop_trade`: Allows manual closure of a trade
2. `/open_positions`: Returns currently open positions
3. `/status`: Returns the current status of the bot

## Key Components

### Sentiment Analysis Models

The system uses a combination of models to analyze sentiment:

1. **RoBERTa Model**: A fine-tuned transformer model that classifies text as positive, negative, or neutral.
2. **Reasoning Engine**: Uses large language models like DeepSeek or OpenAI to provide more nuanced sentiment analysis.
3. **Text Verification**: Classifies text as "genuine" or not to avoid trading on irrelevant or non-actionable proposals.

### Price Prediction Models

Two specialized models are used for price prediction:

1. **Bullish Price Predictor**: A RoBERTa-based regression model that predicts price increases for positive sentiment.
2. **Bearish Price Predictor**: A RoBERTa-based regression model that predicts price decreases for negative sentiment.

### Trade Execution Logic

The trade execution logic includes:

1. **Position Sizing**: Calculates position size based on account balance (typically using 0.95 * (balance * 3) / current_price).
2. **Stop Loss Setting**: Sets stop-loss at 2% from entry price to limit potential losses.
3. **Target Profit Calculation**: Sets take-profit target based on the AI model's price prediction.
4. **Precision Handling**: Adjusts the precision of order quantities and prices based on the specific cryptocurrency.

### Data Storage

The system uses multiple storage mechanisms:

1. **Firebase**: Stores the initial proposal data.
2. **Local CSV Files**: Stores processed proposals and historical data.
3. **JSON Files**: Stores active trades and configuration.
4. **DynamoDB**: Provides long-term storage of trade data for analysis.

## Supported Cryptocurrencies

The system supports trading the following cryptocurrency futures on Binance:

- 0xprotocol (ZRXUSDT)
- Aave (AAVEUSDT)
- ApeCoin (APEUSDT)
- Aragon (ANTUSDT)
- Arbitrum (ARBUSDT)
- Astar (ASTRUSDT)
- Badger (BADGERUSDT)
- Balancer (BALUSDT)
- BeamX (BEAMXUSDT)
- Compound (COMPUSDT)
- Curve (CRVUSDT)
- EtherFi (ETHFIUSDT)
- ImmutableX (IMXUSDT)
- Lido (LDOUSDT)
- MakerDAO (MKRUSDT)
- Optimism (OPUSDT)
- PancakeSwap (CAKEUSDT)
- Pendle (PENDLEUSDT)
- Polygon (MATICUSDT)
- QuickSwap (QUICKUSDT)
- Renzo (RENZOUSDT)
- StarkNet (STRKUSDT)
- Sushi (SUSHIUSDT)
- Synapse (SYNUSDT)
- Uniswap (UNIUSDT)
- Venus (XVSUSDT)

## Notifications

The system provides comprehensive notifications:

1. **New Proposals**: When a new proposal with significant sentiment is detected.
2. **Trade Execution**: When a new trade is opened, including details like:
   - Cryptocurrency
   - Direction (long/short)
   - Entry price
   - Stop-loss price
   - Target price
   - Trade ID
   - Order IDs
   - Position size
3. **Trade Closure**: When a trade is closed, either by hitting stop-loss, take-profit, or manual intervention.
4. **Errors**: Any significant errors that occur during operation.

All notifications are sent to Slack using the `SlackBot` class.

## DynamoDB Integration

The system uses Amazon DynamoDB for long-term storage of trade data:

1. **Table Structure**: Trades are stored in a table with the structure:
   - Coin: The cryptocurrency symbol
   - Description: The proposal description
   - Sentiment Score: The calculated sentiment score
   - Post ID: The unique identifier for the proposal
   - Trade Time: When the trade was executed
   - Trade ID: A unique identifier for the trade

2. **Data Retrieval**: Historical trade data can be accessed for analysis and performance evaluation.

## Configuration System

The Governance Trading Bot uses a flexible configuration system that prioritizes environment variables while maintaining backward compatibility with JSON-based configuration:

### How Configuration Works

1. **Environment Variables First**: The system first looks for configuration in environment variables, typically loaded from a `.env` file
2. **Legacy Fallback**: If essential configuration is missing, it falls back to looking in the `config.json` file
3. **Default Values**: For missing values, sensible defaults are used

This approach:
- Improves security by keeping sensitive information out of code repositories
- Enables easy configuration changes without modifying code
- Allows for different configurations in different environments (development, testing, production)

### Configuration Loading Flow

1. The `ConfigLoader` class initializes and loads the `.env` file
2. It extracts all relevant environment variables into a configuration dictionary
3. If essential parameters are missing, it attempts to load from the legacy `config.json` file
4. Configuration values are accessed via the `get_config()` function throughout the application

```python
# Example of accessing configuration
from proposal_revamp.utils import get_config

config = get_config()
data_dir = config['data_dir']
sentiment_threshold = config.get('sentiment_score_bullish', 0.80)  # With default
```

### Environment Variables Configuration

The recommended approach for configuration is to use a `.env` file in the root directory:

```
# Paths and directories
DATA_DIR=/path/to/data/directory
FIREBASE_CRED=/path/to/firebase/credentials.json
BULLISH_DIR=/path/to/bullish/model/
BEARISH_DIR=/path/to/bearish/model/
SENTIMENT_DIR=/path/to/sentiment/model/

# Binance API credentials
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Slack integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# AI API keys
OPENAI_KEY=your_openai_api_key
AGENT_ENDPOINT=https://your-agent-endpoint.com/api/v1/
AGENT_KEY=your_agent_api_key

# AWS credentials for DynamoDB
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Trading parameters
COUNTDOWN_TIME=60
SENTIMENT_SCORE_BULLISH=0.80
SENTIMENT_SCORE_BEARISH=0.80
TRADE_AMOUNT=5000
LEVERAGE=3
STOP_LOSS_PERCENT=2
MAX_TRADES=4
```

### Key Configuration Parameters

1. **Paths and Directories**:
   - `DATA_DIR`: Directory where trade data and proposal information is stored
   - `FIREBASE_CRED`: Path to Firebase credentials JSON file
   - `BULLISH_DIR`, `BEARISH_DIR`, `SENTIMENT_DIR`: Paths to AI model directories

2. **API Credentials**:
   - `BINANCE_API_KEY` and `BINANCE_API_SECRET`: Binance API credentials
   - `OPENAI_KEY`: OpenAI API key for reasoning models
   - `AGENT_ENDPOINT` and `AGENT_KEY`: DeepSeek API endpoints and credentials

3. **Notification Settings**:
   - `SLACK_WEBHOOK_URL`: Webhook URL for Slack notifications

4. **Trading Parameters**:
   - `COUNTDOWN_TIME`: Seconds between proposal checks (default: 60)
   - `SENTIMENT_SCORE_BULLISH`: Threshold for bullish sentiment to trigger trades (default: 0.80)
   - `SENTIMENT_SCORE_BEARISH`: Threshold for bearish sentiment to trigger trades (default: 0.80)
   - `TRADE_AMOUNT`: Base amount for position sizing (default: 5000)
   - `LEVERAGE`: Leverage multiplier for position sizing (default: 3)
   - `STOP_LOSS_PERCENT`: Stop loss percentage (default: 2%)
   - `MAX_TRADES`: Maximum number of concurrent trades (default: 4)

### Legacy Configuration (Deprecated)

The system previously used `config.json` for configuration. While this is still supported for backward compatibility, using environment variables through a `.env` file is recommended for better security, especially for sensitive information like API keys.

## Running the Bot

The bot is designed to run continuously, scanning for new proposals at regular intervals:

1. The main entry point is `main.py`, which creates a `GovernanceTradingBot` instance.
2. The bot initializes all required components, including the Binance client, sentiment models, and database connections.
3. It enters a continuous loop, scanning for new proposals at specified intervals.
4. The API server runs on port 7111, allowing user interaction while the bot is running.
5. The bot handles errors gracefully, attempting to restart when non-fatal errors occur.
6. Signal handlers ensure graceful shutdown when the bot is terminated.

## Best Practices

1. **Test in Testnet First**: Before running with real money, test the system on Binance's testnet.
2. **Start with Small Position Sizes**: Adjust the position sizing calculation to start with smaller trades.
3. **Monitor Regularly**: Use the API endpoints to monitor open positions and bot status.
4. **Set Up Alerting**: Ensure Slack notifications are properly configured to be alerted to any issues.
5. **Backup Data**: Regularly backup the data directory to prevent data loss.

## Technical Architecture

The bot uses a class-based architecture for better organization and maintainability:

1. **GovernanceTradingBot**: Main class that orchestrates the entire process
2. **ProposalScanner**: Handles fetching and processing proposals
3. **TradeLogic**: Contains the core trading logic and decision-making
4. **BinanceAPI**: Interfaces with the Binance exchange
5. **SlackBot**: Handles notifications to Slack
6. **SentimentPredictor**: Analyzes sentiment of proposals
7. **Monitor**: Monitors and manages active trades

This modular design allows for easier maintenance, testing, and extension of functionality.

## Making the System Modular

The system is designed with modularity in mind, allowing for easy replacement of components with alternative implementations:

### Integrating Alternative Data Sources

To integrate a different data source for governance proposals:

1. **Create a Data Source Adapter**: 
   - Implement a class that follows the same interface as `ProposalScanner`
   - The adapter should implement the following key methods:
     - `download_and_save_proposal`: Retrieve proposals from your data source
     - `clean_content`: Process and clean the proposal content
     - `check_new_post`: Identify new proposals

2. **Example Implementation for a REST API Data Source**:

```python
class CustomAPIProposalScanner(ProposalScanner):
    def __init__(self, config_path='config.json'):
        super().__init__(config_path)
        self.api_endpoint = self.config.get('custom_api_endpoint')
        self.api_key = self.config.get('custom_api_key')
    
    def download_and_save_proposal(self, db, scan=True):
        # Make API call to fetch proposals
        response = requests.get(
            self.api_endpoint,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        proposals = response.json()
        
        # Convert to the expected format
        proposal_dict = {}
        for proposal in proposals:
            proposal_dict[proposal['id']] = {
                'timestamp': proposal['created_at'],
                'coin': proposal['project'],
                'description': proposal['content'],
                'discussion_link': proposal['url']
            }
        
        return proposal_dict
```

3. **Configuration Updates**:
   - Add the necessary configuration parameters to `config.json`:
     ```json
     {
       "custom_api_endpoint": "https://api.example.com/governance-proposals",
       "custom_api_key": "your-api-key"
     }
     ```

4. **Dependency Injection**:
   - Update the main application to use your custom scanner:
     ```python
     # In main.py
     proposal_scanner = CustomAPIProposalScanner(config_path)
     bot = GovernanceTradingBot(config_path, proposal_scanner=proposal_scanner)
     ```

### Integrating Bybit or Other Exchange APIs

The system can be extended to use Bybit or other exchanges by implementing a compatible exchange adapter:

1. **Create an Exchange Adapter**:
   - Implement a class that follows the same interface as `BinanceAPI`
   - The adapter should implement key methods for trading:
     - `create_buy_order_long`
     - `create_buy_order_short`
     - `get_current_price`
     - Similar methods as required

2. **Example Implementation for Bybit**:

```python
from pybit.unified_trading import HTTP

class BybitAPI(ExchangeBase):
    def __init__(self, config_path='config.json'):
        # Load configuration
        with open(config_path, 'r') as json_file:
            self.config = json.load(json_file)
        
        # Initialize Bybit client
        self.client = HTTP(
            testnet=self.config.get('use_testnet', False),
            api_key=self.config.get('BYBIT_API_KEY'),
            api_secret=self.config.get('BYBIT_API_SECRET')
        )
        
        # Load coin configurations
        with open('coin.json', 'r') as json_file:
            self.coin_dict = json.load(json_file)
    
    def get_current_price(self, symbol):
        response = self.client.get_tickers(
            category="linear",
            symbol=symbol
        )
        return response['result']['list'][0]['lastPrice']
    
    def create_buy_order_long(self, coin, target_price):
        symbol = self.coin_dict[coin]
        quantity = self.get_quantity(symbol)
        
        # Create main position order
        order = self.client.place_order(
            category="linear",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=quantity
        )
        
        # Implement stop loss and take profit orders
        # ...
        
        return buying_price, trade_id, stop_loss_price, stop_loss_orderID, target_orderId, targetPrice, quantity
```

3. **Configuration Updates**:
   - Update `config.json` with Bybit-specific parameters:
     ```json
     {
       "BYBIT_API_KEY": "your-bybit-api-key",
       "BYBIT_API_SECRET": "your-bybit-api-secret",
       "use_testnet": false
     }
     ```

4. **Dependency Injection**:
   - Update the main application to use your custom exchange:
     ```python
     # In main.py
     exchange_api = BybitAPI(config_path)
     bot = GovernanceTradingBot(config_path, exchange_api=exchange_api)
     ```

### Creating a Plugin System

For a more advanced modular approach, implement a plugin system:

1. **Define Plugin Interfaces**:
   - Create abstract base classes for different plugin types:
     - `DataSourcePlugin`
     - `ExchangePlugin`
     - `NotificationPlugin`

2. **Plugin Registry**:
   - Implement a plugin registry to discover and load plugins:
     ```python
     class PluginRegistry:
         def __init__(self):
             self.data_sources = {}
             self.exchanges = {}
             self.notification_services = {}
         
         def register_data_source(self, name, plugin_class):
             self.data_sources[name] = plugin_class
         
         def get_data_source(self, name, config):
             return self.data_sources[name](config)
     ```

3. **Configuration-Based Plugin Selection**:
   - Allow selecting plugins via configuration:
     ```json
     {
       "plugins": {
         "data_source": "custom_api",
         "exchange": "bybit",
         "notification": "slack"
       }
     }
     ```

This modular approach allows for easy customization of the system to use different data sources and exchanges without modifying the core logic of the application. 