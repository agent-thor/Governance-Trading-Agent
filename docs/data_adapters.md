# Data Adapters Guide

This guide explains how to configure and use different data adapters for the Governance Trading Agent.

## Available Data Adapters

The agent supports multiple data adapters for fetching governance proposals:

1. **Firebase Adapter** (Default)
2. **MongoDB Adapter**
3. **Custom Adapter**

## Configuring Data Adapters

### Firebase Adapter (Default)

1. Set in `.env`:
   ```
   DATA_PROVIDER_TYPE=firebase
   FIREBASE_CRED=/path/to/firebase/credentials.json
   ```

2. Place your Firebase credentials JSON file in the specified location

### MongoDB Adapter

1. Set in `.env`:
   ```
   DATA_PROVIDER_TYPE=mongodb
   MONGO_CONNECTION_STRING=mongodb://localhost:27017/
   MONGO_DB_NAME=governance_data
   ```

2. Ensure MongoDB is running and accessible

## Creating Custom Data Adapters

To create your own data adapter:

1. Create a new file in `proposal_revamp/database/` (e.g., `custom_adapter.py`)
2. Implement the required methods:
   - `connect()`
   - `disconnect()`
   - `download_proposals()`
   - `check_new_proposals()`

See the [Custom Data Providers](custom_providers.md) documentation for detailed implementation guidelines.

## Required Data Format

Your data adapter must provide data in the following format:

### Proposal Data Format
- `protocol`: Protocol name (e.g., "uniswap")
- `post_id`: Unique proposal identifier
- `timestamp`: Creation timestamp
- `title`: Proposal title
- `description`: Proposal content
- `discussion_link`: Link to discussion (optional)

### New Proposals Format
- `post_id`: Unique identifier
- `coin`: Protocol/coin name
- `description`: Proposal content
- `discussion_link`: Link to discussion
- `timestamp`: Creation timestamp

## Switching Between Adapters

To switch between adapters:

1. Update the `DATA_PROVIDER_TYPE` in your `.env` file
2. Ensure the required credentials for the chosen adapter are configured
3. Restart the agent

## Troubleshooting

Common issues and solutions:

1. **Connection Errors**
   - Verify credentials
   - Check network connectivity
   - Ensure the data source is running

2. **Data Format Issues**
   - Verify data structure matches required format
   - Check for missing required fields
   - Ensure timestamps are in the correct format

3. **Performance Issues**
   - Optimize query patterns
   - Implement caching if needed
   - Consider batch processing for large datasets 