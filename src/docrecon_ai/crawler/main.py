"""
Main document crawler

Coordinates different crawler types and provides a unified interface
for document discovery across various sources.
"""

import os
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Union
from urllib.parse import urlparse
import logging

from .base import BaseCrawler, DocumentInfo
from .local import LocalCrawler
from .smb import SMBCrawler

# Optional Graph crawler
try:
    from .graph import GraphCrawler
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    GraphCrawler = None

logger = logging.getLogger(__name__)


class DocumentCrawler:
    """
    Main document crawler that coordinates different crawler types.
    
    Automatically detects source types and delegates to appropriate crawlers.
    Provides a unified interface for document discovery.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize document crawler.
        
        Args:
            config: Configuration object with crawler settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize crawlers
        self.local_crawler = LocalCrawler(config)
        self.smb_crawler = SMBCrawler(config)
        
        if GRAPH_AVAILABLE and config and config.graph:
            try:
                self.graph_crawler = GraphCrawler(config)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Graph crawler: {e}")
                self.graph_crawler = None
        else:
            self.graph_crawler = None
        
        # Statistics
        self.total_files_found = 0
        self.total_files_processed = 0
        self.total_files_skipped = 0
        self.total_errors = 0
    
    def scan_sources(self, sources: List[Dict[str, Any]]) -> Iterator[DocumentInfo]:
        """
        Scan multiple sources for documents.
        
        Args:
            sources: List of source configurations, each containing:
                - path: Source path/URL
                - type: Source type (auto-detected if not specified)
                - credentials: Authentication credentials (if needed)
                - options: Additional crawler options
                
        Yields:
            DocumentInfo: Information about each discovered document
        """
        for source_config in sources:
            source_path = source_config['path']
            source_type = source_config.get('type', 'auto')
            credentials = source_config.get('credentials', {})
            options = source_config.get('options', {})
            
            self.logger.info(f"Scanning source: {source_path}")
            
            try:
                yield from self.scan(source_path, source_type, credentials, **options)
            except Exception as e:
                self.logger.error(f"Error scanning source {source_path}: {e}")
                self.total_errors += 1
    
    def scan(self, source: str, source_type: str = "auto", 
             credentials: Dict[str, Any] = None, **kwargs) -> Iterator[DocumentInfo]:
        """
        Scan a single source for documents.
        
        Args:
            source: Source path/URL to scan
            source_type: Type of source ("auto", "local", "smb", "sharepoint", "onedrive", "onenote")
            credentials: Authentication credentials
            **kwargs: Additional crawler options
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        if credentials is None:
            credentials = {}
        
        # Auto-detect source type if needed
        if source_type == "auto":
            source_type = self._detect_source_type(source)
        
        self.logger.info(f"Scanning {source_type} source: {source}")
        
        # Select appropriate crawler
        crawler = self._get_crawler(source_type)
        if not crawler:
            self.logger.error(f"No crawler available for source type: {source_type}")
            return
        
        # Reset crawler statistics
        crawler.reset_statistics()
        
        try:
            # Scan with appropriate crawler
            if source_type == "local":
                yield from crawler.scan(source, **kwargs)
                
            elif source_type == "smb":
                username = credentials.get('username')
                password = credentials.get('password')
                domain = credentials.get('domain', '')
                yield from crawler.scan(source, username, password, domain, **kwargs)
                
            elif source_type in ["sharepoint", "onedrive", "onenote"]:
                if not self.graph_crawler:
                    self.logger.error("Graph API crawler not available")
                    return
                yield from crawler.scan(source, source_type, **kwargs)
                
            else:
                self.logger.error(f"Unsupported source type: {source_type}")
                return
            
            # Update total statistics
            stats = crawler.get_statistics()
            self.total_files_found += stats['files_found']
            self.total_files_processed += stats['files_processed']
            self.total_files_skipped += stats['files_skipped']
            self.total_errors += stats['errors']
            
        except Exception as e:
            self.logger.error(f"Error during crawling: {e}")
            self.total_errors += 1
    
    def _detect_source_type(self, source: str) -> str:
        """
        Auto-detect source type from path/URL.
        
        Args:
            source: Source path/URL
            
        Returns:
            str: Detected source type
        """
        # Check for UNC paths (Windows network shares)
        if source.startswith('\\\\') or source.startswith('//'):
            return "smb"
        
        # Check for URLs
        if '://' in source:
            parsed = urlparse(source)
            hostname = parsed.hostname.lower() if parsed.hostname else ''
            
            # SharePoint Online
            if 'sharepoint.com' in hostname:
                return "sharepoint"
            
            # OneDrive
            if 'onedrive' in hostname or '1drv.ms' in hostname:
                return "onedrive"
            
            # Generic SMB URL
            if parsed.scheme in ['smb', 'cifs']:
                return "smb"
        
        # Check for local paths
        path = Path(source)
        if path.exists() or path.is_absolute():
            return "local"
        
        # Default to local
        return "local"
    
    def _get_crawler(self, source_type: str) -> Optional[BaseCrawler]:
        """
        Get appropriate crawler for source type.
        
        Args:
            source_type: Type of source
            
        Returns:
            BaseCrawler: Appropriate crawler instance
        """
        if source_type == "local":
            return self.local_crawler
        elif source_type == "smb":
            return self.smb_crawler
        elif source_type in ["sharepoint", "onedrive", "onenote"]:
            return self.graph_crawler
        else:
            return None
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get overall crawler statistics.
        
        Returns:
            dict: Combined statistics from all crawlers
        """
        return {
            'total_files_found': self.total_files_found,
            'total_files_processed': self.total_files_processed,
            'total_files_skipped': self.total_files_skipped,
            'total_errors': self.total_errors,
        }
    
    def reset_statistics(self):
        """Reset all crawler statistics"""
        self.total_files_found = 0
        self.total_files_processed = 0
        self.total_files_skipped = 0
        self.total_errors = 0
        
        # Reset individual crawler statistics
        self.local_crawler.reset_statistics()
        self.smb_crawler.reset_statistics()
        if self.graph_crawler:
            self.graph_crawler.reset_statistics()
    
    def test_source(self, source: str, source_type: str = "auto", 
                   credentials: Dict[str, Any] = None) -> bool:
        """
        Test if a source is accessible.
        
        Args:
            source: Source path/URL to test
            source_type: Type of source
            credentials: Authentication credentials
            
        Returns:
            bool: True if source is accessible
        """
        if credentials is None:
            credentials = {}
        
        # Auto-detect source type if needed
        if source_type == "auto":
            source_type = self._detect_source_type(source)
        
        try:
            if source_type == "local":
                path = Path(source)
                return path.exists()
                
            elif source_type == "smb":
                username = credentials.get('username')
                password = credentials.get('password')
                domain = credentials.get('domain', '')
                
                # Parse SMB path
                smb_info = self.smb_crawler._parse_smb_path(source)
                if not smb_info:
                    return False
                
                return self.smb_crawler.test_connection(
                    smb_info['server'], smb_info['share'], 
                    username, password, domain
                )
                
            elif source_type in ["sharepoint", "onedrive", "onenote"]:
                if not self.graph_crawler:
                    return False
                return self.graph_crawler.test_connection()
                
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing source {source}: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.
        
        Returns:
            list: Supported file extensions
        """
        if self.config and hasattr(self.config.crawler, 'supported_extensions'):
            return self.config.crawler.supported_extensions
        else:
            # Default extensions
            return [
                '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
                '.txt', '.md', '.html', '.htm', '.rtf', '.odt', '.ods'
            ]
    
    def estimate_scan_time(self, source: str, source_type: str = "auto") -> Dict[str, Any]:
        """
        Estimate scan time for a source (rough estimate).
        
        Args:
            source: Source path/URL
            source_type: Type of source
            
        Returns:
            dict: Estimation information
        """
        if source_type == "auto":
            source_type = self._detect_source_type(source)
        
        estimation = {
            'source_type': source_type,
            'estimated_files': 0,
            'estimated_time_seconds': 0,
            'factors': []
        }
        
        try:
            if source_type == "local":
                path = Path(source)
                if path.exists() and path.is_dir():
                    # Quick directory scan for estimation
                    stats = self.local_crawler.get_directory_stats(str(path))
                    estimation['estimated_files'] = stats.get('total_files', 0)
                    
                    # Rough time estimation: 10-50 files per second depending on size
                    avg_time_per_file = 0.05  # 50ms per file
                    estimation['estimated_time_seconds'] = int(estimation['estimated_files'] * avg_time_per_file)
                    
                    estimation['factors'].append(f"Directory contains {estimation['estimated_files']} files")
                    
            elif source_type == "smb":
                estimation['factors'].append("Network latency affects scan speed")
                estimation['estimated_time_seconds'] = 60  # Default estimate
                
            elif source_type in ["sharepoint", "onedrive", "onenote"]:
                estimation['factors'].append("API rate limits affect scan speed")
                estimation['estimated_time_seconds'] = 120  # Default estimate
                
        except Exception as e:
            self.logger.error(f"Error estimating scan time for {source}: {e}")
            estimation['factors'].append(f"Estimation failed: {e}")
        
        return estimation

