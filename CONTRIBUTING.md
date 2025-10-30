# Contributing to x402IQ Protocol

Thank you for your interest in contributing to x402IQ Protocol! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and considerate
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Follow best practices and maintain code quality

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- Python version and platform information

### Suggesting Features

Feature suggestions are welcome! Please create an issue with:
- Detailed description of the feature
- Use cases and examples
- Potential implementation approach (if applicable)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Submit a pull request

## Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/x402IQ.git
cd x402IQ

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## Code Style

- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small
- Add type hints where appropriate

## Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=x402IQ_protocol
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions and classes
- Keep examples up to date

## Questions?

Open an issue with your question or contact the maintainers.

Thank you for contributing!

