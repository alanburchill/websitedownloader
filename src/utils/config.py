"""
Configuration utilities for the WebSiteDownloader application.

This module provides functions to load, validate, and access configuration settings.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Configure logger
logger = logging.getLogger(__name__)

# Default configuration settings
DEFAULT_CONFIG = {
    "crawler": {
        "max_pages": 1000,
        "respect_robots": True,
        "rate_limit": 1.0,
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
        ]
    },
    "downloader": {
        "max_retries": 3,
        "timeout": 30,
        "request_delay": 1.5
    },
    "converter": {
        "content_selectors": [
            ".post-content",
            ".entry-content",
            "article",
            "#content"
        ],
        "ai_correction": {
            "enabled": False,
            "model": "local-model",
            "api_base": "http://localhost:1234/v1",
            "max_tokens": 4096,
            "temperature": 0.1
        },
        "include_metadata": False
    },
    "asset_handler": {
        "max_image_size": 10485760,  # 10MB
        "supported_extensions": [
            ".jpg", ".jpeg", ".png", ".gif", ".svg"
        ],
        "prefer_original_images": True,
        "image_link_selectors": [
            "a.thumbnail > img",
            ".wp-block-image a > img",
            ".gallery-item a > img"
        ]
    },
    "link_validator": {
        "validate_external": False,
        "fix_anchors": True
    },
    "logging": {
        "level": "INFO",
        "file": "logs/websitedownloader.log",
        "max_size": 10485760  # 10MB
    }
}

@dataclass
class WebsiteConfig:
    """Configuration class for website downloading."""
    url: str
    output_dir: str
    max_pages: int = 1000
    respect_robots: bool = True
    rate_limit: float = 1.0
    download_media: bool = True
    save_html: bool = True
    save_metadata: bool = True
    use_relative_urls: bool = False  # Default to not converting URLs to relative
    user_agent: str = "WebSiteDownloader/1.0"
    timeout: int = 30
    retry_count: int = 3
    ignore_ssl_errors: bool = False

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file and merge with defaults.
    
    Args:
        config_path (str, optional): Path to the configuration file.
            If None, only default configuration is used.
            
    Returns:
        Dict[str, Any]: Merged configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                
            if user_config:
                # Merge user configuration with defaults
                config = _deep_merge(config, user_config)
                logger.info(f"Configuration loaded from {config_path}")
            else:
                logger.warning(f"Empty configuration file at {config_path}")
                
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {str(e)}")
            logger.info("Using default configuration")
    else:
        if config_path:
            logger.warning(f"Configuration file not found at {config_path}")
        logger.info("Using default configuration")
    
    return config


def _deep_merge(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with override values taking precedence.
    
    Args:
        default (Dict[str, Any]): Default dictionary
        override (Dict[str, Any]): Override dictionary
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = default.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required sections
        required_sections = ['crawler', 'downloader', 'converter']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate specific values
        if config['crawler']['max_pages'] <= 0:
            logger.error("max_pages must be greater than 0")
            return False
            
        if config['crawler']['rate_limit'] <= 0:
            logger.error("rate_limit must be greater than 0")
            return False
            
        if config['downloader']['max_retries'] < 0:
            logger.error("max_retries must be greater than or equal to 0")
            return False
            
        if config['downloader']['timeout'] <= 0:
            logger.error("timeout must be greater than 0")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        return False