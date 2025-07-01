"""
OneNote Crawler

Specialized crawler for OneNote documents with support for:
- OneNote files stored in SharePoint
- Local OneNote installations via COM interface
- OneNote section and page extraction
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import xml.etree.ElementTree as ET
import zipfile
import tempfile
import platform

from .base import BaseCrawler, DocumentInfo


logger = logging.getLogger(__name__)


class OneNoteCrawler(BaseCrawler):
    """
    Crawler for OneNote documents with multiple access methods.
    
    Supports both SharePoint-stored OneNote files and local OneNote installations.
    """
    
    def __init__(self, config):
        super().__init__(config)
        
        # OneNote configuration
        self.access_method = config.get('crawler.onenote.access_method', 'sharepoint').lower()
        self.include_sections = config.get('crawler.onenote.include_sections', True)
        self.include_pages = config.get('crawler.onenote.include_pages', True)
        self.extract_text = config.get('crawler.onenote.extract_text', True)
        self.extract_images = config.get('crawler.onenote.extract_images', False)
        
        # SharePoint integration (if using SharePoint method)
        self.sharepoint_crawler = None
        if self.access_method == 'sharepoint':
            from .sharepoint_onprem import SharePointOnPremCrawler
            self.sharepoint_crawler = SharePointOnPremCrawler(config)
        
        # COM interface (if using local method on Windows)
        self.onenote_app = None
        if self.access_method == 'local_com' and platform.system() == 'Windows':
            self._initialize_com_interface()
        
        # File extensions to look for
        self.onenote_extensions = ['.one', '.onetoc2', '.onepkg']
        
        # Statistics
        self.stats = {
            'notebooks_found': 0,
            'sections_found': 0,
            'pages_found': 0,
            'documents_processed': 0,
            'errors_encountered': 0
        }
    
    def _initialize_com_interface(self):
        """Initialize OneNote COM interface for local access."""
        try:
            import win32com.client
            self.onenote_app = win32com.client.Dispatch("OneNote.Application")
            logger.info("OneNote COM interface initialized successfully")
        except ImportError:
            logger.error("pywin32 package required for OneNote COM interface. Install with: pip install pywin32")
            self.onenote_app = None
        except Exception as e:
            logger.error(f"Failed to initialize OneNote COM interface: {e}")
            self.onenote_app = None
    
    def crawl_path(self, path: str) -> List[DocumentInfo]:
        """
        Crawl OneNote documents from specified path.
        
        Args:
            path: Path to crawl (SharePoint site or local directory)
            
        Returns:
            List of DocumentInfo objects
        """
        documents = []
        
        try:
            if self.access_method == 'sharepoint':
                documents = self._crawl_sharepoint_onenote(path)
            elif self.access_method == 'local_com':
                documents = self._crawl_local_onenote_com()
            elif self.access_method == 'local_files':
                documents = self._crawl_local_onenote_files(path)
            else:
                logger.error(f"Unsupported OneNote access method: {self.access_method}")
                
        except Exception as e:
            logger.error(f"Error crawling OneNote documents: {e}")
            self.stats['errors_encountered'] += 1
        
        self.stats['documents_processed'] = len(documents)
        logger.info(f"OneNote crawl completed. Found {len(documents)} documents.")
        
        return documents
    
    def _crawl_sharepoint_onenote(self, site_path: str) -> List[DocumentInfo]:
        """Crawl OneNote files stored in SharePoint."""
        documents = []
        
        if not self.sharepoint_crawler:
            logger.error("SharePoint crawler not initialized")
            return documents
        
        try:
            # Get all documents from SharePoint
            all_documents = self.sharepoint_crawler.crawl_path(site_path)
            
            # Filter for OneNote files
            onenote_documents = [
                doc for doc in all_documents 
                if doc.file_extension.lower() in self.onenote_extensions
            ]
            
            logger.info(f"Found {len(onenote_documents)} OneNote files in SharePoint")
            
            # Process each OneNote file
            for doc in onenote_documents:
                processed_docs = self._process_onenote_file(doc)
                documents.extend(processed_docs)
                
                if doc.file_extension.lower() == '.one':
                    self.stats['notebooks_found'] += 1
                elif doc.file_extension.lower() == '.onetoc2':
                    self.stats['sections_found'] += 1
                    
        except Exception as e:
            logger.error(f"Error crawling SharePoint OneNote files: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _crawl_local_onenote_com(self) -> List[DocumentInfo]:
        """Crawl OneNote using local COM interface."""
        documents = []
        
        if not self.onenote_app:
            logger.error("OneNote COM interface not available")
            return documents
        
        try:
            # Get hierarchy of all notebooks
            hierarchy_xml = self.onenote_app.GetHierarchy("", 4)  # hsNotebooks = 4
            
            # Parse XML hierarchy
            root = ET.fromstring(hierarchy_xml)
            
            # Process each notebook
            for notebook in root.findall('.//{http://schemas.microsoft.com/office/onenote/2013/onenote}Notebook'):
                notebook_docs = self._process_notebook_com(notebook)
                documents.extend(notebook_docs)
                self.stats['notebooks_found'] += 1
                
        except Exception as e:
            logger.error(f"Error crawling OneNote via COM: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _crawl_local_onenote_files(self, directory: str) -> List[DocumentInfo]:
        """Crawl OneNote files from local directory."""
        documents = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in self.onenote_extensions:
                        doc_info = self._create_document_info_from_file(file_path)
                        if doc_info:
                            processed_docs = self._process_onenote_file(doc_info)
                            documents.extend(processed_docs)
                            
                            if file_ext == '.one':
                                self.stats['notebooks_found'] += 1
                            elif file_ext == '.onetoc2':
                                self.stats['sections_found'] += 1
                                
        except Exception as e:
            logger.error(f"Error crawling local OneNote files: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _process_notebook_com(self, notebook_element) -> List[DocumentInfo]:
        """Process a notebook using COM interface."""
        documents = []
        
        try:
            notebook_name = notebook_element.get('name', 'Unknown Notebook')
            notebook_id = notebook_element.get('ID', '')
            notebook_path = notebook_element.get('path', '')
            
            logger.info(f"Processing notebook: {notebook_name}")
            
            # Create notebook document info
            notebook_doc = DocumentInfo(
                filename=f"{notebook_name}.notebook",
                path=notebook_path,
                size=0,  # Will be calculated if needed
                file_extension='.notebook',
                mime_type='application/onenote',
                source_type='onenote_local',
                source_location=notebook_path,
                metadata={
                    'onenote_type': 'notebook',
                    'notebook_id': notebook_id,
                    'notebook_name': notebook_name
                }
            )
            
            documents.append(notebook_doc)
            
            # Process sections if enabled
            if self.include_sections:
                for section in notebook_element.findall('.//{http://schemas.microsoft.com/office/onenote/2013/onenote}Section'):
                    section_docs = self._process_section_com(section, notebook_name)
                    documents.extend(section_docs)
                    self.stats['sections_found'] += 1
                    
        except Exception as e:
            logger.error(f"Error processing notebook via COM: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _process_section_com(self, section_element, notebook_name: str) -> List[DocumentInfo]:
        """Process a section using COM interface."""
        documents = []
        
        try:
            section_name = section_element.get('name', 'Unknown Section')
            section_id = section_element.get('ID', '')
            section_path = section_element.get('path', '')
            
            logger.debug(f"Processing section: {section_name}")
            
            # Create section document info
            section_doc = DocumentInfo(
                filename=f"{section_name}.section",
                path=section_path,
                size=0,
                file_extension='.section',
                mime_type='application/onenote',
                source_type='onenote_local',
                source_location=section_path,
                metadata={
                    'onenote_type': 'section',
                    'section_id': section_id,
                    'section_name': section_name,
                    'notebook_name': notebook_name
                }
            )
            
            documents.append(section_doc)
            
            # Process pages if enabled
            if self.include_pages:
                for page in section_element.findall('.//{http://schemas.microsoft.com/office/onenote/2013/onenote}Page'):
                    page_doc = self._process_page_com(page, section_name, notebook_name)
                    if page_doc:
                        documents.append(page_doc)
                        self.stats['pages_found'] += 1
                        
        except Exception as e:
            logger.error(f"Error processing section via COM: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _process_page_com(self, page_element, section_name: str, notebook_name: str) -> Optional[DocumentInfo]:
        """Process a page using COM interface."""
        try:
            page_name = page_element.get('name', 'Unknown Page')
            page_id = page_element.get('ID', '')
            
            # Extract page content if enabled
            text_content = ""
            if self.extract_text and self.onenote_app:
                try:
                    page_xml = self.onenote_app.GetPageContent(page_id)
                    text_content = self._extract_text_from_page_xml(page_xml)
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_name}: {e}")
            
            # Get page metadata
            date_created = page_element.get('dateTime', '')
            last_modified = page_element.get('lastModifiedTime', '')
            
            created_date = self._parse_onenote_date(date_created)
            modified_date = self._parse_onenote_date(last_modified)
            
            page_doc = DocumentInfo(
                filename=f"{page_name}.page",
                path=f"onenote://{notebook_name}/{section_name}/{page_name}",
                size=len(text_content.encode('utf-8')) if text_content else 0,
                file_extension='.page',
                mime_type='application/onenote',
                created_date=created_date,
                modified_date=modified_date,
                source_type='onenote_local',
                text_content=text_content,
                text_length=len(text_content),
                metadata={
                    'onenote_type': 'page',
                    'page_id': page_id,
                    'page_name': page_name,
                    'section_name': section_name,
                    'notebook_name': notebook_name
                }
            )
            
            return page_doc
            
        except Exception as e:
            logger.error(f"Error processing page via COM: {e}")
            self.stats['errors_encountered'] += 1
            return None
    
    def _process_onenote_file(self, doc_info: DocumentInfo) -> List[DocumentInfo]:
        """Process a OneNote file (for SharePoint or local file access)."""
        documents = [doc_info]  # Include the original file
        
        try:
            if doc_info.file_extension.lower() == '.one':
                # This is a OneNote section file
                if self.extract_text:
                    text_content = self._extract_text_from_one_file(doc_info)
                    if text_content:
                        doc_info.text_content = text_content
                        doc_info.text_length = len(text_content)
                        
            elif doc_info.file_extension.lower() == '.onetoc2':
                # This is a OneNote table of contents file
                logger.debug(f"Processing OneNote TOC file: {doc_info.filename}")
                
            elif doc_info.file_extension.lower() == '.onepkg':
                # This is a OneNote package file
                if self.extract_text:
                    extracted_docs = self._extract_from_onepkg(doc_info)
                    documents.extend(extracted_docs)
                    
        except Exception as e:
            logger.error(f"Error processing OneNote file {doc_info.filename}: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _extract_text_from_one_file(self, doc_info: DocumentInfo) -> str:
        """Extract text content from a .one file."""
        try:
            # OneNote .one files are complex binary formats
            # For basic text extraction, we'll try to read readable strings
            
            if self.access_method == 'sharepoint' and self.sharepoint_crawler:
                # Download file content from SharePoint
                content = self.sharepoint_crawler.download_document_content(doc_info)
                if content:
                    return self._extract_readable_text_from_binary(content)
            elif os.path.exists(doc_info.path):
                # Read local file
                with open(doc_info.path, 'rb') as f:
                    content = f.read()
                    return self._extract_readable_text_from_binary(content)
                    
        except Exception as e:
            logger.error(f"Error extracting text from OneNote file: {e}")
        
        return ""
    
    def _extract_from_onepkg(self, doc_info: DocumentInfo) -> List[DocumentInfo]:
        """Extract content from OneNote package file."""
        documents = []
        
        try:
            # OneNote package files are ZIP archives
            temp_dir = tempfile.mkdtemp()
            
            try:
                if self.access_method == 'sharepoint' and self.sharepoint_crawler:
                    # Download and extract from SharePoint
                    content = self.sharepoint_crawler.download_document_content(doc_info)
                    if content:
                        temp_file = os.path.join(temp_dir, 'package.onepkg')
                        with open(temp_file, 'wb') as f:
                            f.write(content)
                        
                        with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                            
                elif os.path.exists(doc_info.path):
                    # Extract local file
                    with zipfile.ZipFile(doc_info.path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                
                # Process extracted files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.one'):
                            file_path = os.path.join(root, file)
                            extracted_doc = self._create_document_info_from_file(file_path)
                            if extracted_doc:
                                extracted_doc.metadata['parent_package'] = doc_info.filename
                                documents.append(extracted_doc)
                                
            finally:
                # Cleanup temp directory
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Error extracting OneNote package: {e}")
            self.stats['errors_encountered'] += 1
        
        return documents
    
    def _extract_readable_text_from_binary(self, content: bytes) -> str:
        """Extract readable text strings from binary content."""
        try:
            # Simple approach: extract printable ASCII/UTF-8 strings
            text_parts = []
            
            # Try UTF-8 decoding with error handling
            try:
                decoded = content.decode('utf-8', errors='ignore')
                # Extract words (sequences of printable characters)
                import re
                words = re.findall(r'[a-zA-Z0-9\s\.,;:!?\-]+', decoded)
                text_parts.extend([word.strip() for word in words if len(word.strip()) > 2])
            except:
                pass
            
            # Try UTF-16 decoding (common in Microsoft formats)
            try:
                decoded = content.decode('utf-16', errors='ignore')
                import re
                words = re.findall(r'[a-zA-Z0-9\s\.,;:!?\-]+', decoded)
                text_parts.extend([word.strip() for word in words if len(word.strip()) > 2])
            except:
                pass
            
            # Remove duplicates and join
            unique_text = list(dict.fromkeys(text_parts))  # Preserve order
            return ' '.join(unique_text)
            
        except Exception as e:
            logger.error(f"Error extracting readable text: {e}")
            return ""
    
    def _extract_text_from_page_xml(self, page_xml: str) -> str:
        """Extract text content from OneNote page XML."""
        try:
            root = ET.fromstring(page_xml)
            
            # Find all text elements
            text_elements = []
            
            # Look for common text containers in OneNote XML
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_elements.append(elem.text.strip())
            
            return ' '.join(text_elements)
            
        except Exception as e:
            logger.error(f"Error extracting text from page XML: {e}")
            return ""
    
    def _create_document_info_from_file(self, file_path: str) -> Optional[DocumentInfo]:
        """Create DocumentInfo from local OneNote file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            filename = os.path.basename(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            
            doc_info = DocumentInfo(
                filename=filename,
                path=file_path,
                size=stat.st_size,
                file_extension=file_extension,
                mime_type='application/onenote',
                created_date=datetime.fromtimestamp(stat.st_ctime),
                modified_date=datetime.fromtimestamp(stat.st_mtime),
                source_type='onenote_local',
                source_location=os.path.dirname(file_path)
            )
            
            return doc_info
            
        except Exception as e:
            logger.error(f"Error creating DocumentInfo from file {file_path}: {e}")
            return None
    
    def _parse_onenote_date(self, date_str: str) -> Optional[datetime]:
        """Parse OneNote date string."""
        if not date_str:
            return None
        
        try:
            # OneNote dates are typically in ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            logger.warning(f"Could not parse OneNote date: {date_str}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get crawler statistics."""
        return {
            **self.stats,
            'access_method': self.access_method,
            'com_interface_available': self.onenote_app is not None,
            'sharepoint_integration': self.sharepoint_crawler is not None
        }
    
    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate OneNote configuration."""
        errors = []
        
        if self.access_method not in ['sharepoint', 'local_com', 'local_files']:
            errors.append(f"Invalid OneNote access method: {self.access_method}")
        
        if self.access_method == 'local_com' and platform.system() != 'Windows':
            errors.append("OneNote COM interface is only available on Windows")
        
        if self.access_method == 'local_com' and not self.onenote_app:
            errors.append("OneNote COM interface could not be initialized")
        
        if self.access_method == 'sharepoint' and not self.sharepoint_crawler:
            errors.append("SharePoint crawler required for SharePoint OneNote access")
        
        return len(errors) == 0, errors

