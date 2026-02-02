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
        
    def search(self, query_embeddings: np.ndarray, top_k: int = 5) -> List[Tuple[float, Dict]]:
        """
        Search the index and return top-k results with metadata.
        """
        
        query_embeddings = query_embeddings.astype(np.float32)
        scores, indices = self.index.search(query_embeddings, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((score, self.metadata[idx]))
        return results
    
    def save(self) -> None:
        """
        Persist FAISS index and metadata to disk.
        """
        
        faiss.write_index(self.index, str(self.index_path))
        
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
            
        logger.info(
            "FAISS index saved.",
            extra = {
                "path": str(self.index_path),
            }
        )
        
    # internal methods
    def _load(self) -> None:
        """
        Load FAISS index and metadata from disk.
        """
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