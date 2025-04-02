"""
Error handling utility that saves error messages to a file for later analysis.
"""

import os
import time
from datetime import datetime

def save_error(error_message):
    """
    Save an error message to a log file.
    
    Args:
        error_message (str): The error message to save
        
    Returns:
        bool: True if the error was saved successfully, False otherwise
    """
    try:
        # Create a logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Generate a timestamp for the error
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a log filename with the current date
        log_file = os.path.join(log_dir, f"error_log_{datetime.now().strftime('%Y%m%d')}.txt")
        
        # Append the error to the log file
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {error_message}\n")
            
        print(f"Error saved to {log_file}")
        return True
        
    except Exception as e:
        print(f"Failed to save error: {e}")
        return False 