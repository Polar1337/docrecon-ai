"""
Microsoft Graph API crawler

Crawls SharePoint Online, OneDrive, and OneNote using Microsoft Graph API.
Requires Azure AD app registration and appropriate permissions.
"""

import json
import tempfile
from datetime import datetime
from typing import Iterator, Optional, Dict, Any, List
from urllib.parse import quote
import logging

from .base import BaseCrawler, DocumentInfo

logger = logging.getLogger(__name__)

# Optional Graph API dependencies
try:
    import msal
    import requests
    GRAPH_AVAILABLE = True
except ImportError:
    GRAPH_AVAILABLE = False
    logger.warning("Microsoft Graph support not available. Install msal: pip install msal requests")


class GraphCrawler(BaseCrawler):
    """
    Crawler for Microsoft Graph API sources.
    
    Supports crawling:
    - SharePoint Online document libraries
    - OneDrive for Business
    - OneNote notebooks (metadata only)
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize Graph API crawler.
        
        Args:
            config: Configuration object with Graph API settings
        """
        super().__init__(config)
        
        if not GRAPH_AVAILABLE:
            raise ImportError("Microsoft Graph support not available. Install: pip install msal requests")
        
        # Graph API configuration
        if not config or not config.graph:
            raise ValueError("Graph API configuration required")
        
        self.tenant_id = config.graph.tenant_id
        self.client_id = config.graph.client_id
        self.client_secret = config.graph.client_secret
        self.scopes = config.graph.scopes or ["https://graph.microsoft.com/.default"]
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Graph API credentials (tenant_id, client_id, client_secret) required")
        
        # MSAL app and token
        self.app = None
        self.access_token = None
        self.graph_url = "https://graph.microsoft.com/v1.0"
        
        # Request session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocRecon-AI/1.0',
            'Accept': 'application/json',
        })
    
    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Create MSAL app
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority
            )
            
            # Acquire token
            result = self.app.acquire_token_for_client(scopes=self.scopes)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                self.logger.info("Successfully authenticated with Microsoft Graph")
                return True
            else:
                self.logger.error(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Graph API authentication: {e}")
            return False
    
    def scan(self, source: str, source_type: str = "sharepoint", **kwargs) -> Iterator[DocumentInfo]:
        """
        Scan a Microsoft Graph source for documents.
        
        Args:
            source: Source identifier (site URL, user ID, etc.)
            source_type: Type of source ("sharepoint", "onedrive", "onenote")
            **kwargs: Additional options
            
        Yields:
            DocumentInfo: Information about each discovered document
        """
        if not self.authenticate():
            self.logger.error("Failed to authenticate with Microsoft Graph")
            return
        
        self.logger.info(f"Scanning {source_type} source: {source}")
        
        try:
            if source_type.lower() == "sharepoint":
                yield from self._scan_sharepoint(source, **kwargs)
            elif source_type.lower() == "onedrive":
                yield from self._scan_onedrive(source, **kwargs)
            elif source_type.lower() == "onenote":
                yield from self._scan_onenote(source, **kwargs)
            else:
                self.logger.error(f"Unsupported source type: {source_type}")
                
        except Exception as e:
            self.logger.error(f"Error scanning {source_type} source {source}: {e}")
            self.errors += 1
    
    def _scan_sharepoint(self, site_url: str, **kwargs) -> Iterator[DocumentInfo]:
        """Scan SharePoint site for documents"""
        try:
            # Get site ID from URL
            site_id = self._get_site_id(site_url)
            if not site_id:
                return
            
            # Get document libraries
            libraries = self._get_document_libraries(site_id)
            
            for library in libraries:
                library_id = library['id']
                library_name = library['name']
                
                self.logger.info(f"Scanning SharePoint library: {library_name}")
                
                # Scan library contents
                yield from self._scan_drive_items(site_id, library_id, "", "sharepoint")
                
        except Exception as e:
            self.logger.error(f"Error scanning SharePoint site {site_url}: {e}")
            self.errors += 1
    
    def _scan_onedrive(self, user_id: str, **kwargs) -> Iterator[DocumentInfo]:
        """Scan OneDrive for Business for documents"""
        try:
            # Get user's drive
            drive_info = self._get_user_drive(user_id)
            if not drive_info:
                return
            
            drive_id = drive_info['id']
            
            self.logger.info(f"Scanning OneDrive for user: {user_id}")
            
            # Scan drive contents
            yield from self._scan_drive_items(None, drive_id, "", "onedrive")
            
        except Exception as e:
            self.logger.error(f"Error scanning OneDrive for user {user_id}: {e}")
            self.errors += 1
    
    def _scan_onenote(self, user_id: str, **kwargs) -> Iterator[DocumentInfo]:
        """Scan OneNote notebooks (metadata only)"""
        try:
            # Get OneNote notebooks
            notebooks = self._get_onenote_notebooks(user_id)
            
            for notebook in notebooks:
                notebook_id = notebook['id']
                notebook_name = notebook['displayName']
                
                self.logger.info(f"Scanning OneNote notebook: {notebook_name}")
                
                # Get sections
                sections = self._get_onenote_sections(notebook_id)
                
                for section in sections:
                    section_id = section['id']
                    section_name = section['displayName']
                    
                    # Get pages
                    pages = self._get_onenote_pages(section_id)
                    
                    for page in pages:
                        self.files_found += 1
                        doc_info = self._process_onenote_page(page, notebook_name, section_name)
                        if doc_info:
                            yield doc_info
                            
        except Exception as e:
            self.logger.error(f"Error scanning OneNote for user {user_id}: {e}")
            self.errors += 1
    
    def _scan_drive_items(self, site_id: Optional[str], drive_id: str, 
                         folder_path: str, source_type: str) -> Iterator[DocumentInfo]:
        """Recursively scan drive items"""
        try:
            # Build API URL
            if site_id:
                url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root"
            else:
                url = f"{self.graph_url}/drives/{drive_id}/root"
            
            if folder_path:
                url += f":/{quote(folder_path)}:"
            
            url += "/children"
            
            # Get items
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('value', [])
            
            for item in items:
                if 'folder' in item:
                    # Folder - recurse
                    folder_name = item['name']
                    new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                    yield from self._scan_drive_items(site_id, drive_id, new_path, source_type)
                    
                elif 'file' in item:
                    # File - process
                    self.files_found += 1
                    doc_info = self._process_drive_item(item, source_type)
                    if doc_info:
                        yield doc_info
                        
        except Exception as e:
            self.logger.error(f"Error scanning drive items in {folder_path}: {e}")
            self.errors += 1
    
    def _process_drive_item(self, item: Dict[str, Any], source_type: str) -> Optional[DocumentInfo]:
        """Process a drive item (file)"""
        try:
            # Extract basic information
            file_info = item.get('file', {})
            name = item['name']
            size = item['size']
            
            # Parse dates
            created_date = datetime.fromisoformat(item['createdDateTime'].replace('Z', '+00:00'))
            modified_date = datetime.fromisoformat(item['lastModifiedDateTime'].replace('Z', '+00:00'))
            
            # Check if file should be processed
            if not self.should_process_file(name, size):
                self.files_skipped += 1
                return None
            
            # Create document info
            doc_info = DocumentInfo(
                path=item.get('webUrl', ''),
                filename=name,
                size=size,
                modified_date=modified_date,
                created_date=created_date,
                source_type=source_type,
                source_url=item.get('webUrl', '')
            )
            
            # Add Graph-specific metadata
            doc_info.metadata.update({
                'graph_id': item['id'],
                'etag': item.get('eTag', ''),
                'mime_type': file_info.get('mimeType', ''),
                'created_by': item.get('createdBy', {}).get('user', {}).get('displayName', ''),
                'modified_by': item.get('lastModifiedBy', {}).get('user', {}).get('displayName', ''),
                'download_url': item.get('@microsoft.graph.downloadUrl', ''),
            })
            
            # Calculate hash if possible
            if '@microsoft.graph.downloadUrl' in item:
                doc_info.sha256_hash = self._calculate_graph_file_hash(item['@microsoft.graph.downloadUrl'])
            
            self.files_processed += 1
            doc_info.processed = True
            
            return doc_info
            
        except Exception as e:
            self.logger.error(f"Error processing drive item {item.get('name', 'unknown')}: {e}")
            self.errors += 1
            return None
    
    def _process_onenote_page(self, page: Dict[str, Any], notebook_name: str, 
                             section_name: str) -> Optional[DocumentInfo]:
        """Process a OneNote page"""
        try:
            name = page['title']
            
            # Parse dates
            created_date = datetime.fromisoformat(page['createdDateTime'].replace('Z', '+00:00'))
            modified_date = datetime.fromisoformat(page['lastModifiedDateTime'].replace('Z', '+00:00'))
            
            # Create document info
            doc_info = DocumentInfo(
                path=f"{notebook_name}/{section_name}/{name}",
                filename=f"{name}.one",
                size=0,  # OneNote pages don't have traditional file sizes
                modified_date=modified_date,
                created_date=created_date,
                source_type="onenote",
                source_url=page.get('links', {}).get('oneNoteWebUrl', {}).get('href', '')
            )
            
            # Add OneNote-specific metadata
            doc_info.metadata.update({
                'onenote_id': page['id'],
                'notebook': notebook_name,
                'section': section_name,
                'level': page.get('level', 0),
                'order': page.get('order', 0),
                'created_by': page.get('createdByAppId', ''),
            })
            
            self.files_processed += 1
            doc_info.processed = True
            
            return doc_info
            
        except Exception as e:
            self.logger.error(f"Error processing OneNote page {page.get('title', 'unknown')}: {e}")
            self.errors += 1
            return None
    
    def _calculate_graph_file_hash(self, download_url: str) -> Optional[str]:
        """Calculate hash of file from Graph API download URL"""
        try:
            import hashlib
            
            # Download file and calculate hash
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            hash_obj = hashlib.sha256()
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating hash from download URL: {e}")
            return None
    
    def _get_site_id(self, site_url: str) -> Optional[str]:
        """Get SharePoint site ID from URL"""
        try:
            # Extract hostname and site path from URL
            from urllib.parse import urlparse
            parsed = urlparse(site_url)
            hostname = parsed.hostname
            site_path = parsed.path.strip('/')
            
            # Get site by hostname and path
            url = f"{self.graph_url}/sites/{hostname}:/{site_path}"
            response = self.session.get(url)
            response.raise_for_status()
            
            site_data = response.json()
            return site_data['id']
            
        except Exception as e:
            self.logger.error(f"Error getting site ID for {site_url}: {e}")
            return None
    
    def _get_document_libraries(self, site_id: str) -> List[Dict[str, Any]]:
        """Get document libraries for a SharePoint site"""
        try:
            url = f"{self.graph_url}/sites/{site_id}/drives"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            self.logger.error(f"Error getting document libraries for site {site_id}: {e}")
            return []
    
    def _get_user_drive(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get OneDrive for a user"""
        try:
            url = f"{self.graph_url}/users/{user_id}/drive"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error getting drive for user {user_id}: {e}")
            return None
    
    def _get_onenote_notebooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get OneNote notebooks for a user"""
        try:
            url = f"{self.graph_url}/users/{user_id}/onenote/notebooks"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            self.logger.error(f"Error getting OneNote notebooks for user {user_id}: {e}")
            return []
    
    def _get_onenote_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        """Get sections in a OneNote notebook"""
        try:
            url = f"{self.graph_url}/onenote/notebooks/{notebook_id}/sections"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            self.logger.error(f"Error getting sections for notebook {notebook_id}: {e}")
            return []
    
    def _get_onenote_pages(self, section_id: str) -> List[Dict[str, Any]]:
        """Get pages in a OneNote section"""
        try:
            url = f"{self.graph_url}/onenote/sections/{section_id}/pages"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return data.get('value', [])
            
        except Exception as e:
            self.logger.error(f"Error getting pages for section {section_id}: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test Graph API connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            if not self.authenticate():
                return False
            
            # Test with a simple API call
            url = f"{self.graph_url}/me"
            response = self.session.get(url)
            response.raise_for_status()
            
            self.logger.info("Graph API connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Graph API connection test failed: {e}")
            return False

