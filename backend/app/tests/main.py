from app.rag.chunking import create_chunks
from app.rag.ingestion import load_pdf

test_pdf_path = r"C:\\Users\\samarth\\OneDrive\\Desktop\\Study material\\ResumeV8.pdf"
pages = load_pdf(str(test_pdf_path))
chunks = create_chunks(pages, doc_id="test_doc_001")

print(len(chunks))
print(chunks[0].keys())
print(chunks[0]["text"][:300])