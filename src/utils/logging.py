"""
Logging utilities for the Natural Language to SQL Query App.
"""
import logging
from src.config import Config

def setup_logging():
    """Configure logging for the application."""
    log_level = getattr(logging, Config.LOG_LEVEL().upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# Global logger instance
logger = setup_logging() 