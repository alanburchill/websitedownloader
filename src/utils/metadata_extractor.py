"""
Metadata extraction utility for WordPress content.

This module provides functionality to extract metadata from WordPress HTML content.
"""

import re
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Configure logger
logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Class for extracting metadata from HTML content."""
    
    def __init__(self, ai_correction_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the metadata extractor.
        
        Args:
            ai_correction_config (Dict[str, Any], optional): Configuration for AI-based correction
        """
        self.ai_correction_config = ai_correction_config or {}
        logger.info("Metadata Extractor initialized")
    
    def extract_metadata(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML content.
        
        Args:
            html_content (str): HTML content
            url (str): URL of the page
            
        Returns:
            Dict[str, Any]: Extracted metadata
        """
        # Initialize base metadata
        metadata = {
            'url': url,
            'title': '',
            'excerpt': '',
            'date_published': '',
            'date_modified': '',
            'author': '',
            'categories': [],
            'tags': [],
            'featured_image': '',
            'content_type': 'post',
            'extracted_timestamp': time.time()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title - try various methods
            metadata['title'] = self._extract_title(soup)
            
            # Extract publication date
            metadata['date_published'] = self._extract_date(soup, is_modified=False)
            
            # Extract modification date
            metadata['date_modified'] = self._extract_date(soup, is_modified=True)
            
            # Extract author
            metadata['author'] = self._extract_author(soup)
            
            # Extract excerpt/description
            metadata['excerpt'] = self._extract_excerpt(soup)
            
            # Extract categories
            metadata['categories'] = self._extract_categories(soup)
            
            # Extract tags
            metadata['tags'] = self._extract_tags(soup)
            
            # Extract featured image
            metadata['featured_image'] = self._extract_featured_image(soup, url)
            
            # Determine content type
            metadata['content_type'] = self._determine_content_type(soup, url)
            
            # Deduce slug from URL
            metadata['slug'] = self._extract_slug(url)
            
            # Apply AI-based corrections if configured
            if self.ai_correction_config.get('enabled'):
                metadata = self._apply_ai_corrections(metadata, html_content)
            
            # Clean up empty values
            metadata = self._clean_metadata(metadata)
            
            logger.debug(f"Extracted metadata from {url}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {url}: {str(e)}")
            return metadata
    
    def generate_frontmatter(self, metadata: Dict[str, Any]) -> str:
        """
        Generate YAML frontmatter from metadata.
        
        Args:
            metadata (Dict[str, Any]): Metadata dictionary
            
        Returns:
            str: YAML frontmatter string
        """
        frontmatter_lines = ['---']
        
        # Add essential frontmatter fields
        if metadata.get('title'):
            frontmatter_lines.append(f"title: '{metadata['title'].replace(\"'\", \"''\")}'" if "'" in metadata['title'] else f"title: {metadata['title']}")
        
        if metadata.get('date_published'):
            frontmatter_lines.append(f"date: {metadata['date_published']}")
        
        if metadata.get('date_modified'):
            frontmatter_lines.append(f"last_modified_at: {metadata['date_modified']}")
        
        if metadata.get('author'):
            frontmatter_lines.append(f"author: {metadata['author']}")
        
        if metadata.get('excerpt'):
            # Escape single quotes by doubling them
            excerpt = metadata['excerpt'].replace("'", "''")
            frontmatter_lines.append(f"excerpt: '{excerpt}'")
        
        # Handle categories
        if metadata.get('categories') and len(metadata['categories']) > 0:
            frontmatter_lines.append("categories:")
            for category in metadata['categories']:
                frontmatter_lines.append(f"  - {category}")
        
        # Handle tags
        if metadata.get('tags') and len(metadata['tags']) > 0:
            frontmatter_lines.append("tags:")
            for tag in metadata['tags']:
                frontmatter_lines.append(f"  - {tag}")
        
        # Add featured image if available
        if metadata.get('featured_image'):
            frontmatter_lines.append(f"header:")
            frontmatter_lines.append(f"  image: {metadata['featured_image']}")
        
        # Add permalink/slug if available
        if metadata.get('slug'):
            frontmatter_lines.append(f"permalink: /{metadata['slug']}/")
        
        # Add original URL
        if metadata.get('url'):
            frontmatter_lines.append(f"original_url: {metadata['url']}")
        
        frontmatter_lines.append('---')
        frontmatter_lines.append('')  # Add an extra newline
        
        return '\n'.join(frontmatter_lines)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML."""
        title = ''
        
        # Try JSON-LD
        json_ld = self._extract_json_ld(soup)
        if json_ld:
            for item in json_ld:
                if isinstance(item, dict):
                    if item.get('@type') in ['Article', 'BlogPosting', 'WebPage'] and item.get('headline'):
                        title = item.get('headline')
                        break
        
        # Try Open Graph
        if not title:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '')
        
        # Try Twitter Card
        if not title:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title:
                title = twitter_title.get('content', '')
        
        # Try <title> tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text.strip()
                
                # Clean up title (remove site name)
                separators = [' | ', ' - ', ' – ', ' — ', ' // ', ' » ']
                for sep in separators:
                    if sep in title:
                        title = title.split(sep)[0].strip()
        
        # Try h1
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.text.strip()
        
        return title
    
    def _extract_date(self, soup: BeautifulSoup, is_modified: bool = False) -> str:
        """Extract publication or modification date."""
        date_str = ''
        
        # Define which metadata to look for based on type
        meta_attrs = []
        if is_modified:
            meta_attrs = [
                {'property': 'article:modified_time'},
                {'itemprop': 'dateModified'},
                {'name': 'dateModified'}
            ]
        else:
            meta_attrs = [
                {'property': 'article:published_time'},
                {'itemprop': 'datePublished'},
                {'name': 'datePublished'}
            ]
        
        # Check JSON-LD
        json_ld = self._extract_json_ld(soup)
        if json_ld:
            for item in json_ld:
                if isinstance(item, dict):
                    if item.get('@type') in ['Article', 'BlogPosting', 'WebPage']:
                        if is_modified and item.get('dateModified'):
                            date_str = item.get('dateModified')
                            break
                        elif not is_modified and item.get('datePublished'):
                            date_str = item.get('datePublished')
                            break
        
        # Try meta tags
        if not date_str:
            for attrs in meta_attrs:
                meta = soup.find('meta', attrs=attrs)
                if meta and meta.get('content'):
                    date_str = meta.get('content')
                    break
        
        # Try time elements
        if not date_str:
            time_elements = soup.find_all('time')
            for time_element in time_elements:
                datetime_attr = time_element.get('datetime')
                if datetime_attr:
                    date_str = datetime_attr
                    break
        
        # Try looking for common WordPress date structures
        if not date_str:
            date_classes = [
                '.posted-on time', '.entry-date', '.entry-meta .date',
                '.post-date', '.article-date', '.publish-date'
            ]
            for class_name in date_classes:
                date_element = soup.select_one(class_name)
                if date_element:
                    if date_element.get('datetime'):
                        date_str = date_element.get('datetime')
                    else:
                        date_str = date_element.text.strip()
                    break
        
        # Cleanup and format the date
        if date_str:
            # Try ISO format first
            try:
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return parsed_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                # If that fails, try common formats
                try:
                    # Add more format strings if needed
                    for fmt in ['%B %d, %Y', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
                except:
                    # If all parsing fails, return as-is
                    return date_str
        
        return date_str
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author."""
        author = ''
        
        # Try JSON-LD
        json_ld = self._extract_json_ld(soup)
        if json_ld:
            for item in json_ld:
                if isinstance(item, dict):
                    if item.get('@type') in ['Article', 'BlogPosting', 'WebPage']:
                        if item.get('author'):
                            if isinstance(item['author'], dict):
                                author = item['author'].get('name', '')
                            elif isinstance(item['author'], str):
                                author = item['author']
                            break
        
        # Try meta tags
        if not author:
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                author = author_meta.get('content', '')
        
        # Try common author classes
        if not author:
            author_classes = [
                '.author-name', '.author .vcard', '.entry-author', 
                '.author-info', '.byline'
            ]
            for class_name in author_classes:
                author_element = soup.select_one(class_name)
                if author_element:
                    author = author_element.text.strip()
                    break
        
        # Try rel="author" links
        if not author:
            author_link = soup.find('a', attrs={'rel': 'author'})
            if author_link:
                author = author_link.text.strip()
        
        # Clean up author name
        if author:
            # Remove "By" prefix
            author = re.sub(r'^by\s+', '', author, flags=re.IGNORECASE).strip()
            
            # Remove "Posted by" prefix
            author = re.sub(r'^posted by\s+', '', author, flags=re.IGNORECASE).strip()
            
            # Remove trailing commas, etc.
            author = author.rstrip('.,;:')
        
        return author
    
    def _extract_excerpt(self, soup: BeautifulSoup) -> str:
        """Extract article excerpt or description."""
        excerpt = ''
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            excerpt = meta_desc.get('content', '')
        
        # Try Open Graph description
        if not excerpt or len(excerpt) < 10:
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                excerpt = og_desc.get('content', '')
        
        # Try Twitter Card description
        if not excerpt or len(excerpt) < 10:
            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            if twitter_desc:
                excerpt = twitter_desc.get('content', '')
        
        # Try excerpt class
        if not excerpt or len(excerpt) < 10:
            excerpt_classes = [
                '.entry-excerpt', '.excerpt', '.entry-summary',
                '.post-excerpt', '.article-excerpt', '.summary'
            ]
            for class_name in excerpt_classes:
                excerpt_element = soup.select_one(class_name)
                if excerpt_element:
                    excerpt = excerpt_element.text.strip()
                    break
        
        # Clean and truncate excerpt if needed
        if excerpt:
            # Remove newlines and excess spaces
            excerpt = re.sub(r'\s+', ' ', excerpt).strip()
            
            # Truncate if too long (typical meta descriptions are around 155 chars)
            if len(excerpt) > 300:
                excerpt = excerpt[:297] + '...'
        
        return excerpt
    
    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract article categories."""
        categories = []
        
        # Try JSON-LD
        json_ld = self._extract_json_ld(soup)
        if json_ld:
            for item in json_ld:
                if isinstance(item, dict):
                    if item.get('@type') in ['Article', 'BlogPosting', 'WebPage']:
                        if item.get('articleSection'):
                            if isinstance(item['articleSection'], list):
                                categories.extend(item['articleSection'])
                            elif isinstance(item['articleSection'], str):
                                categories.append(item['articleSection'])
        
        # Try common category classes
        if not categories:
            category_selectors = [
                '.cat-links a', '.category-links a', '.categories a', 
                '.post-categories a', '.entry-categories a'
            ]
            for selector in category_selectors:
                for category_element in soup.select(selector):
                    category = category_element.text.strip()
                    if category and category not in categories:
                        categories.append(category)
        
        return categories
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags."""
        tags = []
        
        # Try common tag classes
        tag_selectors = [
            '.tag-links a', '.tags a', '.post-tags a', 
            '.entry-tags a', '.article-tags a'
        ]
        for selector in tag_selectors:
            for tag_element in soup.select(selector):
                tag = tag_element.text.strip()
                if tag and tag.lower() not in [t.lower() for t in tags]:
                    # Remove hash symbols often used for tags
                    tag = tag.lstrip('#')
                    if tag:
                        tags.append(tag)
        
        return tags
    
    def _extract_featured_image(self, soup: BeautifulSoup, url: str) -> str:
        """Extract featured image URL."""
        image_url = ''
        
        # Try Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content', '')
        
        # Try Twitter Card image
        if not image_url:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image:
                image_url = twitter_image.get('content', '')
        
        # Try JSON-LD
        if not image_url:
            json_ld = self._extract_json_ld(soup)
            if json_ld:
                for item in json_ld:
                    if isinstance(item, dict):
                        if item.get('@type') in ['Article', 'BlogPosting', 'WebPage']:
                            if item.get('image'):
                                if isinstance(item['image'], dict):
                                    image_url = item['image'].get('url', '')
                                elif isinstance(item['image'], str):
                                    image_url = item['image']
                                break
        
        # Try featured image classes
        if not image_url:
            featured_selectors = [
                '.post-thumbnail img', '.featured-image img',
                '.entry-featured-image img', '.post-featured-image img'
            ]
            for selector in featured_selectors:
                img = soup.select_one(selector)
                if img and img.has_attr('src'):
                    image_url = img['src']
                    break
        
        # Make relative URLs absolute
        if image_url and not image_url.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            image_url = urljoin(url, image_url)
        
        return image_url
    
    def _determine_content_type(self, soup: BeautifulSoup, url: str) -> str:
        """Determine content type (post, page, etc.)."""
        content_type = 'post'  # Default
        
        # Check URL patterns
        path = urlparse(url).path
        
        # Common page URL patterns
        page_patterns = ['/about/', '/contact/', '/privacy-policy/', '/terms/', '/faq/']
        for pattern in page_patterns:
            if pattern in path.lower():
                return 'page'
        
        # Check body classes (WordPress adds specific classes)
        body = soup.find('body')
        if body and body.has_attr('class'):
            body_classes = body['class']
            if isinstance(body_classes, list):
                body_classes = ' '.join(body_classes)
            
            if 'page' in body_classes and 'single-page' in body_classes:
                content_type = 'page'
            elif 'post' in body_classes and 'single-post' in body_classes:
                content_type = 'post'
            elif 'archive' in body_classes:
                content_type = 'archive'
        
        return content_type
    
    def _extract_slug(self, url: str) -> str:
        """Extract slug from URL."""
        # Parse the URL
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        
        # Remove common parts
        path = re.sub(r'^(blog|posts|articles|news)/', '', path)
        
        # Handle date-based URLs (e.g., /2020/04/15/my-post/)
        date_match = re.match(r'^(\d{4}/\d{2}/\d{2}/)(.*)', path)
        if date_match:
            path = date_match.group(2)
        
        # Remove trailing slashes and file extensions
        path = path.rstrip('/')
        path = re.sub(r'\.(html|php|asp)$', '', path)
        
        # If there's still a path with slashes, take the last part
        if '/' in path:
            path = path.split('/')[-1]
        
        return path
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract JSON-LD data."""
        json_ld_data = []
        
        # Look for JSON-LD scripts
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    json_ld_data.extend(data)
                else:
                    json_ld_data.append(data)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return json_ld_data
    
    def _apply_ai_corrections(self, metadata: Dict[str, Any], html_content: str) -> Dict[str, Any]:
        """
        Apply AI-based corrections to metadata if configured.
        
        This is a placeholder for future implementation.
        In a real implementation, this could make API calls to AI services.
        """
        # This is just a placeholder - no actual AI correction is performed here
        logger.debug("AI-based metadata correction is enabled but not implemented.")
        return metadata
    
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up metadata dictionary."""
        # Remove empty lists
        for key in ['categories', 'tags']:
            if key in metadata and not metadata[key]:
                metadata[key] = []
        
        # Remove empty strings
        for key, value in list(metadata.items()):
            if isinstance(value, str) and not value:
                if key in ['title', 'excerpt', 'date_published', 'date_modified', 'author', 'featured_image', 'slug']:
                    # Keep the key but with empty value for essential fields
                    metadata[key] = ""
        
        return metadata