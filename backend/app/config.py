from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Study Assistant"
    ENV: str = "development"
    
    # security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # database
    DATABASE_URL: str
    
    class Config:
        env_file = ".env"
        
        
settings = Settings()