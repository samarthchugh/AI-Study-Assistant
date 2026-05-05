import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db, SessionLocal
from app.db.models import ChatSession, ChatMessage
from app.schemas.chat import SessionOut, SessionWithMessages
from app.dependencies import get_current_user
from app.rag.pipeline import QueryAnswerPipeline
from app.rag.retriever import Retriever
from app.services.vector_store_instance import vector_store
from app.utils.logging import get_logger

logger = get_logger(__name__)

retriever = Retriever(vector_store=vector_store, top_k=8, score_threshold=0.15, max_context_chars=4000)
pipeline = QueryAnswerPipeline(retriever=retriever)

router = APIRouter(prefix="/chat", tags=["chat"])


class AskChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


@router.post("/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    session = ChatSession(user_id=int(user_id))
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == int(user_id))
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
def get_session(session_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == int(user_id),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    session.messages = messages
    return session


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == int(user_id),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}


@router.post("/sessions/{session_id}/ask-stream")
def ask_chat_stream(
    session_id: int,
    request: AskChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == int(user_id),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build conversation history from existing messages before this turn
    existing = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in existing]

    # Auto-title from first user message
    if not existing:
        title = request.question.strip()[:60]
        session.title = title if title else "New Chat"

    # Save user message and bump updated_at
    user_msg = ChatMessage(session_id=session_id, role="user", content=request.question)
    db.add(user_msg)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()

    uid = int(user_id)

    def event_generator():
        text_chunks: list[str] = []
        sources = None
        confidence = None

        try:
            for item in pipeline.stream_query(request.question, uid, history=history):
                if isinstance(item, dict):
                    sources = item.get("sources")
                    confidence = item.get("confidence")
                    yield f"data: [SOURCES]{json.dumps(item)}\n\n"
                else:
                    text_chunks.append(item)
                    yield f"data: {json.dumps(item)}\n\n"
        except Exception:
            logger.exception("Chat streaming failed")

        yield "data: [DONE]\n\n"

        # Persist the complete assistant response after streaming
        if text_chunks:
            save_db = SessionLocal()
            try:
                ai_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content="".join(text_chunks),
                    sources=sources,
                    confidence=confidence,
                )
                save_db.add(ai_msg)
                save_db.commit()
            except Exception:
                save_db.rollback()
                logger.exception("Failed to save assistant message")
            finally:
                save_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
