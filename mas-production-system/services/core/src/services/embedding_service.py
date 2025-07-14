"""
Embedding Service for semantic search and similarity
"""
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import faiss
import pickle
from pathlib import Path
import asyncio

from src.services.llm_service import LLMService
from src.utils.logger import get_logger
from src.cache import cache, set as cache_set, get as cache_get

logger = get_logger(__name__)

class EmbeddingService:
    """Service for managing embeddings and vector search"""
    
    def __init__(
        self,
        llm_service: LLMService,
        dimension: int = 1536,  # Default for text-embedding-ada-002
        index_type: str = "flat",  # flat, ivf, hnsw
        cache_embeddings: bool = True
    ):
        self.llm_service = llm_service
        self.dimension = dimension
        self.index_type = index_type
        self.cache_embeddings = cache_embeddings
        
        # Initialize FAISS index
        self.index = self._create_index()
        self.id_to_metadata: Dict[int, Any] = {}
        self.next_id = 0
        
        logger.info(f"Initialized embedding service with {index_type} index")
    
    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on type"""
        if self.index_type == "flat":
            return faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatL2(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            return index
        elif self.index_type == "hnsw":
            index = faiss.IndexHNSWFlat(self.dimension, 32)
            return index
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
    
    async def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """Get embedding for a single text"""
        if use_cache and self.cache_embeddings:
            # Try to get from cache
            cache_key = f"embedding:{hash(text)}"
            cached = await cache_get(cache_key)
            if cached:
                return np.array(eval(cached))
        
        # Generate embedding
        embeddings = await self.llm_service.generate_embeddings([text])
        embedding = np.array(embeddings[0], dtype=np.float32)
        
        # Cache the result
        if use_cache and self.cache_embeddings:
            await cache_set(
                cache_key,
                str(embedding.tolist()),
                expire=86400  # 24 hours
            )
        
        return embedding
    
    async def get_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[np.ndarray]:
        """Get embeddings for multiple texts with batching"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.llm_service.generate_embeddings(batch)
            embeddings.extend([
                np.array(emb, dtype=np.float32) for emb in batch_embeddings
            ])
        
        return embeddings
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "content"
    ) -> List[int]:
        """Add documents to the index"""
        texts = [doc[text_field] for doc in documents]
        embeddings = await self.get_embeddings(texts)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to index
        ids = list(range(self.next_id, self.next_id + len(documents)))
        self.index.add(embeddings_array)
        
        # Store metadata
        for i, doc in enumerate(documents):
            self.id_to_metadata[self.next_id + i] = doc
        
        self.next_id += len(documents)
        
        logger.info(f"Added {len(documents)} documents to index")
        return ids
    
    async def search(
        self,
        query: str,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents"""
        # Get query embedding
        query_embedding = await self.get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search in index
        distances, indices = self.index.search(query_embedding, k)
        
        # Filter by threshold if provided
        results = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:  # No more results
                break
            
            if threshold is not None and distance > threshold:
                continue
            
            if idx in self.id_to_metadata:
                results.append((self.id_to_metadata[idx], float(distance)))
        
        return results
    
    async def search_by_embedding(
        self,
        embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search using a pre-computed embedding"""
        embedding = embedding.reshape(1, -1)
        
        distances, indices = self.index.search(embedding, k)
        
        results = []
        for i, (idx, distance) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:
                break
            
            if threshold is not None and distance > threshold:
                continue
            
            if idx in self.id_to_metadata:
                results.append((self.id_to_metadata[idx], float(distance)))
        
        return results
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings"""
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        embedding1 = embedding1 / norm1
        embedding2 = embedding2 / norm2
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    async def find_duplicates(
        self,
        threshold: float = 0.95,
        batch_size: int = 100
    ) -> List[Tuple[int, int, float]]:
        """Find duplicate documents based on similarity threshold"""
        duplicates = []
        
        # Get all embeddings from index
        n_total = self.index.ntotal
        
        for i in range(0, n_total, batch_size):
            end_idx = min(i + batch_size, n_total)
            batch_size_actual = end_idx - i
            
            # Reconstruct embeddings for this batch
            embeddings = np.zeros((batch_size_actual, self.dimension), dtype=np.float32)
            for j in range(batch_size_actual):
                self.index.reconstruct(i + j, embeddings[j])
            
            # Search for similar items
            distances, indices = self.index.search(embeddings, k=10)
            
            for j in range(batch_size_actual):
                for k in range(1, 10):  # Skip first result (self)
                    if indices[j][k] == -1:
                        break
                    
                    similarity = 1 - (distances[j][k] / 2)  # Convert L2 to cosine
                    if similarity >= threshold:
                        # Avoid duplicate pairs
                        if i + j < indices[j][k]:
                            duplicates.append((
                                i + j,
                                indices[j][k],
                                similarity
                            ))
        
        return duplicates
    
    async def cluster_documents(
        self,
        n_clusters: int = 10,
        method: str = "kmeans"
    ) -> Dict[int, List[int]]:
        """Cluster documents into groups"""
        if self.index.ntotal == 0:
            return {}
        
        # Get all embeddings
        n_total = self.index.ntotal
        embeddings = np.zeros((n_total, self.dimension), dtype=np.float32)
        for i in range(n_total):
            self.index.reconstruct(i, embeddings[i])
        
        if method == "kmeans":
            # Use FAISS KMeans
            kmeans = faiss.Kmeans(self.dimension, n_clusters)
            kmeans.train(embeddings)
            _, labels = kmeans.index.search(embeddings, 1)
            
            # Group by cluster
            clusters = {}
            for i, label in enumerate(labels.flatten()):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(i)
            
            return clusters
        else:
            raise ValueError(f"Unknown clustering method: {method}")
    
    def save_index(self, path: str):
        """Save index to disk"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path))
        
        # Save metadata
        metadata_path = path.with_suffix('.pkl')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'id_to_metadata': self.id_to_metadata,
                'next_id': self.next_id,
                'dimension': self.dimension,
                'index_type': self.index_type
            }, f)
        
        logger.info(f"Saved index to {path}")
    
    def load_index(self, path: str):
        """Load index from disk"""
        path = Path(path)
        
        # Load FAISS index
        self.index = faiss.read_index(str(path))
        
        # Load metadata
        metadata_path = path.with_suffix('.pkl')
        with open(metadata_path, 'rb') as f:
            data = pickle.load(f)
            self.id_to_metadata = data['id_to_metadata']
            self.next_id = data['next_id']
            self.dimension = data['dimension']
            self.index_type = data['index_type']
        
        logger.info(f"Loaded index from {path}")

# Global instance
_embedding_service: Optional[EmbeddingService] = None

async def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        from src.services.llm_service import get_llm_service
        llm_service = await get_llm_service()
        _embedding_service = EmbeddingService(llm_service)
    return _embedding_service

__all__ = ["EmbeddingService", "get_embedding_service"]