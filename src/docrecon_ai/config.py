"""
Configuration management for DocRecon AI

Handles loading and validation of configuration settings from files,
environment variables, and command-line arguments.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class CrawlerConfig:
    """Configuration for document crawler"""
    max_file_size: str = "100MB"
    supported_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.txt', '.md', '.html', '.htm', '.rtf', '.odt', '.ods'
    ])
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '~$*', '.tmp', 'Thumbs.db', '.DS_Store', '*.lnk', '*.url'
    ])
    max_depth: int = 10
    follow_symlinks: bool = False
    threads: int = 4


@dataclass
class NLPConfig:
    """Configuration for NLP analysis"""
    model: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.85
    language: str = "de"
    batch_size: int = 32
    max_text_length: int = 10000
    enable_entities: bool = True
    enable_keywords: bool = True
    enable_clustering: bool = True


@dataclass
class DuplicateConfig:
    """Configuration for duplicate detection"""
    hash_algorithm: str = "sha256"
    content_similarity_threshold: float = 0.9
    filename_similarity_threshold: float = 0.8
    size_tolerance: float = 0.05  # 5% size difference tolerance
    enable_fuzzy_matching: bool = True


@dataclass
class GraphConfig:
    """Configuration for Microsoft Graph API"""
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: List[str] = field(default_factory=lambda: [
        "https://graph.microsoft.com/Files.Read.All",
        "https://graph.microsoft.com/Sites.Read.All"
    ])


@dataclass
class ReportingConfig:
    """Configuration for report generation"""
    output_format: str = "html"
    include_thumbnails: bool = True
    max_preview_length: int = 500
    group_by_similarity: bool = True
    show_file_paths: bool = True
    include_metadata: bool = True


@dataclass
class DashboardConfig:
    """Configuration for Streamlit dashboard"""
    port: int = 8501
    host: str = "localhost"
    theme: str = "light"
    page_size: int = 50
    enable_download: bool = True


@dataclass
class Config:
    """Main configuration class"""
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    nlp: NLPConfig = field(default_factory=NLPConfig)
    duplicates: DuplicateConfig = field(default_factory=DuplicateConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    
    # Global settings
    debug: bool = False
    log_level: str = "INFO"
    cache_dir: str = "~/.docrecon_cache"
    temp_dir: str = "/tmp/docrecon"


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file, environment variables, and defaults.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Config: Loaded configuration object
    """
    config = Config()
    
    # Load from file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
            config = _merge_config(config, yaml_config)
    
    # Override with environment variables
    config = _load_env_config(config)
    
    # Validate and normalize paths
    config = _normalize_config(config)
    
    return config


def _merge_config(config: Config, yaml_config: Dict[str, Any]) -> Config:
    """Merge YAML configuration into config object"""
    if 'crawler' in yaml_config:
        for key, value in yaml_config['crawler'].items():
            if hasattr(config.crawler, key):
                setattr(config.crawler, key, value)
    
    if 'nlp' in yaml_config:
        for key, value in yaml_config['nlp'].items():
            if hasattr(config.nlp, key):
                setattr(config.nlp, key, value)
    
    if 'duplicates' in yaml_config:
        for key, value in yaml_config['duplicates'].items():
            if hasattr(config.duplicates, key):
                setattr(config.duplicates, key, value)
    
    if 'graph' in yaml_config:
        for key, value in yaml_config['graph'].items():
            if hasattr(config.graph, key):
                setattr(config.graph, key, value)
    
    if 'reporting' in yaml_config:
        for key, value in yaml_config['reporting'].items():
            if hasattr(config.reporting, key):
                setattr(config.reporting, key, value)
    
    if 'dashboard' in yaml_config:
        for key, value in yaml_config['dashboard'].items():
            if hasattr(config.dashboard, key):
                setattr(config.dashboard, key, value)
    
    # Global settings
    for key in ['debug', 'log_level', 'cache_dir', 'temp_dir']:
        if key in yaml_config:
            setattr(config, key, yaml_config[key])
    
    return config


