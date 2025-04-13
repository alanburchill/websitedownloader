"""
WebSiteDownloader main entry point.
"""

import os
import sys
import logging
import argparse
import json
import yaml
import glob
from datetime import datetime

from .crawler import WebCrawler
from .downloader import ContentDownloader
from .converter import MarkdownConverter

def setup_logging(log_level=logging.INFO):
    """Set up logging configuration."""
    # Create Logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        
    # Create log file path in Logs directory
    log_filename = f"websitedownloader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filepath)
        ]
    )
    
    # Log where the log file is being saved
    root_logger = logging.getLogger()
    root_logger.info(f"Log file saved to: {log_filepath}")
    
def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download websites and convert them to Markdown for GitHub."
    )
    
    # Source options
    parser.add_argument("--source", help="Source URL to crawl or download")
    parser.add_argument("--input-file", help="Input file containing URLs to download")
    parser.add_argument("--sitemap", help="URL to a sitemap.xml file to crawl instead of recursive crawling")
    
    # Operation mode
    parser.add_argument("--crawl", action="store_true", help="Crawl the website and discover URLs")
    parser.add_argument("--download", action="store_true", help="Download discovered URLs")
    parser.add_argument("--download_all", action="store_true", help="Download all resources including images and files from the website itself (excluding external sources)")
    parser.add_argument("--convert", action="store_true", help="Convert HTML to Markdown")
    
    # Output options
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--config", help="Path to YAML configuration file")
    
    # Crawler options
    parser.add_argument("--max-pages", type=int, default=1000, help="Maximum pages to crawl")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
      # Converter options
    parser.add_argument("--base-url", help="Base URL for resolving relative links in HTML")
    parser.add_argument("--html-dir", help="Directory containing HTML files to convert")
    
    # Debug options
    parser.add_argument("--verbose", action="store_true", help="Show verbose output including all assets being downloaded")
    
    return parser.parse_args()

def load_config(config_path):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        return {}

