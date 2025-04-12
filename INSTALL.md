# WebSiteDownloader Installation Guide

This guide provides detailed instructions for installing and setting up the WebSiteDownloader tool on Windows.

## System Requirements

- **Python**: Version 3.7 or higher
- **RAM**: 4GB minimum, 8GB+ recommended for larger websites
- **Disk Space**: Dependent on website size (minimum 500MB free space)
- **Operating System**: Windows 10/11

## Installation Methods

### Method 1: Using the Setup Script (Recommended)

The simplest way to set up WebSiteDownloader is using the included setup script:

1. Clone the repository:
   ```cmd
   git clone https://github.com/yourusername/WebSiteDownloader.git
   cd WebSiteDownloader
   ```

2. Run the setup script to create a virtual environment:
   ```cmd
   python setup.py venv
   ```

3. Activate the virtual environment:
   ```cmd
   activate.cmd
   ```

### Method 2: Manual Installation

If you prefer to set things up manually:

1. Download and install Python from [python.org](https://www.python.org/downloads/).
   - During installation, check "Add Python to PATH"

2. Clone the repository:
   ```cmd
   git clone https://github.com/yourusername/WebSiteDownloader.git
   cd WebSiteDownloader
   ```

3. Create and activate a virtual environment:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

### Method 3: Development Installation

For contributors or developers who want to modify the code:

1. Clone the repository:
   ```cmd
   git clone https://github.com/yourusername/WebSiteDownloader.git
   cd WebSiteDownloader
   ```

2. Create and activate a virtual environment:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install in development mode:
   ```cmd
   pip install -e .
   ```

## Verify Installation

Run the following command to verify the installation:
```cmd
python main.py --help
```

You should see the help message listing all available commands and options.

## Directory Structure

After installation, the tool creates the following directory structure:

```
WebSiteDownloader/
├── Logs/                    # Application logs
└── Sites/                   # Downloaded websites
    └── www_example_com/     # Example website (created during download)
        ├── HTML/            # Downloaded HTML files
        ├── JSON/            # Metadata files
        └── Logs/            # Site-specific logs
```

## Dependencies

### Required Packages

The following key packages will be installed automatically:

- **requests**: For HTTP requests
- **beautifulsoup4**: For parsing HTML
- **pyyaml**: For configuration management
- **html2text**: For HTML to Markdown conversion
- **psutil**: For system resource monitoring
- **lxml**: For HTML parsing

### Optional Dependencies

To enable additional features:

```cmd
# For rich console output (prettier display)
pip install rich

# For better image processing
pip install Pillow
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**:
   ```
   ModuleNotFoundError: No module named 'requests'
   ```
   Solution:
   ```cmd
   pip install requests
   ```

2. **Permission Errors**:
   ```cmd
   pip install --user -r requirements.txt
   ```

3. **SSL Certificate Errors**:
   Update certifi:
   ```cmd
   pip install --upgrade certifi
   ```

4. **Memory Errors** when processing large websites:
   Limit crawling scope:
   ```cmd
   python main.py --crawl --source https://example.com --max-pages 500
   ```

5. **ImportError** for src module:
   Ensure you're running from the project root:
   ```cmd
   cd WebSiteDownloader
   python main.py --help
   ```

### Getting Help

If you encounter issues not covered here:

1. Check the GitHub issues page.
2. Run with verbose logging:
   ```cmd
   python main.py --verbose --crawl --source https://example.com
   ```
3. Check the log files in the ./Logs directory.

## Next Steps

After successful installation, see [README.md](./README.md) for usage instructions and examples.