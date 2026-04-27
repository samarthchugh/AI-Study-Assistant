import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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

retriever = Retriever(vector_store=vector_store, top_k=8, score_threshold=0.15, max_context_chars=4000)

pipeline = QueryAnswerPipeline(retriever=retriever)

@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest, user_id: str = Depends(get_current_user)):
    """
    Ask a question against the uploaded study material.
    """
    logger.info("RAG API called", extra={"question": request.question})
    try:
        result = pipeline.answer_query(request.question, user_id= int(user_id))
        return result
    except Exception as e:
        logger.exception("RAG pipeline failed")
        raise HTTPException(status_code=500, detail="Failed to process the question.")


@router.post("/ask-stream")
def ask_stream(request: AskRequest, user_id: str = Depends(get_current_user)):
    """Stream the RAG answer as Server-Sent Events.

    Protocol:
      data: "<text chunk>"   — streaming answer tokens
      data: [SOURCES]{...}  — source passages after stream ends
      data: [DONE]          — signals end of stream
    """
    def event_generator():
        try:
            for item in pipeline.stream_query(request.question, int(user_id)):
                if isinstance(item, dict):
                    yield f"data: [SOURCES]{json.dumps(item)}\n\n"
                else:
                    yield f"data: {json.dumps(item)}\n\n"
        except Exception:
            logger.exception("RAG streaming failed")
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )