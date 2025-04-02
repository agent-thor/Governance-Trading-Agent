"""
Price utility functions for the Governance Trading Bot.

This module provides functions for fetching and processing cryptocurrency prices.
"""

import requests
import json
import os
import sys
import time

def get_coin_price(coin_symbol, base_currency='USDT'):
    """
    Get the current price of a cryptocurrency from Binance public API.
    
    Args:
        coin_symbol (str): Symbol of the coin (e.g., 'BTC', 'ETH')
        base_currency (str, optional): Base currency for the pair. Default is 'USDT'.
        
    Returns:
        float: Current price of the coin in the base currency
        None: If there was an error fetching the price
    """
    try:
        # Format the trading pair symbol
        symbol = f"{coin_symbol.upper()}{base_currency.upper()}"
        
        # Use Binance public API to get the current price
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        
        # Make the request
        response = requests.get(url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            price = float(data.get('price', 0))
            return price
        else:
            print(f"Error fetching price for {symbol}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error fetching price for {coin_symbol}: {e}")
        return None

def get_multiple_coin_prices(coin_symbols, base_currency='USDT'):
    """
    Get current prices for multiple cryptocurrencies.
    
    Args:
        coin_symbols (list): List of coin symbols (e.g., ['BTC', 'ETH'])
        base_currency (str, optional): Base currency for the pairs. Default is 'USDT'.
        
    Returns:
        dict: Dictionary mapping coin symbols to their current prices
    """
    result = {}
    
    for symbol in coin_symbols:
        price = get_coin_price(symbol, base_currency)
        result[symbol] = price
        
        # Small delay to avoid hitting rate limits
        time.sleep(0.1)
    
    return result 