def _load_env_config(config: Config) -> Config:
    """Load configuration from environment variables"""
    # Graph API settings
    if os.getenv('DOCRECON_TENANT_ID'):
        config.graph.tenant_id = os.getenv('DOCRECON_TENANT_ID')
    if os.getenv('DOCRECON_CLIENT_ID'):
        config.graph.client_id = os.getenv('DOCRECON_CLIENT_ID')
    if os.getenv('DOCRECON_CLIENT_SECRET'):
        config.graph.client_secret = os.getenv('DOCRECON_CLIENT_SECRET')
    
    # Global settings
    if os.getenv('DOCRECON_DEBUG'):
        config.debug = os.getenv('DOCRECON_DEBUG').lower() == 'true'
    if os.getenv('DOCRECON_LOG_LEVEL'):
        config.log_level = os.getenv('DOCRECON_LOG_LEVEL')
    if os.getenv('DOCRECON_CACHE_DIR'):
        config.cache_dir = os.getenv('DOCRECON_CACHE_DIR')
    
    return config


def _normalize_config(config: Config) -> Config:
    """Normalize and validate configuration values"""
    # Expand user paths
    config.cache_dir = os.path.expanduser(config.cache_dir)
    config.temp_dir = os.path.expanduser(config.temp_dir)
    
    # Create directories if they don't exist
    os.makedirs(config.cache_dir, exist_ok=True)
    os.makedirs(config.temp_dir, exist_ok=True)
    
    # Convert file size string to bytes
    if isinstance(config.crawler.max_file_size, str):
        config.crawler.max_file_size = _parse_file_size(config.crawler.max_file_size)
    
    return config


def _parse_file_size(size_str: str) -> int:
    """Parse file size string (e.g., '100MB') to bytes"""
    size_str = size_str.upper().strip()
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = float(size_str[:-len(suffix)])
            return int(number * multiplier)
    
    # If no suffix, assume bytes
    return int(size_str)


def save_config(config: Config, config_path: str) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration object to save
        config_path: Path where to save the configuration
    """
    config_dict = {
        'crawler': {
            'max_file_size': config.crawler.max_file_size,
            'supported_extensions': config.crawler.supported_extensions,
            'ignore_patterns': config.crawler.ignore_patterns,
            'max_depth': config.crawler.max_depth,
            'follow_symlinks': config.crawler.follow_symlinks,
            'threads': config.crawler.threads,
        },
        'nlp': {
            'model': config.nlp.model,
            'similarity_threshold': config.nlp.similarity_threshold,
            'language': config.nlp.language,
            'batch_size': config.nlp.batch_size,
            'max_text_length': config.nlp.max_text_length,
            'enable_entities': config.nlp.enable_entities,
            'enable_keywords': config.nlp.enable_keywords,
            'enable_clustering': config.nlp.enable_clustering,
        },
        'duplicates': {
            'hash_algorithm': config.duplicates.hash_algorithm,
            'content_similarity_threshold': config.duplicates.content_similarity_threshold,
            'filename_similarity_threshold': config.duplicates.filename_similarity_threshold,
            'size_tolerance': config.duplicates.size_tolerance,
            'enable_fuzzy_matching': config.duplicates.enable_fuzzy_matching,
        },
        'reporting': {
            'output_format': config.reporting.output_format,
            'include_thumbnails': config.reporting.include_thumbnails,
            'max_preview_length': config.reporting.max_preview_length,
            'group_by_similarity': config.reporting.group_by_similarity,
            'show_file_paths': config.reporting.show_file_paths,
            'include_metadata': config.reporting.include_metadata,
        },
        'dashboard': {
            'port': config.dashboard.port,
            'host': config.dashboard.host,
            'theme': config.dashboard.theme,
            'page_size': config.dashboard.page_size,
            'enable_download': config.dashboard.enable_download,
        },
        'debug': config.debug,
        'log_level': config.log_level,
        'cache_dir': config.cache_dir,
        'temp_dir': config.temp_dir,
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)


# Default configuration instance
default_config = Config()

