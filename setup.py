#!/usr/bin/env python3
"""
DocRecon AI - Document Consolidation Tool
Setup script for installation and distribution
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="docrecon-ai",
    version="1.0.0",
    author="Manus AI",
    author_email="info@manus.ai",
    description="AI-powered document consolidation and duplicate detection tool",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/docrecon-ai",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: System :: Archiving",
        "Topic :: Text Processing :: General",
    ],
    python_requires=">=3.10",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=22.10.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "dashboard": [
            "streamlit>=1.25.0",
            "plotly>=5.15.0",
            "dash>=2.10.0",
        ],
        "graph": [
            "msal>=1.20.0",
            "requests>=2.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "docrecon=docrecon_ai.cli:main",
            "docrecon-dashboard=docrecon_ai.dashboard:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

