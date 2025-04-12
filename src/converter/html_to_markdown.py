"""
HTML to Markdown converter module.

This module handles the conversion of HTML content to Markdown format with proper frontmatter.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urlparse, urljoin

from src.utils.metadata_extractor import MetadataExtractor
from src.utils.file_manager import safe_filename

# Configure logger
logger = logging.getLogger(__name__)

class HtmlToMarkdownConverter:
    """Converts HTML content to Markdown format with metadata."""
    
    def __init__(self, 
                 output_dir: str, 
                 image_dir: str = "images",
                 download_images: bool = True,
                 preserve_hierarchy: bool = True,
                 metadata_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the HTML to Markdown converter.
        
        Args:
            output_dir (str): Directory to save Markdown files
            image_dir (str): Directory to save images (relative to output_dir)
            download_images (bool): Whether to download images
            preserve_hierarchy (bool): Whether to preserve URL hierarchy in filenames
            metadata_config (Dict[str, Any], optional): Configuration for metadata extraction
        """
        self.output_dir = Path(output_dir)
        self.image_dir = Path(image_dir)
        self.download_images = download_images
        self.preserve_hierarchy = preserve_hierarchy
        self.metadata_extractor = MetadataExtractor(metadata_config)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create image directory if needed
        if download_images:
            (self.output_dir / self.image_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize HTML to text converter
        self.html2text_converter = html2text.HTML2Text()
        self.html2text_converter.ignore_links = False
        self.html2text_converter.wrap_links = False
        self.html2text_converter.body_width = 0  # Don't wrap lines
        self.html2text_converter.protect_links = True  # Don't convert links to references
        self.html2text_converter.ignore_images = False
        self.html2text_converter.unicode_snob = True  # Use Unicode instead of ASCII
        self.html2text_converter.mark_code = True
        
        logger.info(f"HTML to Markdown converter initialized with output dir: {output_dir}")
    
    def convert(self, html_content: str, url: str) -> Tuple[str, Dict[str, Any]]:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content (str): HTML content
            url (str): Original URL
            
        Returns:
            Tuple[str, Dict[str, Any]]: Markdown content and metadata
        """
        try:
            # Clean up HTML content
            cleaned_html = self._clean_html(html_content)
            
            # Extract metadata
            metadata = self.metadata_extractor.extract_metadata(cleaned_html, url)
            
            # Extract main content
            content_html = self._extract_main_content(cleaned_html)
            
            # Replace image links if needed
            if self.download_images:
                content_html, image_map = self._process_images(content_html, url)
                metadata['images'] = list(image_map.keys())
            
            # Convert HTML to Markdown
            markdown_content = self.html2text_converter.handle(content_html)
            
            # Post-process Markdown
            markdown_content = self._post_process_markdown(markdown_content)
            
            # Generate frontmatter
            frontmatter = self.metadata_extractor.generate_frontmatter(metadata)
            
            # Combine frontmatter and content
            full_markdown = f"{frontmatter}\n{markdown_content}"
            
            logger.debug(f"Successfully converted {url} to Markdown")
            return full_markdown, metadata
        
        except Exception as e:
            logger.error(f"Error converting {url} to Markdown: {str(e)}")
            return f"---\ntitle: Error converting content\nurl: {url}\n---\n\nError: {str(e)}", {'url': url}
    
    def save_markdown(self, markdown_content: str, metadata: Dict[str, Any]) -> str:
        """
        Save Markdown content to a file.
        
        Args:
            markdown_content (str): Markdown content with frontmatter
            metadata (Dict[str, Any]): Metadata dictionary
            
        Returns:
            str: Path to the saved file
        """
        try:
            # Determine filename from metadata or URL
            if metadata.get('slug'):
                filename = metadata['slug']
            else:
                url_path = urlparse(metadata['url']).path.strip('/')
                filename = url_path.split('/')[-1] if url_path else 'index'
            
            # Replace common file extensions
            filename = re.sub(r'\.(html|php|asp)$', '', filename)
            
            # Create valid filename
            filename = safe_filename(filename)
            
            # Add .md extension if not present
            if not filename.endswith('.md'):
                filename += '.md'
            
            # Determine directory structure if preserving hierarchy
            if self.preserve_hierarchy:
                url_parts = urlparse(metadata['url'])
                path_parts = url_parts.path.strip('/').split('/')
                
                # Skip the last part (it's the filename)
                if len(path_parts) > 1:
                    subdir = Path(*path_parts[:-1])
                    file_dir = self.output_dir / subdir
                    file_dir.mkdir(parents=True, exist_ok=True)
                else:
                    file_dir = self.output_dir
            else:
                file_dir = self.output_dir
            
            # Create full file path
            file_path = file_dir / filename
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Saved Markdown file to {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"Error saving Markdown file: {str(e)}")
            
            # Attempt to save to a backup location
            try:
                backup_filename = f"backup_{int(time.time())}.md"
                backup_path = self.output_dir / backup_filename
                
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                logger.info(f"Saved backup Markdown file to {backup_path}")
                return str(backup_path)
            
            except Exception as backup_e:
                logger.error(f"Failed to save backup Markdown file: {str(backup_e)}")
                return ""
    
    def _clean_html(self, html_content: str) -> str:
        """
        Clean up HTML content.
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: Cleaned HTML content
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for selector in [
                'script', 'style', 'iframe', 'noscript',
                '.comments', '.comment-section', '.sidebar', '.widget',
                '.header', '.footer', '.site-header', '.site-footer',
                'header', 'footer', 'nav',
                '.nav', '.menu', '.advertisement', '.ad', '.advert',
                '.social-sharing', '.share-buttons',
                '.related-posts', '#related-posts'
            ]:
                for element in soup.select(selector):
                    element.decompose()
            
            return str(soup)
        
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {str(e)}")
            return html_content
    
    def _extract_main_content(self, html_content: str) -> str:
        """
        Extract main content from HTML.
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: HTML of main content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Common selectors for main content in WordPress sites
            content_selectors = [
                'article', '.post-content', '.entry-content',
                '.content', 'main', '.main-content',
                '.article-content', '.post', '#content'
            ]
            
            # Try each selector
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    return str(content)
            
            # If no content container found, just return the body
            body = soup.find('body')
            if body:
                return str(body)
            
            # Fall back to the entire HTML
            return html_content
        
        except Exception as e:
            logger.warning(f"Error extracting main content: {str(e)}")
            return html_content
    
    def _process_images(self, html_content: str, base_url: str) -> Tuple[str, Dict[str, str]]:
        """
        Process images in HTML content.
        
        Args:
            html_content (str): HTML content
            base_url (str): Base URL for resolving relative links
            
        Returns:
            Tuple[str, Dict[str, str]]: Updated HTML and image mapping
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            image_map = {}
            
            # Process all images
            for img in soup.find_all('img'):
                if not img.get('src'):
                    continue
                
                original_src = img['src']
                
                # Make URL absolute if it's relative
                if not original_src.startswith(('http://', 'https://')):
                    img_url = urljoin(base_url, original_src)
                else:
                    img_url = original_src
                
                # Parse image URL and extract filename
                parsed_url = urlparse(img_url)
                img_path = parsed_url.path
                img_filename = os.path.basename(img_path)
                
                # Clean up filename
                img_filename = safe_filename(img_filename)
                
                # Make sure filename is unique
                base_name, ext = os.path.splitext(img_filename)
                counter = 1
                while img_filename in image_map.values():
                    img_filename = f"{base_name}_{counter}{ext}"
                    counter += 1
                
                # Add to image map
                image_map[img_url] = img_filename
                
                # Replace URL in HTML
                img['src'] = f"{self.image_dir}/{img_filename}"
            
            return str(soup), image_map
        
        except Exception as e:
            logger.warning(f"Error processing images: {str(e)}")
            return html_content, {}
    
    def _post_process_markdown(self, markdown_content: str) -> str:
        """
        Post-process Markdown content.
        
        Args:
            markdown_content (str): Markdown content
            
        Returns:
            str: Post-processed Markdown content
        """
        # Fix extra spaces in links
        markdown_content = re.sub(r'\[ (.*?) \]\((.*?)\)', r'[\1](\2)', markdown_content)
        
        # Fix consecutive newlines (more than 2)
        markdown_content = re.sub(r'\n{3,}', r'\n\n', markdown_content)
        
        # Replace non-breaking spaces with regular spaces
        markdown_content = markdown_content.replace('\xa0', ' ')
        
        # Fix code blocks (ensure proper spacing)
        markdown_content = re.sub(r'```(\w+)(?!\n)', r'```\1\n', markdown_content)
        markdown_content = re.sub(r'(?<!\n)```', r'\n```', markdown_content)
        
        # Add space after list markers if missing
        markdown_content = re.sub(r'^([*+-])(?! )', r'\1 ', markdown_content, flags=re.MULTILINE)
        markdown_content = re.sub(r'^(\d+\.)(?! )', r'\1 ', markdown_content, flags=re.MULTILINE)
        
        return markdown_content