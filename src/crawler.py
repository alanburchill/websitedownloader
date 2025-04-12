"""
Website crawler module for discovering URLs.
"""

import logging
import time
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

class WebCrawler:
    """Class to crawl websites and discover URLs."""
    
    def __init__(self, max_pages=1000, respect_robots=True, rate_limit=1.0):
        """
        Initialize the WebCrawler.
        
        Args:
            max_pages: Maximum number of pages to crawl
            respect_robots: Whether to respect robots.txt
            rate_limit: Number of seconds to wait between requests
        """
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.rate_limit = rate_limit
        self.logger = logging.getLogger(__name__)
    
    def crawl_sitemap(self, sitemap_url):
        """
        Parse a sitemap.xml file to discover URLs.
        
        Args:
            sitemap_url: URL of the sitemap.xml file
            
        Returns:
            list: List of discovered URL dictionaries
        """
        self.logger.info(f"Parsing sitemap from {sitemap_url}")
        discovered_urls = []
        
        try:
            # Respect the rate limit
            time.sleep(self.rate_limit)
            
            # Make the request to get the sitemap XML
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Check if it's an XML file
            content_type = response.headers.get('Content-Type', '').lower()
            if not ('xml' in content_type or sitemap_url.endswith('.xml')):
                self.logger.warning(f"The URL doesn't appear to be an XML file: {content_type}")
            
            # Parse the XML
            root = ET.fromstring(response.content)
            
            # Define XML namespaces (commonly used in sitemaps)
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            # Process a sitemap index (collection of sitemaps)
            if root.tag.endswith('sitemapindex'):
                sitemap_urls = []
                for sitemap in root.findall('.//sm:sitemap/sm:loc', namespaces) or root.findall('.//sitemap/loc'):
                    if len(sitemap_urls) < self.max_pages:
                        sitemap_urls.append(sitemap.text)
                
                self.logger.info(f"Found {len(sitemap_urls)} sitemaps in sitemap index")
                
                # Process each sitemap
                for sitemap_url in sitemap_urls:
                    child_urls = self.crawl_sitemap(sitemap_url)
                    discovered_urls.extend(child_urls)
                    if len(discovered_urls) >= self.max_pages:
                        self.logger.info(f"Reached maximum pages ({self.max_pages}), stopping sitemap crawl")
                        break
            
            # Process a regular sitemap with URLs
            else:
                # Look for URLs in the sitemap
                url_elements = root.findall('.//sm:url/sm:loc', namespaces) or root.findall('.//url/loc')
                
                for url_elem in url_elements:
                    if len(discovered_urls) >= self.max_pages:
                        self.logger.info(f"Reached maximum pages ({self.max_pages}), stopping sitemap crawl")
                        break
                    
                    url = url_elem.text
                    if not url:
                        continue
                        
                    # Default metadata
                    metadata = {
                        'url': url,
                        'title': url,  # Default title is URL
                        'description': '',  # No description in sitemap
                        'status_code': 200,  # Assume valid
                        'content_type': 'text/html'  # Assume HTML
                    }
                    
                    # Find the parent <url> element to extract additional metadata
                    # This replaces the getparent() call which isn't supported by ElementTree
                    if url_elem.getparent is None:  # If getparent() doesn't exist
                        # Find the parent by searching for elements containing this loc element
                        parent = None
                        # Try with namespace
                        for url_parent in root.findall('.//sm:url', namespaces):
                            if url_parent.find('sm:loc', namespaces) is url_elem:
                                parent = url_parent
                                break
                        # Try without namespace
                        if parent is None:
                            for url_parent in root.findall('.//url'):
                                if url_parent.find('loc') is url_elem:
                                    parent = url_parent
                                    break
                    else:
                        parent = url_elem.getparent()
                    
                    # Add lastmod if available
                    if parent is not None:
                        lastmod_elem = parent.find('./sm:lastmod', namespaces) or parent.find('./lastmod')
                        if lastmod_elem is not None and lastmod_elem.text:
                            metadata['lastmod'] = lastmod_elem.text
                            
                        # Add priority if available
                        priority_elem = parent.find('./sm:priority', namespaces) or parent.find('./priority')
                        if priority_elem is not None and priority_elem.text:
                            metadata['priority'] = priority_elem.text
                            
                        # Add changefreq if available
                        changefreq_elem = parent.find('./sm:changefreq', namespaces) or parent.find('./changefreq')
                        if changefreq_elem is not None and changefreq_elem.text:
                            metadata['changefreq'] = changefreq_elem.text
                    
                    discovered_urls.append(metadata)
                    
                self.logger.info(f"Found {len(discovered_urls)} URLs in sitemap")
                
            return discovered_urls
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching sitemap {sitemap_url}: {str(e)}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Error parsing sitemap XML {sitemap_url}: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error processing sitemap {sitemap_url}: {str(e)}")
            return []
        
    def crawl(self, start_url):
        """
        Crawl a website starting from the given URL.
        
        Args:
            start_url: The URL to start crawling from
            
        Returns:
            list: List of discovered URL dictionaries
        """
        self.logger.info(f"Starting crawl from {start_url}")
        
        # Parse and normalize the start URL
        parsed_url = urlparse(start_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Initialize the URL queue and visited set
        to_visit = [start_url]
        visited = set()
        discovered_urls = []
        
        while to_visit and len(visited) < self.max_pages:
            # Get the next URL to visit
            current_url = to_visit.pop(0)
            
            if current_url in visited:
                continue
                
            visited.add(current_url)
            self.logger.info(f"Crawling {current_url}")
            
            try:
                # Respect the rate limit
                time.sleep(self.rate_limit)
                
                # Make the request
                response = requests.get(current_url, timeout=30)
                
                # Skip non-HTML responses
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    self.logger.info(f"Skipping non-HTML content: {current_url}")
                    continue
                
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract page data
                title = soup.title.string if soup.title else "No Title"
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc['content'] if meta_desc else "No description"
                
                # Add to discovered URLs
                discovered_urls.append({
                    'url': current_url,
                    'title': title,
                    'description': description,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('Content-Type', '')
                })
                
                # Extract links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Skip fragment identifiers and javascript links
                    if href.startswith('#') or href.startswith('javascript:'):
                        continue
                    
                    # Build absolute URL
                    absolute_url = urljoin(current_url, href)
                    
                    # Skip URLs outside the base domain
                    if not absolute_url.startswith(base_url):
                        continue
                    
                    # Skip query parameters if present in URL
                    parsed = urlparse(absolute_url)
                    if parsed.query:
                        # Strip query parameters
                        absolute_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    
                    # Add URL to queue if not visited
                    if absolute_url not in visited and absolute_url not in to_visit:
                        to_visit.append(absolute_url)
                
            except Exception as e:
                self.logger.error(f"Error crawling {current_url}: {str(e)}")
                continue
                
        self.logger.info(f"Crawl finished. Discovered {len(discovered_urls)} URLs")
        return discovered_urls