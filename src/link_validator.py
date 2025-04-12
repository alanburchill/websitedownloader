"""
Link Validator Module

This module validates and fixes internal links in Markdown files.
"""

import os
import re
import logging
import json
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("websitedownloader.link_validator")

class LinkValidator:
    """A class for validating and fixing internal links in Markdown files."""
    
    def __init__(self):
        """Initialize the LinkValidator."""
        self.pages_map = {}  # Maps URLs to local file paths
        self.internal_links = {}  # Tracks all internal links
        self.external_links = []  # Tracks all external links
        
    def _build_pages_map(self, content_dir):
        """Build a mapping of original URLs to local file paths."""
        pages_dir = os.path.join(content_dir, "pages")
        
        for root, _, files in os.walk(pages_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, content_dir)
                    
                    # Extract original URL from front matter
                    original_url = self._extract_original_url(file_path)
                    if original_url:
                        self.pages_map[original_url] = rel_path
                        logger.debug(f"Mapped {original_url} -> {rel_path}")
        
        logger.info(f"Built pages map with {len(self.pages_map)} entries")
        return self.pages_map
    
    def _extract_original_url(self, markdown_path):
        """Extract original URL from Markdown front matter."""
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for front matter
            front_matter_match = re.search(r'---\s*\n(.*?)\n---', content, re.DOTALL)
            if front_matter_match:
                front_matter = front_matter_match.group(1)
                url_match = re.search(r'original_url:\s*(.*)', front_matter)
                if url_match:
                    return url_match.group(1).strip()
        except Exception as e:
            logger.error(f"Error extracting URL from {markdown_path}: {str(e)}")
        
        return None
    
    def _find_links_in_markdown(self, content_dir):
        """Find all links in Markdown files."""
        pages_dir = os.path.join(content_dir, "pages")
        
        # Regular expression to find Markdown links: [text](url)
        link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        
        for root, _, files in os.walk(pages_dir):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, content_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Find all links
                            for match in re.finditer(link_pattern, content):
                                link_text = match.group(1)
                                link_url = match.group(2)
                                
                                # Skip image links
                                if link_url.startswith('./images/'):
                                    continue
                                
                                # Check if this is an internal or external link
                                parsed_url = urlparse(link_url)
                                if parsed_url.scheme in ('http', 'https'):
                                    self.external_links.append({
                                        'from_file': rel_path,
                                        'url': link_url,
                                        'text': link_text
                                    })
                                else:
                                    self.internal_links[rel_path] = self.internal_links.get(rel_path, []) + [{
                                        'url': link_url,
                                        'text': link_text,
                                        'position': match.span(2)  # Store position for replacement
                                    }]
                    except Exception as e:
                        logger.error(f"Error processing links in {file_path}: {str(e)}")
        
        logger.info(f"Found {len(self.internal_links)} files with internal links and {len(self.external_links)} external links")
    
    def _fix_internal_links(self, content_dir):
        """Fix internal links to point to the correct local files."""
        pages_dir = os.path.join(content_dir, "pages")
        fixed_links = []
        broken_links = []
        
        # Process each file with internal links
        for file_rel_path, links in self.internal_links.items():
            file_path = os.path.join(content_dir, file_rel_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Track if we need to update this file
                file_updated = False
                
                # Process links in reverse order (to maintain positions after replacements)
                for link in sorted(links, key=lambda x: x['position'][0], reverse=True):
                    url = link['url']
                    text = link['text']
                    start_pos, end_pos = link['position']
                    
                    # Skip if already a relative path to a markdown file
                    if url.endswith('.md') and ('/' in url or '\\' in url):
                        continue
                    
                    # Check if this is a URL we have mapped
                    if url in self.pages_map:
                        # Get the relative path to the target file
                        target_path = self.pages_map[url]
                        
                        # Calculate relative path from current file to target file
                        from_dir = os.path.dirname(file_rel_path)
                        to_file = target_path
                        
                        if from_dir:
                            # Need to go up directories
                            rel_path = os.path.relpath(to_file, from_dir)
                        else:
                            # In top directory
                            rel_path = target_path
                        
                        # Replace backslashes with forward slashes for GitHub
                        rel_path = rel_path.replace('\\', '/')
                        
                        # Replace the link in the content
                        old_link_part = content[start_pos:end_pos]
                        content = content[:start_pos] + rel_path + content[end_pos:]
                        
                        fixed_links.append({
                            'file': file_rel_path,
                            'from': url,
                            'to': rel_path,
                            'text': text
                        })
                        file_updated = True
                        
                        # Adjust positions for subsequent links
                        position_shift = len(rel_path) - len(old_link_part)
                        for other_link in links:
                            if other_link['position'][0] < start_pos:
                                other_link['position'] = (
                                    other_link['position'][0],
                                    other_link['position'][1] + position_shift
                                )
                    else:
                        # This is a broken internal link
                        broken_links.append({
                            'file': file_rel_path,
                            'url': url,
                            'text': text
                        })
                
                # Save the updated content if any links were fixed
                if file_updated:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Updated links in {file_rel_path}")
            
            except Exception as e:
                logger.error(f"Error fixing links in {file_path}: {str(e)}")
        
        return {
            'fixed_links': fixed_links,
            'broken_links': broken_links
        }
    
    def validate_links(self, content_dir):
        """
        Validate and fix internal links in the converted content.
        
        Args:
            content_dir (str): Directory containing the GitHub content
            
        Returns:
            dict: Validation results
        """
        logger.info("Starting link validation")
        
        # Build mapping of original URLs to local file paths
        self._build_pages_map(content_dir)
        
        # Find all links in Markdown files
        self._find_links_in_markdown(content_dir)
        
        # Fix internal links
        link_fixes = self._fix_internal_links(content_dir)
        
        # Generate results
        results = {
            'pages_mapped': len(self.pages_map),
            'files_with_internal_links': len(self.internal_links),
            'external_links': len(self.external_links),
            'fixed_links': link_fixes['fixed_links'],
            'broken_links': link_fixes['broken_links']
        }
        
        logger.info(f"Link validation complete. Fixed {len(link_fixes['fixed_links'])} links, found {len(link_fixes['broken_links'])} broken links")
        
        return results