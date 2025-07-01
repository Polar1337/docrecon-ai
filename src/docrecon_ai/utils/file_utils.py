"""
File handling utilities for DocRecon AI

Provides common file operations, validation, and metadata extraction.
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUtils:
    """
    Utility class for file operations and metadata extraction.
    """
    
    # Common file extensions and their categories
    DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
    SPREADSHEET_EXTENSIONS = {'.xls', '.xlsx', '.csv', '.ods'}
    PRESENTATION_EXTENSIONS = {'.ppt', '.pptx', '.odp'}
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'}
    ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz'}
    
    # System files to ignore
    SYSTEM_FILES = {
        'thumbs.db', 'desktop.ini', '.ds_store', 
        'icon\r', '$recycle.bin', 'system volume information'
    }
    
    # Temporary file patterns
    TEMP_PATTERNS = {'~$', '.tmp', '.temp', '.bak', '.swp'}
    
    @staticmethod
    def is_valid_file(file_path: str) -> bool:
        """
        Check if a file is valid for analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file should be analyzed
        """
        try:
            path = Path(file_path)
            
            # Check if file exists and is a file
            if not path.exists() or not path.is_file():
                return False
            
            # Check file name
            filename_lower = path.name.lower()
            
            # Skip system files
            if filename_lower in FileUtils.SYSTEM_FILES:
                return False
            
            # Skip temporary files
            for pattern in FileUtils.TEMP_PATTERNS:
                if pattern in filename_lower:
                    return False
            
            # Check file size (skip empty files and very large files > 1GB)
            try:
                size = path.stat().st_size
                if size == 0 or size > 1024 * 1024 * 1024:  # 1GB limit
                    return False
            except OSError:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating file {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive file metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: File metadata
        """
        try:
            path = Path(file_path)
            stat = path.stat()
            
            # Basic metadata
            metadata = {
                'filename': path.name,
                'path': str(path.absolute()),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'file_extension': path.suffix.lower(),
                'created_date': datetime.fromtimestamp(stat.st_ctime),
                'modified_date': datetime.fromtimestamp(stat.st_mtime),
                'accessed_date': datetime.fromtimestamp(stat.st_atime),
            }
            
            # MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            metadata['mime_type'] = mime_type
            
            # File category
            metadata['file_category'] = FileUtils.get_file_category(path.suffix.lower())
            
            # Additional properties
            metadata['is_hidden'] = path.name.startswith('.')
            metadata['is_readonly'] = not os.access(path, os.W_OK)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {file_path}: {e}")
            return {}
    
    @staticmethod
    def get_file_category(extension: str) -> str:
        """
        Categorize file by extension.
        
        Args:
            extension: File extension (with dot)
            
        Returns:
            str: File category
        """
        extension = extension.lower()
        
        if extension in FileUtils.DOCUMENT_EXTENSIONS:
            return 'document'
        elif extension in FileUtils.SPREADSHEET_EXTENSIONS:
            return 'spreadsheet'
        elif extension in FileUtils.PRESENTATION_EXTENSIONS:
            return 'presentation'
        elif extension in FileUtils.IMAGE_EXTENSIONS:
            return 'image'
        elif extension in FileUtils.ARCHIVE_EXTENSIONS:
            return 'archive'
        else:
            return 'other'
    
    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """
        Check if file contains text content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file likely contains text
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Known text file extensions
        text_extensions = {
            '.txt', '.md', '.rst', '.log', '.csv', '.json', '.xml', '.html', '.htm',
            '.py', '.js', '.css', '.sql', '.yaml', '.yml', '.ini', '.cfg', '.conf'
        }
        
        if extension in text_extensions:
            return True
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and mime_type.startswith('text/'):
            return True
        
        # Document formats that contain extractable text
        document_extensions = {'.pdf', '.doc', '.docx', '.rtf', '.odt'}
        if extension in document_extensions:
            return True
        
        return False
    
    @staticmethod
    def safe_read_text(file_path: str, max_size: int = 10 * 1024 * 1024) -> Optional[str]:
        """
        Safely read text content from a file.
        
        Args:
            file_path: Path to the file
            max_size: Maximum file size to read (bytes)
            
        Returns:
            str: File content or None if unable to read
        """
        try:
            path = Path(file_path)
            
            # Check file size
            if path.stat().st_size > max_size:
                logger.warning(f"File too large to read: {file_path}")
                return None
            
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            logger.warning(f"Could not decode file: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        Calculate total size of a directory.
        
        Args:
            directory: Path to directory
            
        Returns:
            int: Total size in bytes
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except Exception as e:
            logger.error(f"Error calculating directory size for {directory}: {e}")
        
        return total_size
    
    @staticmethod
    def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
        """
        Find files matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (glob style)
            recursive: Whether to search recursively
            
        Returns:
            list: List of matching file paths
        """
        try:
            path = Path(directory)
            
            if recursive:
                return [str(p) for p in path.rglob(pattern) if p.is_file()]
            else:
                return [str(p) for p in path.glob(pattern) if p.is_file()]
                
        except Exception as e:
            logger.error(f"Error finding files with pattern {pattern} in {directory}: {e}")
            return []
    
    @staticmethod
    def normalize_path(file_path: str) -> str:
        """
        Normalize file path for consistent comparison.
        
        Args:
            file_path: File path to normalize
            
        Returns:
            str: Normalized path
        """
        try:
            # Convert to Path object and resolve
            path = Path(file_path).resolve()
            
            # Convert to string with forward slashes
            normalized = str(path).replace('\\', '/')
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing path {file_path}: {e}")
            return file_path
    
    @staticmethod
    def is_duplicate_filename(filename1: str, filename2: str) -> bool:
        """
        Check if two filenames are likely duplicates.
        
        Args:
            filename1: First filename
            filename2: Second filename
            
        Returns:
            bool: True if filenames suggest duplicates
        """
        # Remove extensions for comparison
        name1 = Path(filename1).stem.lower()
        name2 = Path(filename2).stem.lower()
        
        # Exact match
        if name1 == name2:
            return True
        
        # Common duplicate patterns
        duplicate_patterns = [
            ' - copy', ' - copy (', '(copy)', '(1)', '(2)', '(3)',
            '_copy', '_backup', '_bak', '_old', '_new', '_final',
            ' copy', ' backup', ' bak', ' old', ' new', ' final'
        ]
        
        # Remove common duplicate indicators
        clean_name1 = name1
        clean_name2 = name2
        
        for pattern in duplicate_patterns:
            clean_name1 = clean_name1.replace(pattern, '')
            clean_name2 = clean_name2.replace(pattern, '')
        
        # Check if cleaned names match
        return clean_name1 == clean_name2
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"

