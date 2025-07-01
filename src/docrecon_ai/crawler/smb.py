"""
SMB/CIFS network share crawler

Crawls Windows network shares (SMB/CIFS) to discover documents.
Supports authentication and various SMB protocol versions.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Iterator, Optional, Dict, Any
from urllib.parse import urlparse
import logging

from .base import BaseCrawler, DocumentInfo

logger = logging.getLogger(__name__)

# Optional SMB dependencies
try:
    from smbprotocol.connection import Connection
    from smbprotocol.session import Session
    from smbprotocol.tree import TreeConnect
    from smbprotocol.file import File, FileInformation
    from smbprotocol.open import CreateDisposition, CreateOptions, FileAttributes, ImpersonationLevel, ShareAccess
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False
    logger.warning("SMB support not available. Install smbprotocol: pip install smbprotocol")

try:
    from smb.SMBConnection import SMBConnection
    from smb.base import SharedFile
    PYSMB_AVAILABLE = True
except ImportError:
    PYSMB_AVAILABLE = False


class SMBCrawler(BaseCrawler):
    """
    Crawler for SMB/CIFS network shares.
    
    Connects to Windows network shares and recursively scans for documents.
    Supports both smbprotocol and pysmb backends.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize SMB crawler.
        
        Args:
            config: Configuration object with crawler settings
        """
        super().__init__(config)
        
        if not SMB_AVAILABLE and not PYSMB_AVAILABLE:
            raise ImportError("No SMB library available. Install smbprotocol or pysmb.")
        
        self.use_smbprotocol = SMB_AVAILABLE
        self.connection = None
        self.session = None
        self.tree = None
        
        # SMB connection settings
        self.timeout = 30
        self.max_depth = getattr(config.crawler, 'max_depth', 10) if config else 10
    
    def scan(self, source: str, username: str = None, password: str = None, 
             domain: str = "", **kwargs) -> Iterator[DocumentInfo]:
        """
        Scan an SMB share for documents.
        
        Args:
            source: SMB share path (e.g., "//server/share" or "\\\\server\\share")
            username: Username for authentication
            password: Password for authentication  
            domain: Domain for authentication
            **kwargs: Additional options
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        # Parse SMB path
        smb_info = self._parse_smb_path(source)
        if not smb_info:
            self.logger.error(f"Invalid SMB path: {source}")
            return
        
        server = smb_info['server']
        share = smb_info['share']
        path = smb_info['path']
        
        self.logger.info(f"Connecting to SMB share: //{server}/{share}")
        
        try:
            # Connect to SMB share
            if self.use_smbprotocol:
                yield from self._scan_with_smbprotocol(
                    server, share, path, username, password, domain
                )
            else:
                yield from self._scan_with_pysmb(
                    server, share, path, username, password, domain
                )
                
        except Exception as e:
            self.logger.error(f"Error scanning SMB share {source}: {e}")
            self.errors += 1
        finally:
            self._disconnect()
    
    def _parse_smb_path(self, path: str) -> Optional[Dict[str, str]]:
        """
        Parse SMB path into components.
        
        Args:
            path: SMB path (//server/share/path or \\\\server\\share\\path)
            
        Returns:
            dict: Parsed components or None if invalid
        """
        # Normalize path separators
        path = path.replace('\\', '/')
        
        # Remove leading slashes
        if path.startswith('//'):
            path = path[2:]
        
        parts = path.split('/')
        if len(parts) < 2:
            return None
        
        return {
            'server': parts[0],
            'share': parts[1],
            'path': '/'.join(parts[2:]) if len(parts) > 2 else ''
        }
    
    def _scan_with_smbprotocol(self, server: str, share: str, path: str,
                              username: str, password: str, domain: str) -> Iterator[DocumentInfo]:
        """Scan using smbprotocol library"""
        try:
            # Create connection
            self.connection = Connection(uuid.uuid4(), server, 445)
            self.connection.connect()
            
            # Create session
            self.session = Session(self.connection, username, password, domain)
            self.session.connect()
            
            # Connect to tree (share)
            self.tree = TreeConnect(self.session, f"\\\\{server}\\{share}")
            self.tree.connect()
            
            # Start scanning from root path
            yield from self._scan_smb_directory_smbprotocol(path, depth=0)
            
        finally:
            self._disconnect()
    
    def _scan_smb_directory_smbprotocol(self, directory: str, depth: int = 0) -> Iterator[DocumentInfo]:
        """Scan SMB directory using smbprotocol"""
        if depth > self.max_depth:
            return
        
        try:
            # Open directory
            dir_file = File(self.tree, directory, CreateDisposition.FILE_OPEN,
                           CreateOptions.FILE_DIRECTORY_FILE,
                           FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
                           ShareAccess.FILE_SHARE_READ)
            dir_file.open()
            
            # List directory contents
            for file_info in dir_file.query_directory("*"):
                if file_info.file_name in ['.', '..']:
                    continue
                
                file_path = f"{directory}/{file_info.file_name}".replace('//', '/')
                
                if file_info.file_attributes & FileAttributes.FILE_ATTRIBUTE_DIRECTORY:
                    # Subdirectory - recurse
                    yield from self._scan_smb_directory_smbprotocol(file_path, depth + 1)
                else:
                    # File - process
                    self.files_found += 1
                    doc_info = self._process_smb_file_smbprotocol(file_path, file_info)
                    if doc_info:
                        yield doc_info
            
            dir_file.close()
            
        except Exception as e:
            self.logger.error(f"Error scanning SMB directory {directory}: {e}")
            self.errors += 1
    
    def _process_smb_file_smbprotocol(self, file_path: str, file_info) -> Optional[DocumentInfo]:
        """Process SMB file using smbprotocol"""
        try:
            # Check if file should be processed
            if not self.should_process_file(file_path, file_info.end_of_file):
                self.files_skipped += 1
                return None
            
            # Create document info
            doc_info = DocumentInfo(
                path=file_path,
                filename=file_info.file_name,
                size=file_info.end_of_file,
                modified_date=datetime.fromtimestamp(file_info.last_write_time.timestamp()),
                created_date=datetime.fromtimestamp(file_info.creation_time.timestamp()),
                source_type="smb"
            )
            
            # Calculate hash by downloading file temporarily
            if file_info.end_of_file > 0:
                doc_info.sha256_hash = self._calculate_smb_file_hash_smbprotocol(file_path)
            
            # Add SMB-specific metadata
            doc_info.metadata.update({
                'smb_attributes': file_info.file_attributes,
                'last_access_time': file_info.last_access_time.timestamp(),
                'change_time': file_info.change_time.timestamp(),
            })
            
            self.files_processed += 1
            doc_info.processed = True
            
            return doc_info
            
        except Exception as e:
            self.logger.error(f"Error processing SMB file {file_path}: {e}")
            self.errors += 1
            return None
    
    def _calculate_smb_file_hash_smbprotocol(self, file_path: str) -> Optional[str]:
        """Calculate hash of SMB file by downloading it temporarily"""
        try:
            # Open file for reading
            smb_file = File(self.tree, file_path, CreateDisposition.FILE_OPEN,
                           CreateOptions.FILE_NON_DIRECTORY_FILE,
                           FileAttributes.FILE_ATTRIBUTE_NORMAL,
                           ShareAccess.FILE_SHARE_READ)
            smb_file.open()
            
            # Read file content and calculate hash
            import hashlib
            hash_obj = hashlib.sha256()
            
            offset = 0
            chunk_size = 8192
            
            while True:
                chunk = smb_file.read(chunk_size, offset)
                if not chunk:
                    break
                hash_obj.update(chunk)
                offset += len(chunk)
            
            smb_file.close()
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for SMB file {file_path}: {e}")
            return None
    
    def _scan_with_pysmb(self, server: str, share: str, path: str,
                        username: str, password: str, domain: str) -> Iterator[DocumentInfo]:
        """Scan using pysmb library"""
        try:
            # Create SMB connection
            conn = SMBConnection(username, password, "docrecon", server, domain=domain, use_ntlm_v2=True)
            
            # Connect
            if not conn.connect(server, 445, timeout=self.timeout):
                raise ConnectionError(f"Failed to connect to {server}")
            
            # Start scanning
            yield from self._scan_smb_directory_pysmb(conn, share, path, depth=0)
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error with pysmb connection: {e}")
            self.errors += 1
    
    def _scan_smb_directory_pysmb(self, conn: 'SMBConnection', share: str, 
                                 directory: str, depth: int = 0) -> Iterator[DocumentInfo]:
        """Scan SMB directory using pysmb"""
        if depth > self.max_depth:
            return
        
        try:
            # List directory contents
            file_list = conn.listPath(share, directory)
            
            for shared_file in file_list:
                if shared_file.filename in ['.', '..']:
                    continue
                
                file_path = f"{directory}/{shared_file.filename}".replace('//', '/')
                
                if shared_file.isDirectory:
                    # Subdirectory - recurse
                    yield from self._scan_smb_directory_pysmb(conn, share, file_path, depth + 1)
                else:
                    # File - process
                    self.files_found += 1
                    doc_info = self._process_smb_file_pysmb(conn, share, file_path, shared_file)
                    if doc_info:
                        yield doc_info
                        
        except Exception as e:
            self.logger.error(f"Error scanning SMB directory {directory}: {e}")
            self.errors += 1
    
    def _process_smb_file_pysmb(self, conn: 'SMBConnection', share: str, 
                               file_path: str, shared_file: 'SharedFile') -> Optional[DocumentInfo]:
        """Process SMB file using pysmb"""
        try:
            # Check if file should be processed
            if not self.should_process_file(file_path, shared_file.file_size):
                self.files_skipped += 1
                return None
            
            # Create document info
            doc_info = DocumentInfo(
                path=file_path,
                filename=shared_file.filename,
                size=shared_file.file_size,
                modified_date=datetime.fromtimestamp(shared_file.last_write_time),
                created_date=datetime.fromtimestamp(shared_file.create_time),
                source_type="smb"
            )
            
            # Calculate hash by downloading file temporarily
            if shared_file.file_size > 0:
                doc_info.sha256_hash = self._calculate_smb_file_hash_pysmb(conn, share, file_path)
            
            # Add SMB-specific metadata
            doc_info.metadata.update({
                'smb_attributes': shared_file.file_attributes,
                'last_access_time': shared_file.last_access_time,
                'allocation_size': shared_file.alloc_size,
            })
            
            self.files_processed += 1
            doc_info.processed = True
            
            return doc_info
            
        except Exception as e:
            self.logger.error(f"Error processing SMB file {file_path}: {e}")
            self.errors += 1
            return None
    
    def _calculate_smb_file_hash_pysmb(self, conn: 'SMBConnection', share: str, file_path: str) -> Optional[str]:
        """Calculate hash of SMB file using pysmb"""
        try:
            import hashlib
            hash_obj = hashlib.sha256()
            
            # Download file in chunks and calculate hash
            with tempfile.NamedTemporaryFile() as temp_file:
                conn.retrieveFile(share, file_path, temp_file)
                temp_file.seek(0)
                
                for chunk in iter(lambda: temp_file.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for SMB file {file_path}: {e}")
            return None
    
    def _disconnect(self):
        """Disconnect from SMB share"""
        try:
            if self.tree:
                self.tree.disconnect()
            if self.session:
                self.session.disconnect()
            if self.connection:
                self.connection.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting from SMB: {e}")
        finally:
            self.tree = None
            self.session = None
            self.connection = None
    
    def test_connection(self, server: str, share: str, username: str = None, 
                       password: str = None, domain: str = "") -> bool:
        """
        Test SMB connection.
        
        Args:
            server: SMB server hostname/IP
            share: Share name
            username: Username for authentication
            password: Password for authentication
            domain: Domain for authentication
            
        Returns:
            bool: True if connection successful
        """
        try:
            if self.use_smbprotocol:
                connection = Connection(uuid.uuid4(), server, 445)
                connection.connect()
                
                session = Session(connection, username, password, domain)
                session.connect()
                
                tree = TreeConnect(session, f"\\\\{server}\\{share}")
                tree.connect()
                
                tree.disconnect()
                session.disconnect()
                connection.disconnect()
                
            else:
                conn = SMBConnection(username, password, "docrecon", server, domain=domain)
                if not conn.connect(server, 445, timeout=self.timeout):
                    return False
                conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMB connection test failed: {e}")
            return False

