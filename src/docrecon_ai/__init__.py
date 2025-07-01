"""
DocRecon AI - Document Consolidation Tool

AI-powered document analysis, categorization, and duplicate detection
for enterprise document management.
"""

__version__ = "1.0.0"
__author__ = "Manus AI"
__email__ = "info@manus.ai"

# Core imports
from .crawler import DocumentCrawler
from .nlp import NLPAnalyzer, TextExtractor
from .detection import DuplicateDetector, SimilarityAnalyzer
from .reporting import HTMLReporter, CSVReporter, JSONReporter

# Configuration
from .config import Config, load_config

__all__ = [
    # Core classes
    "DocumentCrawler",
    "NLPAnalyzer", 
    "TextExtractor",
    "DuplicateDetector",
    "SimilarityAnalyzer",
    "HTMLReporter",
    "CSVReporter", 
    "JSONReporter",
    
    # Configuration
    "Config",
    "load_config",
    
    # Metadata
    "__version__",
    "__author__",
    "__email__",
]

