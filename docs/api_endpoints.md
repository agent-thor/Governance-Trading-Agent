# API Endpoints Documentation

The trading bot provides a REST API server that runs on port 7111. This document details the available endpoints and how to use them.

## Prerequisites

Before using these API endpoints, ensure you have properly configured a data adapter. When you first run:
```bash
python -m main
```
You might encounter an error as shown in [error.png](error.png). This is because a data adapter needs to be configured first. Please refer to [Data Adapters Guide](data_adapters.md) for setting up one of the following adapters:

1. Firebase Adapter (Default)
2. MongoDB Adapter
3. Custom Adapter

## Server Setup

The API server is implemented in `exchange/open_stop.py` and can be started independently:

```bash
python -m exchange.open_stop
```

This will start a Flask server on port 7111.

## Available Endpoints

### 1. Get Open Positions

**Endpoint:** `/open_positions`  
**Method:** GET  
**Description:** Returns a list of all currently open trading positions

**Example Usage:**
```bash
curl http://localhost:7111/open_positions
```

**Example Response:**
```json
{
  "positions": [
    {
      "symbol": "uniswap",
      "quantity": 10.5,
      "type": "long",
      "stop_orderid": 12345678,
      "target_orderid": 87654321,
      "entry_price": 5.67,
      "current_price": 5.89
    }
  ]
}
```

### 2. Stop/Close Trade

**Endpoint:** `/stop_trade`  
**Method:** POST  
**Description:** Manually close an open position

**Request Parameters:**
```json
{
  "symbol": "uniswap",      // The coin name (not the trading pair)
  "quantity": 10.5,         // The amount to sell
  "stop_orderid": 12345678, // The ID of the stop loss order to cancel
  "target_orderid": 87654321, // The ID of the target price order to cancel
  "type": "long"           // Either "long" or "short"
}
```

**Example Usage:**
```bash
curl -X POST http://localhost:7111/stop_trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "uniswap",
    "quantity": 10.5,
    "stop_orderid": 12345678,
    "target_orderid": 87654321,
    "type": "long"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "message": "Position closed successfully",
  "order_id": 98765432
}
```

## Error Responses

In case of errors, the API will return appropriate HTTP status codes along with error messages:

```json
{
  "error": "Invalid request parameters",
  "details": "Missing required field: symbol"
}
```

Common status codes:
- 400: Bad Request (invalid parameters)
- 404: Position not found
- 500: Internal server error

## Rate Limiting

The API implements basic rate limiting to prevent abuse:
- Maximum 60 requests per minute for GET endpoints
- Maximum 10 requests per minute for POST endpoints

## Notes

1. All requests requiring a body should include the header: `Content-Type: application/json`
2. The server requires proper configuration in `.env` file as detailed in the main documentation
3. Make sure your data provider is properly configured before using these endpoints
4. All timestamps are returned in UTC
5. The API server relies on your configured data adapter to access proposal and position data
6. If you encounter connection errors, verify your data adapter configuration in `.env` 