"""
Time utility functions for the Governance Trading Bot.

This module provides various time-related utility functions.
"""

import datetime
import pytz

def get_ist_time():
    """
    Get the current time in Indian Standard Time (IST).
    
    Returns:
        datetime: Current datetime in IST timezone
    """
    # Get current UTC time
    utc_now = datetime.datetime.now(pytz.UTC)
    
    # Convert to IST (UTC+5:30)
    ist = pytz.timezone('Asia/Kolkata')
    ist_time = utc_now.astimezone(ist)
    
    return ist_time

def format_ist_time(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a datetime object or the current time in IST as a string.
    
    Args:
        dt (datetime, optional): Datetime object to format. If None, current time is used.
        format_str (str, optional): Format string for the output. Default is "%Y-%m-%d %H:%M:%S".
        
    Returns:
        str: Formatted IST time string
    """
    if dt is None:
        dt = get_ist_time()
        
    return dt.strftime(format_str) 