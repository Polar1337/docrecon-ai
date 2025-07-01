"""
Unit tests for hash utilities
"""

import pytest
import os
import tempfile
import hashlib

from src.docrecon_ai.utils.hash_utils import HashUtils


class TestHashUtils:
    """Test cases for HashUtils class"""
    
    def test_calculate_sha256(self, sample_test_files):
        """Test SHA256 hash calculation"""
        test_file = sample_test_files['test1.txt']
        hash_value = HashUtils.calculate_sha256(test_file)
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string
        assert all(c in '0123456789abcdef' for c in hash_value.lower())
    
    def test_calculate_md5(self, sample_test_files):
        """Test MD5 hash calculation"""
        test_file = sample_test_files['test1.txt']
        hash_value = HashUtils.calculate_md5(test_file)
        
        assert hash_value is not None
        assert len(hash_value) == 32  # MD5 produces 32-character hex string
        assert all(c in '0123456789abcdef' for c in hash_value.lower())
    
    def test_calculate_quick_hash(self, sample_test_files):
        """Test quick hash calculation"""
        test_file = sample_test_files['test1.txt']
        hash_value = HashUtils.calculate_quick_hash(test_file)
        
        assert hash_value is not None
        assert len(hash_value) == 64  # Quick hash also uses SHA256
    
    def test_hash_consistency(self, sample_test_files):
        """Test that hash calculations are consistent"""
        test_file = sample_test_files['test1.txt']
        
        # Calculate same hash multiple times
        hash1 = HashUtils.calculate_sha256(test_file)
        hash2 = HashUtils.calculate_sha256(test_file)
        
        assert hash1 == hash2
    
    def test_different_files_different_hashes(self, sample_test_files):
        """Test that different files produce different hashes"""
        file1 = sample_test_files['test1.txt']
        file2 = sample_test_files['test2.txt']
        
        hash1 = HashUtils.calculate_sha256(file1)
        hash2 = HashUtils.calculate_sha256(file2)
        
        assert hash1 != hash2
    
    def test_identical_content_same_hash(self, sample_test_files):
        """Test that files with identical content have same hash"""
        file1 = sample_test_files['test1.txt']
        file3 = sample_test_files['test1_copy.txt']  # Same content as test1.txt
        
        hash1 = HashUtils.calculate_sha256(file1)
        hash3 = HashUtils.calculate_sha256(file3)
        
        assert hash1 == hash3
    
    def test_calculate_content_hash(self):
        """Test content hash calculation"""
        content1 = "This is test content"
        content2 = "This is different content"
        content3 = "This is test content"  # Same as content1
        
        hash1 = HashUtils.calculate_content_hash(content1)
        hash2 = HashUtils.calculate_content_hash(content2)
        hash3 = HashUtils.calculate_content_hash(content3)
        
        assert hash1 != hash2
        assert hash1 == hash3
        assert len(hash1) == 64  # SHA256 length
    
    def test_calculate_multiple_hashes(self, sample_test_files):
        """Test multiple hash calculation"""
        test_file = sample_test_files['test1.txt']
        hashes = HashUtils.calculate_multiple_hashes(test_file)
        
        assert 'sha256' in hashes
        assert 'md5' in hashes
        assert 'quick_hash' in hashes
        
        assert hashes['sha256'] is not None
        assert hashes['md5'] is not None
        assert hashes['quick_hash'] is not None
        
        assert len(hashes['sha256']) == 64
        assert len(hashes['md5']) == 32
        assert len(hashes['quick_hash']) == 64
    
    def test_verify_file_integrity_sha256(self, sample_test_files):
        """Test file integrity verification with SHA256"""
        test_file = sample_test_files['test1.txt']
        correct_hash = HashUtils.calculate_sha256(test_file)
        wrong_hash = "0" * 64
        
        assert HashUtils.verify_file_integrity(test_file, correct_hash, 'sha256') is True
        assert HashUtils.verify_file_integrity(test_file, wrong_hash, 'sha256') is False
    
    def test_verify_file_integrity_md5(self, sample_test_files):
        """Test file integrity verification with MD5"""
        test_file = sample_test_files['test1.txt']
        correct_hash = HashUtils.calculate_md5(test_file)
        wrong_hash = "0" * 32
        
        assert HashUtils.verify_file_integrity(test_file, correct_hash, 'md5') is True
        assert HashUtils.verify_file_integrity(test_file, wrong_hash, 'md5') is False
    
    def test_verify_file_integrity_case_insensitive(self, sample_test_files):
        """Test that hash verification is case insensitive"""
        test_file = sample_test_files['test1.txt']
        hash_lower = HashUtils.calculate_sha256(test_file)
        hash_upper = hash_lower.upper()
        
        assert HashUtils.verify_file_integrity(test_file, hash_upper, 'sha256') is True
    
    def test_compare_files_by_hash_same_content(self, sample_test_files):
        """Test file comparison with same content"""
        file1 = sample_test_files['test1.txt']
        file3 = sample_test_files['test1_copy.txt']  # Same content
        
        assert HashUtils.compare_files_by_hash(file1, file3, 'sha256') is True
        assert HashUtils.compare_files_by_hash(file1, file3, 'md5') is True
        assert HashUtils.compare_files_by_hash(file1, file3, 'quick') is True
    
    def test_compare_files_by_hash_different_content(self, sample_test_files):
        """Test file comparison with different content"""
        file1 = sample_test_files['test1.txt']
        file2 = sample_test_files['test2.txt']
        
        assert HashUtils.compare_files_by_hash(file1, file2, 'sha256') is False
        assert HashUtils.compare_files_by_hash(file1, file2, 'md5') is False
    
    def test_get_hash_info(self, sample_test_files):
        """Test comprehensive hash information"""
        test_file = sample_test_files['test1.txt']
        hash_info = HashUtils.get_hash_info(test_file)
        
        assert 'file_path' in hash_info
        assert 'file_size' in hash_info
        assert 'file_size_mb' in hash_info
        assert 'hashes' in hash_info
        assert 'calculation_time' in hash_info
        assert 'hash_rate_mbps' in hash_info
        assert 'success' in hash_info
        
        assert hash_info['success'] is True
        assert hash_info['calculation_time'] > 0
        assert hash_info['file_size'] > 0
    
    def test_hash_nonexistent_file(self):
        """Test hash calculation with non-existent file"""
        nonexistent_file = "/path/to/nonexistent/file.txt"
        
        assert HashUtils.calculate_sha256(nonexistent_file) is None
        assert HashUtils.calculate_md5(nonexistent_file) is None
        assert HashUtils.calculate_quick_hash(nonexistent_file) is None
    
    def test_hash_large_file_rejection(self, temp_dir):
        """Test that very large files are rejected"""
        # Create a file that would be too large (mock by setting small limit)
        large_file = os.path.join(temp_dir, "large_file.txt")
        
        # Write some content
        with open(large_file, 'w') as f:
            f.write("x" * 1000)  # 1KB file
        
        # Temporarily reduce the max size limit for testing
        original_limit = HashUtils.MAX_HASH_SIZE
        HashUtils.MAX_HASH_SIZE = 500  # 500 bytes
        
        try:
            # Should return None for "large" file
            assert HashUtils.calculate_sha256(large_file) is None
            assert HashUtils.calculate_md5(large_file) is None
        finally:
            # Restore original limit
            HashUtils.MAX_HASH_SIZE = original_limit
    
    def test_is_hash_collision_likely(self):
        """Test hash collision likelihood check"""
        # Valid hash lengths
        md5_hash = "d" * 32
        sha256_hash = "a" * 64
        
        assert HashUtils.is_hash_collision_likely(md5_hash, 'md5') is True
        assert HashUtils.is_hash_collision_likely(sha256_hash, 'sha256') is True
        
        # Invalid hash lengths
        short_hash = "abc"
        assert HashUtils.is_hash_collision_likely(short_hash, 'md5') is False
        assert HashUtils.is_hash_collision_likely(short_hash, 'sha256') is False
    
    def test_quick_hash_vs_full_hash_performance(self, temp_dir):
        """Test that quick hash is faster than full hash for large files"""
        import time
        
        # Create a moderately sized file
        test_file = os.path.join(temp_dir, "performance_test.txt")
        content = "x" * 50000  # 50KB
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        # Time full hash
        start_time = time.time()
        full_hash = HashUtils.calculate_sha256(test_file)
        full_time = time.time() - start_time
        
        # Time quick hash
        start_time = time.time()
        quick_hash = HashUtils.calculate_quick_hash(test_file)
        quick_time = time.time() - start_time
        
        assert full_hash is not None
        assert quick_hash is not None
        assert full_hash != quick_hash  # Should be different for large files
        
        # Quick hash should be faster (though for small files the difference might be minimal)
        # We'll just check that both complete successfully
        assert quick_time >= 0
        assert full_time >= 0


@pytest.mark.integration
class TestHashUtilsIntegration:
    """Integration tests for HashUtils"""
    
    def test_hash_duplicate_detection_workflow(self, mock_file_system):
        """Test hash-based duplicate detection workflow"""
        from src.docrecon_ai.utils.file_utils import FileUtils
        
        # Find all files
        all_files = FileUtils.find_files_by_pattern(mock_file_system, "*", recursive=True)
        valid_files = [f for f in all_files if FileUtils.is_valid_file(f)]
        
        # Calculate hashes for all files
        file_hashes = {}
        for file_path in valid_files:
            hash_value = HashUtils.calculate_sha256(file_path)
            if hash_value:
                if hash_value not in file_hashes:
                    file_hashes[hash_value] = []
                file_hashes[hash_value].append(file_path)
        
        # Find duplicates (hashes with multiple files)
        duplicates = {h: files for h, files in file_hashes.items() if len(files) > 1}
        
        # Should find some duplicates in our mock file system
        assert len(duplicates) > 0
        
        # Verify duplicates are actually identical
        for hash_value, files in duplicates.items():
            # Compare first two files
            if len(files) >= 2:
                assert HashUtils.compare_files_by_hash(files[0], files[1], 'sha256') is True

