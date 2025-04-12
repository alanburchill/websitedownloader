"""
Media downloader module for downloading embedded media from web pages.
"""

import os
import re
import logging
import requests
import time
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class MediaDownloader:
    """Class to download media files embedded in HTML content."""
    
    def __init__(self, max_retries=3, timeout=30, request_delay=1.5, verbose=False):
        """
        Initialize the MediaDownloader.
        
        Args:
            max_retries: Maximum number of retry attempts for failed downloads
            timeout: Request timeout in seconds
            request_delay: Time to wait between requests in seconds
            verbose: Whether to show verbose output
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.request_delay = request_delay
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        # Create a session that will be overridden by ContentDownloader's session
        self.session = requests.Session()
        
        # Track downloaded URLs to avoid duplicates
        self.downloaded_urls = {}
        
        # Store media download info to be combined with page downloads
        self.media_download_info = []
        
    def is_same_domain(self, url, base_url):
        """
        Check if a URL belongs to the same domain as the base URL.
        
        Args:
            url: URL to check
            base_url: Base URL to compare against
            
        Returns:
            bool: True if URL is from the same domain, False otherwise
        """
        url_domain = urlparse(url).netloc
        base_domain = urlparse(base_url).netloc
        
        # Strip 'www.' prefix for comparison if present
        url_domain = url_domain.replace('www.', '')
        base_domain = base_domain.replace('www.', '')
        
        return url_domain == base_domain
    
    def extract_media_urls(self, html_content, base_url):
        """
        Extract media URLs from HTML content.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative URLs
            
        Returns:
            list: List of media URLs
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        media_urls = []
        # Find images
        for img in soup.find_all('img'):
            src = img.get('src') if hasattr(img, 'get') else None
            if src:
                full_url = urljoin(base_url, str(src))
                media_urls.append(full_url)
        
        # Find CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href') if hasattr(link, 'get') else None
            if href:
                full_url = urljoin(base_url, str(href))
                media_urls.append(full_url)
        
        # Find JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src') if hasattr(script, 'get') else None
            if src:
                full_url = urljoin(base_url, str(src))
                media_urls.append(full_url)
        
        # Find other downloadable files (PDF, ZIP, etc.)
        for a in soup.find_all('a', href=True):
            href = a.get('href') if hasattr(a, 'get') else None
            if href:
                full_url = urljoin(base_url, str(href))
                ext = os.path.splitext(full_url.split('?')[0])[1].lower()
                if ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar']:
                    media_urls.append(full_url)
        
        # Find other media elements like video, audio, etc.
        media_tags = ['video', 'audio', 'source']
        for tag_name in media_tags:
            for elem in soup.find_all(tag_name):
                src = elem.get('src') if hasattr(elem, 'get') else None
                if src:
                    full_url = urljoin(base_url, str(src))
                    media_urls.append(full_url)
        return media_urls
    
    def get_url_key(self, url):
        """
        Generate a unique key for a URL by removing query parameters and fragments.
        
        Args:
            url: URL to generate a key for
            
        Returns:
            str: Normalized URL as a key
        """
        parsed = urlparse(url)
        # Normalize the URL by removing query parameters and fragments
        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized_url
        
    def download_media(self, url, site_dir, base_url):
        """
        Download a media file if it belongs to the same domain.
        
        Args:
            url: URL of the media file to download
            site_dir: Site directory (e.g., www_grouppolicy_biz)
            base_url: Base URL of the website
            
        Returns:
            dict: Dictionary with download information or None if failed or external
        """
        # Skip external resources
        if not self.is_same_domain(url, base_url):
            self.logger.debug(f"Skipping external resource: {url}")
            return None
        
        # Check if this URL has already been downloaded
        url_key = self.get_url_key(url)
        if url_key in self.downloaded_urls:
            if self.verbose:
                self.logger.info(f"Asset already downloaded: {url} -> {self.downloaded_urls[url_key]}")
            return {
                'url': url,
                'file_path': self.downloaded_urls[url_key],
                'status': 'exists'
            }
        
        # HTML directory is the root of the web site
        html_dir = os.path.join(site_dir, 'HTML')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        
        # Extract path and filename from URL, preserving directory structure
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        
        if not path:
            # Handle case with no path
            filename = f"media_{hash(url)}"
            rel_path = ""
        else:
            # Split into path parts
            path_parts = path.split('/')
            filename = path_parts[-1]  # Last part is the filename
            rel_path = os.path.join(*path_parts[:-1]) if len(path_parts) > 1 else ""
        
        # Create full path maintaining relative directory structure within HTML folder
        if rel_path:
            # This will create paths like HTML/wp-content/uploads/etc...
            full_media_path = os.path.join(html_dir, rel_path)
            if not os.path.exists(full_media_path):
                os.makedirs(full_media_path)
            file_path = os.path.join(full_media_path, filename)
        else:
            file_path = os.path.join(html_dir, filename)
        
        # Check if we already have a file with this exact path
        if os.path.exists(file_path):
            # Check if the file is identical by doing a HEAD request
            if self._is_same_file(url, file_path):
                if self.verbose:
                    self.logger.info(f"Asset already exists (identical): {url} -> {file_path}")
                # Store the URL in our tracking dictionary
                self.downloaded_urls[url_key] = file_path
                return {
                    'url': url,
                    'file_path': file_path,
                    'status': 'exists'
                }
            else:
                # Files are not identical, use a hash-based approach for renaming
                name, ext = os.path.splitext(filename)
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                filename = f"{name}_{url_hash}{ext}"
                
                if rel_path:
                    file_path = os.path.join(full_media_path, filename)
                else:
                    file_path = os.path.join(html_dir, filename)
        
        retries = 0
        while retries <= self.max_retries:
            try:
                if self.verbose:
                    self.logger.info(f"Downloading asset: {url}")
                else:
                    self.logger.debug(f"Downloading media: {url}")
                    
                # Use the shared session for media downloads
                response = self.session.get(url, timeout=self.timeout, stream=True)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(file_path)
                content_type = response.headers.get('Content-Type', '')
                
                if self.verbose:
                    self.logger.info(f"Downloaded asset: {url} -> {file_path} ({content_type}, {file_size} bytes)")
                else:
                    self.logger.debug(f"Downloaded media: {url} to {file_path}")
                
                # Add to media download info (no separate log file)
                media_info = {
                    'url': url,
                    'file_path': file_path,
                    'content_type': content_type,
                    'size': file_size,
                    'timestamp': time.time(),
                    'type': 'media'
                }
                self.media_download_info.append(media_info)
                
                # Store the URL in our tracking dictionary
                self.downloaded_urls[url_key] = file_path
                
                return {
                    'url': url,
                    'file_path': file_path,
                    'status': 'downloaded',
                    'size': file_size,
                    'content_type': content_type
                }
                
            except requests.exceptions.RequestException as e:
                retries += 1
                self.logger.warning(f"Failed to download media {url} (attempt {retries}/{self.max_retries}): {e}")
                time.sleep(self.request_delay)
        
        self.logger.error(f"Failed to download media after {self.max_retries} attempts: {url}")
        return None
    
    def _is_same_file(self, url, file_path):
        """Check if the remote file is identical to the local file (to avoid duplicate downloads)"""
        try:
            local_size = os.path.getsize(file_path)
            # Use the shared session for HEAD requests too
            head_response = self.session.head(url, timeout=self.timeout)
            
            if 'content-length' in head_response.headers:
                remote_size = int(head_response.headers['content-length'])
                # If sizes match, it's likely the same file
                return local_size == remote_size
            
            # If no content-length, we can't be sure, so let's do a GET request
            # and compare a small part of the content
            if local_size < 1024:  # For small files
                try:
                    range_response = self.session.get(url, headers={'Range': 'bytes=0-1023'}, timeout=self.timeout)
                    with open(file_path, 'rb') as f:
                        local_content = f.read(1024)
                        return local_content == range_response.content[:len(local_content)]
                except:
                    pass
        except Exception as e:
            self.logger.debug(f"Error comparing files: {e}")
        return False
        
    def download_all_media(self, html_content, base_url, site_dir):
        """
        Download all media files embedded in HTML content.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative URLs
            site_dir: Site directory to save downloaded files
            
        Returns:
            dict: Dictionary with download information
        """
        media_urls = self.extract_media_urls(html_content, base_url)
        downloaded_media = []
        
        if self.verbose:
            self.logger.info(f"Found {len(media_urls)} media assets to download from {base_url}")
        
        for i, url in enumerate(media_urls, 1):
            # Respect request delay
            time.sleep(self.request_delay)
            
            if self.verbose:
                self.logger.info(f"Processing asset [{i}/{len(media_urls)}]: {url}")
            
            result = self.download_media(url, site_dir, base_url)
            if result:
                downloaded_media.append(result)
        
        # No separate media log file - this will be handled by the ContentDownloader
        
        if self.verbose and downloaded_media:
            self.logger.info(f"Successfully downloaded {len(downloaded_media)} of {len(media_urls)} assets from {base_url}")
        
        return {
            'total': len(media_urls),
            'downloaded': len(downloaded_media),
            'media': downloaded_media,
            'media_info': self.media_download_info
        }
