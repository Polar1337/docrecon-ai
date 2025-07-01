"""
Document clustering for semantic grouping

Clusters documents based on their semantic embeddings to identify
related content and organize documents by topic/theme.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Optional clustering dependencies
try:
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Install: pip install scikit-learn")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logger.warning("Plotting libraries not available. Install: pip install matplotlib seaborn")


class DocumentClusterer:
    """
    Clusters documents based on their semantic embeddings.
    
    Supports multiple clustering algorithms:
    - K-Means clustering
    - DBSCAN (density-based)
    - Agglomerative clustering
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize document clusterer.
        
        Args:
            config: Configuration object with NLP settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for clustering. Install: pip install scikit-learn")
        
        # Clustering settings
        self.similarity_threshold = getattr(config.nlp, 'similarity_threshold', 0.85) if config else 0.85
        self.enable_clustering = getattr(config.nlp, 'enable_clustering', True) if config else True
        
        # Clustering results
        self.clusters = {}
        self.cluster_labels = {}
        self.cluster_centers = {}
        self.silhouette_scores = {}
        
        # Statistics
        self.documents_clustered = 0
        self.clusters_created = 0
    
    def cluster_documents(self, embeddings: Dict[str, np.ndarray], 
                         method: str = "kmeans", **kwargs) -> Dict[str, Any]:
        """
        Cluster documents based on their embeddings.
        
        Args:
            embeddings: Dictionary mapping document IDs to embedding vectors
            method: Clustering method ("kmeans", "dbscan", "agglomerative")
            **kwargs: Additional clustering parameters
            
        Returns:
            dict: Clustering results with cluster assignments and metadata
        """
        if not embeddings:
            return {}
        
        document_ids = list(embeddings.keys())
        embedding_matrix = np.array(list(embeddings.values()))
        
        self.logger.info(f"Clustering {len(document_ids)} documents using {method}")
        
        # Perform clustering
        if method.lower() == "kmeans":
            results = self._cluster_kmeans(document_ids, embedding_matrix, **kwargs)
        elif method.lower() == "dbscan":
            results = self._cluster_dbscan(document_ids, embedding_matrix, **kwargs)
        elif method.lower() == "agglomerative":
            results = self._cluster_agglomerative(document_ids, embedding_matrix, **kwargs)
        else:
            raise ValueError(f"Unsupported clustering method: {method}")
        
        # Store results
        self.clusters[method] = results
        self.documents_clustered = len(document_ids)
        self.clusters_created = len(set(results['labels']))
        
        return results
    
    def _cluster_kmeans(self, document_ids: List[str], embeddings: np.ndarray, 
                       n_clusters: int = None, **kwargs) -> Dict[str, Any]:
        """Perform K-Means clustering"""
        # Determine optimal number of clusters if not specified
        if n_clusters is None:
            n_clusters = self._estimate_optimal_clusters(embeddings, method="kmeans")
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, **kwargs)
        labels = kmeans.fit_predict(embeddings)
        
        # Calculate silhouette score
        if len(set(labels)) > 1:
            silhouette = silhouette_score(embeddings, labels)
        else:
            silhouette = 0.0
        
        # Create cluster assignments
        cluster_assignments = {}
        for doc_id, label in zip(document_ids, labels):
            cluster_assignments[doc_id] = int(label)
        
        # Get cluster centers
        cluster_centers = {}
        for i, center in enumerate(kmeans.cluster_centers_):
            cluster_centers[i] = center
        
        return {
            'method': 'kmeans',
            'assignments': cluster_assignments,
            'labels': labels,
            'cluster_centers': cluster_centers,
            'n_clusters': n_clusters,
            'silhouette_score': silhouette,
            'inertia': kmeans.inertia_,
        }
    
    def _cluster_dbscan(self, document_ids: List[str], embeddings: np.ndarray,
                       eps: float = None, min_samples: int = None, **kwargs) -> Dict[str, Any]:
        """Perform DBSCAN clustering"""
        # Set default parameters if not specified
        if eps is None:
            eps = 1 - self.similarity_threshold  # Convert similarity to distance
        if min_samples is None:
            min_samples = max(2, len(document_ids) // 50)  # Adaptive min_samples
        
        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine', **kwargs)
        labels = dbscan.fit_predict(embeddings)
        
        # Calculate silhouette score (excluding noise points)
        if len(set(labels)) > 1 and -1 not in labels:
            silhouette = silhouette_score(embeddings, labels)
        else:
            silhouette = 0.0
        
        # Create cluster assignments
        cluster_assignments = {}
        for doc_id, label in zip(document_ids, labels):
            cluster_assignments[doc_id] = int(label)
        
        # Count clusters (excluding noise cluster -1)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = list(labels).count(-1)
        
        return {
            'method': 'dbscan',
            'assignments': cluster_assignments,
            'labels': labels,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'silhouette_score': silhouette,
            'eps': eps,
            'min_samples': min_samples,
        }
    
    def _cluster_agglomerative(self, document_ids: List[str], embeddings: np.ndarray,
                              n_clusters: int = None, linkage: str = 'ward', **kwargs) -> Dict[str, Any]:
        """Perform Agglomerative clustering"""
        # Determine optimal number of clusters if not specified
        if n_clusters is None:
            n_clusters = self._estimate_optimal_clusters(embeddings, method="agglomerative")
        
        # Perform clustering
        agg = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage, **kwargs)
        labels = agg.fit_predict(embeddings)
        
        # Calculate silhouette score
        if len(set(labels)) > 1:
            silhouette = silhouette_score(embeddings, labels)
        else:
            silhouette = 0.0
        
        # Create cluster assignments
        cluster_assignments = {}
        for doc_id, label in zip(document_ids, labels):
            cluster_assignments[doc_id] = int(label)
        
        return {
            'method': 'agglomerative',
            'assignments': cluster_assignments,
            'labels': labels,
            'n_clusters': n_clusters,
            'silhouette_score': silhouette,
            'linkage': linkage,
        }
    
    def _estimate_optimal_clusters(self, embeddings: np.ndarray, method: str = "kmeans") -> int:
        """Estimate optimal number of clusters using elbow method or silhouette analysis"""
        n_samples = len(embeddings)
        
        # Reasonable range for number of clusters
        min_clusters = 2
        max_clusters = min(10, n_samples // 3)
        
        if max_clusters <= min_clusters:
            return min_clusters
        
        best_score = -1
        best_k = min_clusters
        
        for k in range(min_clusters, max_clusters + 1):
            try:
                if method == "kmeans":
                    kmeans = KMeans(n_clusters=k, random_state=42)
                    labels = kmeans.fit_predict(embeddings)
                elif method == "agglomerative":
                    agg = AgglomerativeClustering(n_clusters=k)
                    labels = agg.fit_predict(embeddings)
                else:
                    continue
                
                # Calculate silhouette score
                if len(set(labels)) > 1:
                    score = silhouette_score(embeddings, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k
                        
            except Exception as e:
                self.logger.warning(f"Error evaluating {k} clusters: {e}")
                continue
        
        self.logger.info(f"Estimated optimal clusters: {best_k} (silhouette score: {best_score:.3f})")
        return best_k
    
    def get_cluster_summary(self, cluster_results: Dict[str, Any], 
                           document_info: Dict[str, Any] = None) -> Dict[int, Dict[str, Any]]:
        """
        Get summary information for each cluster.
        
        Args:
            cluster_results: Results from clustering
            document_info: Optional document metadata
            
        Returns:
            dict: Summary for each cluster
        """
        assignments = cluster_results['assignments']
        
        # Group documents by cluster
        clusters = {}
        for doc_id, cluster_id in assignments.items():
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(doc_id)
        
        # Create summary for each cluster
        cluster_summary = {}
        for cluster_id, doc_ids in clusters.items():
            summary = {
                'cluster_id': cluster_id,
                'document_count': len(doc_ids),
                'document_ids': doc_ids,
                'is_noise': cluster_id == -1,  # For DBSCAN
            }
            
            # Add document metadata if available
            if document_info:
                summary['documents'] = []
                total_size = 0
                file_types = {}
                
                for doc_id in doc_ids:
                    if doc_id in document_info:
                        doc = document_info[doc_id]
                        summary['documents'].append({
                            'id': doc_id,
                            'filename': doc.get('filename', ''),
                            'path': doc.get('path', ''),
                            'size': doc.get('size', 0),
                            'modified_date': doc.get('modified_date', ''),
                        })
                        
                        total_size += doc.get('size', 0)
                        
                        # Count file types
                        ext = doc.get('file_extension', '').lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                
                summary['total_size'] = total_size
                summary['file_types'] = file_types
                summary['avg_size'] = total_size / len(doc_ids) if doc_ids else 0
            
            cluster_summary[cluster_id] = summary
        
        return cluster_summary
    
    def find_similar_clusters(self, cluster_results: Dict[str, Any], 
                             similarity_threshold: float = None) -> List[Tuple[int, int, float]]:
        """
        Find clusters that are similar to each other.
        
        Args:
            cluster_results: Results from clustering
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            list: List of (cluster1_id, cluster2_id, similarity) tuples
        """
        if similarity_threshold is None:
            similarity_threshold = self.similarity_threshold
        
        cluster_centers = cluster_results.get('cluster_centers', {})
        if not cluster_centers:
            return []
        
        similar_pairs = []
        cluster_ids = list(cluster_centers.keys())
        
        for i, cluster1_id in enumerate(cluster_ids):
            for cluster2_id in cluster_ids[i+1:]:
                center1 = cluster_centers[cluster1_id]
                center2 = cluster_centers[cluster2_id]
                
                # Calculate cosine similarity
                from sklearn.metrics.pairwise import cosine_similarity
                similarity = cosine_similarity([center1], [center2])[0, 0]
                
                if similarity >= similarity_threshold:
                    similar_pairs.append((cluster1_id, cluster2_id, float(similarity)))
        
        # Sort by similarity (descending)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def visualize_clusters(self, embeddings: Dict[str, np.ndarray], 
                          cluster_results: Dict[str, Any], 
                          output_path: str = None) -> Optional[str]:
        """
        Create a 2D visualization of document clusters.
        
        Args:
            embeddings: Document embeddings
            cluster_results: Clustering results
            output_path: Path to save the plot
            
        Returns:
            str: Path to saved plot, or None if plotting not available
        """
        if not PLOTTING_AVAILABLE:
            self.logger.warning("Plotting libraries not available")
            return None
        
        try:
            # Prepare data
            document_ids = list(embeddings.keys())
            embedding_matrix = np.array(list(embeddings.values()))
            labels = [cluster_results['assignments'].get(doc_id, -1) for doc_id in document_ids]
            
            # Reduce dimensionality to 2D using PCA
            pca = PCA(n_components=2, random_state=42)
            embeddings_2d = pca.fit_transform(embedding_matrix)
            
            # Create plot
            plt.figure(figsize=(12, 8))
            
            # Plot points colored by cluster
            unique_labels = set(labels)
            colors = plt.cm.Set3(np.linspace(0, 1, len(unique_labels)))
            
            for label, color in zip(unique_labels, colors):
                if label == -1:
                    # Noise points (for DBSCAN)
                    mask = np.array(labels) == label
                    plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                              c='black', marker='x', s=50, alpha=0.6, label='Noise')
                else:
                    mask = np.array(labels) == label
                    plt.scatter(embeddings_2d[mask, 0], embeddings_2d[mask, 1], 
                              c=[color], s=50, alpha=0.7, label=f'Cluster {label}')
            
            # Plot cluster centers if available
            if 'cluster_centers' in cluster_results:
                centers_2d = pca.transform(list(cluster_results['cluster_centers'].values()))
                plt.scatter(centers_2d[:, 0], centers_2d[:, 1], 
                          c='red', marker='*', s=200, alpha=0.8, 
                          edgecolors='black', linewidth=1, label='Centers')
            
            plt.title(f"Document Clusters ({cluster_results['method'].upper()})")
            plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
            plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save plot
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Cluster visualization saved to {output_path}")
                plt.close()
                return output_path
            else:
                plt.show()
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating cluster visualization: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get clustering statistics.
        
        Returns:
            dict: Statistics about clustering
        """
        return {
            'documents_clustered': self.documents_clustered,
            'clusters_created': self.clusters_created,
        }
    
    def reset_statistics(self):
        """Reset clustering statistics"""
        self.documents_clustered = 0
        self.clusters_created = 0
        self.clusters = {}
        self.cluster_labels = {}
        self.cluster_centers = {}
        self.silhouette_scores = {}

