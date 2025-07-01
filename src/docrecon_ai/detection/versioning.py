"""
Version detection based on filename patterns

Detects different versions of documents by analyzing filename patterns,
version numbers, and common versioning conventions.
"""

import re
from collections import defaultdict
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import logging

from ..crawler.base import DocumentInfo

logger = logging.getLogger(__name__)

# Optional fuzzy matching
try:
    from difflib import SequenceMatcher
    DIFFLIB_AVAILABLE = True
except ImportError:
    DIFFLIB_AVAILABLE = False

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    logger.warning("fuzzywuzzy not available. Install: pip install fuzzywuzzy")


class VersionDetector:
    """
    Detects document versions based on filename patterns and conventions.
    
    Identifies files that are likely different versions of the same document
    by analyzing naming patterns, version numbers, and timestamps.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize version detector.
        
        Args:
            config: Configuration object with duplicate detection settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.filename_similarity_threshold = getattr(config.duplicates, 'filename_similarity_threshold', 0.8) if config else 0.8
        self.enable_fuzzy_matching = getattr(config.duplicates, 'enable_fuzzy_matching', True) if config else True
        
        # Version patterns (regex patterns to identify version indicators)
        self.version_patterns = [
            # Version numbers: v1, v2.0, version1, ver2
            r'[_\-\s]v(\d+)(?:\.(\d+))?(?:\.(\d+))?[_\-\s]?',
            r'[_\-\s]version[_\-\s]?(\d+)(?:\.(\d+))?(?:\.(\d+))?[_\-\s]?',
            r'[_\-\s]ver[_\-\s]?(\d+)(?:\.(\d+))?(?:\.(\d+))?[_\-\s]?',
            
            # Revision numbers: rev1, revision2, r3
            r'[_\-\s]rev(?:ision)?[_\-\s]?(\d+)[_\-\s]?',
            r'[_\-\s]r(\d+)[_\-\s]?',
            
            # Draft numbers: draft1, draft_2
            r'[_\-\s]draft[_\-\s]?(\d+)[_\-\s]?',
            
            # Copy indicators: copy, copy(1), copy_2
            r'[_\-\s]copy(?:[_\-\s]?\((\d+)\))?[_\-\s]?',
            r'[_\-\s]copy[_\-\s]?(\d+)[_\-\s]?',
            
            # Final/backup indicators
            r'[_\-\s](final|backup|old|new|latest|current)[_\-\s]?(\d+)?[_\-\s]?',
            
            # Date patterns: 20231201, 2023-12-01, 01122023
            r'[_\-\s](\d{4})[_\-]?(\d{2})[_\-]?(\d{2})[_\-\s]?',
            r'[_\-\s](\d{2})[_\-]?(\d{2})[_\-]?(\d{4})[_\-\s]?',
            
            # Timestamp patterns: 143000, 14-30-00
            r'[_\-\s](\d{2})[_\-]?(\d{2})[_\-]?(\d{2})[_\-\s]?',
            
            # Parenthetical numbers: (1), (2), (copy)
            r'\((\d+)\)',
            r'\((copy|backup|final|old|new)\)',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.version_patterns]
        
        # Statistics
        self.documents_processed = 0
        self.version_groups_found = 0
        self.filename_comparisons = 0
    
    def find_document_versions(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """
        Find document versions based on filename analysis.
        
        Args:
            documents: List of DocumentInfo objects to analyze
            
        Returns:
            dict: Version detection results
        """
        self.logger.info(f"Detecting versions for {len(documents)} documents")
        
        # Group documents by base filename (without version indicators)
        base_groups = self._group_by_base_filename(documents)
        
        # Find version groups
        version_groups = []
        for base_name, docs in base_groups.items():
            if len(docs) > 1:
                # Analyze this group for versions
                group_analysis = self._analyze_version_group(base_name, docs)
                if group_analysis:
                    version_groups.append(group_analysis)
        
        # Additional fuzzy matching for similar filenames
        if self.enable_fuzzy_matching:
            fuzzy_groups = self._find_fuzzy_filename_matches(documents)
            version_groups.extend(fuzzy_groups)
        
        self.version_groups_found = len(version_groups)
        self.documents_processed = len(documents)
        
        results = {
            'method': 'filename_versioning',
            'version_groups': version_groups,
            'statistics': {
                'documents_processed': self.documents_processed,
                'version_groups_found': self.version_groups_found,
                'filename_comparisons': self.filename_comparisons,
                'base_filename_groups': len(base_groups),
            }
        }
        
        return results
    
    def _group_by_base_filename(self, documents: List[DocumentInfo]) -> Dict[str, List[DocumentInfo]]:
        """Group documents by their base filename (removing version indicators)"""
        base_groups = defaultdict(list)
        
        for doc in documents:
            base_name = self._extract_base_filename(doc.filename)
            base_groups[base_name].append(doc)
        
        return dict(base_groups)
    
    def _extract_base_filename(self, filename: str) -> str:
        """Extract base filename by removing version indicators"""
        # Remove file extension
        name_without_ext = Path(filename).stem
        
        # Remove version patterns
        base_name = name_without_ext
        for pattern in self.compiled_patterns:
            base_name = pattern.sub('', base_name)
        
        # Clean up extra spaces, dashes, underscores
        base_name = re.sub(r'[_\-\s]+', '_', base_name)
        base_name = base_name.strip('_-')
        
        # If base name is empty or too short, use original
        if len(base_name) < 3:
            base_name = name_without_ext
        
        return base_name.lower()
    
    def _analyze_version_group(self, base_name: str, documents: List[DocumentInfo]) -> Optional[Dict[str, Any]]:
        """Analyze a group of documents with the same base filename"""
        if len(documents) < 2:
            return None
        
        # Extract version information for each document
        version_info = []
        for doc in documents:
            info = self._extract_version_info(doc)
            version_info.append(info)
        
        # Check if this is actually a version group
        if not self._is_valid_version_group(version_info):
            return None
        
        # Sort by version/date
        sorted_versions = self._sort_versions(version_info)
        
        # Create group analysis
        group = {
            'group_id': f"ver_{hash(base_name) % 10000}",
            'type': 'filename_versions',
            'base_name': base_name,
            'document_count': len(documents),
            'documents': [self._document_to_dict(info['document']) for info in sorted_versions],
            'version_analysis': {
                'has_version_numbers': any(info['version_number'] for info in version_info),
                'has_dates': any(info['date_info'] for info in version_info),
                'has_copy_indicators': any(info['copy_indicator'] for info in version_info),
                'version_pattern': self._identify_version_pattern(version_info),
            },
            'timeline': self._create_version_timeline(sorted_versions),
        }
        
        return group
    
    def _extract_version_info(self, document: DocumentInfo) -> Dict[str, Any]:
        """Extract version information from a document"""
        filename = document.filename
        name_without_ext = Path(filename).stem
        
        info = {
            'document': document,
            'filename': filename,
            'base_name': name_without_ext,
            'version_number': None,
            'revision_number': None,
            'copy_indicator': None,
            'date_info': None,
            'timestamp_info': None,
            'special_indicators': [],
            'version_score': 0,  # Higher score = likely newer version
        }
        
        # Check each pattern
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.findall(name_without_ext.lower())
            if matches:
                match = matches[0] if isinstance(matches[0], str) else matches[0][0] if matches[0] else None
                
                if i < 3:  # Version number patterns
                    if isinstance(matches[0], tuple):
                        version_parts = [int(p) for p in matches[0] if p.isdigit()]
                        info['version_number'] = version_parts
                        info['version_score'] += sum(p * (10 ** (len(version_parts) - i - 1)) for i, p in enumerate(version_parts))
                    elif match and match.isdigit():
                        info['version_number'] = [int(match)]
                        info['version_score'] += int(match)
                
                elif i < 5:  # Revision patterns
                    if match and match.isdigit():
                        info['revision_number'] = int(match)
                        info['version_score'] += int(match)
                
                elif i < 7:  # Draft patterns
                    if match and match.isdigit():
                        info['version_score'] += int(match)
                        info['special_indicators'].append(f"draft_{match}")
                
                elif i < 9:  # Copy patterns
                    info['copy_indicator'] = match or 'copy'
                    if match and match.isdigit():
                        info['version_score'] += int(match)
                
                elif i < 10:  # Final/backup indicators
                    indicator = match.lower() if isinstance(match, str) else matches[0][0].lower()
                    info['special_indicators'].append(indicator)
                    
                    # Assign scores based on indicator
                    score_map = {'old': -10, 'backup': -5, 'draft': 0, 'current': 5, 'new': 8, 'latest': 10, 'final': 15}
                    info['version_score'] += score_map.get(indicator, 0)
                
                elif i < 12:  # Date patterns
                    if isinstance(matches[0], tuple) and len(matches[0]) >= 3:
                        try:
                            year, month, day = matches[0][:3]
                            if len(year) == 4:  # YYYY-MM-DD format
                                info['date_info'] = f"{year}-{month}-{day}"
                                info['version_score'] += int(year) * 10000 + int(month) * 100 + int(day)
                            else:  # DD-MM-YYYY format
                                info['date_info'] = f"{matches[0][2]}-{month}-{year}"
                                info['version_score'] += int(matches[0][2]) * 10000 + int(month) * 100 + int(year)
                        except (ValueError, IndexError):
                            pass
        
        # Use file modification date as additional version indicator
        if document.modified_date:
            info['file_modified_date'] = document.modified_date
            # Add timestamp to version score (days since epoch)
            info['version_score'] += document.modified_date.timestamp() / (24 * 3600)
        
        return info
    
    def _is_valid_version_group(self, version_info: List[Dict[str, Any]]) -> bool:
        """Check if a group of files represents valid versions"""
        # Must have at least one version indicator
        has_version_indicators = any(
            info['version_number'] or info['revision_number'] or 
            info['copy_indicator'] or info['date_info'] or 
            info['special_indicators']
            for info in version_info
        )
        
        if not has_version_indicators:
            return False
        
        # Check if files have same extension
        extensions = [Path(info['filename']).suffix for info in version_info]
        same_extension = len(set(extensions)) == 1
        
        # Check if files have similar sizes (within reasonable range)
        sizes = [info['document'].size for info in version_info]
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            size_variance = sum((size - avg_size) ** 2 for size in sizes) / len(sizes)
            reasonable_variance = size_variance < (avg_size * 0.5) ** 2  # 50% variance threshold
        else:
            reasonable_variance = True
        
        return same_extension and reasonable_variance
    
    def _sort_versions(self, version_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort versions by their version score (oldest to newest)"""
        return sorted(version_info, key=lambda x: x['version_score'])
    
    def _identify_version_pattern(self, version_info: List[Dict[str, Any]]) -> str:
        """Identify the versioning pattern used"""
        patterns = []
        
        if any(info['version_number'] for info in version_info):
            patterns.append('version_numbers')
        
        if any(info['revision_number'] for info in version_info):
            patterns.append('revision_numbers')
        
        if any(info['copy_indicator'] for info in version_info):
            patterns.append('copy_indicators')
        
        if any(info['date_info'] for info in version_info):
            patterns.append('date_stamps')
        
        if any(info['special_indicators'] for info in version_info):
            patterns.append('special_indicators')
        
        return ', '.join(patterns) if patterns else 'unknown'
    
    def _create_version_timeline(self, sorted_versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create a timeline of versions"""
        timeline = []
        
        for i, version in enumerate(sorted_versions):
            entry = {
                'order': i + 1,
                'filename': version['filename'],
                'version_score': version['version_score'],
                'is_likely_original': i == 0,
                'is_likely_latest': i == len(sorted_versions) - 1,
                'indicators': [],
            }
            
            # Add version indicators
            if version['version_number']:
                entry['indicators'].append(f"v{'.'.join(map(str, version['version_number']))}")
            
            if version['revision_number']:
                entry['indicators'].append(f"rev{version['revision_number']}")
            
            if version['copy_indicator']:
                entry['indicators'].append(f"copy({version['copy_indicator']})")
            
            if version['date_info']:
                entry['indicators'].append(f"date({version['date_info']})")
            
            if version['special_indicators']:
                entry['indicators'].extend(version['special_indicators'])
            
            if version['document'].modified_date:
                entry['file_date'] = version['document'].modified_date.isoformat()
            
            timeline.append(entry)
        
        return timeline
    
    def _find_fuzzy_filename_matches(self, documents: List[DocumentInfo]) -> List[Dict[str, Any]]:
        """Find documents with similar filenames using fuzzy matching"""
        if not (DIFFLIB_AVAILABLE or FUZZYWUZZY_AVAILABLE):
            return []
        
        fuzzy_groups = []
        processed_docs = set()
        
        for i, doc1 in enumerate(documents):
            if id(doc1) in processed_docs:
                continue
            
            similar_docs = [doc1]
            processed_docs.add(id(doc1))
            
            for j, doc2 in enumerate(documents[i+1:], i+1):
                if id(doc2) in processed_docs:
                    continue
                
                similarity = self._calculate_filename_similarity(doc1.filename, doc2.filename)
                self.filename_comparisons += 1
                
                if similarity >= self.filename_similarity_threshold:
                    similar_docs.append(doc2)
                    processed_docs.add(id(doc2))
            
            if len(similar_docs) > 1:
                # Create fuzzy group
                group = {
                    'group_id': f"fuzzy_{len(fuzzy_groups)}",
                    'type': 'fuzzy_filename_match',
                    'document_count': len(similar_docs),
                    'documents': [self._document_to_dict(doc) for doc in similar_docs],
                    'similarity_analysis': self._analyze_filename_similarities(similar_docs),
                }
                fuzzy_groups.append(group)
        
        return fuzzy_groups
    
    def _calculate_filename_similarity(self, filename1: str, filename2: str) -> float:
        """Calculate similarity between two filenames"""
        # Remove extensions and normalize
        name1 = Path(filename1).stem.lower()
        name2 = Path(filename2).stem.lower()
        
        if FUZZYWUZZY_AVAILABLE:
            # Use fuzzywuzzy for better fuzzy matching
            return fuzz.ratio(name1, name2) / 100.0
        elif DIFFLIB_AVAILABLE:
            # Use difflib as fallback
            return SequenceMatcher(None, name1, name2).ratio()
        else:
            # Simple character-based similarity
            common_chars = set(name1) & set(name2)
            total_chars = set(name1) | set(name2)
            return len(common_chars) / len(total_chars) if total_chars else 0.0
    
    def _analyze_filename_similarities(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """Analyze similarities between filenames in a group"""
        filenames = [doc.filename for doc in documents]
        
        # Calculate pairwise similarities
        similarities = []
        for i, name1 in enumerate(filenames):
            for name2 in filenames[i+1:]:
                sim = self._calculate_filename_similarity(name1, name2)
                similarities.append(sim)
        
        analysis = {
            'avg_similarity': sum(similarities) / len(similarities) if similarities else 0.0,
            'min_similarity': min(similarities) if similarities else 0.0,
            'max_similarity': max(similarities) if similarities else 0.0,
            'filename_lengths': [len(name) for name in filenames],
            'common_words': self._find_common_words(filenames),
        }
        
        return analysis
    
    def _find_common_words(self, filenames: List[str]) -> List[str]:
        """Find common words across filenames"""
        # Extract words from filenames
        all_words = []
        for filename in filenames:
            name = Path(filename).stem.lower()
            # Split on common separators
            words = re.split(r'[_\-\s\.]+', name)
            all_words.extend([word for word in words if len(word) > 2])
        
        # Count word frequencies
        word_counts = defaultdict(int)
        for word in all_words:
            word_counts[word] += 1
        
        # Return words that appear in multiple filenames
        common_words = [word for word, count in word_counts.items() if count > 1]
        return sorted(common_words, key=lambda x: word_counts[x], reverse=True)
    
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
            'source_type': document.source_type,
        }
    
    def _get_document_id(self, document: DocumentInfo) -> str:
        """Generate unique ID for a document"""
        if document.sha256_hash:
            return document.sha256_hash[:16]
        elif document.md5_hash:
            return document.md5_hash[:16]
        else:
            return f"{Path(document.path).stem}_{document.size}"
    
    def get_version_recommendations(self, version_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for handling document versions.
        
        Args:
            version_results: Results from version detection
            
        Returns:
            list: Recommendations for each version group
        """
        recommendations = []
        
        for group in version_results.get('version_groups', []):
            timeline = group.get('timeline', [])
            
            if len(timeline) < 2:
                continue
            
            # Find latest version
            latest_version = max(timeline, key=lambda x: x['version_score'])
            older_versions = [v for v in timeline if v != latest_version]
            
            recommendation = {
                'group_id': group['group_id'],
                'action': 'consolidate_versions',
                'keep_version': latest_version,
                'archive_versions': older_versions,
                'reasoning': f"Keep latest version ({latest_version['filename']}) and archive {len(older_versions)} older versions",
                'space_saved_estimate': sum(
                    doc['size'] for doc in group['documents'] 
                    if doc['filename'] != latest_version['filename']
                ),
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get version detection statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'documents_processed': self.documents_processed,
            'version_groups_found': self.version_groups_found,
            'filename_comparisons': self.filename_comparisons,
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.documents_processed = 0
        self.version_groups_found = 0
        self.filename_comparisons = 0

