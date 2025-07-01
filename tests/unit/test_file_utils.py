"""
Unit tests for file utilities
"""

import pytest
import os
import tempfile
from pathlib import Path

from src.docrecon_ai.utils.file_utils import FileUtils


class TestFileUtils:
    """Test cases for FileUtils class"""
    
    def test_is_valid_file_existing_file(self, sample_test_files):
        """Test validation of existing files"""
        test_file = list(sample_test_files.values())[0]
        assert FileUtils.is_valid_file(test_file) is True
    
    def test_is_valid_file_nonexistent_file(self):
        """Test validation of non-existent files"""
        assert FileUtils.is_valid_file("/nonexistent/file.txt") is False
    
    def test_is_valid_file_system_files(self, temp_dir):
        """Test that system files are rejected"""
        system_files = ['thumbs.db', 'desktop.ini', '.ds_store']
        
        for filename in system_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test")
            
            assert FileUtils.is_valid_file(file_path) is False
    
    def test_is_valid_file_temp_files(self, temp_dir):
        """Test that temporary files are rejected"""
        temp_files = ['~$document.docx', 'file.tmp', 'backup.bak']
        
        for filename in temp_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test")
            
            assert FileUtils.is_valid_file(file_path) is False
    
    def test_is_valid_file_empty_file(self, temp_dir):
        """Test that empty files are rejected"""
        empty_file = os.path.join(temp_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        assert FileUtils.is_valid_file(empty_file) is False
    
    def test_get_file_metadata(self, sample_test_files):
        """Test file metadata extraction"""
        test_file = sample_test_files['test1.txt']
        metadata = FileUtils.get_file_metadata(test_file)
        
        assert metadata['filename'] == 'test1.txt'
        assert metadata['file_extension'] == '.txt'
        assert metadata['size'] > 0
        assert metadata['size_mb'] >= 0
        assert 'created_date' in metadata
        assert 'modified_date' in metadata
        assert metadata['file_category'] == 'other'  # .txt is not in document categories
    
    def test_get_file_category(self):
        """Test file categorization"""
        assert FileUtils.get_file_category('.pdf') == 'document'
        assert FileUtils.get_file_category('.docx') == 'document'
        assert FileUtils.get_file_category('.xlsx') == 'spreadsheet'
        assert FileUtils.get_file_category('.pptx') == 'presentation'
        assert FileUtils.get_file_category('.jpg') == 'image'
        assert FileUtils.get_file_category('.zip') == 'archive'
        assert FileUtils.get_file_category('.unknown') == 'other'
    
    def test_is_text_file(self):
        """Test text file detection"""
        assert FileUtils.is_text_file('document.txt') is True
        assert FileUtils.is_text_file('document.pdf') is True  # PDF contains extractable text
        assert FileUtils.is_text_file('document.docx') is True
        assert FileUtils.is_text_file('script.py') is True
        assert FileUtils.is_text_file('image.jpg') is False
        assert FileUtils.is_text_file('archive.zip') is False
    
    def test_safe_read_text(self, sample_test_files):
        """Test safe text reading"""
        test_file = sample_test_files['test1.txt']
        content = FileUtils.safe_read_text(test_file)
        
        assert content is not None
        assert "This is test file 1 content." in content
    
    def test_safe_read_text_nonexistent(self):
        """Test safe text reading with non-existent file"""
        content = FileUtils.safe_read_text("/nonexistent/file.txt")
        assert content is None
    
    def test_get_directory_size(self, temp_dir):
        """Test directory size calculation"""
        size = FileUtils.get_directory_size(temp_dir)
        assert size >= 0
    
    def test_find_files_by_pattern(self, temp_dir):
        """Test file pattern matching"""
        # Create test files
        test_files = ['test1.txt', 'test2.txt', 'document.pdf']
        for filename in test_files:
            with open(os.path.join(temp_dir, filename), 'w') as f:
                f.write("test content")
        
        # Find .txt files
        txt_files = FileUtils.find_files_by_pattern(temp_dir, "*.txt", recursive=False)
        assert len(txt_files) == 2
        assert all(f.endswith('.txt') for f in txt_files)
        
        # Find all files
        all_files = FileUtils.find_files_by_pattern(temp_dir, "*", recursive=False)
        assert len(all_files) >= 3
    
    def test_normalize_path(self):
        """Test path normalization"""
        # Test with different path separators
        windows_path = "C:\\Users\\test\\document.txt"
        unix_path = "/home/test/document.txt"
        
        normalized_windows = FileUtils.normalize_path(windows_path)
        normalized_unix = FileUtils.normalize_path(unix_path)
        
        # Should use forward slashes
        assert '\\' not in normalized_windows or os.name == 'nt'
        assert '\\' not in normalized_unix
    
    def test_is_duplicate_filename(self):
        """Test duplicate filename detection"""
        # Exact matches
        assert FileUtils.is_duplicate_filename("document.txt", "document.txt") is True
        
        # Copy patterns
        assert FileUtils.is_duplicate_filename("document.txt", "document - copy.txt") is True
        assert FileUtils.is_duplicate_filename("document.txt", "document (copy).txt") is True
        assert FileUtils.is_duplicate_filename("document.txt", "document_copy.txt") is True
        assert FileUtils.is_duplicate_filename("document.txt", "document (1).txt") is True
        
        # Version patterns
        assert FileUtils.is_duplicate_filename("document.txt", "document_final.txt") is True
        assert FileUtils.is_duplicate_filename("document.txt", "document_backup.txt") is True
        
        # Different files
        assert FileUtils.is_duplicate_filename("document1.txt", "document2.txt") is False
        assert FileUtils.is_duplicate_filename("report.pdf", "presentation.pptx") is False
    
    def test_format_file_size(self):
        """Test file size formatting"""
        assert FileUtils.format_file_size(0) == "0 B"
        assert FileUtils.format_file_size(512) == "512.0 B"
        assert FileUtils.format_file_size(1024) == "1.0 KB"
        assert FileUtils.format_file_size(1024 * 1024) == "1.0 MB"
        assert FileUtils.format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert FileUtils.format_file_size(1536) == "1.5 KB"  # 1.5 KB


@pytest.mark.integration
class TestFileUtilsIntegration:
    """Integration tests for FileUtils with real file system"""
    
    def test_full_file_analysis_workflow(self, mock_file_system):
        """Test complete file analysis workflow"""
        # Find all files
        all_files = FileUtils.find_files_by_pattern(mock_file_system, "*", recursive=True)
        
        # Filter valid files
        valid_files = [f for f in all_files if FileUtils.is_valid_file(f)]
        assert len(valid_files) > 0
        
        # Get metadata for each file
        metadata_list = []
        for file_path in valid_files:
            metadata = FileUtils.get_file_metadata(file_path)
            if metadata:
                metadata_list.append(metadata)
        
        assert len(metadata_list) > 0
        
        # Check that we have different file categories
        categories = {meta['file_category'] for meta in metadata_list}
        assert len(categories) > 1  # Should have multiple categories
        
        # Check for potential duplicates by filename
        filenames = [meta['filename'] for meta in metadata_list]
        duplicate_pairs = []
        
        for i, name1 in enumerate(filenames):
            for name2 in filenames[i+1:]:
                if FileUtils.is_duplicate_filename(name1, name2):
                    duplicate_pairs.append((name1, name2))
        
        # Should find some duplicate patterns in our mock file system
        assert len(duplicate_pairs) > 0

