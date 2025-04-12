# Changelog

All notable changes to the WebSiteDownloader project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-04-13

### Added
- Initial public release
- Website crawling functionality with configurable depth and rate limiting
- Content downloading with media asset support
- HTML to Markdown conversion
- Configurable folder structure (HTML/JSON/Logs)
- Session-based logging system
- Consolidated download logs
- Media file deduplication using content hashing
- Progress indicators and status reporting
- Support for website structure preservation
- Detailed metadata extraction for downloaded pages
- Performance monitoring for memory usage and download speeds
- User-friendly command-line interface
- Support for configuration via YAML files

### Changed
- Improved folder structure with all downloads now going to a 'Sites' folder
- Consolidated setup script for easier installation

### Fixed
- Duplicate download handling for media assets
- Proper error handling for network issues
- Memory usage optimization for large websites