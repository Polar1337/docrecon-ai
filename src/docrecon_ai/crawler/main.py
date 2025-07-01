"""
Main document crawler

Coordinates different crawler implementations and provides unified interface.
"""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .base import BaseCrawler, DocumentInfo
from .local import LocalCrawler
from .smb import SMBCrawler

# Optional crawlers
try:
    from .graph import GraphCrawler
except ImportError:
    GraphCrawler = None

try:
    from .sharepoint_onprem import SharePointOnPremCrawler
except ImportError:
    SharePointOnPremCrawler = None

try:
    from .onenote import OneNoteCrawler
except ImportError:
    OneNoteCrawler = None


logger = logging.getLogger(__name__)


class DocumentCrawler:
    """
    Main document crawler that coordinates different crawler implementations.
    
    Supports local files, SMB shares, Microsoft Graph API, SharePoint On-Premise,
    and OneNote documents.
    """
    
    def __init__(self, config):
        self.config = config
        self.crawlers = {}
        self.statistics = {}
        
        # Initialize enabled crawlers
        self._initialize_crawlers()
    
    def _initialize_crawlers(self):
        """Initialize all enabled crawlers."""
        enabled_crawlers = self.config.get('crawler.enabled_crawlers', ['local'])
        
        for crawler_type in enabled_crawlers:
            try:
                if crawler_type == 'local' and self.config.get('crawler.local.enabled', True):
                    self.crawlers['local'] = LocalCrawler(self.config)
                    logger.info("Local crawler initialized")
                
                elif crawler_type == 'smb' and self.config.get('crawler.smb.enabled', False):
                    self.crawlers['smb'] = SMBCrawler(self.config)
                    logger.info("SMB crawler initialized")
                
                elif crawler_type == 'graph' and self.config.get('crawler.graph.enabled', False):
                    if GraphCrawler:
                        self.crawlers['graph'] = GraphCrawler(self.config)
                        logger.info("Microsoft Graph crawler initialized")
                    else:
                        logger.warning("Microsoft Graph crawler not available")
                
                elif crawler_type == 'sharepoint_onprem' and self.config.get('crawler.sharepoint_onprem.enabled', False):
                    if SharePointOnPremCrawler:
                        self.crawlers['sharepoint_onprem'] = SharePointOnPremCrawler(self.config)
                        logger.info("SharePoint On-Premise crawler initialized")
                    else:
                        logger.warning("SharePoint On-Premise crawler not available")
                
                elif crawler_type == 'onenote' and self.config.get('crawler.onenote.enabled', False):
                    if OneNoteCrawler:
                        self.crawlers['onenote'] = OneNoteCrawler(self.config)
                        logger.info("OneNote crawler initialized")
                    else:
                        logger.warning("OneNote crawler not available")
                    
            except Exception as e:
                logger.error(f"Failed to initialize {crawler_type} crawler: {e}")
    
    def crawl_all_sources(self, paths: List[str] = None) -> List[DocumentInfo]:
        """
        Crawl all configured sources.
        
        Args:
            paths: Optional list of specific paths to crawl
            
        Returns:
            List of all discovered documents
        """
        all_documents = []
        start_time = time.time()
        
        logger.info(f"Starting document crawl with {len(self.crawlers)} crawlers")
        
        # Use parallel execution if multiple crawlers
        if len(self.crawlers) > 1:
            all_documents = self._crawl_parallel(paths)
        else:
            all_documents = self._crawl_sequential(paths)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Compile statistics
        self._compile_statistics(all_documents, duration)
        
        logger.info(f"Crawl completed in {duration:.2f} seconds. Found {len(all_documents)} documents.")
        
        return all_documents
    
    def _crawl_parallel(self, paths: List[str] = None) -> List[DocumentInfo]:
        """Crawl sources in parallel."""
        all_documents = []
        max_workers = self.config.get('crawler.parallel_workers', 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit crawler tasks
            future_to_crawler = {}
            
            for crawler_name, crawler in self.crawlers.items():
                if crawler_name == 'local' and paths:
                    # For local crawler, use provided paths
                    for path in paths:
                        future = executor.submit(crawler.crawl_path, path)
                        future_to_crawler[future] = (crawler_name, path)
                elif crawler_name == 'sharepoint_onprem':
                    # For SharePoint, use configured site collections or provided paths
                    sites = paths if paths else getattr(crawler, 'site_collections', ['/'])
                    for site in sites:
                        future = executor.submit(crawler.crawl_path, site)
                        future_to_crawler[future] = (crawler_name, site)
                elif crawler_name == 'onenote':
                    # For OneNote, use provided paths or default
                    onenote_paths = paths if paths else ['/']
                    for path in onenote_paths:
                        future = executor.submit(crawler.crawl_path, path)
                        future_to_crawler[future] = (crawler_name, path)
                else:
                    # For other crawlers, use default crawling
                    future = executor.submit(crawler.crawl_path, paths[0] if paths else None)
                    future_to_crawler[future] = (crawler_name, 'default')
            
            # Collect results
            for future in as_completed(future_to_crawler):
                crawler_name, path = future_to_crawler[future]
                try:
                    documents = future.result()
                    all_documents.extend(documents)
                    logger.info(f"{crawler_name} crawler found {len(documents)} documents in {path}")
                except Exception as e:
                    logger.error(f"Error in {crawler_name} crawler for {path}: {e}")
        
        return all_documents
    
    def _crawl_sequential(self, paths: List[str] = None) -> List[DocumentInfo]:
        """Crawl sources sequentially."""
        all_documents = []
        
        for crawler_name, crawler in self.crawlers.items():
            try:
                logger.info(f"Starting {crawler_name} crawler")
                
                if crawler_name == 'local' and paths:
                    # Crawl each provided path
                    for path in paths:
                        documents = crawler.crawl_path(path)
                        all_documents.extend(documents)
                        logger.info(f"{crawler_name} crawler found {len(documents)} documents in {path}")
                elif crawler_name == 'sharepoint_onprem':
                    # Crawl SharePoint sites
                    sites = paths if paths else getattr(crawler, 'site_collections', ['/'])
                    for site in sites:
                        documents = crawler.crawl_path(site)
                        all_documents.extend(documents)
                        logger.info(f"{crawler_name} crawler found {len(documents)} documents in {site}")
                elif crawler_name == 'onenote':
                    # Crawl OneNote
                    onenote_paths = paths if paths else ['/']
                    for path in onenote_paths:
                        documents = crawler.crawl_path(path)
                        all_documents.extend(documents)
                        logger.info(f"{crawler_name} crawler found {len(documents)} documents in {path}")
                else:
                    # Default crawling
                    documents = crawler.crawl_path(paths[0] if paths else None)
                    all_documents.extend(documents)
                    logger.info(f"{crawler_name} crawler found {len(documents)} documents")
                    
            except Exception as e:
                logger.error(f"Error in {crawler_name} crawler: {e}")
        
        return all_documents
    
    def test_connections(self) -> Dict[str, bool]:
        """Test connections for all crawlers."""
        results = {}
        
        for crawler_name, crawler in self.crawlers.items():
            try:
                if hasattr(crawler, 'test_connection'):
                    results[crawler_name] = crawler.test_connection()
                else:
                    results[crawler_name] = True  # Assume OK if no test method
                    
                logger.info(f"{crawler_name} connection test: {'PASS' if results[crawler_name] else 'FAIL'}")
                
            except Exception as e:
                logger.error(f"Connection test failed for {crawler_name}: {e}")
                results[crawler_name] = False
        
        return results
    
    def validate_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Validate configurations for all crawlers."""
        results = {}
        
        for crawler_name, crawler in self.crawlers.items():
            try:
                if hasattr(crawler, 'validate_configuration'):
                    is_valid, errors = crawler.validate_configuration()
                    results[crawler_name] = {
                        'valid': is_valid,
                        'errors': errors
                    }
                else:
                    results[crawler_name] = {
                        'valid': True,
                        'errors': []
                    }
                    
            except Exception as e:
                logger.error(f"Configuration validation failed for {crawler_name}: {e}")
                results[crawler_name] = {
                    'valid': False,
                    'errors': [str(e)]
                }
        
        return results
    
    def _compile_statistics(self, documents: List[DocumentInfo], duration: float):
        """Compile crawling statistics."""
        self.statistics = {
            'total_documents': len(documents),
            'crawl_duration_seconds': duration,
            'crawlers_used': list(self.crawlers.keys()),
            'documents_per_second': len(documents) / duration if duration > 0 else 0,
            'by_source_type': {},
            'by_file_extension': {},
            'total_size_bytes': 0
        }
        
        # Analyze documents
        for doc in documents:
            # By source type
            source_type = doc.source_type
            if source_type not in self.statistics['by_source_type']:
                self.statistics['by_source_type'][source_type] = 0
            self.statistics['by_source_type'][source_type] += 1
            
            # By file extension
            ext = doc.file_extension.lower()
            if ext not in self.statistics['by_file_extension']:
                self.statistics['by_file_extension'][ext] = 0
            self.statistics['by_file_extension'][ext] += 1
            
            # Total size
            if doc.size:
                self.statistics['total_size_bytes'] += doc.size
        
        # Get individual crawler statistics
        for crawler_name, crawler in self.crawlers.items():
            if hasattr(crawler, 'get_statistics'):
                self.statistics[f'{crawler_name}_stats'] = crawler.get_statistics()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive crawling statistics."""
        return self.statistics
    
    def get_enabled_crawlers(self) -> List[str]:
        """Get list of enabled crawler names."""
        return list(self.crawlers.keys())
    
    def get_crawler(self, crawler_name: str) -> Optional[BaseCrawler]:
        """Get specific crawler instance."""
        return self.crawlers.get(crawler_name)

