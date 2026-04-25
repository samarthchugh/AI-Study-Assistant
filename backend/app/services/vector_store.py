from typing import List, Dict, Tuple
from pathlib import Path
import pickle
import faiss
import numpy as np
from app.utils.logging import get_logger
from app.config import settings

logger = get_logger(__name__)

class FAISSVectorStore:
    """
    Light-weight FAISS-based vector store with metadata persistance.
    """
    
    def __init__(self, embedding_dim: int):
        self.embedding_dim = embedding_dim
        self.index_path = settings.FAISS_INDEX_PATH
        self.meta_path = settings.FAISS_META_PATH
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.metadata: List[Dict] = []
        
        if self.index_path.exists():
            self._load()
            
    # Public APIs
    def add(self, embeddings: np.ndarray, metadatas: List[Dict]) -> None:
        """
        Add embeddings and their corresponding metadata to the store.
        """
        try:
            if embeddings.shape[0] != len(metadatas):
                raise ValueError("Embeddings and metadata count mismatch.")
            
            embeddings = embeddings.astype(np.float32)
            self.index.add(embeddings)
            self.metadata.extend(metadatas)
            
            logger.info(
                "Vectors added to Faiss index. ",
                extra={
                    "num_vectors_added": embeddings.shape[0],
                    "total_vectors": self.index.ntotal,
                },
            )
        except Exception as e:
            logger.error(f"Error adding vectors to Faiss index: {e}")
            raise None
        
    def search(self, query_embeddings: np.ndarray, top_k: int = 8, filters: Dict | None = None, search_k: int = 40) -> List[Tuple[float, Dict]]:
        """
        Search the index and return top-k results with with optional metadata filtering.
        
        Args:
            query_embeddings: embedding of query
            top_k: final number of results to return
            filters: metadata filters like {"topic": "Machine Learning", "user_id": 1}
            search_k: how many vectors to initially retrieve before filtering
        """
        try:
            query_vec = query_embeddings.astype(np.float32)
            if query_vec.ndim == 2:
                query_vec = query_vec[0]
                
            query_vec = query_vec / np.linalg.norm(query_vec)  # Normalize for cosine similarity
            # Step 1: pre-filter metadata indices
            if filters:
                def _matches(meta: Dict, filters: Dict) -> bool:
                    for k, v in filters.items():
                        stored = meta.get(k)
                        if stored == v:
                            continue
                        # Coerce both to str to handle int/str mismatches (e.g. user_id stored as "4" vs 4)
                        if stored is not None and str(stored) == str(v):
                            continue
                        return False
                    return True

                valid_indices = [
                    i for i, meta in enumerate(self.metadata)
                    if _matches(meta, filters)
                ]
            else:
                valid_indices = list(range(len(self.metadata)))
            
            if not valid_indices:
                logger.info("No valid indices found for the given filters.")
                return []
            
            # Step 2: efficiently reconstruct vectores only for valid indices
            vectors = np.vstack([
                self.index.reconstruct(i) for i in valid_indices
            ]).astype(np.float32)
            
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            vectors = vectors / (norms + 1e-10)  # Normalize to prevent division by zero
            
            # Step 3: Compute similarity (inner product)
            scores = np.dot(vectors, query_vec)
            # Step 4: Get top_k indices
            top_k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # STep 5: Build results
            results = []
            
            for i in top_indices:
                idx = valid_indices[i]
                results.append((float(scores[i]), self.metadata[idx]))
            logger.info(
                "Faiss search completed.",
                extra={
                    "query_embedding_shape": query_embeddings.shape,
                    "filters": filters,
                    "results_returned": len(results),
                },
            )
            return results
        except Exception as e:
            logger.error(f"Error during Faiss search: {e}")
            raise None
    
    def save(self) -> None:
        """
        Persist FAISS index and metadata to disk.
        """
        try:
            faiss.write_index(self.index, str(self.index_path))
            
            with open(self.meta_path, 'wb') as f:
                pickle.dump(self.metadata, f)
                
            logger.info(
                "FAISS index saved.",
                extra = {
                    "path": str(self.index_path),
                }
            )
        except Exception as e:
            logger.error(f"Error saving Faiss index: {e}")
            raise None
        
    # internal methods
    def _load(self) -> None:
        """
        Load FAISS index and metadata from disk.
        """
        try:
            self.index = faiss.read_index(str(self.index_path))
            
            with open(self.meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
                
            logger.info(
                "FAISS index loaded.",
                extra = {
                    "path": str(self.index_path),
                    "num_vectors": self.index.ntotal,
                },
            )
        except Exception as e:
            logger.error(f"Error loading Faiss index: {e}")
            raise None