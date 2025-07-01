"""
SharePoint 2019 On-Premise Crawler

Specialized crawler for SharePoint 2019 On-Premise installations using REST API.
Supports NTLM, Kerberos, and Basic authentication methods.
"""

import requests
from requests_ntlm import HttpNtlmAuth
from requests.auth import HTTPBasicAuth
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, quote
import time
from datetime import datetime
import os

from .base import BaseCrawler, DocumentInfo


logger = logging.getLogger(__name__)


class SharePointOnPremCrawler(BaseCrawler):
    """
    Crawler for SharePoint 2019 On-Premise using REST API.
    
    Supports multiple authentication methods and comprehensive document discovery.
    """
    
    def __init__(self, config):
        super().__init__(config)
        
        # SharePoint configuration
        self.server_url = config.get('crawler.sharepoint_onprem.server_url', '').rstrip('/')
        self.auth_method = config.get('crawler.sharepoint_onprem.authentication_method', 'ntlm').lower()
        self.username = config.get('crawler.sharepoint_onprem.username', '')
        self.password = config.get('crawler.sharepoint_onprem.password', '')
        self.domain = config.get('crawler.sharepoint_onprem.domain', '')
        
        # Site collections and libraries to crawl
        self.site_collections = config.get('crawler.sharepoint_onprem.site_collections', [])
        self.document_libraries = config.get('crawler.sharepoint_onprem.document_libraries', ['Shared Documents'])
        self.include_subsites = config.get('crawler.sharepoint_onprem.include_subsites', True)
        self.max_depth = config.get('crawler.sharepoint_onprem.max_depth', 5)
        
        # Request configuration
        self.timeout = config.get('crawler.sharepoint_onprem.timeout_seconds', 30)
        self.retry_attempts = config.get('crawler.sharepoint_onprem.retry_attempts', 3)
        self.batch_size = config.get('crawler.sharepoint_onprem.batch_size', 100)
        
        # Initialize session
        self.session = None
        self._initialize_session()
        
        # Statistics
        self.stats = {
            'sites_crawled': 0,
            'libraries_crawled': 0,
            'documents_found': 0,
            'errors_encountered': 0,
            'api_calls_made': 0
        }
    
    def _initialize_session(self):
        """Initialize HTTP session with appropriate authentication."""
        self.session = requests.Session()
        
        # Set authentication based on method
        if self.auth_method == 'ntlm':
            if self.domain:
                username = f"{self.domain}\\{self.username}"
            else:
                username = self.username
            self.session.auth = HttpNtlmAuth(username, self.password)
            logger.info(f"Initialized NTLM authentication for user: {username}")
            
        elif self.auth_method == 'basic':
            self.session.auth = HTTPBasicAuth(self.username, self.password)
            logger.info(f"Initialized Basic authentication for user: {self.username}")
            
        elif self.auth_method == 'kerberos':
            # For Kerberos, we assume the user is already authenticated
            logger.info("Using Kerberos authentication (current user context)")
            
        else:
            raise ValueError(f"Unsupported authentication method: {self.auth_method}")
        
        # Set common headers
        self.session.headers.update({
            'Accept': 'application/json;odata=verbose',
            'Content-Type': 'application/json;odata=verbose',
            'User-Agent': 'DocRecon-AI/1.0'
        })
        
        # Set timeout
        self.session.timeout = self.timeout
    
    def test_connection(self) -> bool:
        """Test connection to SharePoint server."""
        try:
            test_url = f"{self.server_url}/_api/web"
            response = self._make_api_request(test_url)
            
            if response and response.status_code == 200:
                data = response.json()
                site_title = data.get('d', {}).get('Title', 'Unknown')
                logger.info(f"Successfully connected to SharePoint site: {site_title}")
                return True
            else:
                logger.error(f"Connection test failed with status: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _make_api_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """Make authenticated API request with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                self.stats['api_calls_made'] += 1
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 401:
                    logger.error(f"Authentication failed for URL: {url}")
                    return None
                elif response.status_code == 403:
                    logger.error(f"Access denied for URL: {url}")
                    return None
                elif response.status_code == 404:
                    logger.warning(f"Resource not found: {url}")
                    return None
                else:
                    logger.warning(f"API request failed with status {response.status_code}: {url}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout for URL: {url} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error for URL: {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Unexpected error in API request: {e}")
                
            if attempt < self.retry_attempts - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        self.stats['errors_encountered'] += 1
        return None
    
    def crawl_path(self, path: str) -> List[DocumentInfo]:
        """
        Crawl SharePoint path (site collection or specific site).
        
        Args:
            path: SharePoint site path (e.g., '/sites/documents')
            
        Returns:
            List of DocumentInfo objects
        """
        documents = []
        
        try:
            # Test connection first
            if not self.test_connection():
                logger.error("Cannot establish connection to SharePoint server")
                return documents
            
            # If path is provided, use it; otherwise use configured site collections
            sites_to_crawl = [path] if path else self.site_collections
            
            for site_path in sites_to_crawl:
                site_documents = self._crawl_site(site_path)
                documents.extend(site_documents)
                self.stats['sites_crawled'] += 1
                
        except Exception as e:
            logger.error(f"Error crawling SharePoint path {path}: {e}")
            self.stats['errors_encountered'] += 1
        
        self.stats['documents_found'] = len(documents)
        logger.info(f"SharePoint crawl completed. Found {len(documents)} documents.")
        
        return documents
    
    def _crawl_site(self, site_path: str) -> List[DocumentInfo]:
        """Crawl a specific SharePoint site."""
        documents = []
        
        try:
            # Get site information
            site_url = f"{self.server_url}{site_path}"
            api_url = f"{site_url}/_api/web"
            
            response = self._make_api_request(api_url)
            if not response:
                logger.error(f"Cannot access site: {site_path}")
                return documents
            
            site_data = response.json().get('d', {})
            site_title = site_data.get('Title', 'Unknown')
            logger.info(f"Crawling site: {site_title} ({site_path})")
            
            # Crawl document libraries
            for library_name in self.document_libraries:
                library_documents = self._crawl_document_library(site_url, library_name)
                documents.extend(library_documents)
                self.stats['libraries_crawled'] += 1
            
            # Crawl subsites if enabled
            if self.include_subsites:
                subsites = self._get_subsites(site_url)
                for subsite_path in subsites:
                    if self._get_site_depth(subsite_path) <= self.max_depth:
                        subsite_documents = self._crawl_site(subsite_path)
                        documents.extend(subsite_documents)
                    else:
                        logger.info(f"Skipping subsite due to depth limit: {subsite_path}")
                        
        except Exception as e:
            logger.error(f"Error crawling site {site_path}: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _crawl_document_library(self, site_url: str, library_name: str) -> List[DocumentInfo]:
        """Crawl a specific document library."""
        documents = []
        
        try:
            # Get library information
            library_url = f"{site_url}/_api/web/lists/getbytitle('{quote(library_name)}')"
            response = self._make_api_request(library_url)
            
            if not response:
                logger.warning(f"Cannot access library: {library_name}")
                return documents
            
            library_data = response.json().get('d', {})
            library_id = library_data.get('Id')
            
            if not library_id:
                logger.warning(f"Library not found: {library_name}")
                return documents
            
            logger.info(f"Crawling document library: {library_name}")
            
            # Get all files in library
            files_url = f"{site_url}/_api/web/lists/getbytitle('{quote(library_name)}')/items"
            files_url += "?$expand=File,Folder&$filter=FSObjType eq 0"  # Files only
            
            # Paginate through results
            skip = 0
            while True:
                paginated_url = f"{files_url}&$top={self.batch_size}&$skip={skip}"
                response = self._make_api_request(paginated_url)
                
                if not response:
                    break
                
                data = response.json().get('d', {})
                results = data.get('results', [])
                
                if not results:
                    break
                
                for item in results:
                    doc_info = self._create_document_info_from_sharepoint_item(item, site_url, library_name)
                    if doc_info:
                        documents.append(doc_info)
                
                skip += self.batch_size
                
                # Check if we have more results
                if len(results) < self.batch_size:
                    break
                    
        except Exception as e:
            logger.error(f"Error crawling document library {library_name}: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _create_document_info_from_sharepoint_item(self, item: Dict, site_url: str, library_name: str) -> Optional[DocumentInfo]:
        """Create DocumentInfo object from SharePoint list item."""
        try:
            file_info = item.get('File', {})
            
            if not file_info:
                return None
            
            # Extract file information
            filename = file_info.get('Name', '')
            server_relative_url = file_info.get('ServerRelativeUrl', '')
            file_size = file_info.get('Length', 0)
            
            # Get file extension
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Skip if not a valid file
            if not filename or not self.is_valid_file_type(file_extension):
                return None
            
            # Create full URL
            full_url = f"{self.server_url}{server_relative_url}"
            
            # Get timestamps
            created_str = item.get('Created', '')
            modified_str = item.get('Modified', '')
            
            created_date = self._parse_sharepoint_date(created_str)
            modified_date = self._parse_sharepoint_date(modified_str)
            
            # Get additional metadata
            title = item.get('Title', filename)
            author = item.get('Author', {}).get('Title', 'Unknown')
            
            # Create DocumentInfo
            doc_info = DocumentInfo(
                filename=filename,
                path=full_url,
                size=file_size,
                file_extension=file_extension,
                mime_type=self._get_mime_type(file_extension),
                created_date=created_date,
                modified_date=modified_date,
                source_type='sharepoint_onprem',
                source_location=f"{site_url}/{library_name}",
                metadata={
                    'sharepoint_id': item.get('Id'),
                    'title': title,
                    'author': author,
                    'library': library_name,
                    'site_url': site_url,
                    'server_relative_url': server_relative_url
                }
            )
            
            return doc_info
            
        except Exception as e:
            logger.error(f"Error creating DocumentInfo from SharePoint item: {e}")
            return None
    
    def _get_subsites(self, site_url: str) -> List[str]:
        """Get list of subsites for a given site."""
        subsites = []
        
        try:
            subsites_url = f"{site_url}/_api/web/webs"
            response = self._make_api_request(subsites_url)
            
            if response:
                data = response.json().get('d', {})
                results = data.get('results', [])
                
                for subsite in results:
                    server_relative_url = subsite.get('ServerRelativeUrl', '')
                    if server_relative_url:
                        subsites.append(server_relative_url)
                        
        except Exception as e:
            logger.error(f"Error getting subsites for {site_url}: {e}")
        
        return subsites
    
    def _get_site_depth(self, site_path: str) -> int:
        """Calculate the depth of a site path."""
        return len([p for p in site_path.split('/') if p])
    
    def _parse_sharepoint_date(self, date_str: str) -> Optional[datetime]:
        """Parse SharePoint date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # SharePoint typically returns ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except Exception:
            logger.warning(f"Could not parse date: {date_str}")
            return None
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type for file extension."""
        mime_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.htm': 'text/html',
            '.xml': 'application/xml',
            '.json': 'application/json'
        }
        
        return mime_types.get(file_extension.lower(), 'application/octet-stream')
    
    def download_document_content(self, doc_info: DocumentInfo) -> Optional[bytes]:
        """Download document content from SharePoint."""
        try:
            response = self.session.get(doc_info.path)
            
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Failed to download document: {doc_info.path} (Status: {response.status_code})")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document {doc_info.path}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crawler statistics."""
        return {
            **self.stats,
            'server_url': self.server_url,
            'auth_method': self.auth_method,
            'site_collections_configured': len(self.site_collections),
            'document_libraries_configured': len(self.document_libraries)
        }
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate SharePoint configuration."""
        errors = []
        
        if not self.server_url:
            errors.append("SharePoint server URL is required")
        
        if not self.username:
            errors.append("Username is required")
        
        if not self.password:
            errors.append("Password is required")
        
        if self.auth_method not in ['ntlm', 'basic', 'kerberos']:
            errors.append(f"Invalid authentication method: {self.auth_method}")
        
        if not self.site_collections:
            errors.append("At least one site collection must be configured")
        
        if not self.document_libraries:
            errors.append("At least one document library must be configured")
        
        return len(errors) == 0, errors
    
    def __del__(self):
        """Cleanup session on destruction."""
        if self.session:
            self.session.close()

