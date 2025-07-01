"""
Local file system crawler

Crawls local directories and file systems to discover documents.
Supports recursive scanning with configurable depth limits.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Iterator, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .base import BaseCrawler, DocumentInfo

logger = logging.getLogger(__name__)


class LocalCrawler(BaseCrawler):
    """
    Crawler for local file systems.
    
    Recursively scans local directories to find and analyze documents.
    Supports multi-threading for improved performance on large directories.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize local crawler.
        
        Args:
            config: Configuration object with crawler settings
        """
        super().__init__(config)
        self.max_depth = getattr(config.crawler, 'max_depth', 10) if config else 10
        self.follow_symlinks = getattr(config.crawler, 'follow_symlinks', False) if config else False
        self.threads = getattr(config.crawler, 'threads', 4) if config else 4
    
    def scan(self, source: str, recursive: bool = True, **kwargs) -> Iterator[DocumentInfo]:
        """
        Scan a local directory for documents.
        
        Args:
            source: Local directory path to scan
            recursive: Whether to scan subdirectories recursively
            **kwargs: Additional options
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        source_path = Path(source).resolve()
        
        if not source_path.exists():
            self.logger.error(f"Source path does not exist: {source}")
            self.errors += 1
            return
        
        if not source_path.is_dir():
            # Single file
            if source_path.is_file():
                doc_info = self._process_file(source_path)
                if doc_info:
                    yield doc_info
            return
        
        self.logger.info(f"Scanning directory: {source_path}")
        
        if self.threads > 1:
            # Multi-threaded scanning
            yield from self._scan_multithreaded(source_path, recursive)
        else:
            # Single-threaded scanning
            yield from self._scan_directory(source_path, recursive, depth=0)
    
    def _scan_directory(self, directory: Path, recursive: bool, depth: int = 0) -> Iterator[DocumentInfo]:
        """
        Scan a single directory.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            depth: Current recursion depth
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        if depth > self.max_depth:
            self.logger.warning(f"Maximum depth {self.max_depth} reached at {directory}")
            return
        
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            self.logger.warning(f"Permission denied: {directory}")
            self.errors += 1
            return
        except Exception as e:
            self.logger.error(f"Error reading directory {directory}: {e}")
            self.errors += 1
            return
        
        # Process files first
        for entry in entries:
            if entry.is_file():
                self.files_found += 1
                doc_info = self._process_file(entry)
                if doc_info:
                    yield doc_info
            
            elif entry.is_dir() and recursive:
                # Handle symlinks
                if entry.is_symlink() and not self.follow_symlinks:
                    self.logger.debug(f"Skipping symlink: {entry}")
                    continue
                
                # Recursive scan
                yield from self._scan_directory(entry, recursive, depth + 1)
    
    def _scan_multithreaded(self, directory: Path, recursive: bool) -> Iterator[DocumentInfo]:
        """
        Scan directory using multiple threads.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        # Collect all files first
        all_files = []
        for root, dirs, files in os.walk(directory, followlinks=self.follow_symlinks):
            root_path = Path(root)
            
            # Check depth
            depth = len(root_path.relative_to(directory).parts)
            if depth > self.max_depth:
                dirs.clear()  # Don't descend further
                continue
            
            # Add files
            for filename in files:
                filepath = root_path / filename
                all_files.append(filepath)
                self.files_found += 1
            
            if not recursive:
                dirs.clear()  # Don't recurse
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # Submit all file processing tasks
            future_to_file = {
                executor.submit(self._process_file, filepath): filepath 
                for filepath in all_files
            }
            
            # Yield results as they complete
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    doc_info = future.result()
                    if doc_info:
                        yield doc_info
                except Exception as e:
                    self.logger.error(f"Error processing {filepath}: {e}")
                    self.errors += 1
    
    def _process_file(self, filepath: Path) -> Optional[DocumentInfo]:
        """
        Process a single file and extract information.
        
        Args:
            filepath: Path to the file to process
            
        Returns:
            DocumentInfo: Document information, or None if skipped/error
        """
        try:
            # Get file stats
            stat = filepath.stat()
            
            # Check if file should be processed
            if not self.should_process_file(str(filepath), stat.st_size):
                self.files_skipped += 1
                return None
            
            # Create document info
            doc_info = DocumentInfo(
                path=str(filepath.resolve()),
                filename=filepath.name,
                size=stat.st_size,
                modified_date=datetime.fromtimestamp(stat.st_mtime),
                created_date=datetime.fromtimestamp(stat.st_ctime),
                source_type="local"
            )
            
            # Calculate hashes
            if self.config and hasattr(self.config.duplicates, 'hash_algorithm'):
                algorithm = self.config.duplicates.hash_algorithm
            else:
                algorithm = "sha256"
            
            doc_info.sha256_hash = self.calculate_file_hash(str(filepath), "sha256")
            if algorithm != "sha256":
                if algorithm == "md5":
                    doc_info.md5_hash = self.calculate_file_hash(str(filepath), "md5")
            
            # Add file metadata
            doc_info.metadata.update({
                'absolute_path': str(filepath.resolve()),
                'parent_directory': str(filepath.parent),
                'file_permissions': oct(stat.st_mode)[-3:],
                'inode': stat.st_ino,
            })
            
            # Platform-specific metadata
            if sys.platform == "win32":
                doc_info.metadata.update({
                    'drive': str(filepath.drive) if filepath.drive else None,
                })
            else:
                doc_info.metadata.update({
                    'owner_uid': stat.st_uid,
                    'group_gid': stat.st_gid,
                })
            
            self.files_processed += 1
            doc_info.processed = True
            
            return doc_info
            
        except PermissionError:
            self.logger.warning(f"Permission denied: {filepath}")
            self.files_skipped += 1
            return None
        except Exception as e:
            self.logger.error(f"Error processing file {filepath}: {e}")
            self.errors += 1
            
            # Return partial info with error
            return DocumentInfo(
                path=str(filepath),
                filename=filepath.name,
                size=0,
                modified_date=datetime.now(),
                source_type="local",
                error_message=str(e)
            )
    
    def get_directory_stats(self, directory: str) -> dict:
        """
        Get statistics about a directory.
        
        Args:
            directory: Directory path to analyze
            
        Returns:
            dict: Directory statistics
        """
        directory_path = Path(directory)
        
        if not directory_path.exists() or not directory_path.is_dir():
            return {}
        
        stats = {
            'total_files': 0,
            'total_size': 0,
            'file_types': {},
            'largest_file': None,
            'oldest_file': None,
            'newest_file': None,
        }
        
        try:
            for filepath in directory_path.rglob('*'):
                if filepath.is_file():
                    try:
                        file_stat = filepath.stat()
                        stats['total_files'] += 1
                        stats['total_size'] += file_stat.st_size
                        
                        # File type counting
                        ext = filepath.suffix.lower()
                        stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
                        
                        # Largest file
                        if (stats['largest_file'] is None or 
                            file_stat.st_size > stats['largest_file']['size']):
                            stats['largest_file'] = {
                                'path': str(filepath),
                                'size': file_stat.st_size
                            }
                        
                        # Oldest file
                        if (stats['oldest_file'] is None or 
                            file_stat.st_mtime < stats['oldest_file']['mtime']):
                            stats['oldest_file'] = {
                                'path': str(filepath),
                                'mtime': file_stat.st_mtime
                            }
                        
                        # Newest file
                        if (stats['newest_file'] is None or 
                            file_stat.st_mtime > stats['newest_file']['mtime']):
                            stats['newest_file'] = {
                                'path': str(filepath),
                                'mtime': file_stat.st_mtime
                            }
                            
                    except (PermissionError, OSError):
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error getting directory stats for {directory}: {e}")
        
        return stats

