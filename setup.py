"""
Setup script for Claude Contract Compliance Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="claude-compliance-agent",
    version="1.0.0",
    author="B-MAD Greenfield Method",
    description="AI-powered real estate contract processing using Claude 3 Opus",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jerbud308/Jeremy-Project-1-Claude",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.40.0",
        "pydantic>=2.0.0",
        "python-dateutil>=2.8.2",
        "python-dotenv>=1.0.0",
        "structlog>=23.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-compliance=claude_compliance_agent:main",
        ],
    },
)
