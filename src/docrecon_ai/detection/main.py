"""
Main duplicate detector that coordinates all detection methods

Provides a unified interface for detecting duplicates using multiple methods:
- Hash-based exact duplicate detection
- Semantic similarity analysis
- Filename pattern version detection
"""

import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Optional
import logging

from ..crawler.base import DocumentInfo
from .hash import HashDuplicateDetector
from .similarity import SimilarityAnalyzer
from .versioning import VersionDetector

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Main duplicate detector that coordinates all detection methods.
    
    Provides a comprehensive analysis of document duplicates using:
    - Exact hash-based duplicate detection
    - Semantic content similarity analysis
    - Filename pattern version detection
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize duplicate detector.
        
        Args:
            config: Configuration object with duplicate detection settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize detection components
        self.hash_detector = HashDuplicateDetector(config)
        self.similarity_analyzer = SimilarityAnalyzer(config)
        self.version_detector = VersionDetector(config)
        
        # Detection settings
        self.enable_hash_detection = True
        self.enable_similarity_analysis = True
        self.enable_version_detection = True
        
        # Results storage
        self.hash_results = {}
        self.similarity_results = {}
        self.version_results = {}
        self.combined_results = {}
        
        # Statistics
        self.total_documents = 0
        self.total_duplicate_groups = 0
        self.total_duplicates_found = 0
        self.total_space_wasted = 0
    
    def detect_all_duplicates(self, documents: List[DocumentInfo], 
                             embeddings: Dict[str, np.ndarray] = None) -> Dict[str, Any]:
        """
        Perform comprehensive duplicate detection using all methods.
        
        Args:
            documents: List of DocumentInfo objects to analyze
            embeddings: Optional document embeddings for similarity analysis
            
        Returns:
            dict: Complete duplicate detection results
        """
        self.logger.info(f"Starting comprehensive duplicate detection for {len(documents)} documents")
        
        self.total_documents = len(documents)
        
        results = {
            'total_documents': len(documents),
            'hash_duplicates': {},
            'similarity_duplicates': {},
            'version_groups': {},
            'combined_analysis': {},
            'recommendations': {},
            'statistics': {},
        }
        
        # Step 1: Hash-based exact duplicate detection
        if self.enable_hash_detection:
            self.logger.info("Detecting exact duplicates using hashes...")
            hash_results = self.hash_detector.find_hash_duplicates(documents)
            results['hash_duplicates'] = hash_results
            self.hash_results = hash_results
        
        # Step 2: Semantic similarity analysis
        if self.enable_similarity_analysis and embeddings:
            self.logger.info("Analyzing semantic similarity...")
            similarity_results = self.similarity_analyzer.find_similar_documents(documents, embeddings)
            results['similarity_duplicates'] = similarity_results
            self.similarity_results = similarity_results
        
        # Step 3: Version detection
        if self.enable_version_detection:
            self.logger.info("Detecting document versions...")
            version_results = self.version_detector.find_document_versions(documents)
            results['version_groups'] = version_results
            self.version_results = version_results
        
        # Step 4: Combined analysis
        self.logger.info("Performing combined analysis...")
        combined_analysis = self._perform_combined_analysis()
        results['combined_analysis'] = combined_analysis
        self.combined_results = combined_analysis
        
        # Step 5: Generate recommendations
        self.logger.info("Generating recommendations...")
        recommendations = self._generate_comprehensive_recommendations()
        results['recommendations'] = recommendations
        
        # Step 6: Compile statistics
        results['statistics'] = self._compile_statistics()
        
        self.logger.info("Duplicate detection completed")
        return results
    
    def detect_exact_duplicates(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """
        Detect only exact duplicates using hash comparison.
        
        Args:
            documents: List of DocumentInfo objects
            
        Returns:
            dict: Hash-based duplicate detection results
        """
        return self.hash_detector.find_hash_duplicates(documents)
    
    def detect_similar_documents(self, documents: List[DocumentInfo], 
                               embeddings: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Detect similar documents using semantic analysis.
        
        Args:
            documents: List of DocumentInfo objects
            embeddings: Document embeddings
            
        Returns:
            dict: Similarity analysis results
        """
        return self.similarity_analyzer.find_similar_documents(documents, embeddings)
    
    def detect_document_versions(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """
        Detect document versions using filename analysis.
        
        Args:
            documents: List of DocumentInfo objects
            
        Returns:
            dict: Version detection results
        """
        return self.version_detector.find_document_versions(documents)
    
    def _perform_combined_analysis(self) -> Dict[str, Any]:
        """Perform combined analysis across all detection methods"""
        combined = {
            'cross_method_matches': [],
            'unique_to_hash': [],
            'unique_to_similarity': [],
            'unique_to_versions': [],
            'confidence_scores': {},
            'overlap_analysis': {},
        }
        
        # Get document IDs from each method
        hash_doc_ids = set()
        similarity_doc_ids = set()
        version_doc_ids = set()
        
        # Extract document IDs from hash results
        if self.hash_results:
            for group in self.hash_results.get('duplicate_groups', []):
                for doc in group['documents']:
                    hash_doc_ids.add(doc['id'])
        
        # Extract document IDs from similarity results
        if self.similarity_results:
            for group in self.similarity_results.get('similarity_groups', []):
                for doc in group['documents']:
                    similarity_doc_ids.add(doc['id'])
        
        # Extract document IDs from version results
        if self.version_results:
            for group in self.version_results.get('version_groups', []):
                for doc in group['documents']:
                    version_doc_ids.add(doc['id'])
        
        # Find overlaps
        all_methods = hash_doc_ids & similarity_doc_ids & version_doc_ids
        hash_similarity = hash_doc_ids & similarity_doc_ids - version_doc_ids
        hash_version = hash_doc_ids & version_doc_ids - similarity_doc_ids
        similarity_version = similarity_doc_ids & version_doc_ids - hash_doc_ids
        
        combined['overlap_analysis'] = {
            'all_three_methods': len(all_methods),
            'hash_and_similarity': len(hash_similarity),
            'hash_and_version': len(hash_version),
            'similarity_and_version': len(similarity_version),
            'hash_only': len(hash_doc_ids - similarity_doc_ids - version_doc_ids),
            'similarity_only': len(similarity_doc_ids - hash_doc_ids - version_doc_ids),
            'version_only': len(version_doc_ids - hash_doc_ids - similarity_doc_ids),
        }
        
        # Find cross-method matches (documents identified by multiple methods)
        cross_matches = self._find_cross_method_matches()
        combined['cross_method_matches'] = cross_matches
        
        # Calculate confidence scores for each duplicate group
        confidence_scores = self._calculate_confidence_scores()
        combined['confidence_scores'] = confidence_scores
        
        return combined
    
    def _find_cross_method_matches(self) -> List[Dict[str, Any]]:
        """Find documents identified as duplicates by multiple methods"""
        cross_matches = []
        
        # Create mapping of document IDs to groups
        doc_to_groups = defaultdict(list)
        
        # Add hash groups
        if self.hash_results:
            for group in self.hash_results.get('duplicate_groups', []):
                for doc in group['documents']:
                    doc_to_groups[doc['id']].append({
                        'method': 'hash',
                        'group_id': group['group_id'],
                        'confidence': 1.0,  # Hash matches are 100% confident
                    })
        
        # Add similarity groups
        if self.similarity_results:
            for group in self.similarity_results.get('similarity_groups', []):
                for doc in group['documents']:
                    doc_to_groups[doc['id']].append({
                        'method': 'similarity',
                        'group_id': group['group_id'],
                        'confidence': group['avg_similarity'],
                    })
        
        # Add version groups
        if self.version_results:
            for group in self.version_results.get('version_groups', []):
                for doc in group['documents']:
                    doc_to_groups[doc['id']].append({
                        'method': 'version',
                        'group_id': group['group_id'],
                        'confidence': 0.8,  # Version detection is moderately confident
                    })
        
        # Find documents with multiple method matches
        for doc_id, groups in doc_to_groups.items():
            if len(groups) > 1:
                cross_match = {
                    'document_id': doc_id,
                    'methods': [g['method'] for g in groups],
                    'group_ids': [g['group_id'] for g in groups],
                    'avg_confidence': sum(g['confidence'] for g in groups) / len(groups),
                    'method_count': len(groups),
                }
                cross_matches.append(cross_match)
        
        # Sort by confidence and method count
        cross_matches.sort(key=lambda x: (x['method_count'], x['avg_confidence']), reverse=True)
        
        return cross_matches
    
    def _calculate_confidence_scores(self) -> Dict[str, float]:
        """Calculate confidence scores for duplicate groups"""
        confidence_scores = {}
        
        # Hash duplicates have highest confidence
        if self.hash_results:
            for group in self.hash_results.get('duplicate_groups', []):
                confidence_scores[group['group_id']] = 1.0
        
        # Similarity duplicates have variable confidence based on similarity score
        if self.similarity_results:
            for group in self.similarity_results.get('similarity_groups', []):
                confidence_scores[group['group_id']] = group['avg_similarity']
        
        # Version groups have moderate confidence
        if self.version_results:
            for group in self.version_results.get('version_groups', []):
                # Base confidence on version pattern strength
                pattern = group.get('version_analysis', {}).get('version_pattern', '')
                if 'version_numbers' in pattern:
                    confidence = 0.9
                elif 'date_stamps' in pattern:
                    confidence = 0.8
                elif 'copy_indicators' in pattern:
                    confidence = 0.7
                else:
                    confidence = 0.6
                
                confidence_scores[group['group_id']] = confidence
        
        return confidence_scores
    
    def _generate_comprehensive_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive recommendations for all detected duplicates"""
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'summary': {},
        }
        
        # Hash duplicate recommendations (high priority)
        if self.hash_results:
            hash_recs = self.hash_detector.generate_deletion_recommendations(self.hash_results)
            for rec in hash_recs:
                rec['priority'] = 'high'
                rec['method'] = 'hash'
                rec['confidence'] = 1.0
                recommendations['high_priority'].append(rec)
        
        # Similarity recommendations (medium to high priority)
        if self.similarity_results:
            sim_recs = self.similarity_analyzer.get_similarity_recommendations(self.similarity_results)
            for rec in sim_recs:
                if rec.get('avg_similarity', 0) > 0.95:
                    rec['priority'] = 'high'
                    recommendations['high_priority'].append(rec)
                elif rec.get('avg_similarity', 0) > 0.85:
                    rec['priority'] = 'medium'
                    recommendations['medium_priority'].append(rec)
                else:
                    rec['priority'] = 'low'
                    recommendations['low_priority'].append(rec)
                
                rec['method'] = 'similarity'
                rec['confidence'] = rec.get('avg_similarity', 0)
        
        # Version recommendations (medium priority)
        if self.version_results:
            version_recs = self.version_detector.get_version_recommendations(self.version_results)
            for rec in version_recs:
                rec['priority'] = 'medium'
                rec['method'] = 'version'
                rec['confidence'] = 0.8
                recommendations['medium_priority'].append(rec)
        
        # Generate summary
        total_space_saved = 0
        total_files_to_remove = 0
        
        for priority_list in [recommendations['high_priority'], recommendations['medium_priority'], recommendations['low_priority']]:
            for rec in priority_list:
                if 'space_saved_bytes' in rec:
                    total_space_saved += rec['space_saved_bytes']
                if 'delete_documents' in rec:
                    total_files_to_remove += len(rec['delete_documents'])
                elif 'archive_versions' in rec:
                    total_files_to_remove += len(rec['archive_versions'])
        
        recommendations['summary'] = {
            'total_recommendations': len(recommendations['high_priority']) + len(recommendations['medium_priority']) + len(recommendations['low_priority']),
            'high_priority_count': len(recommendations['high_priority']),
            'medium_priority_count': len(recommendations['medium_priority']),
            'low_priority_count': len(recommendations['low_priority']),
            'total_space_saved_bytes': total_space_saved,
            'total_space_saved_mb': round(total_space_saved / (1024 * 1024), 2),
            'total_files_to_remove': total_files_to_remove,
        }
        
        return recommendations
    
    def _compile_statistics(self) -> Dict[str, Any]:
        """Compile comprehensive statistics from all detection methods"""
        stats = {
            'total_documents': self.total_documents,
            'hash_detection': self.hash_detector.get_statistics(),
            'similarity_analysis': self.similarity_analyzer.get_statistics(),
            'version_detection': self.version_detector.get_statistics(),
            'combined_totals': {},
        }
        
        # Calculate combined totals
        total_groups = 0
        total_duplicates = 0
        
        if self.hash_results:
            total_groups += len(self.hash_results.get('duplicate_groups', []))
            total_duplicates += sum(group['document_count'] - 1 for group in self.hash_results.get('duplicate_groups', []))
        
        if self.similarity_results:
            total_groups += len(self.similarity_results.get('similarity_groups', []))
            total_duplicates += sum(group['document_count'] - 1 for group in self.similarity_results.get('similarity_groups', []))
        
        if self.version_results:
            total_groups += len(self.version_results.get('version_groups', []))
            total_duplicates += sum(group['document_count'] - 1 for group in self.version_results.get('version_groups', []))
        
        stats['combined_totals'] = {
            'total_duplicate_groups': total_groups,
            'total_duplicate_files': total_duplicates,
            'duplicate_percentage': round((total_duplicates / self.total_documents) * 100, 2) if self.total_documents > 0 else 0,
        }
        
        return stats
    
    def get_duplicate_summary(self) -> Dict[str, Any]:
        """
        Get a high-level summary of duplicate detection results.
        
        Returns:
            dict: Summary of all duplicate detection results
        """
        summary = {
            'documents_analyzed': self.total_documents,
            'exact_duplicates': 0,
            'similar_documents': 0,
            'version_groups': 0,
            'total_wasted_space_mb': 0,
            'recommendations_count': 0,
        }
        
        if self.hash_results:
            summary['exact_duplicates'] = len(self.hash_results.get('duplicate_groups', []))
            summary['total_wasted_space_mb'] += self.hash_results.get('statistics', {}).get('total_wasted_space_mb', 0)
        
        if self.similarity_results:
            summary['similar_documents'] = len(self.similarity_results.get('similarity_groups', []))
        
        if self.version_results:
            summary['version_groups'] = len(self.version_results.get('version_groups', []))
        
        if self.combined_results:
            recommendations = self._generate_comprehensive_recommendations()
            summary['recommendations_count'] = recommendations['summary']['total_recommendations']
        
        return summary
    
    def reset_analysis(self):
        """Reset all analysis data and statistics"""
        self.hash_results = {}
        self.similarity_results = {}
        self.version_results = {}
        self.combined_results = {}
        
        self.total_documents = 0
        self.total_duplicate_groups = 0
        self.total_duplicates_found = 0
        self.total_space_wasted = 0
        
        # Reset component statistics
        self.hash_detector.reset_statistics()
        self.similarity_analyzer.reset_statistics()
        self.version_detector.reset_statistics()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics from all detection methods.
        
        Returns:
            dict: Combined statistics
        """
        return {
            'hash_detection': self.hash_detector.get_statistics(),
            'similarity_analysis': self.similarity_analyzer.get_statistics(),
            'version_detection': self.version_detector.get_statistics(),
            'total_documents': self.total_documents,
        }

