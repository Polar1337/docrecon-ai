"""
Natural Language Processing Module

This module provides NLP capabilities for document analysis:
- Text extraction from various file formats
- Embedding generation for semantic similarity
- Named entity recognition
- Keyword extraction
- Document clustering
"""

from .extractor import TextExtractor
from .embeddings import EmbeddingGenerator
from .clustering import DocumentClusterer
from .entities import EntityExtractor
from .analyzer import NLPAnalyzer

__all__ = [
    "TextExtractor",
    "EmbeddingGenerator", 
    "DocumentClusterer",
    "EntityExtractor",
    "NLPAnalyzer",
]

