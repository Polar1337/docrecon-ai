"""
Embedding generation for semantic document analysis

Generates vector embeddings from text content using various models
for semantic similarity analysis and document clustering.
"""

import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import logging

logger = logging.getLogger(__name__)

# Optional embedding dependencies
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Install: pip install sentence-transformers")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install: pip install scikit-learn")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class EmbeddingGenerator:
    """
    Generates embeddings from text content for semantic analysis.
    
    Supports multiple embedding models and methods:
    - Sentence Transformers (recommended)
    - TF-IDF vectors (fallback)
    - Custom models
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize embedding generator.
        
        Args:
            config: Configuration object with NLP settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Model configuration
        self.model_name = getattr(config.nlp, 'model', 'sentence-transformers/all-MiniLM-L6-v2') if config else 'sentence-transformers/all-MiniLM-L6-v2'
        self.batch_size = getattr(config.nlp, 'batch_size', 32) if config else 32
        self.max_text_length = getattr(config.nlp, 'max_text_length', 10000) if config else 10000
        
        # Cache settings
        self.cache_dir = getattr(config, 'cache_dir', '~/.docrecon_cache') if config else '~/.docrecon_cache'
        self.cache_dir = Path(self.cache_dir).expanduser()
        self.cache_dir.mkdir(exist_ok=True)
        
        # Model and vectorizer
        self.model = None
        self.vectorizer = None
        self.embedding_dim = None
        self.method = None
        
        # Statistics
        self.embeddings_generated = 0
        self.cache_hits = 0
        
        # Initialize model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self._initialize_sentence_transformer()
            elif SKLEARN_AVAILABLE:
                self._initialize_tfidf()
            else:
                raise ImportError("No embedding library available")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    def _initialize_sentence_transformer(self):
        """Initialize Sentence Transformer model"""
        try:
            self.logger.info(f"Loading Sentence Transformer model: {self.model_name}")
            
            # Check if model is cached
            model_cache_path = self.cache_dir / "models" / self.model_name.replace('/', '_')
            
            if model_cache_path.exists():
                self.model = SentenceTransformer(str(model_cache_path))
                self.logger.info("Loaded model from cache")
            else:
                self.model = SentenceTransformer(self.model_name)
                
                # Cache the model
                model_cache_path.parent.mkdir(parents=True, exist_ok=True)
                self.model.save(str(model_cache_path))
                self.logger.info("Model cached for future use")
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"])
            self.embedding_dim = test_embedding.shape[1]
            self.method = "sentence_transformer"
            
            self.logger.info(f"Sentence Transformer initialized. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Sentence Transformer: {e}")
            # Fallback to TF-IDF
            if SKLEARN_AVAILABLE:
                self._initialize_tfidf()
            else:
                raise
    
    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer as fallback"""
        try:
            self.logger.info("Initializing TF-IDF vectorizer")
            
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
            
            self.method = "tfidf"
            self.embedding_dim = 1000  # Will be adjusted after fitting
            
            self.logger.info("TF-IDF vectorizer initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TF-IDF vectorizer: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], document_ids: List[str] = None) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text content to embed
            document_ids: Optional list of document IDs for caching
            
        Returns:
            dict: Mapping of document IDs to embedding vectors
        """
        if not texts:
            return {}
        
        if document_ids is None:
            document_ids = [f"doc_{i}" for i in range(len(texts))]
        
        if len(texts) != len(document_ids):
            raise ValueError("Number of texts and document IDs must match")
        
        embeddings = {}
        texts_to_process = []
        ids_to_process = []
        
        # Check cache for existing embeddings
        for text, doc_id in zip(texts, document_ids):
            cached_embedding = self._get_cached_embedding(doc_id)
            if cached_embedding is not None:
                embeddings[doc_id] = cached_embedding
                self.cache_hits += 1
            else:
                texts_to_process.append(text)
                ids_to_process.append(doc_id)
        
        # Generate embeddings for uncached texts
        if texts_to_process:
            if self.method == "sentence_transformer":
                new_embeddings = self._generate_sentence_transformer_embeddings(texts_to_process)
            elif self.method == "tfidf":
                new_embeddings = self._generate_tfidf_embeddings(texts_to_process)
            else:
                raise ValueError(f"Unknown embedding method: {self.method}")
            
            # Store new embeddings
            for doc_id, embedding in zip(ids_to_process, new_embeddings):
                embeddings[doc_id] = embedding
                self._cache_embedding(doc_id, embedding)
                self.embeddings_generated += 1
        
        return embeddings
    
    def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using Sentence Transformer"""
        # Truncate texts if needed
        processed_texts = []
        for text in texts:
            if len(text) > self.max_text_length:
                text = text[:self.max_text_length]
            processed_texts.append(text)
        
        # Generate embeddings in batches
        embeddings = []
        for i in range(0, len(processed_texts), self.batch_size):
            batch = processed_texts[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def _generate_tfidf_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using TF-IDF"""
        # Fit vectorizer if not already fitted
        if not hasattr(self.vectorizer, 'vocabulary_'):
            self.logger.info("Fitting TF-IDF vectorizer")
            self.vectorizer.fit(texts)
            self.embedding_dim = len(self.vectorizer.vocabulary_)
        
        # Transform texts to vectors
        vectors = self.vectorizer.transform(texts)
        
        # Convert to dense numpy arrays
        embeddings = [vector.toarray().flatten() for vector in vectors]
        
        return embeddings
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        try:
            # Reshape if needed
            if embedding1.ndim == 1:
                embedding1 = embedding1.reshape(1, -1)
            if embedding2.ndim == 1:
                embedding2 = embedding2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(embedding1, embedding2)[0, 0]
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_similar_documents(self, query_embedding: np.ndarray, 
                              document_embeddings: Dict[str, np.ndarray],
                              threshold: float = 0.8, top_k: int = None) -> List[Tuple[str, float]]:
        """
        Find documents similar to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Dictionary of document embeddings
            threshold: Minimum similarity threshold
            top_k: Maximum number of results to return
            
        Returns:
            list: List of (document_id, similarity_score) tuples
        """
        similarities = []
        
        for doc_id, doc_embedding in document_embeddings.items():
            similarity = self.calculate_similarity(query_embedding, doc_embedding)
            if similarity >= threshold:
                similarities.append((doc_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results if requested
        if top_k is not None:
            similarities = similarities[:top_k]
        
        return similarities
    
    def _get_cached_embedding(self, document_id: str) -> Optional[np.ndarray]:
        """Get cached embedding for a document"""
        cache_file = self.cache_dir / "embeddings" / f"{document_id}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding_data = pickle.load(f)
                
                # Check if embedding is compatible with current model
                if (embedding_data.get('method') == self.method and
                    embedding_data.get('model_name') == self.model_name):
                    return embedding_data['embedding']
                    
            except Exception as e:
                self.logger.warning(f"Failed to load cached embedding for {document_id}: {e}")
        
        return None
    
    def _cache_embedding(self, document_id: str, embedding: np.ndarray):
        """Cache an embedding for future use"""
        try:
            cache_dir = self.cache_dir / "embeddings"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_file = cache_dir / f"{document_id}.pkl"
            
            embedding_data = {
                'embedding': embedding,
                'method': self.method,
                'model_name': self.model_name,
                'embedding_dim': self.embedding_dim,
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding_data, f)
                
        except Exception as e:
            self.logger.warning(f"Failed to cache embedding for {document_id}: {e}")
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """
        Get information about the current embedding model.
        
        Returns:
            dict: Model information
        """
        return {
            'method': self.method,
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'batch_size': self.batch_size,
            'max_text_length': self.max_text_length,
        }
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get embedding generation statistics.
        
        Returns:
            dict: Statistics about embedding generation
        """
        return {
            'embeddings_generated': self.embeddings_generated,
            'cache_hits': self.cache_hits,
        }
    
    def reset_statistics(self):
        """Reset embedding statistics"""
        self.embeddings_generated = 0
        self.cache_hits = 0
    
    def clear_cache(self):
        """Clear embedding cache"""
        try:
            cache_dir = self.cache_dir / "embeddings"
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info("Embedding cache cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear embedding cache: {e}")
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], filepath: str):
        """
        Save embeddings to file.
        
        Args:
            embeddings: Dictionary of embeddings to save
            filepath: Path to save file
        """
        try:
            save_data = {
                'embeddings': embeddings,
                'model_info': self.get_embedding_info(),
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(save_data, f)
                
            self.logger.info(f"Embeddings saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save embeddings to {filepath}: {e}")
    
    def load_embeddings(self, filepath: str) -> Dict[str, np.ndarray]:
        """
        Load embeddings from file.
        
        Args:
            filepath: Path to load file
            
        Returns:
            dict: Loaded embeddings
        """
        try:
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
            
            embeddings = save_data.get('embeddings', {})
            model_info = save_data.get('model_info', {})
            
            # Check compatibility
            if (model_info.get('method') != self.method or
                model_info.get('model_name') != self.model_name):
                self.logger.warning("Loaded embeddings may be incompatible with current model")
            
            self.logger.info(f"Embeddings loaded from {filepath}")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to load embeddings from {filepath}: {e}")
            return {}

