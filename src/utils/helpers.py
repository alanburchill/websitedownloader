"""
Helper utilities for the WebSiteDownloader application.

This module provides common utility functions used throughout the application.
"""

import os
import re
import json
import time
import hashlib
import logging
from urllib.parse import urlparse, urljoin, unquote
from typing import Dict, List, Any, Optional, Union

# Configure logger
logger = logging.getLogger(__name__)

def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize a URL: handle relative URLs, remove fragments, etc.
    
    Args:
        url (str): URL to normalize
        base_url (str, optional): Base URL for resolving relative URLs
        
    Returns:
        str: Normalized URL
    """
    # Handle empty URLs
    if not url:
        return ""
    
    # Remove fragments
    url = url.split("#")[0]
    
    # Handle relative URLs if base_url is provided
    if base_url and not bool(urlparse(url).netloc):
        url = urljoin(base_url, url)
    
    # URL decode
    url = unquote(url)
    
    return url


def get_domain(url: str) -> str:
    """
    Extract domain from a URL.
    
    Args:
        url (str): URL to extract domain from
        
    Returns:
        str: Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs belong to the same domain.
    
    Args:
        url1 (str): First URL
        url2 (str): Second URL
        
    Returns:
        bool: True if same domain, False otherwise
    """
    return get_domain(url1) == get_domain(url2)


def url_to_filename(url: str, extension: str = ".html") -> str:
    """
    Convert a URL to a safe filename.
    
    Args:
        url (str): URL to convert
        extension (str): File extension to append
        
    Returns:
        str: Safe filename
    """
    # Remove scheme and query parameters
    parsed = urlparse(url)
    path = parsed.netloc + parsed.path
    
    # Replace problematic characters
    path = path.replace("://", "_")
    path = path.replace("/", "_")
    path = path.replace(".", "_")
    path = path.replace("?", "_")
    path = path.replace("&", "_")
    path = path.replace("=", "_")
    path = path.replace(" ", "_")
    path = path.replace("%", "_")
    
    # Handle overly long filenames
    if len(path) > 200:
        # Use the first 100 chars, a hash of the URL, and the extension
        url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
        path = f"{path[:100]}_{url_hash}"
    
    return f"page_{path}{extension}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to make it safe for all operating systems.
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Handle reserved names in Windows
    reserved_names = [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    ]
    
    name_without_ext, ext = os.path.splitext(filename)
    if name_without_ext.upper() in reserved_names:
        filename = f"_{name_without_ext}{ext}"
    
    # Remove trailing dots and spaces (problematic in Windows)
    filename = filename.rstrip(". ")
    
    if not filename:
        filename = "unnamed"
        
    return filename


def save_json(data: Any, filepath: str) -> bool:
    """
    Save data to a JSON file with proper formatting.
    
    Args:
        data (Any): Data to save
        filepath (str): Path to save to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved JSON data to {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {str(e)}")
        return False


def load_json(filepath: str) -> Optional[Any]:
    """
    Load data from a JSON file.
    
    Args:
        filepath (str): Path to load from
        
    Returns:
        Any: Loaded data or None if failed
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded JSON data from {filepath}")
            return data
        else:
            logger.warning(f"JSON file not found: {filepath}")
            return None
    
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {str(e)}")
        return None


def create_directory_structure(base_dir: str) -> bool:
    """
    Create the directory structure for the project.
    
    Args:
        base_dir (str): Base directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create main directories
        directories = [
            'github-content',
            'github-content/pages',
            'github-content/images',
            'github-content/metadata',
            'archive',
            'logs',
            'phase-output'
        ]
        
        for directory in directories:
            path = os.path.join(base_dir, directory)
            if not os.path.exists(path):
                os.makedirs(path)
                logger.debug(f"Created directory: {path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating directory structure: {str(e)}")
        return False


def rate_limited(max_per_second: float):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_per_second (float): Maximum calls per second
        
    Returns:
        function: Decorated function
    """
    min_interval = 10 / max_per_second
    last_called = [0.0]
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            now = time.time()
            elapsed = now - last_called[0]
            remaining = min_interval - elapsed
            
            if remaining > 0:
                time.sleep(remaining)
                
            last_called[0] = time.time()
            return func(*args, **kwargs)
            
        return wrapper
        
    return decorator