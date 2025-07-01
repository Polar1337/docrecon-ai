"""
CSV export functionality for DocRecon AI results

Exports analysis results to CSV format for further processing in spreadsheet
applications or data analysis tools.
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    Exports DocRecon AI analysis results to CSV format.
    
    Provides structured data export for:
    - Document inventory
    - Duplicate detection results
    - NLP analysis results
    - Recommendations
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize CSV exporter.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Export settings
        self.delimiter = ','
        self.quotechar = '"'
        self.encoding = 'utf-8-sig'  # UTF-8 with BOM for Excel compatibility
        
        # Statistics
        self.files_exported = 0
        self.rows_exported = 0
    
    def export_document_inventory(self, documents: List[Any], output_path: str) -> bool:
        """
        Export document inventory to CSV.
        
        Args:
            documents: List of DocumentInfo objects
            output_path: Path to output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting document inventory to {output_path}")
            
            # Define CSV headers
            headers = [
                'Document_ID',
                'Filename',
                'Path',
                'Size_Bytes',
                'Size_MB',
                'File_Extension',
                'MIME_Type',
                'Created_Date',
                'Modified_Date',
                'SHA256_Hash',
                'MD5_Hash',
                'Source_Type',
                'Text_Length',
                'Text_Preview',
            ]
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for doc in documents:
                    row = [
                        self._get_document_id(doc),
                        doc.filename,
                        doc.path,
                        doc.size,
                        round(doc.size / (1024 * 1024), 2),
                        doc.file_extension,
                        doc.mime_type or '',
                        doc.created_date.isoformat() if doc.created_date else '',
                        doc.modified_date.isoformat() if doc.modified_date else '',
                        doc.sha256_hash or '',
                        doc.md5_hash or '',
                        doc.source_type or '',
                        doc.text_length or 0,
                        (doc.text_content[:100] + '...') if doc.text_content else '',
                    ]
                    writer.writerow(row)
                    self.rows_exported += 1
            
            self.files_exported += 1
            self.logger.info(f"Successfully exported {len(documents)} documents to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting document inventory: {e}")
            return False
    
    def export_duplicate_groups(self, duplicate_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export duplicate detection results to CSV.
        
        Args:
            duplicate_results: Results from duplicate detection
            output_path: Path to output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting duplicate groups to {output_path}")
            
            # Define CSV headers
            headers = [
                'Group_ID',
                'Group_Type',
                'Document_Count',
                'Document_ID',
                'Filename',
                'Path',
                'Size_Bytes',
                'Size_MB',
                'Modified_Date',
                'Hash_Value',
                'Similarity_Score',
                'Wasted_Space_Bytes',
                'Recommendation',
                'Priority',
            ]
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                
                # Write header
                writer.writerow(headers)
                
                # Process different types of duplicate groups
                self._write_hash_duplicates(writer, duplicate_results.get('hash_duplicates', {}))
                self._write_similarity_duplicates(writer, duplicate_results.get('similarity_duplicates', {}))
                self._write_version_groups(writer, duplicate_results.get('version_groups', {}))
            
            self.files_exported += 1
            self.logger.info(f"Successfully exported duplicate groups to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting duplicate groups: {e}")
            return False
    
    def _write_hash_duplicates(self, writer: csv.writer, hash_results: Dict[str, Any]):
        """Write hash duplicate groups to CSV"""
        for group in hash_results.get('duplicate_groups', []):
            group_id = group['group_id']
            group_type = 'exact_duplicate'
            doc_count = group['document_count']
            hash_value = group.get('hash', '')
            wasted_space = group.get('wasted_space', 0)
            
            for doc in group['documents']:
                row = [
                    group_id,
                    group_type,
                    doc_count,
                    doc['id'],
                    doc['filename'],
                    doc['path'],
                    doc['size'],
                    doc['size_mb'],
                    doc['modified_date'],
                    hash_value,
                    1.0,  # Exact duplicates have 100% similarity
                    wasted_space // doc_count,  # Distribute wasted space
                    'delete_duplicate',
                    'high',
                ]
                writer.writerow(row)
                self.rows_exported += 1
    
    def _write_similarity_duplicates(self, writer: csv.writer, similarity_results: Dict[str, Any]):
        """Write similarity duplicate groups to CSV"""
        for group in similarity_results.get('similarity_groups', []):
            group_id = group['group_id']
            group_type = 'similar_content'
            doc_count = group['document_count']
            avg_similarity = group.get('avg_similarity', 0)
            
            for doc in group['documents']:
                row = [
                    group_id,
                    group_type,
                    doc_count,
                    doc['id'],
                    doc['filename'],
                    doc['path'],
                    doc['size'],
                    doc['size_mb'],
                    doc['modified_date'],
                    '',  # No hash for similarity groups
                    avg_similarity,
                    0,  # No direct space calculation for similarity
                    'review_similarity',
                    'medium' if avg_similarity > 0.9 else 'low',
                ]
                writer.writerow(row)
                self.rows_exported += 1
    
    def _write_version_groups(self, writer: csv.writer, version_results: Dict[str, Any]):
        """Write version groups to CSV"""
        for group in version_results.get('version_groups', []):
            group_id = group['group_id']
            group_type = 'document_versions'
            doc_count = group['document_count']
            
            for doc in group['documents']:
                row = [
                    group_id,
                    group_type,
                    doc_count,
                    doc['id'],
                    doc['filename'],
                    doc['path'],
                    doc['size'],
                    doc['size_mb'],
                    doc['modified_date'],
                    '',  # No hash for version groups
                    0.8,  # Estimated similarity for versions
                    0,  # No direct space calculation
                    'consolidate_versions',
                    'medium',
                ]
                writer.writerow(row)
                self.rows_exported += 1
    
    def export_nlp_results(self, nlp_results: Dict[str, Any], output_path: str) -> bool:
        """
        Export NLP analysis results to CSV.
        
        Args:
            nlp_results: Results from NLP analysis
            output_path: Path to output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting NLP results to {output_path}")
            
            # Define CSV headers
            headers = [
                'Document_ID',
                'Text_Length',
                'Entity_Type',
                'Entity_Text',
                'Entity_Count',
                'Keyword',
                'Keyword_Score',
                'Cluster_ID',
                'Cluster_Similarity',
            ]
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                
                # Write header
                writer.writerow(headers)
                
                # Process entities and keywords
                entities = nlp_results.get('entities', {})
                keywords = nlp_results.get('keywords', [])
                clusters = nlp_results.get('clusters', {})
                
                # Write entity data
                for entity_type, entity_list in entities.items():
                    for entity in entity_list:
                        for doc_id in entity.get('documents', []):
                            row = [
                                doc_id,
                                '',  # Text length will be filled separately
                                entity_type,
                                entity['text'],
                                entity['count'],
                                '',  # No keyword data in this row
                                '',  # No keyword score
                                '',  # No cluster data in this row
                                '',  # No cluster similarity
                            ]
                            writer.writerow(row)
                            self.rows_exported += 1
                
                # Write keyword data
                for keyword in keywords:
                    row = [
                        '',  # No specific document ID for aggregated keywords
                        '',
                        '',  # No entity data in this row
                        '',
                        '',
                        keyword['word'],
                        keyword['avg_score'],
                        '',  # No cluster data in this row
                        '',
                    ]
                    writer.writerow(row)
                    self.rows_exported += 1
            
            self.files_exported += 1
            self.logger.info(f"Successfully exported NLP results to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting NLP results: {e}")
            return False
    
    def export_recommendations(self, recommendations: Dict[str, Any], output_path: str) -> bool:
        """
        Export recommendations to CSV.
        
        Args:
            recommendations: Recommendations from analysis
            output_path: Path to output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting recommendations to {output_path}")
            
            # Define CSV headers
            headers = [
                'Recommendation_ID',
                'Priority',
                'Action',
                'Method',
                'Confidence',
                'Group_ID',
                'Document_Count',
                'Space_Saved_MB',
                'Reasoning',
                'Document_IDs',
            ]
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                
                # Write header
                writer.writerow(headers)
                
                # Write recommendations from all priority levels
                rec_id = 1
                for priority in ['high_priority', 'medium_priority', 'low_priority']:
                    for rec in recommendations.get(priority, []):
                        # Get document IDs
                        doc_ids = []
                        if 'delete_documents' in rec:
                            doc_ids = [doc['id'] for doc in rec['delete_documents']]
                        elif 'documents' in rec:
                            doc_ids = [doc['id'] for doc in rec['documents']]
                        
                        row = [
                            f"REC_{rec_id:04d}",
                            rec.get('priority', priority.replace('_priority', '')),
                            rec.get('action', ''),
                            rec.get('method', ''),
                            rec.get('confidence', 0),
                            rec.get('group_id', ''),
                            len(doc_ids),
                            rec.get('space_saved_mb', 0),
                            rec.get('reasoning', ''),
                            ';'.join(doc_ids),
                        ]
                        writer.writerow(row)
                        self.rows_exported += 1
                        rec_id += 1
            
            self.files_exported += 1
            self.logger.info(f"Successfully exported recommendations to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting recommendations: {e}")
            return False
    
    def export_summary_statistics(self, statistics: Dict[str, Any], output_path: str) -> bool:
        """
        Export summary statistics to CSV.
        
        Args:
            statistics: Statistics from analysis
            output_path: Path to output CSV file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Exporting summary statistics to {output_path}")
            
            # Define CSV headers
            headers = [
                'Metric',
                'Value',
                'Unit',
                'Category',
                'Description',
            ]
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Write CSV
            with open(output_path, 'w', newline='', encoding=self.encoding) as csvfile:
                writer = csv.writer(csvfile, delimiter=self.delimiter, quotechar=self.quotechar)
                
                # Write header
                writer.writerow(headers)
                
                # Flatten statistics into rows
                self._write_statistics_rows(writer, statistics, '')
            
            self.files_exported += 1
            self.logger.info(f"Successfully exported statistics to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting statistics: {e}")
            return False
    
    def _write_statistics_rows(self, writer: csv.writer, data: Any, prefix: str):
        """Recursively write statistics data to CSV"""
        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                self._write_statistics_rows(writer, value, new_prefix)
        elif isinstance(data, (int, float, str)):
            # Determine unit and category
            unit = ''
            category = prefix.split('.')[0] if '.' in prefix else 'general'
            description = prefix.replace('_', ' ').title()
            
            # Add units for common metrics
            if 'bytes' in prefix.lower():
                unit = 'bytes'
            elif 'mb' in prefix.lower():
                unit = 'MB'
            elif 'count' in prefix.lower() or 'total' in prefix.lower():
                unit = 'count'
            elif 'percentage' in prefix.lower():
                unit = '%'
            elif 'score' in prefix.lower():
                unit = 'score'
            
            row = [prefix, data, unit, category, description]
            writer.writerow(row)
            self.rows_exported += 1
    
    def _get_document_id(self, document: Any) -> str:
        """Generate unique ID for a document"""
        if hasattr(document, 'sha256_hash') and document.sha256_hash:
            return document.sha256_hash[:16]
        elif hasattr(document, 'md5_hash') and document.md5_hash:
            return document.md5_hash[:16]
        else:
            return f"{Path(document.path).stem}_{document.size}"
    
    def export_all_results(self, analysis_results: Dict[str, Any], output_dir: str) -> Dict[str, bool]:
        """
        Export all analysis results to separate CSV files.
        
        Args:
            analysis_results: Complete analysis results
            output_dir: Directory to save CSV files
            
        Returns:
            dict: Export status for each file
        """
        export_status = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Export document inventory
        if 'documents' in analysis_results:
            status = self.export_document_inventory(
                analysis_results['documents'],
                os.path.join(output_dir, 'document_inventory.csv')
            )
            export_status['document_inventory'] = status
        
        # Export duplicate groups
        if any(key in analysis_results for key in ['hash_duplicates', 'similarity_duplicates', 'version_groups']):
            duplicate_results = {
                'hash_duplicates': analysis_results.get('hash_duplicates', {}),
                'similarity_duplicates': analysis_results.get('similarity_duplicates', {}),
                'version_groups': analysis_results.get('version_groups', {}),
            }
            status = self.export_duplicate_groups(
                duplicate_results,
                os.path.join(output_dir, 'duplicate_groups.csv')
            )
            export_status['duplicate_groups'] = status
        
        # Export NLP results
        if any(key in analysis_results for key in ['entities', 'keywords', 'clusters']):
            nlp_results = {
                'entities': analysis_results.get('entities', {}),
                'keywords': analysis_results.get('keywords', []),
                'clusters': analysis_results.get('clusters', {}),
            }
            status = self.export_nlp_results(
                nlp_results,
                os.path.join(output_dir, 'nlp_analysis.csv')
            )
            export_status['nlp_analysis'] = status
        
        # Export recommendations
        if 'recommendations' in analysis_results:
            status = self.export_recommendations(
                analysis_results['recommendations'],
                os.path.join(output_dir, 'recommendations.csv')
            )
            export_status['recommendations'] = status
        
        # Export statistics
        if 'statistics' in analysis_results:
            status = self.export_summary_statistics(
                analysis_results['statistics'],
                os.path.join(output_dir, 'summary_statistics.csv')
            )
            export_status['summary_statistics'] = status
        
        return export_status
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get export statistics.
        
        Returns:
            dict: Export statistics
        """
        return {
            'files_exported': self.files_exported,
            'rows_exported': self.rows_exported,
        }
    
    def reset_statistics(self):
        """Reset export statistics"""
        self.files_exported = 0
        self.rows_exported = 0

