"""
Path manipulation utilities for DocRecon AI

Provides cross-platform path handling and validation.
"""

import os
import re
from pathlib import Path, PurePath
from typing import List, Optional, Tuple, Dict, Any
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PathUtils:
    """
    Utility class for path manipulation and validation.
    """
    
    # Windows reserved names
    WINDOWS_RESERVED = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Invalid characters for filenames
    INVALID_CHARS = {'<', '>', ':', '"', '|', '?', '*'}
    INVALID_CHARS_WINDOWS = INVALID_CHARS | {'/', '\\'}
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalize a path for consistent handling across platforms.
        
        Args:
            path: Path to normalize
            
        Returns:
            str: Normalized path
        """
        try:
            # Convert to Path object and resolve
            normalized = Path(path).resolve()
            
            # Convert to string with forward slashes for consistency
            return str(normalized).replace('\\', '/')
            
        except Exception as e:
            logger.error(f"Error normalizing path {path}: {e}")
            return path
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """
        Check if a path is valid.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is valid
        """
        try:
            # Try to create Path object
            Path(path)
            
            # Check for invalid characters
            if os.name == 'nt':  # Windows
                invalid_chars = PathUtils.INVALID_CHARS_WINDOWS
            else:
                invalid_chars = PathUtils.INVALID_CHARS
            
            if any(char in path for char in invalid_chars):
                return False
            
            # Check for Windows reserved names
            if os.name == 'nt':
                parts = Path(path).parts
                for part in parts:
                    name = part.upper().split('.')[0]
                    if name in PathUtils.WINDOWS_RESERVED:
                        return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def is_unc_path(path: str) -> bool:
        """
        Check if path is a UNC (Universal Naming Convention) path.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if UNC path
        """
        return path.startswith('\\\\') or path.startswith('//')
    
    @staticmethod
    def is_network_path(path: str) -> bool:
        """
        Check if path is a network path.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if network path
        """
        # UNC paths
        if PathUtils.is_unc_path(path):
            return True
        
        # URLs
        try:
            parsed = urlparse(path)
            return parsed.scheme in ['smb', 'cifs', 'ftp', 'sftp', 'http', 'https']
        except Exception:
            return False
    
    @staticmethod
    def split_unc_path(unc_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Split UNC path into server, share, and path components.
        
        Args:
            unc_path: UNC path to split
            
        Returns:
            tuple: (server, share, path) or (None, None, None) if invalid
        """
        try:
            if not PathUtils.is_unc_path(unc_path):
                return None, None, None
            
            # Remove leading slashes
            path = unc_path.lstrip('\\/')
            
            # Split into components
            parts = path.split('\\') if '\\' in path else path.split('/')
            
            if len(parts) < 2:
                return None, None, None
            
            server = parts[0]
            share = parts[1]
            remaining_path = '/'.join(parts[2:]) if len(parts) > 2 else ''
            
            return server, share, remaining_path
            
        except Exception as e:
            logger.error(f"Error splitting UNC path {unc_path}: {e}")
            return None, None, None
    
    @staticmethod
    def join_paths(*paths: str) -> str:
        """
        Join multiple path components safely.
        
        Args:
            *paths: Path components to join
            
        Returns:
            str: Joined path
        """
        try:
            if not paths:
                return ''
            
            # Use pathlib for cross-platform joining
            result = Path(paths[0])
            for path in paths[1:]:
                result = result / path
            
            return str(result)
            
        except Exception as e:
            logger.error(f"Error joining paths {paths}: {e}")
            return str(paths[0]) if paths else ''
    
    @staticmethod
    def get_relative_path(path: str, base: str) -> str:
        """
        Get relative path from base directory.
        
        Args:
            path: Target path
            base: Base directory
            
        Returns:
            str: Relative path
        """
        try:
            path_obj = Path(path)
            base_obj = Path(base)
            
            return str(path_obj.relative_to(base_obj))
            
        except ValueError:
            # Paths are not relative to each other
            return path
        except Exception as e:
            logger.error(f"Error getting relative path from {base} to {path}: {e}")
            return path
    
    @staticmethod
    def get_common_path(paths: List[str]) -> str:
        """
        Get common path prefix for a list of paths.
        
        Args:
            paths: List of paths
            
        Returns:
            str: Common path prefix
        """
        try:
            if not paths:
                return ''
            
            if len(paths) == 1:
                return str(Path(paths[0]).parent)
            
            # Convert to Path objects
            path_objects = [Path(p) for p in paths]
            
            # Find common parts
            common_parts = []
            min_parts = min(len(p.parts) for p in path_objects)
            
            for i in range(min_parts):
                part = path_objects[0].parts[i]
                if all(p.parts[i] == part for p in path_objects):
                    common_parts.append(part)
                else:
                    break
            
            if common_parts:
                return str(Path(*common_parts))
            else:
                return ''
                
        except Exception as e:
            logger.error(f"Error finding common path for {paths}: {e}")
            return ''
    
    @staticmethod
    def sanitize_filename(filename: str, replacement: str = '_') -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            replacement: Character to replace invalid chars with
            
        Returns:
            str: Sanitized filename
        """
        try:
            # Remove invalid characters
            if os.name == 'nt':  # Windows
                invalid_chars = PathUtils.INVALID_CHARS_WINDOWS
            else:
                invalid_chars = PathUtils.INVALID_CHARS
            
            sanitized = filename
            for char in invalid_chars:
                sanitized = sanitized.replace(char, replacement)
            
            # Handle Windows reserved names
            if os.name == 'nt':
                name_part = sanitized.split('.')[0].upper()
                if name_part in PathUtils.WINDOWS_RESERVED:
                    sanitized = f"{replacement}{sanitized}"
            
            # Remove leading/trailing spaces and dots
            sanitized = sanitized.strip(' .')
            
            # Ensure filename is not empty
            if not sanitized:
                sanitized = 'unnamed'
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing filename {filename}: {e}")
            return 'unnamed'
    
    @staticmethod
    def get_path_depth(path: str) -> int:
        """
        Get the depth (number of directory levels) of a path.
        
        Args:
            path: Path to analyze
            
        Returns:
            int: Path depth
        """
        try:
            return len(Path(path).parts)
        except Exception:
            return 0
    
    @staticmethod
    def is_subdirectory(path: str, parent: str) -> bool:
        """
        Check if path is a subdirectory of parent.
        
        Args:
            path: Path to check
            parent: Potential parent directory
            
        Returns:
            bool: True if path is subdirectory of parent
        """
        try:
            path_obj = Path(path).resolve()
            parent_obj = Path(parent).resolve()
            
            return parent_obj in path_obj.parents or path_obj == parent_obj
            
        except Exception as e:
            logger.error(f"Error checking if {path} is subdirectory of {parent}: {e}")
            return False
    
    @staticmethod
    def get_path_components(path: str) -> Dict[str, str]:
        """
        Get all components of a path.
        
        Args:
            path: Path to analyze
            
        Returns:
            dict: Path components
        """
        try:
            path_obj = Path(path)
            
            return {
                'full_path': str(path_obj.absolute()),
                'directory': str(path_obj.parent),
                'filename': path_obj.name,
                'stem': path_obj.stem,
                'extension': path_obj.suffix,
                'extensions': ''.join(path_obj.suffixes),
                'drive': str(path_obj.drive) if path_obj.drive else '',
                'anchor': str(path_obj.anchor),
                'parts': list(path_obj.parts),
            }
            
        except Exception as e:
            logger.error(f"Error getting path components for {path}: {e}")
            return {}
    
    @staticmethod
    def find_duplicate_paths(paths: List[str]) -> Dict[str, List[str]]:
        """
        Find duplicate paths in a list (case-insensitive).
        
        Args:
            paths: List of paths to check
            
        Returns:
            dict: Dictionary mapping normalized paths to original paths
        """
        duplicates = {}
        
        try:
            for path in paths:
                normalized = PathUtils.normalize_path(path).lower()
                
                if normalized not in duplicates:
                    duplicates[normalized] = []
                
                duplicates[normalized].append(path)
            
            # Return only actual duplicates
            return {k: v for k, v in duplicates.items() if len(v) > 1}
            
        except Exception as e:
            logger.error(f"Error finding duplicate paths: {e}")
            return {}
    
    @staticmethod
    def expand_path_variables(path: str) -> str:
        """
        Expand environment variables and user home in path.
        
        Args:
            path: Path with potential variables
            
        Returns:
            str: Expanded path
        """
        try:
            # Expand environment variables
            expanded = os.path.expandvars(path)
            
            # Expand user home directory
            expanded = os.path.expanduser(expanded)
            
            return expanded
            
        except Exception as e:
            logger.error(f"Error expanding path variables in {path}: {e}")
            return path
    
    @staticmethod
    def get_mount_point(path: str) -> str:
        """
        Get the mount point for a given path.
        
        Args:
            path: Path to check
            
        Returns:
            str: Mount point path
        """
        try:
            path_obj = Path(path).resolve()
            
            # On Windows, return the drive
            if os.name == 'nt':
                return str(path_obj.drive) if path_obj.drive else ''
            
            # On Unix-like systems, find mount point
            current = path_obj
            while current != current.parent:
                if current.is_mount():
                    return str(current)
                current = current.parent
            
            return str(current)  # Root directory
            
        except Exception as e:
            logger.error(f"Error getting mount point for {path}: {e}")
            return ''

