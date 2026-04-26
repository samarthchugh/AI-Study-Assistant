from pydantic_settings import BaseSettings
from pathlib import Path
import os
import redis

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "AI Study Assistant"
    ENV: str = "development"
    
    # security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    
    # database
    DATABASE_URL: str
    
    # Vector store
    DATA_DIR: Path = Path(os.getenv("FAISS_DATA_DIR", BASE_DIR / "faiss_data"))
    FAISS_INDEX_NAME: str = "index_v1_flat"
    FAISS_INDEX_TYPE: str = "flat"
    
    # LLM
    LLM_MODEL_PATH: str 
    GROQ_API_KEY: str
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"
    
    # Redis
    # TODO (Docker): change REDIS_HOST in .env from "localhost" to "study_redis"
    #   (the container name defined in infra/docker-compose.yaml)
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    
    @property
    def FAISS_DIR(self) -> Path:
        path = self.DATA_DIR / "faiss"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def FAISS_INDEX_PATH(self) -> Path:
        return self.FAISS_DIR / f"{self.FAISS_INDEX_NAME}.faiss"
    
    @property
    def FAISS_META_PATH(self) -> Path:
        return self.FAISS_DIR / f"{self.FAISS_INDEX_NAME}.meta.pkl"
    
    class Config:
        env_file = BASE_DIR / ".env"
        extra = "ignore"
        
        
settings = Settings()

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)