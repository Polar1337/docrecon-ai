"""
Document Crawler Module

This module provides various crawlers for different document sources:
- Local file system crawler
- SMB/CIFS network share crawler  
- Microsoft Graph API crawler (SharePoint, OneDrive, OneNote)
"""

from .base import BaseCrawler, DocumentInfo
from .local import LocalCrawler
from .smb import SMBCrawler
from .main import DocumentCrawler

# Optional Graph API crawler (requires additional dependencies)
try:
    from .graph import GraphCrawler
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    GraphCrawler = None

__all__ = [
    "BaseCrawler",
    "DocumentInfo", 
    "LocalCrawler",
    "SMBCrawler",
    "DocumentCrawler",
    "GraphCrawler",
    "GRAPH_AVAILABLE",
]

