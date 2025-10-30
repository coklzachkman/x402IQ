"""
Setup configuration for x402IQ Protocol
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="x402iq-protocol",
    version="1.0.0",
    author="x402IQ Development Team",
    author_email="contact@x402iq.com",
    description="High-performance protocol implementation for distributed systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/x402IQ",
    py_modules=["x402IQ_protocol"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "pylint>=2.15.0",
            "mypy>=1.0.0",
        ],
    },
)

