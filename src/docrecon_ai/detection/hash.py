"""
Hash-based duplicate detection

Detects exact duplicates using file hashes (SHA256, MD5) and file size comparison.
This is the most reliable method for finding identical files.
"""

import os
from collections import defaultdict
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import logging

from ..crawler.base import DocumentInfo

logger = logging.getLogger(__name__)


class HashDuplicateDetector:
    """
    Detects exact duplicate files using hash comparison.
    
    Uses SHA256 hashes as primary method with optional MD5 fallback.
    Also considers file size for quick pre-filtering.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize hash duplicate detector.
        
        Args:
            config: Configuration object with duplicate detection settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.hash_algorithm = getattr(config.duplicates, 'hash_algorithm', 'sha256') if config else 'sha256'
        self.size_tolerance = getattr(config.duplicates, 'size_tolerance', 0.0) if config else 0.0
        
        # Statistics
        self.documents_processed = 0
        self.duplicate_groups_found = 0
        self.total_duplicates = 0
        
        # Results
        self.hash_groups = {}
        self.size_groups = {}
    
    def find_hash_duplicates(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """
        Find exact duplicates using file hashes.
        
        Args:
            documents: List of DocumentInfo objects to analyze
            
        Returns:
            dict: Duplicate detection results
        """
        self.logger.info(f"Finding hash duplicates for {len(documents)} documents")
        
        # Group documents by hash
        hash_groups = defaultdict(list)
        size_groups = defaultdict(list)
        
        # Process documents
        for doc in documents:
            self.documents_processed += 1
            
            # Group by size first (quick filter)
            if doc.size > 0:
                size_groups[doc.size].append(doc)
            
            # Group by hash
            hash_value = self._get_document_hash(doc)
            if hash_value:
                hash_groups[hash_value].append(doc)
        
        # Find duplicate groups
        duplicate_groups = []
        hash_duplicates = {}
        
        for hash_value, docs in hash_groups.items():
            if len(docs) > 1:
                # Found duplicates
                group_id = f"hash_{len(duplicate_groups)}"
                duplicate_group = {
                    'group_id': group_id,
                    'type': 'exact_hash',
                    'hash': hash_value,
                    'algorithm': self.hash_algorithm,
                    'document_count': len(docs),
                    'documents': [self._document_to_dict(doc) for doc in docs],
                    'total_size': sum(doc.size for doc in docs),
                    'wasted_space': sum(doc.size for doc in docs[1:]),  # All but first are wasted
                }
                
                duplicate_groups.append(duplicate_group)
                
                # Add to hash duplicates mapping
                for doc in docs:
                    doc_id = self._get_document_id(doc)
                    hash_duplicates[doc_id] = group_id
                
                self.duplicate_groups_found += 1
                self.total_duplicates += len(docs) - 1  # Subtract original
        
        # Store results
        self.hash_groups = hash_groups
        self.size_groups = size_groups
        
        # Analyze size-based potential duplicates (same size, different hash)
        size_duplicates = self._find_size_duplicates(size_groups, hash_duplicates)
        
        results = {
            'method': 'hash_based',
            'algorithm': self.hash_algorithm,
            'duplicate_groups': duplicate_groups,
            'hash_duplicates': hash_duplicates,
            'size_duplicates': size_duplicates,
            'statistics': {
                'documents_processed': self.documents_processed,
                'duplicate_groups_found': self.duplicate_groups_found,
                'total_duplicates': self.total_duplicates,
                'total_wasted_space': sum(group['wasted_space'] for group in duplicate_groups),
                'unique_hashes': len(hash_groups),
                'unique_sizes': len(size_groups),
            }
        }
        
        return results
    
    def _find_size_duplicates(self, size_groups: Dict[int, List[DocumentInfo]], 
                             hash_duplicates: Dict[str, str]) -> List[Dict[str, Any]]:
        """Find documents with same size but different hashes (potential duplicates)"""
        size_duplicate_groups = []
        
        for size, docs in size_groups.items():
            if len(docs) > 1:
                # Filter out documents already identified as hash duplicates
                filtered_docs = []
                for doc in docs:
                    doc_id = self._get_document_id(doc)
                    if doc_id not in hash_duplicates:
                        filtered_docs.append(doc)
                
                if len(filtered_docs) > 1:
                    # Group by hash to separate different files with same size
                    hash_subgroups = defaultdict(list)
                    for doc in filtered_docs:
                        hash_value = self._get_document_hash(doc)
                        hash_subgroups[hash_value].append(doc)
                    
                    # Only include if there are multiple different hashes
                    if len(hash_subgroups) > 1:
                        group_id = f"size_{len(size_duplicate_groups)}"
                        size_group = {
                            'group_id': group_id,
                            'type': 'same_size',
                            'size': size,
                            'document_count': len(filtered_docs),
                            'hash_subgroups': len(hash_subgroups),
                            'documents': [self._document_to_dict(doc) for doc in filtered_docs],
                        }
                        size_duplicate_groups.append(size_group)
        
        return size_duplicate_groups
    
    def find_zero_byte_files(self, documents: List[DocumentInfo]) -> List[Dict[str, Any]]:
        """
        Find zero-byte (empty) files.
        
        Args:
            documents: List of DocumentInfo objects
            
        Returns:
            list: Zero-byte files
        """
        zero_byte_files = []
        
        for doc in documents:
            if doc.size == 0:
                zero_byte_files.append(self._document_to_dict(doc))
        
        return zero_byte_files
    
    def find_large_duplicates(self, documents: List[DocumentInfo], 
                             min_size_mb: float = 10.0) -> List[Dict[str, Any]]:
        """
        Find large duplicate files that waste significant space.
        
        Args:
            documents: List of DocumentInfo objects
            min_size_mb: Minimum file size in MB to consider
            
        Returns:
            list: Large duplicate groups
        """
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        
        # Filter large files
        large_files = [doc for doc in documents if doc.size >= min_size_bytes]
        
        if not large_files:
            return []
        
        # Find duplicates among large files
        results = self.find_hash_duplicates(large_files)
        
        # Filter duplicate groups by size
        large_duplicate_groups = []
        for group in results['duplicate_groups']:
            if group['total_size'] >= min_size_bytes:
                large_duplicate_groups.append(group)
        
        return large_duplicate_groups
    
    def _get_document_hash(self, document: DocumentInfo) -> Optional[str]:
        """Get hash value for a document"""
        if self.hash_algorithm.lower() == 'sha256':
            return document.sha256_hash
        elif self.hash_algorithm.lower() == 'md5':
            return document.md5_hash
        else:
            # Try SHA256 first, then MD5
            return document.sha256_hash or document.md5_hash
    
    def _get_document_id(self, document: DocumentInfo) -> str:
        """Generate unique ID for a document"""
        if document.sha256_hash:
            return document.sha256_hash[:16]
        elif document.md5_hash:
            return document.md5_hash[:16]
        else:
            return f"{Path(document.path).stem}_{document.size}"
    
    def _document_to_dict(self, document: DocumentInfo) -> Dict[str, Any]:
        """Convert DocumentInfo to dictionary for results"""
        return {
            'id': self._get_document_id(document),
            'filename': document.filename,
            'path': document.path,
            'size': document.size,
            'size_mb': round(document.size / (1024 * 1024), 2),
            'modified_date': document.modified_date.isoformat() if document.modified_date else None,
            'created_date': document.created_date.isoformat() if document.created_date else None,
            'file_extension': document.file_extension,
            'mime_type': document.mime_type,
            'sha256_hash': document.sha256_hash,
            'md5_hash': document.md5_hash,
            'source_type': document.source_type,
        }
    
    def get_duplicate_summary(self, duplicate_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary statistics for duplicate detection results.
        
        Args:
            duplicate_results: Results from find_hash_duplicates
            
        Returns:
            dict: Summary statistics
        """
        duplicate_groups = duplicate_results.get('duplicate_groups', [])
        
        summary = {
            'total_duplicate_groups': len(duplicate_groups),
            'total_duplicate_files': sum(group['document_count'] - 1 for group in duplicate_groups),
            'total_wasted_space_bytes': sum(group['wasted_space'] for group in duplicate_groups),
            'total_wasted_space_mb': round(sum(group['wasted_space'] for group in duplicate_groups) / (1024 * 1024), 2),
            'largest_duplicate_group': None,
            'most_wasted_space_group': None,
            'file_type_distribution': {},
        }
        
        if duplicate_groups:
            # Find largest group by count
            largest_group = max(duplicate_groups, key=lambda x: x['document_count'])
            summary['largest_duplicate_group'] = {
                'group_id': largest_group['group_id'],
                'document_count': largest_group['document_count'],
                'wasted_space_mb': round(largest_group['wasted_space'] / (1024 * 1024), 2),
            }
            
            # Find group with most wasted space
            most_wasted_group = max(duplicate_groups, key=lambda x: x['wasted_space'])
            summary['most_wasted_space_group'] = {
                'group_id': most_wasted_group['group_id'],
                'document_count': most_wasted_group['document_count'],
                'wasted_space_mb': round(most_wasted_group['wasted_space'] / (1024 * 1024), 2),
            }
            
            # Analyze file type distribution
            file_types = defaultdict(lambda: {'count': 0, 'wasted_space': 0})
            for group in duplicate_groups:
                for doc in group['documents']:
                    ext = doc.get('file_extension', '').lower()
                    file_types[ext]['count'] += 1
                    file_types[ext]['wasted_space'] += doc['size']
            
            # Convert to regular dict and sort by wasted space
            summary['file_type_distribution'] = dict(sorted(
                file_types.items(), 
                key=lambda x: x[1]['wasted_space'], 
                reverse=True
            ))
        
        return summary
    
    def generate_deletion_recommendations(self, duplicate_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for which duplicate files to delete.
        
        Args:
            duplicate_results: Results from find_hash_duplicates
            
        Returns:
            list: Deletion recommendations
        """
        recommendations = []
        
        for group in duplicate_results.get('duplicate_groups', []):
            docs = group['documents']
            
            if len(docs) < 2:
                continue
            
            # Sort documents by preference (keep the "best" one)
            sorted_docs = self._sort_documents_by_preference(docs)
            
            # Keep the first (best) document, recommend deleting others
            keep_doc = sorted_docs[0]
            delete_docs = sorted_docs[1:]
            
            recommendation = {
                'group_id': group['group_id'],
                'action': 'delete_duplicates',
                'keep_document': keep_doc,
                'delete_documents': delete_docs,
                'space_saved_bytes': sum(doc['size'] for doc in delete_docs),
                'space_saved_mb': round(sum(doc['size'] for doc in delete_docs) / (1024 * 1024), 2),
                'reasoning': self._get_keep_reasoning(keep_doc, delete_docs),
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _sort_documents_by_preference(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort documents by preference (best to keep first)"""
        def preference_score(doc):
            score = 0
            
            # Prefer files in certain locations (e.g., not in temp folders)
            path = doc['path'].lower()
            if any(temp in path for temp in ['temp', 'tmp', 'cache', 'recycle']):
                score -= 100
            
            # Prefer files with better names (not containing "copy", "backup", etc.)
            filename = doc['filename'].lower()
            if any(word in filename for word in ['copy', 'backup', 'duplicate', 'old']):
                score -= 50
            
            # Prefer newer files
            if doc.get('modified_date'):
                try:
                    from datetime import datetime
                    mod_date = datetime.fromisoformat(doc['modified_date'].replace('Z', '+00:00'))
                    # Score based on days since epoch (newer = higher score)
                    score += mod_date.timestamp() / (24 * 3600)
                except Exception:
                    pass
            
            # Prefer files in root directories over nested ones
            path_depth = doc['path'].count(os.sep)
            score -= path_depth
            
            return score
        
        return sorted(documents, key=preference_score, reverse=True)
    
    def _get_keep_reasoning(self, keep_doc: Dict[str, Any], delete_docs: List[Dict[str, Any]]) -> str:
        """Generate reasoning for why a document was chosen to keep"""
        reasons = []
        
        # Check location
        keep_path = keep_doc['path'].lower()
        if not any(temp in keep_path for temp in ['temp', 'tmp', 'cache', 'recycle']):
            reasons.append("located in a permanent directory")
        
        # Check filename
        keep_filename = keep_doc['filename'].lower()
        if not any(word in keep_filename for word in ['copy', 'backup', 'duplicate', 'old']):
            reasons.append("has a clean filename")
        
        # Check if it's the newest
        if keep_doc.get('modified_date'):
            try:
                from datetime import datetime
                keep_date = datetime.fromisoformat(keep_doc['modified_date'].replace('Z', '+00:00'))
                is_newest = True
                for delete_doc in delete_docs:
                    if delete_doc.get('modified_date'):
                        delete_date = datetime.fromisoformat(delete_doc['modified_date'].replace('Z', '+00:00'))
                        if delete_date > keep_date:
                            is_newest = False
                            break
                if is_newest:
                    reasons.append("is the most recently modified")
            except Exception:
                pass
        
        if not reasons:
            reasons.append("was selected based on file location and naming")
        
        return f"Keep this file because it {', '.join(reasons)}"
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get hash duplicate detection statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'documents_processed': self.documents_processed,
            'duplicate_groups_found': self.duplicate_groups_found,
            'total_duplicates': self.total_duplicates,
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.documents_processed = 0
        self.duplicate_groups_found = 0
        self.total_duplicates = 0
        self.hash_groups = {}
        self.size_groups = {}

