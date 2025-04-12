# Technical Specification Document

## 1. Main Application Entry Point (main.py)

### 1.1 Overview
The main.py file serves as the primary entry point for the WebSiteDownloader application. It initializes the application and delegates to the main function in the websitedownloader package.

### 1.2 Core Functionality
- Initializes the application by importing the main function from websitedownloader.main
- Handles system exit codes properly
- Provides a convenient execution point for the application

### 1.3 Websitedownloader Main Module

The main module in the websitedownloader package provides the following key functions:

#### 1.3.1 Command-Line Interface
- Parses command-line arguments through `parse_arguments()` function
- Supports multiple operation modes:
  - Crawl: Discover URLs on a website
  - Download: Retrieve HTML content from specified URLs
  - Download All: Get HTML and related media (images, stylesheets)
  - Convert: Transform HTML to Markdown format
- Configurable parameters including output directory, max pages, request delay, etc.

#### 1.3.2 Configuration Management
- Loads configuration from YAML files using `load_config()`
- Supports flexible configuration overrides via command-line parameters
- Implements a hierarchical configuration structure for different components

#### 1.3.3 Logging
- Sets up robust logging with both console and file outputs
- Generates timestamped log files in the dedicated ./Logs directory
- Provides different log levels based on verbose flag
- Logs key operations and statistics for later analysis

#### 1.3.4 Core Processing Flow
1. Parses arguments and initializes logging
2. Loads configuration (if specified)
3. Creates output directories
4. Executes requested operation mode(s):
   - Crawling discovers URLs and saves them to JSON
   - Downloading retrieves content from URLs
   - Converting transforms HTML to Markdown
5. Supports chained operations (e.g., crawl + download + convert)

#### 1.3.5 Utility Functions
- `save_urls()`: Stores discovered URLs to JSON files
- `load_urls()`: Reads URLs from JSON or text files
- `find_html_files()`: Locates HTML files for conversion

## 2. Core Components

### 2.1 Web Crawler (crawler.py)

#### 2.1.1 Overview
The WebCrawler class is responsible for discovering URLs by traversing the link structure of a website, starting from a given URL.

#### 2.1.2 Key Features
- Configurable crawling parameters:
  - Maximum pages to crawl
  - Rate limiting to prevent server overload
  - Option to respect robots.txt directives
- Domain restriction to stay within the target website
- URL normalization and query parameter handling
- HTML parsing with BeautifulSoup
- Metadata extraction (title, description)
- Sitemap-based crawling for faster discovery
- Pattern-based URL exclusion

#### 2.1.3 Output
- Generates a list of discovered URLs with metadata:
  - URL
  - Page title
  - Page description
  - HTTP status code
  - Content type

### 2.2 Content Downloader (downloader.py)

#### 2.2.1 Overview
The ContentDownloader class handles retrieving HTML content and optionally embedded media from URLs.

#### 2.2.2 Key Features
- Configurable download settings:
  - Maximum retry attempts for failed downloads
  - Request timeout
  - Rate limiting between requests
- URL to filename mapping with collision avoidance
- Metadata extraction and storage in JSON
- Integration with MediaDownloader for embedded content
- Site-specific folder organization
- HTTP status code tracking and reporting
- Adaptive rate limiting based on server responses
- Memory usage monitoring
- Download speed and progress reporting
- Color-coded status code display

#### 2.2.3 Status Code Monitoring
- Real-time display of HTTP status codes with color coding:
  - 1xx (Informational): Blue
  - 2xx (Success): Green
  - 3xx (Redirection): Yellow
  - 4xx (Client Error): Red
  - 5xx (Server Error): Bright Red
- Status code icons and descriptions
- Automatic retry for specific status codes (429, 5xx)
- Generation of status code summary reports

#### 2.2.4 Performance Monitoring
- Request rate tracking
- Download speed calculation
- Memory usage monitoring using psutil
- Progress indicators for batch operations
- Adaptive rate limiting that automatically adjusts based on server responses

#### 2.2.5 Output
- Creates a site-specific folder structure based on domain name
- Saves HTML content within the appropriate site folder
- Creates metadata JSON files in a JSON subfolder with:
  - Original URL
  - Download timestamp
  - HTTP headers
  - Status code
  - Content size
  - Download time
- Generates error logs in the Logs directory
- Creates status code reports in the Reports directory

### 2.3 Markdown Converter (converter.py)

#### 2.3.1 Overview
The MarkdownConverter class transforms HTML content into Markdown format suitable for GitHub or other documentation systems.

#### 2.3.2 Key Features
- Configurable conversion settings:
  - GitHub Flavored Markdown support
  - Image download options
