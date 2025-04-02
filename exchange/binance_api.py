from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from binance.enums import *
import json
import os
import math
import pandas as pd
import sys

# Use direct imports instead of relative imports
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from services import post_error_to_slack
from utils import get_config


class BinanceAPI:
    """
    Class for handling Binance API interactions.
    
    This class encapsulates all Binance API functionality, including trading,
    account information, and price data retrieval.
    """
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the Binance API client with configurations.
        
        Args:
            config_path (str): Path to the configuration file
        """
        # Load configuration using environment variables or fallback to config.json
        self.config = get_config().config
        
        # Get the path to the exchange directory where the json files are stored
        exchange_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load coin configuration
        with open(os.path.join(exchange_dir, 'coin.json'), 'r') as json_file:
            self.coin_dict = json.load(json_file)
        
        # Load precision configuration
        with open(os.path.join(exchange_dir, 'precision.json'), 'r') as json_file:
            self.precision_dict = json.load(json_file)
        
        # Initialize the Binance client
        self.client = Client(
            self.config.get('binance_api_key'), 
            self.config.get('binance_api_secret'), 
            tld='com'
        )
    
    def get_account_info(self):
        """Get account information from Binance."""
        account_info = self.client.get_account()
        
        return account_info
    
    def get_balance_future(self):
        """Get futures account balance."""
        balance = self.client.futures_account_balance()[4]['balance']
        
        return float(balance)
    
    def get_current_price(self, symbol):
        """
        Get current price for a symbol.
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            str: Current price
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        
        return ticker['price']
    
    def get_last_5_days_price(self, coin_name, initial_date, final_date, interval="1d"):
        """
        Get price data for the last 5 days for a coin.
        
        Args:
            coin_name (str): Name of the coin
            initial_date (str): Start date
            final_date (str): End date
            interval (str): Time interval
            
        Returns:
            dict: Price data organized by date
        """
        symbol_name = self.coin_dict[coin_name]
        
        # Get one day after final_date to ensure we include final_date in results
        final_date_obj = pd.to_datetime(final_date) + pd.DateOffset(days=1)
        end_str = final_date_obj.strftime('%Y-%m-%d')
        
        # Always use daily interval
        interval = "1d"
        
        klines = self.client.get_historical_klines(
            symbol=symbol_name,
            interval=interval,
            start_str=initial_date,
            end_str=end_str  # Using the adjusted end date
        )
        
        # Create empty result dictionary
        result_dict = {}
        
        for kline in klines:
            # Convert timestamp (milliseconds) to date string
            timestamp_ms = kline[0]
            date_obj = pd.to_datetime(timestamp_ms, unit='ms')
            date_str = date_obj.strftime('%Y-%m-%d')
            
            # Extract OHLC values and convert to float
            ohlc_data = {
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4])
            }
            
            # Add to result dictionary
            result_dict[date_str] = ohlc_data
        
        # Check if we retrieved all expected dates
        expected_dates = pd.date_range(start=initial_date, end=final_date)
        expected_date_strs = [date.strftime('%Y-%m-%d') for date in expected_dates]
        
        missing_dates = set(expected_date_strs) - set(result_dict.keys())
        if missing_dates:
            print(f"Warning: No data found for dates: {missing_dates}")
        
        return result_dict
    
    def get_quantity(self, symbol):
        """
        Calculate the trading quantity based on balance and current price.
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            str: Calculated quantity formatted to appropriate precision
        """
        # Use configured trade amount from environment variable if available
        balance = self.config.get('trade_amount', 5000)
        # Use leverage from environment variable if available
        leverage = self.config.get('leverage', 3)
        
        print(f"Balance is {balance}, using leverage {leverage}x")
        print(f"Taking trade balance of: {balance}")
            
        current_price = self.get_current_price(symbol)
        quantity = 0.95 * ((balance * leverage) / float(current_price))
        print("quantity is ", quantity)
    
        coin_precision = self.precision_dict[symbol]    
        rounded_quantity = format(quantity, f".{coin_precision}f")   
        
        if float(rounded_quantity) > quantity:
            rounded_quantity = math.floor(quantity * 10) / 10
    
        return rounded_quantity
    
    def update_stop_loss(self, trade_type, symbol, previous_stop_loss_orderId):
        """
        Update the stop loss order.
        
        Args:
            trade_type (str): Type of trade ('long' or 'short')
            symbol (str): Trading pair symbol
            previous_stop_loss_orderId: ID of the previous stop loss order
            
        Returns:
            tuple: Order ID and stop price
        """
        buying_price = self.get_current_price(symbol)
        
        #cancel the previous_stop_loss_order
        try:
            result = self.client.futures_cancel_order(symbol=symbol, orderId=previous_stop_loss_orderId)
            print("Stop loss order canceled successfully.")
        except Exception as e:
            print("Failed cancelling stop loss", e)
        
        #placing stop loss order
        stop_loss_percent = self.config.get('stop_loss_percent', 2)
        print(f"Using stop loss percentage: {stop_loss_percent}%")
        
        if trade_type == 'long':
            stopPrice = float(float(buying_price) - ((stop_loss_percent/100) * float(buying_price)))
            
            if stopPrice < 10:
                stopPrice = "{:.2f}".format(stopPrice)
            
            elif stopPrice < 50:
                stopPrice = "{:.1f}".format(stopPrice)
            
            else:
                stopPrice = int(stopPrice)
            
            
            try:
                # Create a stop-loss order
                stop_loss_order = self.client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='STOP_MARKET',
                    stopPrice=stopPrice,
                    closePosition='true'
                )
                print(f"Stop-loss order updated successfully to {stopPrice}.")
                print("Order Details:", stop_loss_order)
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Retrying to place the stop-loss order...")
        
        if trade_type == 'short':
            stopPrice = int(float(buying_price) + ((stop_loss_percent/100) * float(buying_price)))
            
            try:
                # Create a stop-loss order
                stop_loss_order = self.client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='STOP_MARKET',
                    stopPrice=stopPrice,
                    closePosition='true'
                )
                print(f"Stop-loss order updated successfully to {stopPrice}.")
                print("Order Details:", stop_loss_order)
            except Exception as e:
                print(f"An error occurred: {e}")
                print("Retrying to place the stop-loss order...")
    
        
        return stop_loss_order['orderId'], stopPrice
    
    def get_precision1(self, buying_price):
        """
        Determine the precision needed based on the buying price.
        
        Args:
            buying_price (float): Current buying price
            
        Returns:
            int: Precision value
        """
        if float(buying_price) <= 10:
            precision1 = 2
        
        elif float(buying_price) <=50:
            precision1 = 1  
            
        else:
            precision1 = 0 
        
        return precision1
        
    
    def create_buy_order_long(self, coin, target_price):
        """
        Create a long buy order with a stop loss and target profit.
        
        Args:
            coin (str): Coin name
            target_price (float): Target price percentage
            
        Returns:
            tuple: Order details including prices and IDs
        """
        #####-----------
        # coin = 'uniswap'
        # target_price = 0.02
        ####-------------
        
        
        symbol = self.coin_dict[coin]
        quantity = self.get_quantity(symbol)   
        print("Bought Quantity", quantity)
    
        # Optionally set the leverage, if needed
        result = self.client.futures_change_leverage(symbol=symbol, leverage=3)
    
        try:
            # result = client.futures_change_leverage(symbol=symbol, leverage = 5)1
            market_buy_order = self.client.futures_create_order(
               symbol = symbol,
               side = SIDE_BUY,
               type = ORDER_TYPE_MARKET,
               quantity = quantity
            )
            buying_price = self.get_current_price(symbol)
    
            print(f"Market long order placed successfully at price {buying_price}.")
            print("Order Details:", market_buy_order)
        except Exception as e:
            print(f"An error occurred: {e}")
            post_error_to_slack(f"An error occurred: {e}")
            print("Retrying to place the Market order...")
        
        buying_price = self.get_current_price(symbol)
        print(f"Bought {symbol} at price {buying_price}")
        
        #placing stop loss order
        stop_loss_percent = 2
        stopPrice = float(float(buying_price) - ((stop_loss_percent/100) * float(buying_price)))
        precision1 = self.get_precision1(buying_price)
        stopPrice = round(stopPrice, precision1)
        
        if market_buy_order:
            try:
                # Create a stop-loss order
                stop_loss_order = self.client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='STOP_MARKET',
                    stopPrice=stopPrice,
                    closePosition='true'
                )
                print("Stop-loss order placed successfully.")
                print("Order Details:", stop_loss_order)
            except Exception as e:
                print(f"An error occurred: {e}")
                post_error_to_slack(f"An error occurred: {e}")
                print("Retrying to place the stop-loss order...")
            
            stop_loss_orderID = stop_loss_order['orderId']
        
        if market_buy_order:
            target_profit_price = float(buying_price) + (abs(target_price) * float(buying_price))
            target_profit_price = round(target_profit_price, precision1)        
                
    
            # Create a limit order for target profit
            target_profit_order = self.client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                price=target_profit_price,
                quantity=quantity,  # Specify the quantity to sell
                timeInForce='GTC'  # Good Till Canceled
            )
            print("Target profit order placed successfully.")
            print("Order Details:", target_profit_order)
        
        target_order_id = target_profit_order['orderId']
        target_price = target_profit_order['price']
        
        return buying_price, market_buy_order['orderId'], stopPrice, stop_loss_orderID, target_order_id, target_price, quantity
    
        #placing a target price
        
    
    def create_buy_order_short(self, coin, target_price):
        """
        Create a short sell order with a stop loss and target profit.
        
        Args:
            coin (str): Coin name
            target_price (float): Target price percentage
            
        Returns:
            tuple: Order details including prices and IDs
        """
        #####-----------
        # coin = 'uniswap'
        # target_price = 0.02
        ####-------------
        
        symbol = self.coin_dict[coin]
        quantity = self.get_quantity(symbol)
        print("Bought Quantity", quantity)
        
        # Optionally set the leverage, if needed
        result = self.client.futures_change_leverage(symbol=symbol, leverage=3)
    
        
        try:
            # Create a stop-loss order
            # result = client.futures_change_leverage(symbol=symbol, leverage = 5)
            market_buy_order = self.client.futures_create_order(
               symbol = symbol,
               side = SIDE_SELL,
               type = ORDER_TYPE_MARKET,
               quantity = quantity
            )
            buying_price = self.get_current_price(symbol)
    
            print(f"Market short order placed successfully at price {buying_price}.")
            print("Order Details:", market_buy_order)
        except Exception as e:
            print(f"An error occurred: {e}")
            post_error_to_slack(f"An error occurred: {e}")
            print("Retrying to place the Market order...")
        
        buying_price = self.get_current_price(symbol)
        print(f"Bought {symbol} at price {buying_price}")
        
        #placing stop loss order
        stop_loss_percent = 2
        stopPrice = float(float(buying_price) + ((stop_loss_percent/100) * float(buying_price)))
        precision1 = self.get_precision1(buying_price)
        stopPrice = round(stopPrice, precision1)
        
        if market_buy_order:
            try:
                # Create a stop-loss order
                stop_loss_order = self.client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='STOP_MARKET',
                    stopPrice=stopPrice,
                    closePosition='true'
                )
                print("Stop-loss order placed successfully.")
                print("Order Details:", stop_loss_order)
            except Exception as e:
                print(f"An error occurred: {e}")
                post_error_to_slack(f"An error occurred: {e}")
                print("Retrying to place the stop-loss order...")
            
            stop_loss_orderID = stop_loss_order['orderId']
        
        if market_buy_order:
            target_profit_price = float(buying_price) - (abs(target_price) * float(buying_price))
            target_profit_price = round(target_profit_price, precision1)
    
            # Create a limit order for target profit
            target_profit_order = self.client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='LIMIT',
                price=target_profit_price,
                quantity=quantity,  # Specify the quantity to sell
                timeInForce='GTC'  # Good Till Canceled
            )
            print("Target profit order placed successfully.")
            print("Order Details:", target_profit_order)
        
        target_order_id = target_profit_order['orderId']
        target_price = target_profit_order['price']
        
        return buying_price, market_buy_order['orderId'], stopPrice, stop_loss_orderID, target_order_id, target_price, quantity
    
    def check_order_status(self, symbol, order_id):
        """
        Check the status of an order.
        
        Args:
            symbol (str): Trading pair symbol
            order_id: Order ID
            
        Returns:
            str: Order status ('filled' or 'notFilled')
        """
        try:
            open_orders_list = self.client.futures_get_open_orders()
            for open_order in open_orders_list:
                if open_order['symbol'] == symbol and open_order['orderId'] == order_id:
                    return 'filled'
            
            return 'notFilled'
        except Exception as e:
            print(f"An error occurred while detetcting status: {e}")
            return None



