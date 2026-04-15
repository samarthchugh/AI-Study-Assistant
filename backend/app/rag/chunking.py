import uuid
from typing import List, Dict
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---- Configuration ----
CHUNK_SIZE = 800  # approx tokens (word-based approximation) if this not works going back to 600
CHUNK_OVERLAP = 200  # Number of overlapping characters between chunks (helps maintain context for retrieval) if not works going back to 120

# ---- Public APIs ----
def create_chunks(pages: List[Dict[str, str]], doc_id: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict[str, str]]:
    """Convert extracted PDF pages into semantically coherent chunks.

    Args:
        pages (List[Dict]): Output from ingestion.load_pdf()
        doc_id (str): Unique document identifier
        chunk_size (int): Target chunk size (approx tokens)
        overlap (int): Overlap size between consecutive chunks

    Returns:
        List[Dict]: List of chunk objects with metadata
    """
    chunks: List[Dict[str, str]] = []
    
    for page in pages:
        page_number = page["page"]
        text = page["text"]
        
        page_chunks = _chunk_text(
            text=text,
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        for chunk_text in page_chunks:
            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "doc_id": doc_id,
                    "page": page_number,
                    "text": chunk_text
                }
            )
    logger.info(
        "Chunking completed",
        extra={
            "doc_id": doc_id,
            "pages_processed": len(pages),
            "chunks_created": len(chunks),
        }
    )
    return chunks

# ---- Internal logic ----
def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Recursively chunk text using semantic boundaries.

    Priority:
    1. Paragraphs
    2. Sentences
    3. Word-level fallback
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks : List[str] = []
    current_chunk : List[str] = []
    current_length = 0
    
    for para in paragraphs:
        para_length = _length(para)
        
        if current_length + para_length <= chunk_size:
            current_chunk.append(para)
            current_length += para_length
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                
            current_chunk = _apply_overlap(
                previous_chunk=current_chunk,
                overlap=overlap
            )
            
            current_chunk.append(para)
            current_length = _length(" ".join(current_chunk))
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    # final safety pass for long paragraphs
    final_chunks: List[str] = []
    for chunk in chunks:
        if _length(chunk) <= chunk_size:
            final_chunks.append(chunk)
        else:
            final_chunks.extend(_fallback_word_split(chunk, chunk_size, overlap))
            
    return final_chunks

def _apply_overlap(previous_chunk: List[str], overlap: int) -> List[str]:
    """
    Carry overlap tokens from previous chunk into the next chunk.
    """
    if not previous_chunk:
        return []
    
    words = " ".join(previous_chunk).split()
    return [" ".join(words[-overlap:])] if len(words) >= overlap else previous_chunk

def _fallback_word_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Fallback splitter for edge cases (very long text blocks).
    """
    words = text.split()
    chunks = []
    
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start = end - overlap  # apply overlap
        
    return chunks

def _length(text: str) -> int:
    """
    Approximate token length using word count.
    """
    return len(text.split())
        