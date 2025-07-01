"""
Hash calculation utilities for DocRecon AI

Provides efficient hash calculation for duplicate detection.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class HashUtils:
    """
    Utility class for calculating file hashes efficiently.
    """
    
    # Buffer size for reading files (64KB)
    BUFFER_SIZE = 64 * 1024
    
    # Maximum file size for hash calculation (100MB)
    MAX_HASH_SIZE = 100 * 1024 * 1024
    
    @staticmethod
    def calculate_sha256(file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: SHA256 hash or None if error
        """
        try:
            path = Path(file_path)
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > HashUtils.MAX_HASH_SIZE:
                logger.warning(f"File too large for hashing: {file_path} ({file_size} bytes)")
                return None
            
            sha256_hash = hashlib.sha256()
            
            with open(path, 'rb') as f:
                # Read file in chunks
                while chunk := f.read(HashUtils.BUFFER_SIZE):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating SHA256 for {file_path}: {e}")
            return None
    
    @staticmethod
    def calculate_md5(file_path: str) -> Optional[str]:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MD5 hash or None if error
        """
        try:
            path = Path(file_path)
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > HashUtils.MAX_HASH_SIZE:
                logger.warning(f"File too large for hashing: {file_path} ({file_size} bytes)")
                return None
            
            md5_hash = hashlib.md5()
            
            with open(path, 'rb') as f:
                # Read file in chunks
                while chunk := f.read(HashUtils.BUFFER_SIZE):
                    md5_hash.update(chunk)
            
            return md5_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating MD5 for {file_path}: {e}")
            return None
    
    @staticmethod
    def calculate_quick_hash(file_path: str, sample_size: int = 8192) -> Optional[str]:
        """
        Calculate a quick hash based on file beginning, middle, and end.
        
        This is faster than full file hashing but less accurate.
        Useful for initial duplicate screening.
        
        Args:
            file_path: Path to the file
            sample_size: Size of each sample in bytes
            
        Returns:
            str: Quick hash or None if error
        """
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            
            # For small files, use full content
            if file_size <= sample_size * 3:
                return HashUtils.calculate_sha256(file_path)
            
            sha256_hash = hashlib.sha256()
            
            with open(path, 'rb') as f:
                # Read beginning
                beginning = f.read(sample_size)
                sha256_hash.update(beginning)
                
                # Read middle
                f.seek(file_size // 2)
                middle = f.read(sample_size)
                sha256_hash.update(middle)
                
                # Read end
                f.seek(max(0, file_size - sample_size))
                end = f.read(sample_size)
                sha256_hash.update(end)
            
            # Include file size in hash to distinguish files with same samples
            sha256_hash.update(str(file_size).encode())
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating quick hash for {file_path}: {e}")
            return None
    
    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """
        Calculate hash of text content.
        
        Args:
            content: Text content to hash
            
        Returns:
            str: SHA256 hash of content
        """
        try:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating content hash: {e}")
            return ""
    
    @staticmethod
    def calculate_multiple_hashes(file_path: str) -> Dict[str, Optional[str]]:
        """
        Calculate multiple hash types for a file efficiently.
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: Dictionary with hash types as keys
        """
        try:
            path = Path(file_path)
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > HashUtils.MAX_HASH_SIZE:
                logger.warning(f"File too large for hashing: {file_path} ({file_size} bytes)")
                return {
                    'sha256': None,
                    'md5': None,
                    'quick_hash': None
                }
            
            # Initialize hash objects
            sha256_hash = hashlib.sha256()
            md5_hash = hashlib.md5()
            
            with open(path, 'rb') as f:
                # Read file once and update all hashes
                while chunk := f.read(HashUtils.BUFFER_SIZE):
                    sha256_hash.update(chunk)
                    md5_hash.update(chunk)
            
            # Calculate quick hash separately
            quick_hash = HashUtils.calculate_quick_hash(file_path)
            
            return {
                'sha256': sha256_hash.hexdigest(),
                'md5': md5_hash.hexdigest(),
                'quick_hash': quick_hash
            }
            
        except Exception as e:
            logger.error(f"Error calculating multiple hashes for {file_path}: {e}")
            return {
                'sha256': None,
                'md5': None,
                'quick_hash': None
            }
    
    @staticmethod
    def verify_file_integrity(file_path: str, expected_hash: str, hash_type: str = 'sha256') -> bool:
        """
        Verify file integrity against expected hash.
        
        Args:
            file_path: Path to the file
            expected_hash: Expected hash value
            hash_type: Type of hash ('sha256', 'md5')
            
        Returns:
            bool: True if file matches expected hash
        """
        try:
            if hash_type.lower() == 'sha256':
                actual_hash = HashUtils.calculate_sha256(file_path)
            elif hash_type.lower() == 'md5':
                actual_hash = HashUtils.calculate_md5(file_path)
            else:
                logger.error(f"Unsupported hash type: {hash_type}")
                return False
            
            if actual_hash is None:
                return False
            
            return actual_hash.lower() == expected_hash.lower()
            
        except Exception as e:
            logger.error(f"Error verifying file integrity for {file_path}: {e}")
            return False
    
    @staticmethod
    def get_hash_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive hash information for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: Hash information including performance metrics
        """
        import time
        
        start_time = time.time()
        
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            
            # Calculate hashes
            hashes = HashUtils.calculate_multiple_hashes(file_path)
            
            end_time = time.time()
            calculation_time = end_time - start_time
            
            return {
                'file_path': str(path.absolute()),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'hashes': hashes,
                'calculation_time': calculation_time,
                'hash_rate_mbps': round((file_size / (1024 * 1024)) / calculation_time, 2) if calculation_time > 0 else 0,
                'success': all(h is not None for h in hashes.values() if h != hashes['quick_hash'])
            }
            
        except Exception as e:
            logger.error(f"Error getting hash info for {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def compare_files_by_hash(file1: str, file2: str, hash_type: str = 'sha256') -> bool:
        """
        Compare two files by their hash values.
        
        Args:
            file1: Path to first file
            file2: Path to second file
            hash_type: Type of hash to use for comparison
            
        Returns:
            bool: True if files have the same hash
        """
        try:
            if hash_type.lower() == 'sha256':
                hash1 = HashUtils.calculate_sha256(file1)
                hash2 = HashUtils.calculate_sha256(file2)
            elif hash_type.lower() == 'md5':
                hash1 = HashUtils.calculate_md5(file1)
                hash2 = HashUtils.calculate_md5(file2)
            elif hash_type.lower() == 'quick':
                hash1 = HashUtils.calculate_quick_hash(file1)
                hash2 = HashUtils.calculate_quick_hash(file2)
            else:
                logger.error(f"Unsupported hash type: {hash_type}")
                return False
            
            if hash1 is None or hash2 is None:
                return False
            
            return hash1 == hash2
            
        except Exception as e:
            logger.error(f"Error comparing files {file1} and {file2}: {e}")
            return False
    
    @staticmethod
    def is_hash_collision_likely(hash_value: str, hash_type: str = 'sha256') -> bool:
        """
        Check if a hash collision is likely (for testing purposes).
        
        Args:
            hash_value: Hash value to check
            hash_type: Type of hash
            
        Returns:
            bool: True if collision is theoretically possible but unlikely
        """
        # This is mainly for educational/testing purposes
        # Real hash collisions are extremely rare
        
        if hash_type.lower() == 'md5':
            # MD5 has known collision vulnerabilities
            return len(hash_value) == 32
        elif hash_type.lower() == 'sha256':
            # SHA256 collisions are theoretically possible but practically impossible
            return len(hash_value) == 64
        
        return False

