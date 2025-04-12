"""
Report Generator Module

This module generates reports and site indexes for the downloaded content.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("websitedownloader.report_generator")

class ReportGenerator:
    """Generates reports and site indexes for the downloaded content."""
    
    def generate_site_index(self, content_dir, conversion_results):
        """
        Generate main README.md for GitHub repository.
        
        Args:
            content_dir (str): Directory containing the GitHub content
            conversion_results (list): List of converted pages
        """
        logger.info("Generating site index (README.md)")
        
        # Extract domain from first URL
        domain = None
        if conversion_results and len(conversion_results) > 0:
            for result in conversion_results:
                if result.get("url"):
                    parsed_url = urlparse(result.get("url"))
                    domain = parsed_url.netloc
                    break
        
        site_title = f"{domain} Content Archive" if domain else "Website Content Archive"
        
        # Group pages by directory structure
        page_structure = {}
        
        for result in conversion_results:
            if not result.get("converted", False) or not result.get("markdown_path"):
                continue
                
            # Get the relative path from the content directory
            rel_path = os.path.relpath(result["markdown_path"], content_dir).replace("\\", "/")
            
            # Extract directory parts
            parts = os.path.dirname(rel_path).split(os.sep)
            
            # Build nested structure
            current = page_structure
            for part in parts:
                if part and part != ".":
                    if part not in current:
                        current[part] = {"__files": []}
                    current = current[part]
                    
            # Add file to current level
            filename = os.path.basename(rel_path)
            current["__files"].append({
                "path": rel_path,
                "title": result.get("title", filename)
            })
        
        # Generate README content
        readme_content = f"""# {site_title}

This repository contains archived content from {domain if domain else 'a website'}, converted to Markdown format for easy viewing on GitHub.

## Content

"""
        
        # Add table of contents
        readme_content += self._generate_toc(page_structure)
        
        # Add metadata and generation info
        readme_content += f"""
---

## About This Archive

