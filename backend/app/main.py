from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# from app.services.llm import generate_completion
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.rag import router as rag_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.analytics import router as analytics_router
from app.utils.logging import get_logger

import threading

logger = get_logger(__name__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # --------- startup code ---------
#     logger.info("Application is starting up...")
#     try:
#         # Generate a dummy completion to warm up the model
#         warmup_model()
#         # logger.info("LLM is warmed up and ready to go!")
#     except Exception as e:
#         # logger.exception("LLM warm-up failed")
#         pass
#     threading.Thread(target=warmup_model, daemon=True).start()
#     yield
    
#     # --------- shutdown code ---------
#     logger.info("Shutting down the application...")

app = FastAPI(title="AI Study Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(rag_router)
app.include_router(quiz_router)
app.include_router(analytics_router)