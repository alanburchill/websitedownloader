"""
Module to convert HTML content to Markdown format.
"""

import os
import re
import logging
import json
from bs4 import BeautifulSoup
import html2text
import markdown
from urllib.parse import urljoin, urlparse

class MarkdownConverter:
    """Class to convert HTML content to Markdown format."""
    
    def __init__(self, github_flavored=True, image_download=True):
        """
        Initialize the Markdown converter.
        
        Args:
            github_flavored: Whether to use GitHub Flavored Markdown
            image_download: Whether to download images
        """
        self.github_flavored = github_flavored
        self.image_download = image_download
        self.logger = logging.getLogger(__name__)
        
        # Configure HTML to Markdown converter
        self.html2md = html2text.HTML2Text()
        self.html2md.ignore_links = False
        self.html2md.ignore_images = False
        self.html2md.ignore_emphasis = False
        self.html2md.ignore_tables = False
        self.html2md.body_width = 0  # No wrapping
        self.html2md.unicode_snob = True
        self.html2md.protect_links = True
        
    def convert_file(self, html_file, output_dir, base_url=None):
        """
        Convert an HTML file to Markdown.
        
        Args:
            html_file: Path to HTML file
            output_dir: Directory to save Markdown output
            base_url: Base URL for resolving relative links
            
        Returns:
            str: Path to the generated Markdown file
        """
        try:
            # Load HTML content
            with open(html_file, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            
            # Extract metadata from companion JSON file if it exists
            metadata = {}
            metadata_file = os.path.splitext(html_file)[0] + '_meta.json'
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Get base URL from metadata if not provided
            if base_url is None and 'url' in metadata:
                base_url = metadata['url']
                parsed_url = urlparse(base_url)
                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Convert HTML to Markdown
            md_content = self.convert_html(html_content, base_url)
            
            # Generate output filename
            filename = os.path.basename(html_file)
            md_filename = os.path.splitext(filename)[0] + '.md'
            md_path = os.path.join(output_dir, md_filename)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Add YAML frontmatter with metadata
            frontmatter = self._generate_frontmatter(metadata)
            md_content = frontmatter + md_content
            
            # Write Markdown to file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            self.logger.info(f"Successfully converted {html_file} to {md_path}")
            return md_path
        
        except Exception as e:
            self.logger.error(f"Failed to convert {html_file}: {str(e)}")
            return None
    
    def convert_html(self, html_content, base_url=None):
        """
        Convert HTML string to Markdown.
        
        Args:
            html_content: HTML content as string
            base_url: Base URL for resolving relative links
            
        Returns:
            str: Markdown content
        """
        # Parse HTML with BeautifulSoup for preprocessing
        # Try lxml parser first, fall back to html.parser if lxml has issues
        try:
            soup = BeautifulSoup(html_content, 'lxml')
        except:
            self.logger.warning("Failed to use lxml parser, falling back to html.parser")
            soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup.select('script, style, iframe, [style*="display:none"], [hidden]'):
            element.extract()
        
        # Fix relative URLs if base_url is provided
        if base_url:
            for link in soup.find_all('a', href=True):
                link['href'] = urljoin(base_url, link['href'])
            
            for img in soup.find_all('img', src=True):
                img['src'] = urljoin(base_url, img['src'])
        
        # Convert to Markdown
        md_content = self.html2md.handle(str(soup))
        
        # Post-process Markdown content
        md_content = self._post_process_markdown(md_content)
        
        return md_content
    
    def _generate_frontmatter(self, metadata):
        """Generate YAML frontmatter for Markdown files."""
        frontmatter = ['---']
        
        # Add title if available
        if 'title' in metadata:
            frontmatter.append(f"title: \"{metadata['title']}\"")
        
        # Add original URL
        if 'url' in metadata:
            frontmatter.append(f"original_url: \"{metadata['url']}\"")
        
        # Add timestamp
        if 'timestamp' in metadata:
            frontmatter.append(f"date: \"{metadata['timestamp']}\"")
        
        # Add description if available
        if 'description' in metadata:
            # Escape quotes in description
            description = metadata['description'].replace('"', '\\"')
            frontmatter.append(f"description: \"{description}\"")
        
        frontmatter.append('---\n\n')
        return '\n'.join(frontmatter)
    
    def _post_process_markdown(self, content):
        """Post-process Markdown content for better formatting."""
        # Fix multiple consecutive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Fix spacing around headers
        content = re.sub(r'(\n#{1,6} .+)\n(?=[^\n])', r'\1\n\n', content)
        
        # Fix code block formatting for GitHub flavored markdown
        if self.github_flavored:
            # Replace indented code blocks with fenced code blocks
            content = re.sub(r'(?m)^( {4,}[^\n]+\n)+', lambda m: 
                             '```\n' + re.sub(r'^    ', '', m.group(0), flags=re.MULTILINE) + '```\n', content)
        
        return content

    def batch_convert(self, html_files, output_dir, base_url=None):
        """
        Convert multiple HTML files to Markdown.
        
        Args:
            html_files: List of paths to HTML files
            output_dir: Directory to save Markdown output
            base_url: Base URL for resolving relative links
            
        Returns:
            list: Paths to generated Markdown files
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        converted_files = []
        
        for i, html_file in enumerate(html_files):
            self.logger.info(f"Converting [{i+1}/{len(html_files)}]: {html_file}")
            md_path = self.convert_file(html_file, output_dir, base_url)
            if md_path:
                converted_files.append(md_path)
        
        self.logger.info(f"Batch conversion completed. Converted {len(converted_files)} files.")
        return converted_files