"""
Semantic similarity analysis for duplicate detection

Detects documents with similar content using embeddings and semantic analysis.
Useful for finding near-duplicates, different versions, and related documents.
"""

import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Set
import logging

from ..crawler.base import DocumentInfo

logger = logging.getLogger(__name__)

# Optional similarity dependencies
try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install: pip install scikit-learn")


class SimilarityAnalyzer:
    """
    Analyzes semantic similarity between documents to find near-duplicates.
    
    Uses document embeddings to calculate similarity scores and identify
    documents with similar content even if they are not exact duplicates.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize similarity analyzer.
        
        Args:
            config: Configuration object with duplicate detection settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for similarity analysis. Install: pip install scikit-learn")
        
        # Configuration
        self.similarity_threshold = getattr(config.duplicates, 'content_similarity_threshold', 0.9) if config else 0.9
        self.size_tolerance = getattr(config.duplicates, 'size_tolerance', 0.05) if config else 0.05
        self.enable_fuzzy_matching = getattr(config.duplicates, 'enable_fuzzy_matching', True) if config else True
        
        # Statistics
        self.documents_processed = 0
        self.similarity_groups_found = 0
        self.comparisons_made = 0
        
        # Results
        self.similarity_matrix = None
        self.similarity_groups = []
    
    def find_similar_documents(self, documents: List[DocumentInfo], 
                              embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Find documents with similar content using embeddings.
        
        Args:
            documents: List of DocumentInfo objects
            embeddings: Dictionary mapping document IDs to embedding vectors
            
        Returns:
            dict: Similarity analysis results
        """
        self.logger.info(f"Analyzing similarity for {len(documents)} documents")
        
        if not embeddings:
            self.logger.warning("No embeddings provided for similarity analysis")
            return {'similarity_groups': [], 'statistics': {}}
        
        # Create document ID to info mapping
        doc_id_to_info = {}
        for doc in documents:
            doc_id = self._get_document_id(doc)
            doc_id_to_info[doc_id] = doc
        
        # Filter embeddings to only include documents we have info for
        filtered_embeddings = {
            doc_id: embedding for doc_id, embedding in embeddings.items()
            if doc_id in doc_id_to_info
        }
        
        if not filtered_embeddings:
            self.logger.warning("No matching embeddings found for documents")
            return {'similarity_groups': [], 'statistics': {}}
        
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(filtered_embeddings)
        self.similarity_matrix = similarity_matrix
        
        # Find similarity groups
        similarity_groups = self._find_similarity_groups(
            filtered_embeddings, similarity_matrix, doc_id_to_info
        )
        
        # Analyze groups for additional insights
        enhanced_groups = self._enhance_similarity_groups(similarity_groups, doc_id_to_info)
        
        self.similarity_groups = enhanced_groups
        self.documents_processed = len(filtered_embeddings)
        self.similarity_groups_found = len(enhanced_groups)
        
        results = {
            'method': 'semantic_similarity',
            'similarity_threshold': self.similarity_threshold,
            'similarity_groups': enhanced_groups,
            'similarity_matrix_shape': similarity_matrix.shape,
            'statistics': {
                'documents_processed': self.documents_processed,
                'similarity_groups_found': self.similarity_groups_found,
                'comparisons_made': self.comparisons_made,
                'avg_group_size': np.mean([len(group['documents']) for group in enhanced_groups]) if enhanced_groups else 0,
            }
        }
        
        return results
    
    def _calculate_similarity_matrix(self, embeddings: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate pairwise similarity matrix for all embeddings"""
        doc_ids = list(embeddings.keys())
        embedding_matrix = np.array(list(embeddings.values()))
        
        # Calculate cosine similarity matrix
        similarity_matrix = cosine_similarity(embedding_matrix)
        
        self.comparisons_made = len(doc_ids) * (len(doc_ids) - 1) // 2
        
        return similarity_matrix
    
    def _find_similarity_groups(self, embeddings: Dict[str, np.ndarray], 
                               similarity_matrix: np.ndarray,
                               doc_id_to_info: Dict[str, DocumentInfo]) -> List[Dict[str, Any]]:
        """Find groups of similar documents using clustering"""
        doc_ids = list(embeddings.keys())
        
        # Use DBSCAN clustering to find similarity groups
        # Convert similarity to distance (1 - similarity)
        distance_matrix = 1 - similarity_matrix
        
        # Set DBSCAN parameters
        eps = 1 - self.similarity_threshold  # Distance threshold
        min_samples = 2  # Minimum group size
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # Group documents by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            if label != -1:  # Ignore noise points
                clusters[label].append(doc_ids[i])
        
        # Create similarity groups
        similarity_groups = []
        for cluster_id, doc_ids_in_cluster in clusters.items():
            if len(doc_ids_in_cluster) >= 2:
                # Calculate average similarity within group
                similarities = []
                for i, doc_id1 in enumerate(doc_ids_in_cluster):
                    for doc_id2 in doc_ids_in_cluster[i+1:]:
                        idx1 = doc_ids.index(doc_id1)
                        idx2 = doc_ids.index(doc_id2)
                        similarities.append(similarity_matrix[idx1, idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                
                group = {
                    'group_id': f"sim_{cluster_id}",
                    'type': 'semantic_similarity',
                    'document_count': len(doc_ids_in_cluster),
                    'avg_similarity': float(avg_similarity),
                    'min_similarity': float(np.min(similarities)) if similarities else 0.0,
                    'max_similarity': float(np.max(similarities)) if similarities else 0.0,
                    'document_ids': doc_ids_in_cluster,
                    'documents': [self._document_to_dict(doc_id_to_info[doc_id]) for doc_id in doc_ids_in_cluster],
                }
                
                similarity_groups.append(group)
        
        return similarity_groups
    
    def _enhance_similarity_groups(self, similarity_groups: List[Dict[str, Any]], 
                                  doc_id_to_info: Dict[str, DocumentInfo]) -> List[Dict[str, Any]]:
        """Enhance similarity groups with additional analysis"""
        enhanced_groups = []
        
        for group in similarity_groups:
            enhanced_group = group.copy()
            
            # Analyze file characteristics
            docs = [doc_id_to_info[doc_id] for doc_id in group['document_ids']]
            
            # File size analysis
            sizes = [doc.size for doc in docs]
            enhanced_group['size_analysis'] = {
                'min_size': min(sizes),
                'max_size': max(sizes),
                'avg_size': np.mean(sizes),
                'size_variance': np.var(sizes),
                'similar_sizes': self._check_similar_sizes(sizes),
            }
            
            # File type analysis
            extensions = [doc.file_extension for doc in docs]
            enhanced_group['file_type_analysis'] = {
                'extensions': list(set(extensions)),
                'same_extension': len(set(extensions)) == 1,
                'extension_distribution': {ext: extensions.count(ext) for ext in set(extensions)},
            }
            
            # Temporal analysis
            mod_dates = [doc.modified_date for doc in docs if doc.modified_date]
            if mod_dates:
                enhanced_group['temporal_analysis'] = {
                    'date_range_days': (max(mod_dates) - min(mod_dates)).days,
                    'oldest_file': min(mod_dates).isoformat(),
                    'newest_file': max(mod_dates).isoformat(),
                }
            
            # Path analysis
            paths = [doc.path for doc in docs]
            enhanced_group['path_analysis'] = {
                'common_directory': self._find_common_directory(paths),
                'same_directory': len(set([str(Path(p).parent) for p in paths])) == 1,
                'directory_distribution': self._analyze_directory_distribution(paths),
            }
            
            # Content length analysis (if available)
            text_lengths = [doc.text_length for doc in docs if doc.text_length > 0]
            if text_lengths:
                enhanced_group['content_analysis'] = {
                    'min_length': min(text_lengths),
                    'max_length': max(text_lengths),
                    'avg_length': np.mean(text_lengths),
                    'length_variance': np.var(text_lengths),
                }
            
            # Determine likely relationship type
            enhanced_group['relationship_type'] = self._determine_relationship_type(enhanced_group)
            
            enhanced_groups.append(enhanced_group)
        
        return enhanced_groups
    
    def _check_similar_sizes(self, sizes: List[int]) -> bool:
        """Check if file sizes are similar within tolerance"""
        if len(sizes) < 2:
            return True
        
        avg_size = np.mean(sizes)
        tolerance = avg_size * self.size_tolerance
        
        return all(abs(size - avg_size) <= tolerance for size in sizes)
    
    def _find_common_directory(self, paths: List[str]) -> str:
        """Find common directory path for a list of file paths"""
        if not paths:
            return ""
        
        from pathlib import Path
        
        # Convert to Path objects
        path_objects = [Path(p) for p in paths]
        
        # Find common parent
        common_parts = []
        if path_objects:
            # Get parts of first path
            first_parts = path_objects[0].parts
            
            # Check each part
            for i, part in enumerate(first_parts):
                if all(len(p.parts) > i and p.parts[i] == part for p in path_objects):
                    common_parts.append(part)
                else:
                    break
        
        return str(Path(*common_parts)) if common_parts else ""
    
    def _analyze_directory_distribution(self, paths: List[str]) -> Dict[str, int]:
        """Analyze distribution of files across directories"""
        from pathlib import Path
        
        directories = [str(Path(p).parent) for p in paths]
        distribution = {}
        for directory in directories:
            distribution[directory] = distribution.get(directory, 0) + 1
        
        return distribution
    
    def _determine_relationship_type(self, group: Dict[str, Any]) -> str:
        """Determine the likely relationship type between similar documents"""
        # Check various characteristics to determine relationship
        
        # Same extension and similar sizes -> likely versions
        if (group['file_type_analysis']['same_extension'] and 
            group['size_analysis']['similar_sizes']):
            return "likely_versions"
        
        # Different extensions but similar content -> format conversions
        if not group['file_type_analysis']['same_extension']:
            return "format_variants"
        
        # Same directory and high similarity -> duplicates or versions
        if group['path_analysis']['same_directory'] and group['avg_similarity'] > 0.95:
            return "near_duplicates"
        
        # High similarity but different locations -> copied files
        if group['avg_similarity'] > 0.98:
            return "copied_files"
        
        # Moderate similarity -> related content
        if group['avg_similarity'] > 0.85:
            return "related_content"
        
        return "similar_content"
    
    def find_near_duplicates(self, documents: List[DocumentInfo], 
                           embeddings: Dict[str, np.ndarray],
                           threshold: float = None) -> List[Dict[str, Any]]:
        """
        Find near-duplicate documents (very high similarity).
        
        Args:
            documents: List of DocumentInfo objects
            embeddings: Document embeddings
            threshold: Similarity threshold (default: 0.95)
            
        Returns:
            list: Near-duplicate groups
        """
        if threshold is None:
            threshold = 0.95
        
        # Temporarily adjust threshold
        original_threshold = self.similarity_threshold
        self.similarity_threshold = threshold
        
        try:
            results = self.find_similar_documents(documents, embeddings)
            near_duplicates = [
                group for group in results['similarity_groups']
                if group['avg_similarity'] >= threshold
            ]
            return near_duplicates
        finally:
            # Restore original threshold
            self.similarity_threshold = original_threshold
    
    def find_content_variants(self, documents: List[DocumentInfo], 
                            embeddings: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
        """
        Find documents that are variants of the same content (different formats, versions).
        
        Args:
            documents: List of DocumentInfo objects
            embeddings: Document embeddings
            
        Returns:
            list: Content variant groups
        """
        results = self.find_similar_documents(documents, embeddings)
        
        content_variants = []
        for group in results['similarity_groups']:
            # Look for groups with different file extensions or significant size differences
            if (not group['file_type_analysis']['same_extension'] or
                not group['size_analysis']['similar_sizes']):
                
                variant_group = group.copy()
                variant_group['type'] = 'content_variants'
                content_variants.append(variant_group)
        
        return content_variants
    
    def calculate_document_similarity(self, doc1_embedding: np.ndarray, 
                                    doc2_embedding: np.ndarray) -> float:
        """
        Calculate similarity between two document embeddings.
        
        Args:
            doc1_embedding: First document embedding
            doc2_embedding: Second document embedding
            
        Returns:
            float: Similarity score (0-1)
        """
        # Reshape if needed
        if doc1_embedding.ndim == 1:
            doc1_embedding = doc1_embedding.reshape(1, -1)
        if doc2_embedding.ndim == 1:
            doc2_embedding = doc2_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(doc1_embedding, doc2_embedding)[0, 0]
        return float(similarity)
    
    def _get_document_id(self, document: DocumentInfo) -> str:
        """Generate unique ID for a document"""
        if document.sha256_hash:
            return document.sha256_hash[:16]
        elif document.md5_hash:
            return document.md5_hash[:16]
        else:
            from pathlib import Path
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
            'text_length': document.text_length,
            'source_type': document.source_type,
        }
    
    def get_similarity_recommendations(self, similarity_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for handling similar documents.
        
        Args:
            similarity_results: Results from similarity analysis
            
        Returns:
            list: Recommendations for each similarity group
        """
        recommendations = []
        
        for group in similarity_results.get('similarity_groups', []):
            recommendation = {
                'group_id': group['group_id'],
                'relationship_type': group.get('relationship_type', 'similar_content'),
                'documents': group['documents'],
                'avg_similarity': group['avg_similarity'],
            }
            
            # Generate specific recommendations based on relationship type
            rel_type = group.get('relationship_type', 'similar_content')
            
            if rel_type == 'near_duplicates':
                recommendation['action'] = 'review_for_deletion'
                recommendation['reasoning'] = 'Documents are nearly identical and may be duplicates'
                recommendation['priority'] = 'high'
                
            elif rel_type == 'likely_versions':
                recommendation['action'] = 'consolidate_versions'
                recommendation['reasoning'] = 'Documents appear to be different versions of the same content'
                recommendation['priority'] = 'medium'
                
            elif rel_type == 'format_variants':
                recommendation['action'] = 'choose_preferred_format'
                recommendation['reasoning'] = 'Same content in different file formats'
                recommendation['priority'] = 'medium'
                
            elif rel_type == 'copied_files':
                recommendation['action'] = 'remove_copies'
                recommendation['reasoning'] = 'Documents appear to be copies in different locations'
                recommendation['priority'] = 'high'
                
            else:
                recommendation['action'] = 'review_relationship'
                recommendation['reasoning'] = 'Documents have similar content and should be reviewed'
                recommendation['priority'] = 'low'
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get similarity analysis statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'documents_processed': self.documents_processed,
            'similarity_groups_found': self.similarity_groups_found,
            'comparisons_made': self.comparisons_made,
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.documents_processed = 0
        self.similarity_groups_found = 0
        self.comparisons_made = 0
        self.similarity_matrix = None
        self.similarity_groups = []

