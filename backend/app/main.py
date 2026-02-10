from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.rag import router as rag_router
from app.services.llm import generate_completion
from app.utils.logging import get_logger

logger = get_logger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # --------- startup code ---------
#     logger.info("Warming up the LLM...")
#     try:
#         # Generate a dummy completion to warm up the model
#         generate_completion("Hello, this is a warm-up call.")
#         logger.info("LLM is warmed up and ready to go!")
#     except Exception as e:
#         logger.exception("LLM warm-up failed")
#     yield
    
#     # --------- shutdown code ---------
#     logger.info("Shutting down the application...")

app = FastAPI(title="AI Study Assistant")

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(rag_router)