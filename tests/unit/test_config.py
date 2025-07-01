"""
Unit tests for configuration management
"""

import pytest
import os
import tempfile
import yaml

from src.docrecon_ai.config import DocReconConfig


class TestDocReconConfig:
    """Test cases for DocReconConfig class"""
    
    def test_default_config_creation(self):
        """Test creation with default configuration"""
        config = DocReconConfig()
        
        # Check that default values are set
        assert config.get('crawler.max_file_size_mb') > 0
        assert config.get('nlp.similarity_threshold') > 0
        assert config.get('detection.hash_algorithm') is not None
        assert isinstance(config.get('reporting.output_formats'), list)
    
    def test_config_from_file(self, mock_config_file):
        """Test configuration loading from file"""
        config = DocReconConfig(mock_config_file)
        
        # Check loaded values
        assert config.get('crawler.max_file_size_mb') == 50
        assert config.get('nlp.embedding_model') == "all-MiniLM-L6-v2"
        assert config.get('detection.hash_algorithm') == "sha256"
        assert 'html' in config.get('reporting.output_formats')
    
    def test_config_get_with_default(self, sample_config):
        """Test getting configuration values with defaults"""
        # Existing key
        value = sample_config.get('crawler.max_file_size_mb')
        assert value is not None
        
        # Non-existing key with default
        value = sample_config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
        
        # Non-existing key without default
        value = sample_config.get('nonexistent.key')
        assert value is None
    
    def test_config_set_value(self, sample_config):
        """Test setting configuration values"""
        # Set new value
        sample_config.set('test.new_key', 'test_value')
        assert sample_config.get('test.new_key') == 'test_value'
        
        # Override existing value
        original_value = sample_config.get('crawler.max_file_size_mb')
        sample_config.set('crawler.max_file_size_mb', 200)
        assert sample_config.get('crawler.max_file_size_mb') == 200
        assert sample_config.get('crawler.max_file_size_mb') != original_value
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = DocReconConfig()
        
        # Valid configuration should pass
        assert config.validate() is True
        
        # Test with invalid values
        config.set('crawler.max_file_size_mb', -1)  # Negative value
        assert config.validate() is False
        
        config.set('crawler.max_file_size_mb', 100)  # Fix it
        config.set('nlp.similarity_threshold', 2.0)  # Value > 1
        assert config.validate() is False
    
    def test_config_to_dict(self, sample_config):
        """Test configuration export to dictionary"""
        config_dict = sample_config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'crawler' in config_dict
        assert 'nlp' in config_dict
        assert 'detection' in config_dict
        assert 'reporting' in config_dict
    
    def test_config_save_and_load(self, temp_dir, sample_config):
        """Test saving and loading configuration"""
        config_file = os.path.join(temp_dir, 'test_save_config.yaml')
        
        # Save configuration
        sample_config.save(config_file)
        assert os.path.exists(config_file)
        
        # Load saved configuration
        loaded_config = DocReconConfig(config_file)
        
        # Compare key values
        assert loaded_config.get('crawler.max_file_size_mb') == sample_config.get('crawler.max_file_size_mb')
        assert loaded_config.get('nlp.embedding_model') == sample_config.get('nlp.embedding_model')
    
    def test_config_merge(self, temp_dir):
        """Test configuration merging"""
        # Create base config
        base_config = {
            'crawler': {'max_file_size_mb': 100},
            'nlp': {'enable_embeddings': True}
        }
        
        # Create override config
        override_config = {
            'crawler': {'max_file_size_mb': 200},  # Override
            'detection': {'hash_algorithm': 'md5'}  # New section
        }
        
        # Save configs to files
        base_file = os.path.join(temp_dir, 'base.yaml')
        override_file = os.path.join(temp_dir, 'override.yaml')
        
        with open(base_file, 'w') as f:
            yaml.dump(base_config, f)
        
        with open(override_file, 'w') as f:
            yaml.dump(override_config, f)
        
        # Load and merge
        config = DocReconConfig(base_file)
        config.merge_from_file(override_file)
        
        # Check merged values
        assert config.get('crawler.max_file_size_mb') == 200  # Overridden
        assert config.get('nlp.enable_embeddings') is True  # Preserved
        assert config.get('detection.hash_algorithm') == 'md5'  # Added
    
    def test_config_environment_variables(self):
        """Test configuration from environment variables"""
        # Set environment variable
        os.environ['DOCRECON_CRAWLER_MAX_FILE_SIZE_MB'] = '150'
        
        try:
            config = DocReconConfig()
            config.load_from_environment()
            
            # Should use environment value
            assert config.get('crawler.max_file_size_mb') == 150
        finally:
            # Clean up
            if 'DOCRECON_CRAWLER_MAX_FILE_SIZE_MB' in os.environ:
                del os.environ['DOCRECON_CRAWLER_MAX_FILE_SIZE_MB']
    
    def test_config_invalid_file(self):
        """Test handling of invalid configuration file"""
        with pytest.raises(Exception):
            DocReconConfig('/nonexistent/config.yaml')
    
    def test_config_malformed_yaml(self, temp_dir):
        """Test handling of malformed YAML file"""
        malformed_file = os.path.join(temp_dir, 'malformed.yaml')
        
        with open(malformed_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(Exception):
            DocReconConfig(malformed_file)
    
    def test_config_get_nested_dict(self, sample_config):
        """Test getting nested configuration sections"""
        crawler_config = sample_config.get_section('crawler')
        assert isinstance(crawler_config, dict)
        assert 'max_file_size_mb' in crawler_config
        
        nlp_config = sample_config.get_section('nlp')
        assert isinstance(nlp_config, dict)
        assert 'enable_embeddings' in nlp_config
    
    def test_config_update_section(self, sample_config):
        """Test updating entire configuration section"""
        new_crawler_config = {
            'max_file_size_mb': 500,
            'include_hidden_files': True,
            'new_setting': 'test_value'
        }
        
        sample_config.update_section('crawler', new_crawler_config)
        
        assert sample_config.get('crawler.max_file_size_mb') == 500
        assert sample_config.get('crawler.include_hidden_files') is True
        assert sample_config.get('crawler.new_setting') == 'test_value'
    
    def test_config_has_key(self, sample_config):
        """Test checking for key existence"""
        assert sample_config.has('crawler.max_file_size_mb') is True
        assert sample_config.has('nonexistent.key') is False
        assert sample_config.has('crawler') is True  # Section exists
    
    def test_config_remove_key(self, sample_config):
        """Test removing configuration keys"""
        # Add a test key
        sample_config.set('test.removable_key', 'test_value')
        assert sample_config.has('test.removable_key') is True
        
        # Remove it
        sample_config.remove('test.removable_key')
        assert sample_config.has('test.removable_key') is False
    
    def test_config_list_keys(self, sample_config):
        """Test listing configuration keys"""
        all_keys = sample_config.list_keys()
        assert isinstance(all_keys, list)
        assert len(all_keys) > 0
        
        # Check for expected keys
        expected_keys = [
            'crawler.max_file_size_mb',
            'nlp.enable_embeddings',
            'detection.hash_algorithm',
            'reporting.output_formats'
        ]
        
        for key in expected_keys:
            assert any(key in k for k in all_keys)
    
    def test_config_copy(self, sample_config):
        """Test configuration copying"""
        config_copy = sample_config.copy()
        
        # Should be independent copies
        assert config_copy is not sample_config
        
        # But with same values
        assert config_copy.get('crawler.max_file_size_mb') == sample_config.get('crawler.max_file_size_mb')
        
        # Modifying copy shouldn't affect original
        config_copy.set('test.copy_key', 'copy_value')
        assert sample_config.has('test.copy_key') is False
        assert config_copy.has('test.copy_key') is True


@pytest.mark.integration
class TestDocReconConfigIntegration:
    """Integration tests for configuration management"""
    
    def test_config_with_real_application(self, temp_dir):
        """Test configuration in realistic application scenario"""
        # Create a comprehensive config file
        config_data = {
            'crawler': {
                'max_file_size_mb': 100,
                'include_hidden_files': False,
                'file_extensions': ['.pdf', '.docx', '.txt', '.xlsx', '.pptx'],
                'exclude_patterns': ['*.tmp', '~$*', '.git/*'],
                'max_depth': 10,
                'follow_symlinks': False
            },
            'nlp': {
                'enable_embeddings': True,
                'embedding_model': 'all-MiniLM-L6-v2',
                'similarity_threshold': 0.8,
                'max_text_length': 50000,
                'language': 'auto',
                'enable_entities': True,
                'enable_keywords': True,
                'enable_clustering': True
            },
            'detection': {
                'hash_algorithm': 'sha256',
                'enable_quick_hash': True,
                'similarity_threshold': 0.9,
                'version_patterns': [
                    r'v\d+',
                    r'version\d+',
                    r'copy',
                    r'final',
                    r'backup',
                    r'\(\d+\)'
                ],
                'min_file_size': 1024
            },
            'reporting': {
                'output_formats': ['html', 'csv', 'json'],
                'include_charts': True,
                'max_items_per_table': 1000,
                'chart_theme': 'modern',
                'export_full_paths': True
            },
            'dashboard': {
                'enable_dashboard': True,
                'default_port': 8501,
                'auto_refresh': True,
                'max_display_items': 100
            },
            'performance': {
                'max_workers': 4,
                'chunk_size': 1000,
                'memory_limit_mb': 2048,
                'enable_caching': True,
                'cache_ttl_hours': 24
            }
        }
        
        config_file = os.path.join(temp_dir, 'comprehensive_config.yaml')
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration
        config = DocReconConfig(config_file)
        
        # Validate all sections are loaded correctly
        assert config.validate() is True
        
        # Test accessing various configuration values
        assert config.get('crawler.max_file_size_mb') == 100
        assert len(config.get('crawler.file_extensions')) == 5
        assert config.get('nlp.embedding_model') == 'all-MiniLM-L6-v2'
        assert config.get('detection.hash_algorithm') == 'sha256'
        assert 'html' in config.get('reporting.output_formats')
        assert config.get('dashboard.default_port') == 8501
        assert config.get('performance.max_workers') == 4
        
        # Test configuration sections
        crawler_section = config.get_section('crawler')
        assert len(crawler_section) == 6
        
        nlp_section = config.get_section('nlp')
        assert nlp_section['enable_embeddings'] is True
        
        # Test configuration modification
        config.set('performance.max_workers', 8)
        assert config.get('performance.max_workers') == 8
        
        # Test saving modified configuration
        modified_config_file = os.path.join(temp_dir, 'modified_config.yaml')
        config.save(modified_config_file)
        
        # Load modified configuration and verify
        modified_config = DocReconConfig(modified_config_file)
        assert modified_config.get('performance.max_workers') == 8
        assert modified_config.get('crawler.max_file_size_mb') == 100  # Unchanged

