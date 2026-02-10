from fastapi import APIRouter, Depends, HTTPException
from app.schemas.request import AskRequest, AskResponse
from app.rag.pipeline import QueryAnswerPipeline
from app.rag.retriever import Retriever
from app.services.vector_store_instance import vector_store
from app.dependencies import get_current_user
from app.rag.embeddings import embed_text
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


vector_store = vector_store  # ensure vector store is initialized at module load time

retriever = Retriever(vector_store=vector_store, top_k=5, score_threshold=0.15, max_context_chars=4000)

pipeline = QueryAnswerPipeline(retriever=retriever)

@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, user_id: str = Depends(get_current_user)):
    """
    Ask a question against the uploaded study material.
    """
    logger.info("RAG API called", extra={"question": request.question})
    try:
        result = pipeline.answer_query(request.question)
        return result
    except Exception as e:
        logger.exception("RAG pipeline failed")
        raise HTTPException(status_code=500, detail="Failed to process the question.")