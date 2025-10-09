"""
This module provides a centralized logging configuration for the entire application.

It sets up a logger that writes to a file and the console, and provides a
convenience function to log messages at different levels.
"""

import sys
import logging
import os

# Define the log file name. This is where all application logs will be stored.
LOG_FILE = "centrix.log"

def setup_logger():
    """
    Configures the application's logging system.
    
    This function sets up a logger to write messages to both a file (app.log)
    and the console (stdout) for real-time monitoring.
    """
    # Create the log file if it doesn't exist to prevent errors on startup.
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'a').close()
        
    logging.basicConfig(
        level=logging.INFO,  # Set the minimum logging level to INFO.
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),      # Log to a file.
            logging.StreamHandler(sys.stdout)   # Also log to the console.
        ]
    )
    # Get the root logger instance to use throughout the application.
    logger = logging.getLogger(__name__)
    logger.info("Logger has been set up successfully. All logs will be written to both the console and the '%s' file.", LOG_FILE)
    return logger

# Call the logger setup function at the beginning of the script.
logger = setup_logger()

# A single, reusable function for logging messages.
def log_message(level: str, message: str):
    """
    Logs a message at a specified level using the configured logger.

    Args:
        level (str): The logging level ('info', 'warning', 'error', 'critical', 'debug').
        message (str): The message to log.
    """
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'critical':
        logger.critical(message)
    elif level == 'debug':
        logger.debug(message)
    else:
        logger.info(message) 
