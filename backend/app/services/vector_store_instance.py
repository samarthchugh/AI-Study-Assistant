from app.services.vector_store import FAISSVectorStore
from app.rag.embeddings import embed_text

_dummy = embed_text(["warmup"])
embedding_dim = _dummy.shape[1]

vector_store = FAISSVectorStore(embedding_dim=embedding_dim)
