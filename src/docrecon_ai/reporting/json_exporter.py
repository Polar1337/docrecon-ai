"""
JSON export functionality for DocRecon AI results

Exports analysis results to JSON format for programmatic access,
API integration, and further processing by other tools.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Exports DocRecon AI analysis results to JSON format.
    
    Provides structured JSON export for:
    - Complete analysis results
    - Individual components (duplicates, NLP, etc.)
    - API-friendly formats
    - Compressed exports for large datasets
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize JSON exporter.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Export settings
        self.indent = 2
        self.ensure_ascii = False
        self.sort_keys = True
        
        # Statistics
        self.files_exported = 0
        self.total_size_exported = 0
    
    def export_complete_results(self, analysis_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export complete analysis results to JSON.
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting complete results to {output_path}")
            
            # Prepare data for JSON serialization
            json_data = self._prepare_for_json(analysis_results)
            
            # Add metadata
            json_data['export_metadata'] = {
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0',
                'tool_name': 'DocRecon AI',
                'data_format': 'complete_analysis',
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys,
                         default=self._json_serializer)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported complete results to {output_path} ({file_size:,} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting complete results: {e}")
            return False
    
    def export_document_inventory(self, documents: List[Any], output_path: str) -> bool:
        """
        Export document inventory to JSON.
        
        Args:
            documents: List of DocumentInfo objects
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting document inventory to {output_path}")
            
            # Convert documents to JSON-serializable format
            json_documents = []
            for doc in documents:
                doc_data = {
                    'id': self._get_document_id(doc),
                    'filename': doc.filename,
                    'path': doc.path,
                    'size': doc.size,
                    'size_mb': round(doc.size / (1024 * 1024), 2),
                    'file_extension': doc.file_extension,
                    'mime_type': doc.mime_type,
                    'created_date': doc.created_date.isoformat() if doc.created_date else None,
                    'modified_date': doc.modified_date.isoformat() if doc.modified_date else None,
                    'sha256_hash': doc.sha256_hash,
                    'md5_hash': doc.md5_hash,
                    'source_type': doc.source_type,
                    'text_length': doc.text_length,
                    'text_preview': (doc.text_content[:200] + '...') if doc.text_content else None,
                }
                json_documents.append(doc_data)
            
            # Create JSON structure
            json_data = {
                'document_inventory': {
                    'total_documents': len(documents),
                    'documents': json_documents,
                },
                'export_metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'export_version': '1.0',
                    'data_format': 'document_inventory',
                }
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported {len(documents)} documents to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting document inventory: {e}")
            return False
    
    def export_duplicate_results(self, duplicate_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export duplicate detection results to JSON.
        
        Args:
            duplicate_results: Results from duplicate detection
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting duplicate results to {output_path}")
            
            # Prepare duplicate results for JSON
            json_data = {
                'duplicate_analysis': self._prepare_for_json(duplicate_results),
                'export_metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'export_version': '1.0',
                    'data_format': 'duplicate_analysis',
                }
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys,
                         default=self._json_serializer)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported duplicate results to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting duplicate results: {e}")
            return False
    
    def export_nlp_results(self, nlp_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export NLP analysis results to JSON.
        
        Args:
            nlp_results: Results from NLP analysis
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting NLP results to {output_path}")
            
            # Prepare NLP results for JSON
            json_data = {
                'nlp_analysis': self._prepare_for_json(nlp_results),
                'export_metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'export_version': '1.0',
                    'data_format': 'nlp_analysis',
                }
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys,
                         default=self._json_serializer)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported NLP results to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting NLP results: {e}")
            return False
    
    def export_recommendations(self, recommendations: Dict[str, Any], output_path: str) -> bool:
        """
        Export recommendations to JSON.
        
        Args:
            recommendations: Recommendations from analysis
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting recommendations to {output_path}")
            
            # Prepare recommendations for JSON
            json_data = {
                'recommendations': self._prepare_for_json(recommendations),
                'export_metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'export_version': '1.0',
                    'data_format': 'recommendations',
                }
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys,
                         default=self._json_serializer)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported recommendations to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting recommendations: {e}")
            return False
    
    def export_api_format(self, analysis_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export results in API-friendly format.
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path to output JSON file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting API format to {output_path}")
            
            # Create API-friendly structure
            api_data = {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'data': {
                    'summary': self._create_api_summary(analysis_results),
                    'duplicates': self._create_api_duplicates(analysis_results),
                    'recommendations': self._create_api_recommendations(analysis_results),
                    'statistics': self._create_api_statistics(analysis_results),
                }
            }
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(api_data, f, 
                         indent=self.indent, 
                         ensure_ascii=self.ensure_ascii,
                         sort_keys=self.sort_keys,
                         default=self._json_serializer)
            
            # Update statistics
            file_size = os.path.getsize(output_path)
            self.files_exported += 1
            self.total_size_exported += file_size
            
            self.logger.info(f"Successfully exported API format to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting API format: {e}")
            return False
    
    def _prepare_for_json(self, data: Any) -> Any:
        """Prepare data for JSON serialization by handling special types"""
        if isinstance(data, dict):
            return {key: self._prepare_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, set):
            return list(data)
        elif hasattr(data, 'isoformat'):  # datetime objects
            return data.isoformat()
        else:
            return data
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def _create_api_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create API-friendly summary"""
        stats = results.get('statistics', {})
        
        return {
            'total_documents': stats.get('total_documents', 0),
            'duplicate_groups_found': self._count_duplicate_groups(results),
            'total_duplicates': self._count_total_duplicates(results),
            'space_wasted_mb': self._calculate_space_wasted(results),
            'recommendations_count': self._count_recommendations(results),
        }
    
    def _create_api_duplicates(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create API-friendly duplicate list"""
        duplicates = []
        
        # Hash duplicates
        if 'hash_duplicates' in results:
            for group in results['hash_duplicates'].get('duplicate_groups', []):
                duplicates.append({
                    'group_id': group['group_id'],
                    'type': 'exact_duplicate',
                    'method': 'hash',
                    'document_count': group['document_count'],
                    'confidence': 1.0,
                    'wasted_space_mb': group.get('wasted_space', 0) / (1024 * 1024),
                    'documents': [doc['id'] for doc in group['documents']],
                })
        
        # Similarity duplicates
        if 'similarity_duplicates' in results:
            for group in results['similarity_duplicates'].get('similarity_groups', []):
                duplicates.append({
                    'group_id': group['group_id'],
                    'type': 'similar_content',
                    'method': 'similarity',
                    'document_count': group['document_count'],
                    'confidence': group['avg_similarity'],
                    'documents': [doc['id'] for doc in group['documents']],
                })
        
        # Version groups
        if 'version_groups' in results:
            for group in results['version_groups'].get('version_groups', []):
                duplicates.append({
                    'group_id': group['group_id'],
                    'type': 'document_versions',
                    'method': 'versioning',
                    'document_count': group['document_count'],
                    'confidence': 0.8,
                    'documents': [doc['id'] for doc in group['documents']],
                })
        
        return duplicates
    
    def _create_api_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create API-friendly recommendations"""
        recommendations = []
        rec_data = results.get('recommendations', {})
        
        for priority in ['high_priority', 'medium_priority', 'low_priority']:
            for rec in rec_data.get(priority, []):
                recommendations.append({
                    'id': rec.get('group_id', ''),
                    'priority': rec.get('priority', priority.replace('_priority', '')),
                    'action': rec.get('action', ''),
                    'method': rec.get('method', ''),
                    'confidence': rec.get('confidence', 0),
                    'space_saved_mb': rec.get('space_saved_mb', 0),
                    'reasoning': rec.get('reasoning', ''),
                })
        
        return recommendations
    
    def _create_api_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create API-friendly statistics"""
        stats = results.get('statistics', {})
        
        return {
            'processing': {
                'total_documents': stats.get('total_documents', 0),
                'processing_time': stats.get('processing_time', 0),
            },
            'duplicates': {
                'exact_duplicates': len(results.get('hash_duplicates', {}).get('duplicate_groups', [])),
                'similar_documents': len(results.get('similarity_duplicates', {}).get('similarity_groups', [])),
                'version_groups': len(results.get('version_groups', {}).get('version_groups', [])),
            },
            'storage': {
                'total_size_mb': self._calculate_total_size(results),
                'wasted_space_mb': self._calculate_space_wasted(results),
                'potential_savings_mb': self._calculate_potential_savings(results),
            }
        }
    
    def _count_duplicate_groups(self, results: Dict[str, Any]) -> int:
        """Count total duplicate groups across all methods"""
        count = 0
        if 'hash_duplicates' in results:
            count += len(results['hash_duplicates'].get('duplicate_groups', []))
        if 'similarity_duplicates' in results:
            count += len(results['similarity_duplicates'].get('similarity_groups', []))
        if 'version_groups' in results:
            count += len(results['version_groups'].get('version_groups', []))
        return count
    
    def _count_total_duplicates(self, results: Dict[str, Any]) -> int:
        """Count total duplicate files across all methods"""
        count = 0
        if 'hash_duplicates' in results:
            for group in results['hash_duplicates'].get('duplicate_groups', []):
                count += group['document_count'] - 1  # Subtract original
        if 'similarity_duplicates' in results:
            for group in results['similarity_duplicates'].get('similarity_groups', []):
                count += group['document_count'] - 1
        if 'version_groups' in results:
            for group in results['version_groups'].get('version_groups', []):
                count += group['document_count'] - 1
        return count
    
    def _calculate_space_wasted(self, results: Dict[str, Any]) -> float:
        """Calculate total wasted space in MB"""
        wasted = 0
        if 'hash_duplicates' in results:
            stats = results['hash_duplicates'].get('statistics', {})
            wasted += stats.get('total_wasted_space_mb', 0)
        return wasted
    
    def _calculate_total_size(self, results: Dict[str, Any]) -> float:
        """Calculate total size of all documents in MB"""
        # This would need to be calculated from document inventory
        return 0  # Placeholder
    
    def _calculate_potential_savings(self, results: Dict[str, Any]) -> float:
        """Calculate potential storage savings in MB"""
        savings = 0
        rec_data = results.get('recommendations', {})
        summary = rec_data.get('summary', {})
        savings += summary.get('total_space_saved_mb', 0)
        return savings
    
    def _count_recommendations(self, results: Dict[str, Any]) -> int:
        """Count total recommendations"""
        rec_data = results.get('recommendations', {})
        summary = rec_data.get('summary', {})
        return summary.get('total_recommendations', 0)
    
    def _get_document_id(self, document: Any) -> str:
        """Generate unique ID for a document"""
        if hasattr(document, 'sha256_hash') and document.sha256_hash:
            return document.sha256_hash[:16]
        elif hasattr(document, 'md5_hash') and document.md5_hash:
            return document.md5_hash[:16]
        else:
            return f"{Path(document.path).stem}_{document.size}"
    
    def export_all_formats(self, analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, bool]:
        """
        Export results in all JSON formats.
        
        Args:
            analysis_results: Complete analysis results
            output_dir: Directory to save JSON files
            
        Returns:
            dict: Export status for each format
        """
        export_status = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Export complete results
        status = self.export_complete_results(
            analysis_results,
            os.path.join(output_dir, 'complete_analysis.json')
        )
        export_status['complete_analysis'] = status
        
        # Export API format
        status = self.export_api_format(
            analysis_results,
            os.path.join(output_dir, 'api_format.json')
        )
        export_status['api_format'] = status
        
        # Export individual components
        if 'documents' in analysis_results:
            status = self.export_document_inventory(
                analysis_results['documents'],
                os.path.join(output_dir, 'document_inventory.json')
            )
            export_status['document_inventory'] = status
        
        if any(key in analysis_results for key in ['hash_duplicates', 'similarity_duplicates', 'version_groups']):
            duplicate_results = {
                'hash_duplicates': analysis_results.get('hash_duplicates', {}),
                'similarity_duplicates': analysis_results.get('similarity_duplicates', {}),
                'version_groups': analysis_results.get('version_groups', {}),
            }
            status = self.export_duplicate_results(
                duplicate_results,
                os.path.join(output_dir, 'duplicate_analysis.json')
            )
            export_status['duplicate_analysis'] = status
        
        if any(key in analysis_results for key in ['entities', 'keywords', 'clusters']):
            nlp_results = {
                'entities': analysis_results.get('entities', {}),
                'keywords': analysis_results.get('keywords', []),
                'clusters': analysis_results.get('clusters', {}),
            }
            status = self.export_nlp_results(
                nlp_results,
                os.path.join(output_dir, 'nlp_analysis.json')
            )
            export_status['nlp_analysis'] = status
        
        if 'recommendations' in analysis_results:
            status = self.export_recommendations(
                analysis_results['recommendations'],
                os.path.join(output_dir, 'recommendations.json')
            )
            export_status['recommendations'] = status
        
        return export_status
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get export statistics.
        
        Returns:
            dict: Export statistics
        """
        return {
            'files_exported': self.files_exported,
            'total_size_exported': self.total_size_exported,
            'total_size_mb': round(self.total_size_exported / (1024 * 1024), 2),
        }
    
    def reset_statistics(self):
        """Reset export statistics"""
        self.files_exported = 0
        self.total_size_exported = 0