- HTML to Markdown transformation using html2text
- Metadata preservation via YAML frontmatter
- Relative link resolution using base URL
- Batch conversion support

#### 2.3.3 Output
- Generates Markdown files with preserved structure
- Includes YAML frontmatter with metadata from JSON
- Handles internal and external links appropriately
- Preserves directory structure in the markdown output folder

### 2.4 Media Downloader (media_downloader.py)

#### 2.4.1 Overview
The MediaDownloader class extracts and downloads media files (images, stylesheets, scripts) embedded in HTML content.

#### 2.4.2 Key Features
- Domain filtering to only download files from the same domain
- Support for various media types (images, CSS, JavaScript, etc.)
- Rate limiting between requests
- Retry mechanism for failed downloads
- Path normalization for consistent directory structure
- Site-specific content organization
- Prevention of duplicate downloads
- Content type filtering

#### 2.4.3 Output
- Downloads media files to a 'media' subfolder within the site-specific directory
- Preserves original file structure where possible
- Updates HTML references to point to local files
- Ensures all media assets are organized under the appropriate site folder

## 3. Configuration System

### 3.1 Configuration File Format

The system uses YAML configuration files with the following structure:

```yaml
crawler:
  max_pages: 1000
  respect_robots: true
  rate_limit: 0.05
  excluded_patterns:
    - "/pattern1/.*"
    - "/pattern2/.*"
  status_codes:
    log_all: true
    show_console: true
    generate_report: true
    retry_codes:
      - 429
      - 500
      - 502
      - 503
      - 504

downloader:
  max_retries: 3
  timeout: 30
  request_delay: 0.01
  concurrency: 1
  monitoring:
    show_progress: true
    log_speed: true
    check_bandwidth: false
    track_memory: true
  rate_limiting:
    adaptive: true
    min_delay: 0.01
    max_delay: 5.0
    backoff_factor: 2.0

converter:
  content_selectors:
    - ".post-content"
    - ".entry-content"
    - "article"
  remove_selectors:
    - ".comments-area"
    - "#comments"
  images:
    download: true
    max_width: 1200
    fix_paths: true
```

### 3.2 Configuration Priorities

Configuration values are applied in the following order of precedence:
1. Command-line arguments (highest priority)
2. Configuration file values
3. Default values defined in the code (lowest priority)

### 3.3 Configuration Validation

The system validates configuration values to ensure they are within acceptable ranges, with the following checks:
- `max_pages` must be greater than 0
- `rate_limit` must be greater than 0
- `max_retries` must be greater than or equal to 0
- `timeout` must be greater than 0

## 4. Logging System

### 4.1 Log File Structure

Log files are stored in the ./Logs directory with timestamped filenames:
```
websitedownloader_YYYYMMDD_HHMMSS.log
```

### 4.2 Log Format
```
YYYY-MM-DD HH:MM:SS,ms - module_name - LOG_LEVEL - message
```

### 4.3 Log Levels
- DEBUG: Detailed debugging information (only when verbose mode is enabled)
- INFO: Confirmation that things are working as expected
- WARNING: Indication that something unexpected happened, but the application continues
- ERROR: Error events that might still allow the application to continue running
- CRITICAL: Serious error events that may prevent parts of the application from working

### 4.4 Site-Specific Logs

In addition to application-wide logs, site-specific logs are stored in the site's Logs directory:
- Download logs (successful downloads)
- Error logs (failed downloads)
- These logs are in JSON format for easier parsing and analysis

## 5. Report Generation

### 5.1 HTTP Status Code Reports

Reports are generated in the site's Reports directory with the following information:
- Total requests made
- Successful requests count
- Breakdown of all encountered status codes with counts
- Timestamp of report generation

### 5.2 Report Format

Reports are stored in JSON format:
```json
{
  "total_requests": 150,
  "successful_requests": 142,
  "status_codes": {
    "200": 142,
    "404": 5,
    "429": 2,
    "500": 1
  },
  "timestamp": "2025-04-12T19:51:38.123456"
}
```

## 6. Error Handling

### 6.1 Network Errors
- Connection errors trigger automatic retries with exponential backoff
- Rate limiting detection (HTTP 429) triggers adaptive delay adjustment
- Failed requests after maximum retries are logged in detail

### 6.2 Filesystem Errors
- Directory creation failures are handled with appropriate error messages
- File write failures are caught and reported
- File collision handling through file renaming

### 6.3 Parsing Errors
- HTML parsing errors are caught and logged
- Metadata extraction failures are handled gracefully
- URL normalization errors are reported but non-blocking
