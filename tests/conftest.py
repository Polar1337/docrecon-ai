"""
Pytest configuration and fixtures for DocRecon AI tests
"""

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
import json

from src.docrecon_ai.config import DocReconConfig
from src.docrecon_ai.crawler.base import DocumentInfo


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing"""
    config_data = {
        'crawler': {
            'max_file_size_mb': 100,
            'include_hidden_files': False,
            'file_extensions': ['.pdf', '.docx', '.txt'],
        },
        'nlp': {
            'enable_embeddings': True,
            'embedding_model': 'all-MiniLM-L6-v2',
            'similarity_threshold': 0.8,
        },
        'detection': {
            'hash_algorithm': 'sha256',
            'similarity_threshold': 0.9,
            'enable_quick_hash': True,
        },
        'reporting': {
            'output_formats': ['html', 'csv', 'json'],
            'include_charts': True,
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        config_path = f.name
    
    yield DocReconConfig(config_path)
    
    os.unlink(config_path)


@pytest.fixture
def sample_documents():
    """Create sample DocumentInfo objects for testing"""
    documents = [
        DocumentInfo(
            filename="document1.pdf",
            path="/test/path/document1.pdf",
            size=1024000,
            file_extension=".pdf",
            mime_type="application/pdf",
            sha256_hash="abc123def456",
            md5_hash="def456abc123",
            source_type="local",
            text_content="This is a sample document content.",
            text_length=35
        ),
        DocumentInfo(
            filename="document2.docx",
            path="/test/path/document2.docx",
            size=2048000,
            file_extension=".docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            sha256_hash="xyz789uvw012",
            md5_hash="uvw012xyz789",
            source_type="local",
            text_content="This is another sample document with different content.",
            text_length=54
        ),
        DocumentInfo(
            filename="document1_copy.pdf",
            path="/test/path/copy/document1_copy.pdf",
            size=1024000,
            file_extension=".pdf",
            mime_type="application/pdf",
            sha256_hash="abc123def456",  # Same hash as document1.pdf
            md5_hash="def456abc123",
            source_type="local",
            text_content="This is a sample document content.",
            text_length=35
        )
    ]
    return documents


@pytest.fixture
def sample_test_files(temp_dir):
    """Create sample test files in temporary directory"""
    files = {}
    
    # Create test files
    test_files = [
        ("test1.txt", "This is test file 1 content."),
        ("test2.txt", "This is test file 2 content."),
        ("test1_copy.txt", "This is test file 1 content."),  # Duplicate content
        ("test3.pdf", b"PDF content placeholder"),
        ("test4.docx", b"DOCX content placeholder"),
    ]
    
    for filename, content in test_files:
        file_path = os.path.join(temp_dir, filename)
        
        if isinstance(content, str):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            with open(file_path, 'wb') as f:
                f.write(content)
        
        files[filename] = file_path
    
    return files


@pytest.fixture
def sample_analysis_results():
    """Create sample analysis results for testing"""
    return {
        'metadata': {
            'analysis_timestamp': 1640995200.0,
            'analysis_duration': 45.5,
            'tool_version': '1.0.0',
            'total_documents': 3,
        },
        'statistics': {
            'total_documents': 3,
            'processing_time': 45.5,
            'paths_analyzed': 1,
        },
        'hash_duplicates': {
            'statistics': {
                'documents_processed': 3,
                'duplicate_groups_found': 1,
                'total_duplicates': 1,
                'total_wasted_space_mb': 1.0,
            },
            'duplicate_groups': [
                {
                    'group_id': 'hash_group_001',
                    'hash': 'abc123def456',
                    'document_count': 2,
                    'wasted_space': 1024000,
                    'documents': [
                        {
                            'id': 'doc_001',
                            'filename': 'document1.pdf',
                            'path': '/test/path/document1.pdf',
                            'size': 1024000,
                            'size_mb': 1.0,
                            'modified_date': '2023-01-01T12:00:00',
                        },
                        {
                            'id': 'doc_003',
                            'filename': 'document1_copy.pdf',
                            'path': '/test/path/copy/document1_copy.pdf',
                            'size': 1024000,
                            'size_mb': 1.0,
                            'modified_date': '2023-01-02T12:00:00',
                        }
                    ]
                }
            ]
        },
        'recommendations': {
            'summary': {
                'total_recommendations': 1,
                'high_priority_count': 1,
                'total_space_saved_mb': 1.0,
            },
            'high_priority': [
                {
                    'group_id': 'hash_group_001',
                    'action': 'delete_duplicate',
                    'method': 'hash_duplicate',
                    'confidence': 1.0,
                    'space_saved_mb': 1.0,
                    'reasoning': 'Exact duplicate detected by hash comparison',
                    'delete_documents': [
                        {
                            'id': 'doc_003',
                            'filename': 'document1_copy.pdf',
                            'path': '/test/path/copy/document1_copy.pdf',
                        }
                    ]
                }
            ],
            'medium_priority': [],
            'low_priority': [],
        }
    }


@pytest.fixture
def mock_file_system(temp_dir):
    """Create a mock file system structure for testing"""
    structure = {
        'documents': {
            'reports': {
                'annual_report_2023.pdf': 'Annual report content',
                'quarterly_report_q1.pdf': 'Q1 report content',
                'quarterly_report_q2.pdf': 'Q2 report content',
            },
            'presentations': {
                'company_overview.pptx': b'PowerPoint content',
                'product_demo.pptx': b'Demo content',
            },
            'spreadsheets': {
                'budget_2023.xlsx': b'Excel content',
                'sales_data.csv': 'Date,Sales\n2023-01-01,1000\n2023-01-02,1200',
            },
            'duplicates': {
                'annual_report_2023_copy.pdf': 'Annual report content',  # Duplicate
                'budget_2023_backup.xlsx': b'Excel content',  # Duplicate
            }
        },
        'archive': {
            'old_documents': {
                'legacy_report.doc': 'Old document content',
            }
        }
    }
    
    def create_structure(base_path, structure_dict):
        for name, content in structure_dict.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                if isinstance(content, str):
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                else:
                    with open(path, 'wb') as f:
                        f.write(content)
    
    create_structure(temp_dir, structure)
    return temp_dir


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing"""
    import numpy as np
    
    # Create sample embeddings (384-dimensional vectors)
    embeddings = {
        'doc_001': np.random.rand(384).tolist(),
        'doc_002': np.random.rand(384).tolist(),
        'doc_003': np.random.rand(384).tolist(),
    }
    
    # Make doc_001 and doc_003 similar (same content)
    embeddings['doc_003'] = embeddings['doc_001'].copy()
    
    return embeddings


