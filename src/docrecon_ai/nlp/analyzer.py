"""
Main NLP analyzer that coordinates all NLP components

Provides a unified interface for text extraction, embedding generation,
entity recognition, and document clustering.
"""

from typing import List, Dict, Any, Optional, Iterator
import logging
from pathlib import Path

from ..crawler.base import DocumentInfo
from .extractor import TextExtractor
from .embeddings import EmbeddingGenerator
from .clustering import DocumentClusterer
from .entities import EntityExtractor

logger = logging.getLogger(__name__)


class NLPAnalyzer:
    """
    Main NLP analyzer that coordinates all NLP processing.
    
    Provides a unified interface for:
    - Text extraction from documents
    - Embedding generation for semantic analysis
    - Named entity recognition and keyword extraction
    - Document clustering based on content similarity
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize NLP analyzer.
        
        Args:
            config: Configuration object with NLP settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        self.text_extractor = TextExtractor(config)
        self.embedding_generator = EmbeddingGenerator(config)
        self.document_clusterer = DocumentClusterer(config)
        self.entity_extractor = EntityExtractor(config)
        
        # Processing settings
        self.enable_text_extraction = True
        self.enable_embeddings = True
        self.enable_clustering = getattr(config.nlp, 'enable_clustering', True) if config else True
        self.enable_entities = getattr(config.nlp, 'enable_entities', True) if config else True
        self.enable_keywords = getattr(config.nlp, 'enable_keywords', True) if config else True
        
        # Results storage
        self.document_texts = {}
        self.document_embeddings = {}
        self.document_entities = {}
        self.document_keywords = {}
        self.cluster_results = {}
        
        # Statistics
        self.documents_processed = 0
        self.processing_errors = 0
    
    def analyze_documents(self, documents: List[DocumentInfo], 
                         extract_text: bool = True,
                         generate_embeddings: bool = True,
                         extract_entities: bool = True,
                         cluster_documents: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive NLP analysis on a list of documents.
        
        Args:
            documents: List of DocumentInfo objects to analyze
            extract_text: Whether to extract text content
            generate_embeddings: Whether to generate embeddings
            extract_entities: Whether to extract entities and keywords
            cluster_documents: Whether to cluster documents
            
        Returns:
            dict: Complete analysis results
        """
        self.logger.info(f"Starting NLP analysis of {len(documents)} documents")
        
        results = {
            'documents_analyzed': len(documents),
            'text_extraction': {},
            'embeddings': {},
            'entities': {},
            'keywords': {},
            'clusters': {},
            'statistics': {},
        }
        
        # Step 1: Extract text content
        if extract_text and self.enable_text_extraction:
            self.logger.info("Extracting text content...")
            text_results = self._extract_text_from_documents(documents)
            results['text_extraction'] = text_results
        
        # Step 2: Generate embeddings
        if generate_embeddings and self.enable_embeddings:
            self.logger.info("Generating embeddings...")
            embedding_results = self._generate_document_embeddings()
            results['embeddings'] = embedding_results
        
        # Step 3: Extract entities and keywords
        if extract_entities and (self.enable_entities or self.enable_keywords):
            self.logger.info("Extracting entities and keywords...")
            entity_results = self._extract_entities_and_keywords()
            results['entities'] = entity_results['entities']
            results['keywords'] = entity_results['keywords']
        
        # Step 4: Cluster documents
        if cluster_documents and self.enable_clustering and self.document_embeddings:
            self.logger.info("Clustering documents...")
            cluster_results = self._cluster_documents()
            results['clusters'] = cluster_results
        
        # Step 5: Compile statistics
        results['statistics'] = self._get_analysis_statistics()
        
        self.logger.info("NLP analysis completed")
        return results
    
    def analyze_single_document(self, document: DocumentInfo) -> Dict[str, Any]:
        """
        Analyze a single document.
        
        Args:
            document: DocumentInfo object to analyze
            
        Returns:
            dict: Analysis results for the document
        """
        doc_id = self._get_document_id(document)
        
        result = {
            'document_id': doc_id,
            'filename': document.filename,
            'path': document.path,
            'text_content': None,
            'text_length': 0,
            'embedding': None,
            'entities': {},
            'keywords': [],
            'success': False,
            'error': None,
        }
        
        try:
            # Extract text
            if self.enable_text_extraction:
                text_result = self.text_extractor.extract_text(document.path, document.file_extension)
                if text_result['success']:
                    result['text_content'] = text_result['text']
                    result['text_length'] = text_result['length']
                    self.document_texts[doc_id] = text_result['text']
                    
                    # Update document info
                    document.text_content = text_result['text']
                    document.text_length = text_result['length']
                else:
                    result['error'] = text_result.get('error', 'Text extraction failed')
            
            # Generate embedding
            if self.enable_embeddings and result['text_content']:
                embeddings = self.embedding_generator.generate_embeddings(
                    [result['text_content']], [doc_id]
                )
                if doc_id in embeddings:
                    result['embedding'] = embeddings[doc_id]
                    self.document_embeddings[doc_id] = embeddings[doc_id]
            
            # Extract entities and keywords
            if (self.enable_entities or self.enable_keywords) and result['text_content']:
                entity_result = self.entity_extractor.extract_entities_and_keywords(
                    result['text_content']
                )
                result['entities'] = entity_result['entities']
                result['keywords'] = entity_result['keywords']
                
                self.document_entities[doc_id] = entity_result['entities']
                self.document_keywords[doc_id] = entity_result['keywords']
            
            result['success'] = True
            self.documents_processed += 1
            
        except Exception as e:
            self.logger.error(f"Error analyzing document {document.filename}: {e}")
            result['error'] = str(e)
            self.processing_errors += 1
        
        return result
    
    def _extract_text_from_documents(self, documents: List[DocumentInfo]) -> Dict[str, Any]:
        """Extract text from all documents"""
        results = {
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_text_length': 0,
            'extraction_methods': {},
            'errors': [],
        }
        
        for document in documents:
            doc_id = self._get_document_id(document)
            
            try:
                text_result = self.text_extractor.extract_text(document.path, document.file_extension)
                
                if text_result['success']:
                    self.document_texts[doc_id] = text_result['text']
                    
                    # Update document info
                    document.text_content = text_result['text']
                    document.text_length = text_result['length']
                    
                    # Update statistics
                    results['successful_extractions'] += 1
                    results['total_text_length'] += text_result['length']
                    
                    method = text_result.get('extraction_method', 'unknown')
                    results['extraction_methods'][method] = results['extraction_methods'].get(method, 0) + 1
                    
                else:
                    results['failed_extractions'] += 1
                    error_msg = f"{document.filename}: {text_result.get('error', 'Unknown error')}"
                    results['errors'].append(error_msg)
                    
            except Exception as e:
                results['failed_extractions'] += 1
                error_msg = f"{document.filename}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(f"Error extracting text from {document.filename}: {e}")
        
        return results
    
    def _generate_document_embeddings(self) -> Dict[str, Any]:
        """Generate embeddings for all documents with text"""
        results = {
            'embeddings_generated': 0,
            'cache_hits': 0,
            'embedding_dimension': None,
            'model_info': {},
        }
        
        if not self.document_texts:
            return results
        
        try:
            # Generate embeddings
            texts = list(self.document_texts.values())
            doc_ids = list(self.document_texts.keys())
            
            embeddings = self.embedding_generator.generate_embeddings(texts, doc_ids)
            self.document_embeddings.update(embeddings)
            
            # Update statistics
            stats = self.embedding_generator.get_statistics()
            results['embeddings_generated'] = stats['embeddings_generated']
            results['cache_hits'] = stats['cache_hits']
            
            # Get model info
            results['model_info'] = self.embedding_generator.get_embedding_info()
            results['embedding_dimension'] = results['model_info'].get('embedding_dim')
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {e}")
        
        return results
    
    def _extract_entities_and_keywords(self) -> Dict[str, Any]:
        """Extract entities and keywords from all documents"""
        results = {
            'entities': {},
            'keywords': {},
            'entity_summary': {},
            'keyword_summary': {},
        }
        
        all_entities = {}
        all_keywords = []
        
        for doc_id, text in self.document_texts.items():
            try:
                entity_result = self.entity_extractor.extract_entities_and_keywords(text)
                
                # Store per-document results
                self.document_entities[doc_id] = entity_result['entities']
                self.document_keywords[doc_id] = entity_result['keywords']
                
                # Aggregate entities
                for entity_type, entities in entity_result['entities'].items():
                    if entity_type not in all_entities:
                        all_entities[entity_type] = {}
                    
                    for entity in entities:
                        entity_text = entity['text']
                        if entity_text in all_entities[entity_type]:
                            all_entities[entity_type][entity_text]['count'] += entity['count']
                            all_entities[entity_type][entity_text]['documents'].add(doc_id)
                        else:
                            all_entities[entity_type][entity_text] = {
                                'count': entity['count'],
                                'documents': {doc_id},
                                'confidence': entity.get('confidence', 1.0)
                            }
                
                # Aggregate keywords
                all_keywords.extend(entity_result['keywords'])
                
            except Exception as e:
                self.logger.error(f"Error extracting entities for document {doc_id}: {e}")
        
        # Process aggregated entities
        processed_entities = {}
        for entity_type, entities in all_entities.items():
            processed_entities[entity_type] = []
            for entity_text, entity_data in entities.items():
                processed_entities[entity_type].append({
                    'text': entity_text,
                    'count': entity_data['count'],
                    'document_count': len(entity_data['documents']),
                    'documents': list(entity_data['documents']),
                    'confidence': entity_data['confidence']
                })
            
            # Sort by count
            processed_entities[entity_type].sort(key=lambda x: x['count'], reverse=True)
        
        results['entities'] = processed_entities
        results['entity_summary'] = self.entity_extractor.get_entity_summary(processed_entities)
        
        # Process aggregated keywords
        keyword_counts = {}
        for kw in all_keywords:
            word = kw['word']
            if word in keyword_counts:
                keyword_counts[word]['total_score'] += kw['score']
                keyword_counts[word]['count'] += 1
            else:
                keyword_counts[word] = {
                    'total_score': kw['score'],
                    'count': 1,
                    'methods': {kw.get('method', 'unknown')}
                }
        
        # Create final keyword list
        final_keywords = []
        for word, data in keyword_counts.items():
            avg_score = data['total_score'] / data['count']
            final_keywords.append({
                'word': word,
                'avg_score': avg_score,
                'document_count': data['count'],
                'methods': list(data['methods'])
            })
        
        # Sort by average score
        final_keywords.sort(key=lambda x: x['avg_score'], reverse=True)
        results['keywords'] = final_keywords[:50]  # Top 50 keywords
        
        return results
    
    def _cluster_documents(self, method: str = "kmeans") -> Dict[str, Any]:
        """Cluster documents based on embeddings"""
        results = {}
        
        if not self.document_embeddings:
            return results
        
        try:
            # Perform clustering
            cluster_result = self.document_clusterer.cluster_documents(
                self.document_embeddings, method=method
            )
            
            # Get cluster summary
            document_info = {}
            for doc_id in self.document_embeddings.keys():
                # Find corresponding document
                document_info[doc_id] = {
                    'filename': doc_id,  # Simplified for now
                    'text_length': len(self.document_texts.get(doc_id, '')),
                }
            
            cluster_summary = self.document_clusterer.get_cluster_summary(
                cluster_result, document_info
            )
            
            # Find similar clusters
            similar_clusters = self.document_clusterer.find_similar_clusters(cluster_result)
            
            results = {
                'method': method,
                'cluster_assignments': cluster_result['assignments'],
                'n_clusters': cluster_result.get('n_clusters', 0),
                'silhouette_score': cluster_result.get('silhouette_score', 0.0),
                'cluster_summary': cluster_summary,
                'similar_clusters': similar_clusters,
                'statistics': self.document_clusterer.get_statistics(),
            }
            
            self.cluster_results[method] = cluster_result
            
        except Exception as e:
            self.logger.error(f"Error clustering documents: {e}")
        
        return results
    
    def find_similar_documents(self, query_text: str, top_k: int = 10, 
                              threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find documents similar to a query text.
        
        Args:
            query_text: Text to search for
            top_k: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            list: Similar documents with similarity scores
        """
        if not self.document_embeddings:
            return []
        
        try:
            # Generate embedding for query
            query_embeddings = self.embedding_generator.generate_embeddings(
                [query_text], ["query"]
            )
            
            if "query" not in query_embeddings:
                return []
            
            query_embedding = query_embeddings["query"]
            
            # Find similar documents
            similar_docs = self.embedding_generator.find_similar_documents(
                query_embedding, self.document_embeddings, threshold, top_k
            )
            
            # Add document information
            results = []
            for doc_id, similarity in similar_docs:
                result = {
                    'document_id': doc_id,
                    'similarity': similarity,
                    'text_preview': self.document_texts.get(doc_id, '')[:200] + '...',
                }
                
                # Add entities and keywords if available
                if doc_id in self.document_entities:
                    result['entities'] = self.document_entities[doc_id]
                if doc_id in self.document_keywords:
                    result['keywords'] = self.document_keywords[doc_id][:5]  # Top 5 keywords
                
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error finding similar documents: {e}")
            return []
    
    def _get_document_id(self, document: DocumentInfo) -> str:
        """Generate a unique ID for a document"""
        # Use hash of path as ID, or filename if path not available
        if document.sha256_hash:
            return document.sha256_hash[:16]  # Use first 16 chars of hash
        else:
            return f"{Path(document.path).stem}_{document.size}"
    
    def _get_analysis_statistics(self) -> Dict[str, Any]:
        """Get comprehensive analysis statistics"""
        stats = {
            'documents_processed': self.documents_processed,
            'processing_errors': self.processing_errors,
            'text_extraction': self.text_extractor.get_statistics(),
            'embeddings': self.embedding_generator.get_statistics(),
            'clustering': self.document_clusterer.get_statistics(),
            'entities': self.entity_extractor.get_statistics(),
        }
        
        return stats
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current analysis state.
        
        Returns:
            dict: Analysis summary
        """
        return {
            'documents_with_text': len(self.document_texts),
            'documents_with_embeddings': len(self.document_embeddings),
            'documents_with_entities': len(self.document_entities),
            'total_clusters': len(self.cluster_results),
            'processing_statistics': self._get_analysis_statistics(),
        }
    
    def reset_analysis(self):
        """Reset all analysis data and statistics"""
        self.document_texts = {}
        self.document_embeddings = {}
        self.document_entities = {}
        self.document_keywords = {}
        self.cluster_results = {}
        
        self.documents_processed = 0
        self.processing_errors = 0
        
        # Reset component statistics
        self.text_extractor.reset_statistics()
        self.embedding_generator.reset_statistics()
        self.document_clusterer.reset_statistics()
        self.entity_extractor.reset_statistics()

