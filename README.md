# WebSiteDownloader

A powerful Python tool for crawling, downloading, and converting websites to GitHub-compatible Markdown with comprehensive monitoring and configuration options. This tool is designed to work seamlessly on Windows.

## Features

- Crawl websites and discover URLs
- Download HTML content and embedded media
- Convert HTML to GitHub-flavored Markdown
- Generate reports and logs for analysis
- Preserve website structure in downloaded files
- Consolidated logging system for easier analysis

## Quick Start

### Prerequisites

- Python 3.7 or higher installed on your system
- Ensure `pip` is updated:
  ```cmd
  python -m pip install --upgrade pip
  ```

### Installation

1. Clone the repository:
   ```cmd
   git clone https://github.com/alanburchill/WebSiteDownloader.git
   cd WebSiteDownloader
   ```

2. Create and activate a virtual environment (choose one option):
   ```cmd
   # Using the setup script (recommended):
   python setup.py venv
   activate.cmd

   # Or manually:
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Usage

#### Crawl a Website

To crawl a website and discover URLs:
```cmd
python main.py --crawl --source https://example.com --max-pages 100
```

#### Download a Website

To download discovered URLs:
```cmd
python main.py --download --source https://example.com
```

#### Download a Website with Media

To download a website including all media assets:
```cmd
python main.py --download_all --source https://example.com
```

#### Convert HTML to Markdown

To convert downloaded HTML files to Markdown:
```cmd
python main.py --convert --html-dir ./Sites/www_example_com/HTML
```

### Logs and Reports

- Application logs are saved in the `./Logs` directory
- Site-specific logs are generated in the `./Sites/<sitename>/Logs` directory
- Download logs are consolidated into a single file per session

### Example Workflow

1. Crawl a website:
   ```cmd
   python main.py --crawl --source https://example.com --max-pages 50
   ```

2. Download the website with all media:
   ```cmd
   python main.py --download_all --source https://example.com
   ```

3. Convert HTML to Markdown:
   ```cmd
   python main.py --convert --html-dir ./Sites/www_example_com/HTML
   ```

4. View the Markdown files in `./Sites/www_example_com/Markdown`.

## Advanced Configuration

### Using a Configuration File

Create a `config.yaml` file to set all options:

```yaml
# Crawler configuration
crawler:
  max_pages: 1000
  respect_robots: true
  rate_limit: 0.05
  excluded_patterns:
    - "/author/.*"
    - "/tag/.*"
  status_codes:
    log_all: true
    show_console: true
    generate_report: true

# Downloader configuration
downloader:
  max_retries: 3
  timeout: 30
  request_delay: 0.01
  concurrency: 1
  monitoring:
    show_progress: true
    log_speed: true
    track_memory: true
  rate_limiting:
    adaptive: true
    min_delay: 0.01
    max_delay: 5.0
```

Run with the configuration:

```cmd
python main.py --config config.yaml --crawl --source https://example.com --download_all
```

### Advanced Command-Line Options

```cmd
# Crawl with Sitemap
python main.py --crawl --sitemap https://example.com/sitemap.xml --output ./Sites/custom_folder

# Set custom rate limits
python main.py --crawl --source https://example.com --delay 2.0 --max-pages 100

# Download from a JSON file of URLs
python main.py --download --input-file urls.json 

# Verbose mode for detailed output
python main.py --crawl --source https://example.com --verbose
```

## Monitoring and Reporting

WebSiteDownloader provides comprehensive monitoring:

- Color-coded HTTP status indicators in real-time
- Memory usage tracking
- Download speed and request rate statistics
- Summary reports of all HTTP status codes
- Detailed logs in the ./Logs directory

## Project Structure

```
WebSiteDownloader/
├── config.yaml              # Configuration file
├── main.py                  # Entry point script
├── requirements.txt         # Dependencies
├── setup.py                 # Setup and installation script
├── activate.cmd             # Virtual environment activation (Windows)
├── Logs/                    # Application logs
├── Sites/                   # Downloaded website content
└── src/                     # Source code
    ├── __init__.py          # Package initialization
    ├── main.py              # CLI implementation
    ├── crawler.py           # Website crawling
    ├── downloader.py        # Content downloading
    ├── converter.py         # HTML to MD conversion
    ├── media_downloader.py  # Media asset handling
    ├── report_generator.py  # Report generation
    └── utils/               # Utility modules
        ├── metadata_extractor.py  # Extract metadata from HTML
        ├── config.py        # Configuration handling
        └── helpers.py       # Helper functions
```

## Troubleshooting

For common issues and solutions, see [INSTALL.md](./INSTALL.md#troubleshooting).

## Contributing

Contributions are welcome! Please see [Docs/technical_specification.md](./Docs/technical_specification.md) for details on the project structure and development guidelines.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

For version history and updates, see [CHANGELOG.md](./CHANGELOG.md).