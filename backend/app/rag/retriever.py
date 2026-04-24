from typing import List, Dict
import numpy as np
from app.services.vector_store import FAISSVectorStore
from app.rag.contracts import RetrievedChunk
from app.rag.embeddings import embed_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    Retriever = Query -> Relevant document chunks (FAISS-based)
    """
    def __init__(self, vector_store: FAISSVectorStore, top_k: int = 8, score_threshold: float = 0.10, max_context_chars: int = 8000):
        self.vector_store = vector_store
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.max_context_chars = max_context_chars
        
    def retrieve(self, query: str, filters: Dict | None = None) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a given query
        with optional metadata filtering.
        """
        
        if not query or not query.strip():
            logger.warning("Empty query received.")
            return []
        
        # 1. Query -> embedding (normalised cosine space)
        query_embedding = embed_text([query])  # Shape (1, embedding_dim)
        
        # 2. FAISS search (over-fetch)
        results = self.vector_store.search(
            query_embeddings=query_embedding,
            top_k=self.top_k * 2,  # Over-fetching
            filters=filters,
            search_k=self.top_k * 6  # Retrieve more for better filtering
        )
        
        candidates: List[RetrievedChunk] = []
        
        # 3. Score filtering + structuring
        for score, metadata in results:
            if score < self.score_threshold:
                continue
            
            text = metadata.get("text", "")
            if not text:
                continue
            
            candidates.append(
                RetrievedChunk(
                    text=text,
                    score=float(score),
                    metadata=metadata
                )
            )
            
        # 4. Sort by cosine simialrity (higher is better)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # 5. Context Trucation
        final_chunks = self._truncate_context(candidates)
        
        logger.info(
            "Retriever Completed",
            extra = {
                "query": query,
                "chunks_returned": len(final_chunks),
            }
        )
        
        return final_chunks
    
    def _truncate_context(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Limit total context size and enforce top_k.
        """
        final_chunks: List[RetrievedChunk] = []
        total_chars = 0
        
        for chunk in chunks:
            chunk_len = len(chunk.text)
            
            if total_chars + chunk_len > self.max_context_chars:
                break
            
            final_chunks.append(chunk)
            total_chars += chunk_len
            
            if len(final_chunks) >= self.top_k:
                break
                
        return final_chunks