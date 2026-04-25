from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from tempfile import NamedTemporaryFile
import shutil

from app.dependencies import get_current_user
from app.services.vector_store_instance import vector_store
from app.rag.ingestion import ingest_pdf_to_vectorstore
from app.rag.embeddings import embed_text
from app.utils.topic_utils import normalize_topic
from app.config import redis_client

router = APIRouter(prefix="/documents", tags=["Documents"])

vector_store = vector_store  # ensure vector store is initialized at module load time


@router.post("/upload")
def upload_document(
    topic: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user)
):
    """
    Accept a PDF upload, ingest it into the FAISS vector store, and register the topic in Redis.
    Only PDF files are accepted; returns 400 for any other file type.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # save temp file
        with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        topic = normalize_topic(topic)
        # ingest
        ingest_pdf_to_vectorstore(
            pdf_path=tmp_path,
            vector_store=vector_store,
            topic=topic,
            user_id=int(current_user_id),
            source="user_upload"
        )
        
        redis_client.sadd(f"user:{int(current_user_id)}:topics", topic)

        return {"status": "success", "message": "Document uploaded and indexed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
