"""
Base crawler class and document information structure

Defines the common interface and data structures used by all crawler implementations.
"""

import os
import hashlib
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentInfo:
    """
    Information about a discovered document.
    
    This class holds all metadata and content information
    extracted from a document during the crawling process.
    """
    # Basic file information
    path: str
    filename: str
    size: int
    modified_date: datetime
    created_date: Optional[datetime] = None
    
    # Content identification
    file_extension: str = ""
    mime_type: str = ""
    encoding: Optional[str] = None
    
    # Hash for duplicate detection
    sha256_hash: Optional[str] = None
    md5_hash: Optional[str] = None
    
    # Extracted content
    text_content: Optional[str] = None
    text_length: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Source information
    source_type: str = "local"  # local, smb, sharepoint, onedrive, onenote
    source_url: Optional[str] = None
    
    # Processing status
    processed: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.file_extension and self.filename:
            self.file_extension = Path(self.filename).suffix.lower()
        
        if not self.mime_type and self.filename:
            self.mime_type, _ = mimetypes.guess_type(self.filename)
            if not self.mime_type:
                self.mime_type = "application/octet-stream"
    
    @property
    def size_mb(self) -> float:
        """File size in megabytes"""
        return self.size / (1024 * 1024)
    
    @property
    def is_text_file(self) -> bool:
        """Check if file is a text-based format"""
        text_extensions = {'.txt', '.md', '.html', '.htm', '.xml', '.json', '.csv'}
        text_mimes = {'text/', 'application/json', 'application/xml'}
        
        return (self.file_extension in text_extensions or 
                any(self.mime_type.startswith(mime) for mime in text_mimes))
    
    @property
    def is_office_document(self) -> bool:
        """Check if file is an Office document"""
        office_extensions = {'.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'}
        office_mimes = {
            'application/vnd.openxmlformats-officedocument',
            'application/vnd.ms-',
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint'
        }
        
        return (self.file_extension in office_extensions or
                any(self.mime_type.startswith(mime) for mime in office_mimes))
    
    @property
    def is_pdf(self) -> bool:
        """Check if file is a PDF"""
        return self.file_extension == '.pdf' or self.mime_type == 'application/pdf'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'path': self.path,
            'filename': self.filename,
            'size': self.size,
            'size_mb': self.size_mb,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'file_extension': self.file_extension,
            'mime_type': self.mime_type,
            'encoding': self.encoding,
            'sha256_hash': self.sha256_hash,
            'md5_hash': self.md5_hash,
            'text_length': self.text_length,
            'metadata': self.metadata,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'processed': self.processed,
            'error_message': self.error_message,
            'is_text_file': self.is_text_file,
            'is_office_document': self.is_office_document,
            'is_pdf': self.is_pdf,
        }


class BaseCrawler(ABC):
    """
    Abstract base class for all document crawlers.
    
    Defines the common interface that all crawler implementations must follow.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the crawler.
        
        Args:
            config: Configuration object with crawler settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistics
        self.files_found = 0
        self.files_processed = 0
        self.files_skipped = 0
        self.errors = 0
        
    @abstractmethod
    def scan(self, source: str, **kwargs) -> Iterator[DocumentInfo]:
        """
        Scan a source for documents.
        
        Args:
            source: Source path/URL to scan
            **kwargs: Additional crawler-specific options
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        pass
    
    def should_process_file(self, filepath: str, size: int) -> bool:
        """
        Check if a file should be processed based on configuration.
        
        Args:
            filepath: Path to the file
            size: File size in bytes
            
        Returns:
            bool: True if file should be processed
        """
        if not self.config:
            return True
            
        # Check file extension
        file_ext = Path(filepath).suffix.lower()
        if (hasattr(self.config.crawler, 'supported_extensions') and 
            self.config.crawler.supported_extensions and
            file_ext not in self.config.crawler.supported_extensions):
            return False
        
        # Check file size
        if (hasattr(self.config.crawler, 'max_file_size') and
            size > self.config.crawler.max_file_size):
            return False
        
        # Check ignore patterns
        if hasattr(self.config.crawler, 'ignore_patterns'):
            filename = Path(filepath).name
            for pattern in self.config.crawler.ignore_patterns:
                if self._matches_pattern(filename, pattern):
                    return False
        
        return True
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches ignore pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)
    
    def calculate_file_hash(self, filepath: str, algorithm: str = "sha256") -> Optional[str]:
        """
        Calculate hash of a file.
        
        Args:
            filepath: Path to the file
            algorithm: Hash algorithm (sha256, md5)
            
        Returns:
            str: Hex digest of the hash, or None if error
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(filepath, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating {algorithm} hash for {filepath}: {e}")
            return None
    
    def get_file_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        Extract basic file metadata.
        
        Args:
            filepath: Path to the file
            
        Returns:
            dict: File metadata
        """
        try:
            stat = os.stat(filepath)
            
            return {
                'size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'access_time': datetime.fromtimestamp(stat.st_atime),
                'mode': stat.st_mode,
                'uid': stat.st_uid,
                'gid': stat.st_gid,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metadata for {filepath}: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get crawler statistics.
        
        Returns:
            dict: Statistics about the crawling process
        """
        return {
            'files_found': self.files_found,
            'files_processed': self.files_processed,
            'files_skipped': self.files_skipped,
            'errors': self.errors,
        }
    
    def reset_statistics(self):
        """Reset crawler statistics"""
        self.files_found = 0
        self.files_processed = 0
        self.files_skipped = 0
        self.errors = 0