This content was archived using the [WebSiteDownloader](https://github.com/yourusername/WebSiteDownloader) tool on {datetime.now().strftime('%Y-%m-%d')}.

The original website content belongs to its respective copyright holders. This archive is intended for personal reference only.
"""
        
        # Write README.md to content directory
        readme_path = os.path.join(content_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        logger.info(f"Generated site index: {readme_path}")
    
    def _generate_toc(self, structure, level=0, path=""):
        """Generate a table of contents from the page structure."""
        indent = "  " * level
        content = ""
        
        # Add files at this level first
        files = structure.pop("__files", [])
        for file_info in sorted(files, key=lambda x: x["title"]):
            title = file_info["title"]
            rel_path = file_info["path"]
            content += f"{indent}- [{title}]({rel_path})\n"
        
        # Then add directories
        for dirname, sub_structure in sorted(structure.items()):
            if dirname == "__files":
                continue
                
            dir_path = os.path.join(path, dirname) if path else dirname
            content += f"{indent}- **{dirname}/**\n"
            content += self._generate_toc(sub_structure, level + 1, dir_path)
            
        return content
    
    def generate_download_report(self, logs_dir, all_results):
        """
        Generate a download summary report.
        
        Args:
            logs_dir (str): Directory to save the report
            all_results (dict): Results from different phases
        """
        logger.info("Generating download summary report")
        
        # Calculate statistics
        stats = {
            "crawled_urls": len(all_results.get("discovered_urls", [])),
            "downloaded_pages": 0,
            "failed_downloads": 0,
            "converted_pages": 0,
            "failed_conversions": 0,
            "downloaded_images": 0,
            "fixed_links": 0,
            "broken_links": 0
        }
        
        # Page download stats
        downloaded_pages = all_results.get("downloaded_pages", [])
        if downloaded_pages:
            stats["downloaded_pages"] = sum(1 for p in downloaded_pages if p.get("downloaded", False))
            stats["failed_downloads"] = sum(1 for p in downloaded_pages if not p.get("downloaded", False))
        
        # Conversion stats
        conversion_results = all_results.get("conversion_results", [])
        if conversion_results:
            stats["converted_pages"] = sum(1 for r in conversion_results if r.get("converted", False))
            stats["failed_conversions"] = sum(1 for r in conversion_results if not r.get("converted", False))
            
            # Count images
            for result in conversion_results:
                if result.get("converted", False) and "images" in result:
                    stats["downloaded_images"] += len(result["images"])
        
        # Link validation stats
        validation_results = all_results.get("validation_results", {})
        if validation_results:
            stats["fixed_links"] = len(validation_results.get("fixed_links", []))
            stats["broken_links"] = len(validation_results.get("broken_links", []))
        
        # Generate the report markdown
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_content = f"""# WebSiteDownloader Summary Report
Generated on: {now}

## Statistics

- **Crawled URLs:** {stats["crawled_urls"]}
- **Downloaded Pages:** {stats["downloaded_pages"]} (Failed: {stats["failed_downloads"]})
- **Converted to Markdown:** {stats["converted_pages"]} (Failed: {stats["failed_conversions"]})
- **Downloaded Images:** {stats["downloaded_images"]}
- **Fixed Internal Links:** {stats["fixed_links"]}
- **Broken Links:** {stats["broken_links"]}

## Errors and Warnings

"""
        
        # Add errors from different phases
        if "downloaded_pages" in all_results:
            failed_downloads = [p for p in all_results["downloaded_pages"] if not p.get("downloaded", False)]
            if failed_downloads:
                report_content += "### Download Errors\n\n"
                for page in failed_downloads[:10]:  # Limit to first 10
                    report_content += f"- **{page.get('url')}**: {page.get('error', 'Unknown error')}\n"
                if len(failed_downloads) > 10:
                    report_content += f"- ... and {len(failed_downloads) - 10} more\n"
                report_content += "\n"
        
        if "conversion_results" in all_results:
            failed_conversions = [r for r in all_results["conversion_results"] if not r.get("converted", False)]
            if failed_conversions:
                report_content += "### Conversion Errors\n\n"
                for result in failed_conversions[:10]:  # Limit to first 10
                    report_content += f"- **{result.get('url')}**: {result.get('error', 'Unknown error')}\n"
                if len(failed_conversions) > 10:
                    report_content += f"- ... and {len(failed_conversions) - 10} more\n"
                report_content += "\n"
        
        if "validation_results" in all_results and "broken_links" in all_results["validation_results"]:
            broken_links = all_results["validation_results"]["broken_links"]
            if broken_links:
                report_content += "### Broken Links\n\n"
                for link in broken_links[:10]:  # Limit to first 10
                    report_content += f"- In **{link.get('file')}**: `{link.get('url')}` (Text: \"{link.get('text')}\")\n"
                if len(broken_links) > 10:
                    report_content += f"- ... and {len(broken_links) - 10} more\n"
        
        # Save report
        os.makedirs(logs_dir, exist_ok=True)
        report_path = os.path.join(logs_dir, "download-summary.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        logger.info(f"Generated download summary report: {report_path}")
    
    def generate_metadata(self, conversion_results, metadata_dir):
        """
        Generate metadata files for each page.
        
        Args:
            conversion_results (list): List of converted pages
            metadata_dir (str): Directory to save metadata files
        """
        logger.info("Generating page metadata")
        
        # Create metadata directory if it doesn't exist
        os.makedirs(metadata_dir, exist_ok=True)
        
        for i, result in enumerate(conversion_results):
            if not result.get("converted", False):
                continue
                
            # Create a metadata file for this page
            url = result.get("url", "")
            title = result.get("title", "Untitled")
            
            # Create a filename from URL
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            if not path_parts or path_parts == [""]:
                filename = f"{parsed_url.netloc}_index.json"
            else:
                filename = f"{parsed_url.netloc}_{path_parts[-1]}.json"
            
            # Sanitize filename
            filename = filename.replace('.', '_')
            if len(filename) > 100:
                filename = f"{filename[:95]}_{i}.json"
            
            # Build metadata object
            metadata = {
                "url": url,
                "title": title,
                "download_date": result.get("download_date", datetime.now().isoformat()),
                "markdown_path": os.path.relpath(result.get("markdown_path", ""), os.path.dirname(metadata_dir)),
                "images": result.get("images", []),
                "word_count": self._estimate_word_count(result.get("markdown_path")),
                "reading_time": 0  # Will calculate below
            }
            
            # Calculate approximate reading time (200 words per minute)
            if metadata["word_count"] > 0:
                metadata["reading_time"] = round(metadata["word_count"] / 200, 1)
            
            # Save metadata
            metadata_path = os.path.join(metadata_dir, filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        logger.info(f"Generated metadata for {sum(1 for r in conversion_results if r.get('converted', False))} pages")
    
    def _estimate_word_count(self, markdown_path):
        """Estimate word count in a Markdown file."""
        if not markdown_path or not os.path.exists(markdown_path):
            return 0
            
        try:
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Skip front matter
                content = content.split('---', 2)[-1] if '---' in content else content
                
                # Count words (rough estimation)
                return len(content.split())
        except Exception as e:
            logger.error(f"Error estimating word count: {str(e)}")
            return 0