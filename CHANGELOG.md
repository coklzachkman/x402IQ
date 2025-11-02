# Changelog

All notable changes to x402IQ Protocol will be documented in this file.

## [1.1.0] - 2025-01-XX

### Added
- **Logging Support**: Added comprehensive logging framework with configurable levels (DEBUG, INFO, WARNING, ERROR)
  - Logs message creation, receipt, validation, and errors
  - Configurable per-node logging with `enable_logging` and `log_level` parameters
  - Logs compression/decompression operations

- **Timeout Management**: Added timeout handling for requests
  - Default timeout configuration per protocol instance
  - `check_timeout()` method to verify if a request has timed out
  - `cleanup_timed_out_requests()` method for automatic cleanup
  - Enhanced statistics to include timeout information

- **Message Compression**: Added compression support for large payloads
  - Gzip compression with base64 encoding
  - Automatic compression/decompression on send/receive
  - `compress` parameter in message creation methods
  - Compression flag in protocol headers for compatibility checking
  - Compression ratio tracking and logging

- **Test Suite**: Added comprehensive test suite with pytest
  - Unit tests for basic protocol functionality
  - Tests for all message types
  - Serialization/deserialization tests
  - Validation and error handling tests
  - Custom protocol implementation tests
  - Statistics and cleanup tests
  - Timeout and request tracking tests

- **Example Scripts**: Added example usage scripts
  - `compression_example.py`: Demonstrates message compression
  - `logging_example.py`: Shows logging capabilities
  - `timeout_example.py`: Illustrates timeout handling

- **Development Tools**: 
  - Added `.gitignore` file for Python projects
  - Organized examples in dedicated directory

### Changed
- Protocol header now includes optional `compressed` field (backward compatible)
- `create_message()` method now accepts `compress` parameter
- `receive_message()` now automatically decompresses messages when needed
- Statistics now include default timeout information
- Enhanced error handling with better logging support

### Fixed
- Improved backward compatibility for message headers
- Better error messages throughout the protocol

### Security
- Enhanced checksum validation with logging
- Compression uses standard library gzip (no external dependencies)

## [1.0.0] - Initial Release

### Features
- Core protocol implementation
- Request/Response pattern
- Checksum validation
- Message tracking
- Statistics and monitoring
- Multiple message types (Request, Response, Notification, Error)
- JSON serialization
- Message deduplication
- Protocol versioning
- Cleanup management

[1.1.0]: https://github.com/coklzachkman/x402IQ/compare/v1.0.0...v1.1.0

