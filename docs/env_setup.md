# Environment Variables Setup Guide

This guide details all environment variables used in the Governance Trading Agent, their descriptions, and whether they are required or optional.

## Required Environment Variables

### Paths and Directories
- `DATA_DIR`: Directory for storing data files (default: ./data)
- `FIREBASE_CRED`: Path to Firebase credentials JSON file
- `BULLISH_DIR`: Directory for bullish model files (default: ./trained_model/bullish)
- `BEARISH_DIR`: Directory for bearish model files (default: ./trained_model/bearish) 
- `SENTIMENT_DIR`: Directory for sentiment model files (default: ./trained_model/sentiment)

### API Credentials
- `BINANCE_API_KEY`: Your Binance API key for trading operations
- `BINANCE_API_SECRET`: Your Binance API secret key for trading operations

### AI Configuration
- `OPENAI_KEY`: Your OpenAI API key (required)
- `AGENT_ENDPOINT`: Endpoint URL for agent API (optional)
- `AGENT_KEY`: API key for agent access (optional)
- `OLLAMA_HOST`: Host URL for Ollama (default: http://localhost:11434)
- `OLLAMA_MODEL`: Model name for Ollama (default: mistral:7b)

### AWS Configuration (only required if you want to save taken trade on db otherwise it will save locally)
- `AWS_ACCESS_KEY_ID`: AWS access key for DynamoDB 
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for DynamoDB
- `AWS_REGION`: AWS region (default: us-east-1)

### Data Provider Configuration
- `DATA_PROVIDER_TYPE`: Type of data provider to use (e.g., "firebase", "mongodb")
- `MONGO_CONNECTION_STRING`: MongoDB connection string (if using MongoDB)
- `MONGO_DB_NAME`: MongoDB database name (if using MongoDB)

### Notifications
- `SLACK_WEBHOOK_URL`: Slack webhook URL for notifications

### Trading Parameters
- `COUNTDOWN_TIME`: Time in seconds for countdown (default: 60)
- `SENTIMENT_SCORE_BULLISH`: Score threshold for bullish sentiment (default: 0.80)
- `SENTIMENT_SCORE_BEARISH`: Score threshold for bearish sentiment (default: 0.80)
- `TRADE_AMOUNT`: Amount to trade in USD (default: 5000)
- `LEVERAGE`: Trading leverage multiplier (default: 3)
- `STOP_LOSS_PERCENT`: Stop loss percentage (default: 2)
- `MAX_TRADES`: Maximum number of concurrent trades (default: 4)

### Logging
- `LOG_LEVEL`: Logging level (default: INFO)

## Example .env File

```env
# Paths and Directories
DATA_DIR=./data
FIREBASE_CRED=path/to/firebase/credentials.json
BULLISH_DIR=./trained_model/bullish
BEARISH_DIR=./trained_model/bearish
SENTIMENT_DIR=./trained_model/sentiment

# API Credentials
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# AI Configuration
OPENAI_KEY=your_openai_api_key
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# AWS Configuration (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Data Provider Configuration
DATA_PROVIDER_TYPE=firebase
MONGO_CONNECTION_STRING=your_mongo_connection_string
MONGO_DB_NAME=your_mongo_db_name

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Trading Parameters
COUNTDOWN_TIME=60
SENTIMENT_SCORE_BULLISH=0.80
SENTIMENT_SCORE_BEARISH=0.80
TRADE_AMOUNT=5000
LEVERAGE=3
STOP_LOSS_PERCENT=2
MAX_TRADES=4

# Logging
LOG_LEVEL=INFO
```

