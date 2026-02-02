from app.rag.chunking import create_chunks
from app.rag.ingestion import load_pdf
from app.rag.embeddings import embed_text
from app.services.vector_store import FAISSVectorStore

test_pdf_path = r"C:\\Users\\samarth\\OneDrive\\Desktop\\Study material\\ResumeV8.pdf"
pages = load_pdf(str(test_pdf_path))
chunks = create_chunks(pages, doc_id="test_doc_001")

print(len(chunks))
print(chunks[0].items())
print(chunks[0]["text"][:300])

texts = [c['text'] for c in chunks]
vectors = embed_text(texts)

store = FAISSVectorStore(embedding_dim=vectors.shape[1])
store.add(vectors, chunks)
store.save()