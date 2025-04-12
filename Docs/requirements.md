# Requirements Specification Document

## Project Overview

WebSiteDownloader is a tool designed to efficiently download websites and convert them to a Markdown-based format suitable for hosting on GitHub or other documentation platforms. The tool crawls websites, downloads HTML content and associated media, converts HTML to Markdown, and organizes everything in a clean, structured format.

## Functional Requirements

### 1. Website Crawling

1.1. **URL Discovery**
- The system must crawl a website starting from a given URL
- The system must follow links within the same domain
- The system must support limiting the maximum number of pages to crawl
- The system must support sitemap-based URL discovery

1.2. **Rate Control**
- The system must implement configurable rate limiting
- The system must support adaptive rate limiting based on server responses
- The system must respect specified delays between requests

1.3. **URL Filtering**
- The system must support excluding URLs based on regex patterns
- The system must normalize URLs to prevent duplicate downloads
- The system must handle URL query parameters according to configuration

### 2. Content Downloading

2.1. **HTML Retrieval**
- The system must download HTML content from discovered URLs
- The system must handle various HTTP status codes appropriately
- The system must support retrying failed downloads with exponential backoff
- The system must organize downloaded content by domain name

2.2. **Media Downloading**
- The system must identify and download embedded media (images, CSS, JS)
- The system must update HTML references to point to local media files
- The system must support filtering media by domain (same-origin only)
- The system must handle duplicate media files appropriately

2.3. **Error Handling**
- The system must log failed downloads with detailed error information
- The system must continue operation despite individual download failures
- The system must detect and handle rate limiting by remote servers

### 3. Content Conversion

3.1. **HTML to Markdown**
- The system must convert HTML content to Markdown format
- The system must support GitHub-Flavored Markdown
- The system must extract and preserve metadata as YAML frontmatter
- The system must handle internal and external links appropriately

3.2. **Structure Preservation**
- The system must maintain the website's directory structure
- The system must ensure image references in Markdown point to correct local paths
- The system must organize Markdown files in a logical hierarchy

### 4. Monitoring and Reporting

4.1. **Progress Tracking**
- The system must display crawling and download progress
- The system must report download speeds and request rates
- The system must track memory usage during operations

4.2. **Status Reporting**
- The system must log and report HTTP status codes
- The system must generate summary reports of status codes
- The system must provide color-coded status information in real-time

4.3. **Logging**
- The system must maintain detailed logs of all operations
- The system must store logs in both application and site-specific directories
- The system must generate json logs for machine processing

## Non-Functional Requirements

### 1. Performance

1.1. **Optimization**
- The system should optimize memory usage for large websites
- The system should manage resources efficiently during downloads
- The system should handle websites with thousands of pages

1.2. **Rate Limiting**
- The system should automatically adjust request rates to prevent overloading servers
- The system should implement configurable concurrency controls

### 2. Usability

2.1. **Command-Line Interface**
- The system should provide an intuitive command-line interface
- The system should support both simple and advanced usage patterns
- The system should display help information when requested

2.2. **Configuration**
- The system should support configuration via YAML files
- The system should allow command-line parameters to override configuration
- The system should provide reasonable defaults for all settings

### 3. Reliability

3.1. **Fault Tolerance**
- The system should continue operation despite individual failures
- The system should implement retry mechanisms for transient errors
- The system should preserve partial results in case of interruption

3.2. **Validation**
- The system should validate inputs before processing
- The system should verify the integrity of downloaded content
- The system should check for and handle content encoding issues

## System Architecture

### Directory Structure

```
WebSiteDownloader/
├── Logs/                    # Application-level logs
└── Sites/                   # Downloaded websites
    └── www_example_com/     # Example website
        ├── HTML/            # Downloaded HTML files
        ├── JSON/            # Metadata files
        ├── Logs/            # Site-specific logs
        ├── Reports/         # Status code reports
        └── Markdown/        # Converted Markdown files
```

### Configuration Structure

The tool uses a hierarchical YAML configuration structure:

```yaml
# Example configuration
crawler:
  max_pages: 1000
  rate_limit: 0.05
  excluded_patterns:
    - "/pattern1/.*"
    - "/pattern2/.*"

downloader:
  max_retries: 3
  timeout: 30
  request_delay: 0.01
  
  monitoring:
    show_progress: true
    track_memory: true
```

## Current Status and Future Development

### Implemented Features
- Website crawling with configurable depth and rate limiting
- Content downloading with structure preservation
- Media asset downloading and organization
- HTML to Markdown conversion
- Comprehensive logging and reporting
- Configurable settings via YAML and command line
- Progress monitoring and status code tracking

### Planned Enhancements
- Additional conversion options for different Markdown flavors
- Improved media handling with optimization options
- Enhanced filtering capabilities for more precise content selection
- Interactive mode with real-time control over crawling/downloading
- Integration with content management systems