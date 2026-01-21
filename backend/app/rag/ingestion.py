from pathlib import Path
from typing import List, Dict

import fitz # PyMuPDF
from app.utils.logging import get_logger
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