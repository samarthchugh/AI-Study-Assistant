from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
from app.utils.logging import get_logger

logger = get_logger(__name__)

class EmbeddingModel:
    """Singleton-style wrapper around SentenceTransformer.
        Ensures the model is loaded only once per process.
    """
    
    _model: SentenceTransformer | None = None
    
    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            logger.info("Loading embedding model 'all-MiniLM-L6-v2'")
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model
    
def embed_text(texts: List[str]) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts (List[str]): List of chunk texts

    Returns:
        np.ndarray: 2d array of shape (num_texts, embedding_dim)
    """
    if not texts:
        raise ValueError("Input texts list is empty.")
    
    model = EmbeddingModel.get_model()
    logger.info(
        "Generating embeddings",
        extra={"num_texts": len(texts)}
    )
    
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True
    )
    
    return np.array(embeddings)