@pytest.fixture
def sample_entities():
    """Create sample named entities for testing"""
    return {
        'PERSON': [
            {'text': 'John Smith', 'count': 3, 'documents': ['doc_001', 'doc_002']},
            {'text': 'Jane Doe', 'count': 2, 'documents': ['doc_001']},
        ],
        'ORG': [
            {'text': 'Acme Corporation', 'count': 5, 'documents': ['doc_001', 'doc_002', 'doc_003']},
            {'text': 'Tech Solutions Inc', 'count': 2, 'documents': ['doc_002']},
        ],
        'DATE': [
            {'text': '2023', 'count': 8, 'documents': ['doc_001', 'doc_002', 'doc_003']},
            {'text': 'January 2023', 'count': 3, 'documents': ['doc_001', 'doc_003']},
        ]
    }


@pytest.fixture
def sample_keywords():
    """Create sample keywords for testing"""
    return [
        {'word': 'document', 'avg_score': 0.95, 'frequency': 15},
        {'word': 'analysis', 'avg_score': 0.87, 'frequency': 12},
        {'word': 'report', 'avg_score': 0.82, 'frequency': 10},
        {'word': 'data', 'avg_score': 0.78, 'frequency': 8},
        {'word': 'system', 'avg_score': 0.75, 'frequency': 7},
    ]


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    import logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise in tests


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock configuration file"""
    config_content = """
crawler:
  max_file_size_mb: 50
  include_hidden_files: false
  file_extensions:
    - .pdf
    - .docx
    - .txt
    - .xlsx

nlp:
  enable_embeddings: true
  embedding_model: "all-MiniLM-L6-v2"
  similarity_threshold: 0.8
  max_text_length: 10000

detection:
  hash_algorithm: "sha256"
  similarity_threshold: 0.9
  enable_quick_hash: true
  version_patterns:
    - "v\\d+"
    - "version\\d+"
    - "copy"
    - "final"

reporting:
  output_formats:
    - html
    - csv
    - json
  include_charts: true
  max_items_per_table: 100
"""
    
    config_path = os.path.join(temp_dir, 'test_config.yaml')
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    return config_path

