"""
Logging utilities for the WebSiteDownloader application.

This module provides functions to set up and configure logging.
"""

import os
import logging
import logging.handlers
from typing import Dict, Any, Optional


def setup_logging(config: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Set up logging based on configuration.
    
    Args:
        config (Dict[str, Any], optional): Configuration dictionary.
            If None, default configuration is used.
            
    Returns:
        logging.Logger: Configured logger instance
    """
    # Use default config if none provided
    if config is None:
        config = {
            "logging": {
                "level": "INFO",
                "file": "logs/websitedownloader.log",
                "max_size": 10485760  # 10MB
            }
        }
    
    log_config = config.get("logging", {})
    
    # Get configuration values with defaults
    log_level_name = log_config.get("level", "INFO")
    log_file = log_config.get("file", "logs/websitedownloader.log")
    max_size = log_config.get("max_size", 10485760)
    
    # Map string log level to logging constant
    log_level = getattr(logging, log_level_name.upper(), logging.INFO)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates when reconfiguring
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
    )
    simple_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # File handlers
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Main log file (with rotation)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=3
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
        
        # Error log file (only ERROR and above)
        error_log = os.path.join(log_dir, "error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log, maxBytes=max_size, backupCount=3
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        
    except Exception as e:
        logger.error(f"Failed to set up file logging: {str(e)}")
        logger.info("Continuing with console logging only")
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Named logger instance
    """
    return logging.getLogger(name)