def save_urls(urls, output_dir):
    """Save discovered URLs to a JSON file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, f"urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, 'w') as f:
        json.dump(urls, f, indent=2)
    
    logging.info(f"Saved {len(urls)} URLs to {output_path}")
    return output_path

def load_urls(input_path):
    """Load URLs from a JSON or text file."""
    _, ext = os.path.splitext(input_path)
    
    try:
        if ext.lower() == '.json':
            with open(input_path, 'r') as f:
                return json.load(f)
        else:
            # Assume it's a text file with one URL per line
            with open(input_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logging.error(f"Failed to load URLs from {input_path}: {e}")
        return []

def find_html_files(html_dir):
    """Find HTML files in the specified directory."""
    html_files = []
    html_patterns = ['*.html', '*.htm']
    
    for pattern in html_patterns:
        html_files.extend(glob.glob(os.path.join(html_dir, pattern)))
    
    return html_files

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set log level based on verbose flag
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level=log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting WebSiteDownloader")
    
    # Load configuration if provided
    config = {}
    if args.config:
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    
    # Create output directory if it doesn't exist
    output_dir = args.output
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Crawl mode - discover URLs
    if args.crawl:
        # Use config values if available, otherwise use command line arguments
        max_pages = args.max_pages
        rate_limit = args.delay
        
        if config and 'crawler' in config:
            max_pages = config['crawler'].get('max_pages', max_pages)
            rate_limit = config['crawler'].get('rate_limit', rate_limit)
        
        crawler = WebCrawler(
            max_pages=max_pages,
            rate_limit=rate_limit,
            use_relative_urls=config.get('use_relative_urls', True)  # Pass the new parameter
        )
        
        if args.sitemap:
            # Use sitemap-based crawler
            logger.info(f"Crawling sitemap: {args.sitemap}")
            urls = crawler.crawl_sitemap(args.sitemap)
        elif args.source:
            # Use recursive crawler
            logger.info(f"Recursively crawling: {args.source}")
            urls = crawler.crawl(args.source)
        else:
            logger.error("Either source URL or sitemap URL is required for crawl mode")
            sys.exit(1)
            
        if not urls:
            logger.error("No URLs discovered during crawl")
            sys.exit(1)
            
        # Save discovered URLs
        urls_file = save_urls(urls, output_dir)
        logger.info(f"Crawl completed. Found {len(urls)} URLs.")
        
        # Download mode after crawl if requested
        if args.download or args.download_all:
            # Get configuration values for the downloader
            request_delay = args.delay
            max_retries = 3
            timeout = 30
            
            if config and 'downloader' in config:
                request_delay = config['downloader'].get('request_delay', request_delay)
                max_retries = config['downloader'].get('max_retries', max_retries)
                timeout = config['downloader'].get('timeout', timeout)
            
            # Initialize downloader with config
            downloader = ContentDownloader(
                request_delay=request_delay,
                max_retries=max_retries,
                timeout=timeout,
                verbose=args.verbose,
                config=config
            )
            
            downloads = downloader.download_all(urls, output_dir, download_media=args.download_all)
            logger.info(f"Download completed. Downloaded {len(downloads)} files.")
            
            # Convert mode after download if requested
            if args.convert:
                html_files = find_html_files(output_dir)
                converter = MarkdownConverter(github_flavored=True)
                md_files = converter.batch_convert(html_files, os.path.join(output_dir, 'markdown'), args.base_url)
                logger.info(f"Conversion completed. Generated {len(md_files)} Markdown files.")
    # Download mode - from existing URL list
    elif args.download or args.download_all:
        urls = []
        if args.source:
            urls = [args.source]
        elif args.input_file:
            urls = load_urls(args.input_file)
        else:
            logger.error("Source URL or input file is required for download mode")
            sys.exit(1)
            
        if not urls:
            logger.error("No URLs to download")
            sys.exit(1)
            
        logger.info(f"Downloading {len(urls)} URLs")
        
        if args.download_all:
            logger.info("Also downloading all embedded media (images, stylesheets, etc.) from the same domain")
        
        # Get configuration values for the downloader
        request_delay = args.delay
        max_retries = 3
        timeout = 30
        
        if config and 'downloader' in config:
            request_delay = config['downloader'].get('request_delay', request_delay)
            max_retries = config['downloader'].get('max_retries', max_retries)
            timeout = config['downloader'].get('timeout', timeout)
        
        # Initialize downloader with config
        downloader = ContentDownloader(
            request_delay=request_delay,
            max_retries=max_retries,
            timeout=timeout,
            verbose=args.verbose,
            config=config
        )
        
        downloads = downloader.download_all(urls, output_dir, download_media=args.download_all)
        logger.info(f"Download completed. Downloaded {len(downloads)} files.")
        
        # Convert mode after download if requested
        if args.convert:
            html_files = find_html_files(output_dir)
            converter = MarkdownConverter(github_flavored=True)
            md_files = converter.batch_convert(html_files, os.path.join(output_dir, 'markdown'), args.base_url)
            logger.info(f"Conversion completed. Generated {len(md_files)} Markdown files.")
    
    # Convert mode - standalone
    elif args.convert:
        html_dir = args.html_dir or output_dir
        base_url = args.base_url
        
        html_files = find_html_files(html_dir)
        if not html_files:
            logger.error(f"No HTML files found in {html_dir}")
            sys.exit(1)
        
        logger.info(f"Converting {len(html_files)} HTML files to Markdown")
        converter = MarkdownConverter(github_flavored=True)
        md_output_dir = os.path.join(output_dir, 'markdown')
        md_files = converter.batch_convert(html_files, md_output_dir, base_url)
        logger.info(f"Conversion completed. Generated {len(md_files)} Markdown files.")
    
    # If no mode specified, show help
    else:
        logger.error("No operation mode specified. Use --crawl, --download, or --convert.")
        sys.exit(1)
        
    logger.info("WebSiteDownloader completed successfully")

if __name__ == "__main__":
    main()