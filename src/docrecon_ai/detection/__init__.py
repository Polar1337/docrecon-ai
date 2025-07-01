"""
Duplicate Detection Module

This module provides various methods for detecting duplicate documents:
- Hash-based exact duplicate detection
- Semantic similarity analysis
- Filename pattern recognition for versions
- Content-based fuzzy matching
"""

from .hash import HashDuplicateDetector
from .similarity import SimilarityAnalyzer
from .versioning import VersionDetector
from .main import DuplicateDetector

__all__ = [
    "HashDuplicateDetector",
    "SimilarityAnalyzer",
    "VersionDetector", 
    "DuplicateDetector",
]

