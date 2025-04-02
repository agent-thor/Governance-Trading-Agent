"""
Time formatting utilities.
"""

import time
from datetime import datetime, timezone

def format_time_utc():
    """
    Format the current UTC time as a string.
    
    Returns:
        str: The formatted UTC time string in the format "YYYY-MM-DD HH:MM:SS"
    """
    # Get current UTC time
    utc_now = datetime.now(timezone.utc)
    
    # Format the time
    formatted_time = utc_now.strftime("%Y-%m-%d %H:%M:%S")
    
    return formatted_time 