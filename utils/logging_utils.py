import logging
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Set up logging with custom configuration.
    
    Args:
        level (int): Logging level (default: logging.INFO)
        log_to_file (bool): Whether to save logs to file (default: True)
        
    Returns:
        logging.Logger: The configured logger
    """
    # Create formatter for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create a stream handler for console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create a file handler for saving logs to file
    if log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create log file with current date
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'governance_bot_{today}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create a logger for each module
def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name (str): Module name
        
    Returns:
        logging.Logger: Logger instance for the module
    """
    return logging.getLogger(name) 