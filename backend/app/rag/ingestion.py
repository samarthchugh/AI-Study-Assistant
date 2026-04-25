from pathlib import Path
from typing import List, Dict
import uuid
from datetime import datetime
import fitz # PyMuPDF
from app.utils.logging import get_logger
from app.rag.chunking import create_chunks
from app.rag.embeddings import embed_text
from app.services.vector_store import FAISSVectorStore
from app.utils.topic_utils import normalize_topic
logger = get_logger(__name__)

class PDFIngestionError(Exception):
    """
    Domain-specific exception for PDF ingestion failuers.
    Used to clearly separate ingestion errors from system errors.
    """
    pass

def load_pdf(file_path: str) -> List[Dict[str, str]]:
    """Load a PDF file and extract text page by page.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with:
        - page (int): Page number (1-indexed).
        - text (str): Cleaned text extracted from the page.
        
    Raises:
        PDFIngestionError: If the PDF file is invalid or text extraction fails.
    """
    
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise PDFIngestionError(f"PDF file does not exist")
    
    if pdf_path.suffix.lower() != ".pdf":
        raise PDFIngestionError(f"Invalid file type: {pdf_path.suffix}. Expected a .pdf file.")
    
    extracted_pages: List[Dict[str, str]] = []

    try:
        document  = fitz.open(str(pdf_path))
        for page_number, page in enumerate(document, start=1):
            raw_text = page.get_text("text")
            cleaned_text = _clean_text(raw_text)
            
            if cleaned_text:
                extracted_pages.append({
                    "page": page_number,
                    "text": cleaned_text
                })
        document.close()
    except Exception as e:
        logger.exception(
            "PDF ingestion failed",
            extra = {"file_path": str(pdf_path)}
        )
        raise PDFIngestionError(str(e)) from e
    
    if not extracted_pages:
        raise PDFIngestionError("No extractable text found in the PDF.")
    
    logger.info(
        "PDF ingestion completed",
        extra={
            "file_path": str(pdf_path),
            "pages_extracted": len(extracted_pages)
        }
    )
    return extracted_pages

def _clean_text(text: str) -> str:
    """
    Normalize text extracted from a PDF page.

    - Removes excessive whitespace
    - Preserves paragraph structure
    - Avoids aggressive NLP preprocessing (important for embeddings)

    Args:
        text (str): Raw extracted text

    Returns:
        str: Cleaned text
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def ingest_pdf_to_vectorstore(
    pdf_path: str,
    vector_store: FAISSVectorStore,
    topic: str ,
    user_id: int,
    source: str = "user_upload"
):
    """
    Full Ingestion Pipeline
    PDF -> pages -> chunks -> embeddings -> FAISS
    """
    try:
        # 1. Load PDF
        pages = load_pdf(pdf_path)
        
        # 2. Create document ID (One-per Document)
        doc_id = str(uuid.uuid4())
        
        # 3. Chunk pages
        chunks = create_chunks(pages, doc_id=doc_id)
        if not chunks:
            logger.warning("No chunks created from the PDF.")
            return
        
        # 4. Prepare text + metadata
        texts = []
        metadatas = []
        
        for i,chunk in enumerate(chunks):
            texts.append(chunk['text'])
            metadatas.append({
                "chunk_id": chunk['chunk_id'],
                "doc_id": chunk['doc_id'],
                "chunk_index": i,
                "page": chunk['page'],
                "source": source,
                "created_at": datetime.utcnow().isoformat(),
                
                # placeholder 
                "user_id": user_id,
                "topic": normalize_topic(topic),
                "subtopic": None,
                "difficulty": None,
                
                # required for retrivel
                "text": chunk['text'],      
            })
            
        # 5. Embed chunks
        embeddings = embed_text(texts)
        
        # 6. store in vector store
        vector_store.add(embeddings, metadatas)
        vector_store.save()
        logger.info(
            "PDF ingestion and vector store update completed",
            extra={
                "pdf_path": pdf_path,
                "num_chunks": len(chunks),
                "doc_id": doc_id
            }
        )
    except PDFIngestionError as e:
        logger.error(f"PDF ingestion error: {e}")
        
    
# if __name__ == "__main__":
#     # Simple test
#     test_pdf_path = r"C:\\Users\\samarth\\OneDrive\\Desktop\\Study material\\ResumeV8.pdf"
#     try:
#         pages = load_pdf(str(test_pdf_path))
#         for page in pages:
#             print(f"--- Page {page['page']} ---")
#             print(page['text'][:1000])  # Print first 200 characters of each page
#             print()
#     except PDFIngestionError as e:
#         print(f"Error during PDF ingestion: {e}")