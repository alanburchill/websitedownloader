"""
Content downloader module for fetching web content.
"""

import os
import time
import logging
import json
import requests
import psutil
import sys
from urllib.parse import urlparse, urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from collections import Counter

from .media_downloader import MediaDownloader

class ContentDownloader:
    """Class to download content from discovered URLs."""
    def __init__(self, max_retries=3, timeout=30, request_delay=1.5, verbose=False, config=None):
        """
        Initialize the ContentDownloader.
        
        Args:
            max_retries: Maximum number of retry attempts for failed downloads
            timeout: Request timeout in seconds
            request_delay: Time to wait between requests in seconds
            verbose: Whether to show verbose output
            config: Configuration dictionary (optional)
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.request_delay = request_delay
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.media_downloader = MediaDownloader(max_retries, timeout, request_delay, verbose=verbose)
        self.request_count = 0
        self.start_time = time.time()
        
        # Status code tracking
        self.status_codes = Counter()
        
        # Configuration settings
        self.config = config or {}
        self.log_all_status_codes = self._get_config('crawler.status_codes.log_all', True)
        self.show_status_console = self._get_config('crawler.status_codes.show_console', True)
        self.generate_status_report = self._get_config('crawler.status_codes.generate_report', True)
        self.retry_status_codes = self._get_config('crawler.status_codes.retry_codes', [429, 500, 502, 503, 504])
        
        # Performance monitoring
        self.show_progress = self._get_config('downloader.monitoring.show_progress', True)
        self.log_speed = self._get_config('downloader.monitoring.log_speed', True)
        self.check_bandwidth = self._get_config('downloader.monitoring.check_bandwidth', False)
        self.track_memory = self._get_config('downloader.monitoring.track_memory', True)
        
        # Adaptive rate limiting
        self.adaptive_rate_limit = self._get_config('downloader.rate_limiting.adaptive', True)
        self.min_delay = self._get_config('downloader.rate_limiting.min_delay', 0.01)
        self.max_delay = self._get_config('downloader.rate_limiting.max_delay', 5.0)
        self.backoff_factor = self._get_config('downloader.rate_limiting.backoff_factor', 2.0)
        
        # Create a persistent session for all HTTP requests
        self.session = requests.Session()
        
        # Pass the session to the media downloader
        self.media_downloader.session = self.session
        
        # Session logs (accumulated download entries)
        self.session_logs = []
        self.error_logs = []
        
        # Track all URLs for URL list JSON
        self.all_urls = []

    def _get_config(self, path, default=None):
        """
        Get a configuration value by dot-separated path.
        
        Args:
            path: Dot-separated configuration path (e.g., 'crawler.rate_limit')
            default: Default value if path doesn't exist
            
        Returns:
            Configuration value or default
        """
        if not self.config:
            return default
            
        parts = path.split('.')
        value = self.config
        
        try:
            for part in parts:
                value = value.get(part, {})
            
            # If we've reached a non-dict value or an empty dict, return it
            if not isinstance(value, dict) or value:
                return value
            # Otherwise return the default
            return default
        except (AttributeError, KeyError):
            return default
    
    def download_all(self, urls, archive_dir, download_media=False):
        """
        Download content from all URLs and save to archive directory.
        
        Args:
            urls: List of URL dictionaries or strings to download
            archive_dir: Directory to save downloaded content
            download_media: Whether to download embedded media (images, CSS, JS, etc.)
            
        Returns:
            list: List of dictionaries with download information
        """
        # Ensure the archive_dir is under the 'Sites' folder
        sites_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Sites')
        archive_dir = os.path.join(sites_root, os.path.basename(archive_dir))

        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)
            
        results = []
        self.request_count = 0
        self.start_time = time.time()
        total_bytes = 0
        
        # Create session timestamp for log filenames
        session_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_log_filename = f"download_log_{session_timestamp}.json"
        self.error_log_filename = f"error_log_{session_timestamp}.json"
        self.url_list_filename = f"url_list_{session_timestamp}.json"
        
        # Create status code report directory
        if self.generate_status_report:
            report_dir = os.path.join(archive_dir, 'Reports')
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
        
        for i, url_item in enumerate(urls):
            # Handle both URL strings and dictionaries
            if isinstance(url_item, dict):
                url = url_item['url']
            else:
                url = url_item
                
            # Add to URL list
            self.all_urls.append(url)
                
            self.logger.info(f"Downloading [{i+1}/{len(urls)}]: {url}")
            
            # Show progress if enabled
            if self.show_progress:
                progress = f"[{i+1}/{len(urls)}] ({(i+1)/len(urls)*100:.1f}%)"
                sys.stdout.write(f"\r{progress} Processing: {url[:60]}{'...' if len(url) > 60 else ''}  ")
                sys.stdout.flush()
            
            # Respect request delay
            time.sleep(self.request_delay)
            
            # Track memory if enabled
            if self.track_memory:
                mem_before = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
            
            # Download the content
            result = self._download_url(url, archive_dir, download_media)
            if result:
                results.append(result)
                total_bytes += result.get('size', 0)
                
                # Track memory if enabled
                if self.track_memory:
                    mem_after = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
                    if self.verbose:
                        self.logger.debug(f"Memory usage: {mem_after:.2f}MB (+{mem_after - mem_before:.2f}MB)")
            
            # Output the actual request rate based on configuration
            self.request_count += 1
            if self.log_speed and (self.request_count % 10 == 0 or self.verbose):
                elapsed_time = time.time() - self.start_time
                rate = self.request_count / elapsed_time if elapsed_time > 0 else 0
                download_speed = total_bytes / elapsed_time / 1024 if elapsed_time > 0 else 0  # KB/s
                self.logger.info(f"Download rate: {rate:.2f} req/s, Speed: {download_speed:.2f} KB/s, Completed: {self.request_count}/{len(urls)}")
                
        # Generate status code report at the end if enabled
        if self.generate_status_report and self.status_codes:
            report_path = os.path.join(report_dir, f"status_codes_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
            report = {
                'total_requests': self.request_count,
                'successful_requests': len(results),
                'status_codes': {str(k): v for k, v in self.status_codes.items()},
                'timestamp': datetime.now().isoformat()
            }
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Status code report generated: {report_path}")
            
            # Print a summary with colored status codes
            print("\nHTTP Status Code Summary:")
            for status, count in sorted(self.status_codes.items()):
                color, icon, description = self._get_status_color_and_icon(status)
                reset = "\033[0m"
                print(f"  {color}{icon} HTTP {status} ({description}){reset}: {count} requests")
                
        # Clear the progress line if used
        if self.show_progress:
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()
        
        # Write the URL list to JSON file
        logs_dir = os.path.join(archive_dir, 'Logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        url_list_path = os.path.join(logs_dir, self.url_list_filename)
        with open(url_list_path, 'w') as f:
            json.dump({
                'urls': self.all_urls,
                'count': len(self.all_urls),
                'timestamp': datetime.now().isoformat(),
                'session': session_timestamp
            }, f, indent=2)
        
        # Write the consolidated session logs to a single file
        if self.session_logs:
            log_path = os.path.join(logs_dir, self.session_log_filename)
            with open(log_path, 'w') as f:
                json.dump(self.session_logs, f, indent=2)
            self.logger.info(f"Session download log written to: {log_path}")
            
        # Write error logs if any
        if self.error_logs:
            error_log_path = os.path.join(logs_dir, self.error_log_filename)
            with open(error_log_path, 'w') as f:
                json.dump(self.error_logs, f, indent=2)
            self.logger.info(f"Session error log written to: {error_log_path}")
            
        return results
    
    def _write_session_log(self, logs_dir, filename, log_entries):
        """Write accumulated log entries to a single session log file."""
        log_path = os.path.join(logs_dir, filename)
        
        # If the file exists, read existing content
        existing_log = []
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                try:
                    existing_log = json.load(f)
                    if not isinstance(existing_log, list):
                        existing_log = []
                except:
                    existing_log = []
        
        # Append new entries and write the file
        updated_log = existing_log + log_entries
        with open(log_path, 'w') as f:
            json.dump(updated_log, f, indent=2)
    
    def _extract_links(self, html_content, base_url):
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href and not href.startswith('#'):  # Skip fragment-only links
                full_url = urljoin(base_url, href)
                link_text = a.get_text().strip() or "(No text)"
                links.append({
                    'url': full_url,
                    'text': link_text[:100],  # Limit text length
                    'internal': self._is_same_domain(full_url, base_url)
                })
                
        return links
        
    def _is_same_domain(self, url, base_url):
        """Check if URLs are from the same domain"""
        url_domain = urlparse(url).netloc
        base_domain = urlparse(base_url).netloc
        
        # Strip 'www.' prefix for comparison if present
        url_domain = url_domain.replace('www.', '')
        base_domain = base_domain.replace('www.', '')
        
        return url_domain == base_domain
    
    def _download_url(self, url, archive_dir, download_media):
        """
        Download content from a single URL with retries.
        
        Args:
            url: URL to download
            archive_dir: Directory to save downloaded content
            download_media: Whether to download embedded media
            
        Returns:
            dict: Dictionary with download information or None if failed
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                # Make the request using the persistent session
                response = self.session.get(url, timeout=self.timeout)
                
                # Track status code regardless of success
                status_code = response.status_code
                self.status_codes[status_code] += 1
                
                # Log status code if configured
                if self.log_all_status_codes:
                    self.logger.info(f"HTTP {status_code} from {url}")
                
                # Show status code on console if configured
                self._display_status_code(status_code, url)
                
                # Check for retry status codes
                if status_code in self.retry_status_codes and retries < self.max_retries:
                    retries += 1
                    self.logger.warning(f"Got status code {status_code}, will retry ({retries}/{self.max_retries})")
                    
                    # Adjust delay for adaptive rate limiting
                    if self.adaptive_rate_limit:
                        self.request_delay = min(self.request_delay * self.backoff_factor, self.max_delay)
                        self.logger.info(f"Increased rate limit to {self.request_delay:.2f}s")
                    
                    wait_time = self.request_delay * (2 ** retries)
                    self.logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
                
                # Raise for other error status codes
                response.raise_for_status()
                
                # Parse the URL to extract domain and path components
                parsed = urlparse(url)
                domain_name = parsed.netloc.replace('.', '_')
                path = parsed.path.strip('/')
                
                # Main site directory (e.g., www_grouppolicy_biz)
                site_dir = archive_dir
                
                # Create HTML, JSON and Logs directories
                html_dir = os.path.join(site_dir, 'HTML')
                json_dir = os.path.join(site_dir, 'JSON')
                logs_dir = os.path.join(site_dir, 'Logs')
                
                for directory in [html_dir, json_dir, logs_dir]:
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                
                # Determine the file path based on the URL path structure
                if path:
                    # Extract path components, preserving directory structure
                    path_parts = path.split('/')
                    filename = path_parts[-1]
                    
                    # If the filename doesn't have an extension, add .html
                    if '.' not in filename:
                        filename = f"{filename}.html"
                        path_parts[-1] = filename
                    
                    # Create the directory structure within the HTML folder
                    rel_dir = os.path.join(html_dir, *path_parts[:-1])
                    if not os.path.exists(rel_dir):
                        os.makedirs(rel_dir)
                    
                    # Full path including filename
                    file_path = os.path.join(html_dir, *path_parts)
                else:
                    # No path, just use domain_index.html
                    filename = f"{domain_name}_index.html"
                    file_path = os.path.join(html_dir, filename)
                
                # Handle filename collisions by skipping instead of renaming
                if os.path.exists(file_path):
                    self.logger.info(f"File already exists, skipping download: {file_path}")
                    return {
                        'url': url,
                        'file_path': file_path,
                        'status_code': response.status_code,
                        'status': 'skipped',
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Save content based on content type
                content = response.content
                
                # Extract all links before downloading media
                page_links = self._extract_links(content, url)
                
                # If requested, download all embedded media from the same domain
                media_results = None
                if download_media and 'text/html' in response.headers.get('Content-Type', ''):
                    self.logger.info(f"Downloading embedded media from {url}")
                    # Clear the media download info before downloading for this page
                    self.media_downloader.media_download_info = []
                    
                    # Pass the site_dir to ensure media goes in with proper structure
                    media_results = self.media_downloader.download_all_media(content, url, site_dir)
                    self.logger.info(f"Downloaded {media_results['downloaded']} of {media_results['total']} media files from {url}")
                
                # Write the HTML content to file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Get relative path for logging
                rel_path = os.path.relpath(file_path, site_dir)
                self.logger.info(f"Successfully downloaded {url} to {site_dir}/{rel_path}")
                
                # Save metadata in JSON folder with same directory structure as HTML
                metadata = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'download_path': file_path,
                    'content_type': response.headers.get('Content-Type', ''),
                    'size_bytes': len(content),
                    'download_time_ms': int((time.time() - self.start_time) * 1000),
                    'links': page_links,  # Add all links extracted from the page
                }
                
                # Add media information to metadata if available
                if media_results:
                    metadata['media'] = {
                        'total': media_results.get('total', 0),
                        'downloaded': media_results.get('downloaded', 0),
                        'items': media_results.get('media', [])  # List of all downloaded media items
                    }
                
                # Store JSON files in the JSON directory with same structure as HTML
                # Get the relative path from HTML directory to the file
                rel_path = os.path.relpath(file_path, html_dir)
                base_filename = os.path.basename(file_path)
                json_filename = f"{os.path.splitext(base_filename)[0]}_meta.json"
                
                # Create the same directory structure in JSON folder
                json_rel_dir = os.path.dirname(rel_path)
                if json_rel_dir:
                    full_json_dir = os.path.join(json_dir, json_rel_dir)
                    if not os.path.exists(full_json_dir):
                        os.makedirs(full_json_dir)
                    metadata_path = os.path.join(full_json_dir, json_filename)
                else:
                    metadata_path = os.path.join(json_dir, json_filename)
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Add to consolidated session logs
                log_entry = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success',
                    'status_code': response.status_code,
                    'file_path': file_path,
                    'metadata_path': metadata_path,
                    'size_bytes': len(content),
                    'content_type': response.headers.get('Content-Type', ''),
                    'type': 'page'
                }
                self.session_logs.append(log_entry)
                
                # Add any media download info to the consolidated logs
                if download_media and media_results and 'media_info' in media_results:
                    self.session_logs.extend(media_results['media_info'])
                
                result = {
                    'url': url,
                    'file_path': file_path,
                    'metadata_path': metadata_path,
                    'content_type': response.headers.get('Content-Type', ''),
                    'status_code': response.status_code,
                    'size': len(content),
                    'timestamp': datetime.now().isoformat()
                }
                
                if media_results:
                    result['media'] = media_results
                
                return result
                
            except requests.exceptions.RequestException as e:
                retries += 1
                
                # Extract status code from the exception if available
                status_code = None
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    self.status_codes[status_code] += 1
                    
                    # Log status code if configured
                    if self.log_all_status_codes:
                        self.logger.info(f"HTTP {status_code} from {url}")
                    
                    # Show status code on console if configured
                    self._display_status_code(status_code, url)
                
                # Check if this might be a rate limiting issue
                is_rate_limit = False
                if status_code == 429:
                    is_rate_limit = True
                    self.logger.warning(f"RATE LIMITED: Attempt {retries} failed for {url}: {str(e)}")
                    print(f"⚠️ RATE LIMITED by server! Backing off and retrying...")
                elif "rate" in str(e).lower() and ("limit" in str(e).lower() or "exceed" in str(e).lower()):
                    is_rate_limit = True
                    self.logger.warning(f"POSSIBLE RATE LIMITING: Attempt {retries} failed for {url}: {str(e)}")
                    print(f"⚠️ Possible rate limiting detected! Backing off and retrying...")
                else:
                    self.logger.warning(f"Attempt {retries} failed for {url}: {str(e)}")
                
                # Adjust delay for adaptive rate limiting if rate limiting is detected
                if is_rate_limit and self.adaptive_rate_limit:
                    old_delay = self.request_delay
                    self.request_delay = min(self.request_delay * self.backoff_factor, self.max_delay)
                    self.logger.info(f"Adjusted rate limit from {old_delay:.2f}s to {self.request_delay:.2f}s")
                
                # Log error to consolidated error logs
                error_entry = {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'status_code': status_code,
                    'attempt': retries
                }
                self.error_logs.append(error_entry)
                
                if retries <= self.max_retries:
                    # Exponential backoff
                    wait_time = self.request_delay * (2 ** retries)
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    print(f"Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed to download {url} after {self.max_retries} attempts")
                    return None
        
        return None

    def _get_status_color_and_icon(self, status_code):
        """
        Get the appropriate color and icon for a status code based on its severity.
        
        Args:
            status_code: HTTP status code
            
        Returns:
            tuple: Color code, icon, and status description
        """
        # Informational responses (100–199)
        if 100 <= status_code < 200:
            return "\033[94m", "ℹ️", "INFO"  # Blue
            
        # Successful responses (200–299)
        elif status_code == 200:
            return "\033[92m", "✅", "OK"  # Green
        elif status_code == 201:
            return "\033[92m", "➕", "Created"  # Green
        elif status_code == 204:
            return "\033[92m", "⭕", "No Content"  # Green
        elif 200 <= status_code < 300:
            return "\033[92m", "✓", "Success"  # Green
            
        # Redirection messages (300–399)
        elif status_code == 301:
            return "\033[93m", "➡️", "Moved Permanently"  # Yellow
        elif status_code == 302:
            return "\033[93m", "↪️", "Found"  # Yellow
        elif status_code == 304:
            return "\033[96m", "📋", "Not Modified"  # Cyan
        elif 300 <= status_code < 400:
            return "\033[93m", "⤴️", "Redirect"  # Yellow
            
        # Client error responses (400–499)
        elif status_code == 400:
            return "\033[91m", "⚠️", "Bad Request"  # Red
        elif status_code == 401:
            return "\033[91m", "🔒", "Unauthorized"  # Red
        elif status_code == 403:
            return "\033[91m", "🚫", "Forbidden"  # Red
        elif status_code == 404:
            return "\033[91m", "❓", "Not Found"  # Red
        elif status_code == 429:
            return "\033[95m", "⏱️", "Too Many Requests"  # Magenta
        elif 400 <= status_code < 500:
            return "\033[91m", "❌", "Client Error"  # Red
            
        # Server error responses (500–599)
        elif status_code == 500:
            return "\033[31;1m", "💥", "Internal Server Error"  # Bright Red
        elif status_code == 502:
            return "\033[31;1m", "🌐", "Bad Gateway"  # Bright Red
        elif status_code == 503:
            return "\033[31;1m", "🛑", "Service Unavailable"  # Bright Red
        elif status_code == 504:
            return "\033[31;1m", "⌛", "Gateway Timeout"  # Bright Red
        elif 500 <= status_code < 600:
            return "\033[31;1m", "⛔", "Server Error"  # Bright Red
            
        # Unknown status codes
        else:
            return "\033[90m", "❔", "Unknown"  # Gray

    def _format_status_code_message(self, status_code, url):
        """
        Format a status code message with color and icon.
        
        Args:
            status_code: HTTP status code
            url: The URL that generated this status code
            
        Returns:
            str: Formatted message
        """
        color, icon, description = self._get_status_color_and_icon(status_code)
        reset = "\033[0m"
        
        # Format the status code part
        status_part = f"{color}{icon} HTTP {status_code} ({description}){reset}"
        
        # Show URL in default color
        return f"{status_part} - {url}"

    def _display_status_code(self, status_code, url):
        """
        Display a status code message to the console if configured to do so.
        
        Args:
            status_code: HTTP status code
            url: URL that generated this status code
        """
        if not self.show_status_console:
            return
            
        # Format the message and print it
        message = self._format_status_code_message(status_code, url)
        print(message)
        
        # For certain status codes, add helpful information
        if status_code == 429:
            print("   \033[95mRate limit detected! Automatically backing off and retrying...\033[0m")
        elif status_code == 403:
            print("   \033[91mAccess forbidden. The server may require authentication or block scrapers.\033[0m")
        elif status_code == 503:
            print("   \033[91mService unavailable. The server might be overloaded or temporarily down.\033[0m")