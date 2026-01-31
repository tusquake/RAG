from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "AI Document Q&A"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "document_qa"
    
    REDIS_URL: str = "redis://localhost:6379"
    
    JWT_SECRET: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    HUGGINGFACE_API_KEY: Optional[str] = None
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    
    WHISPER_MODEL: str = "base"
    
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_PDF_EXTENSIONS: list = [".pdf"]
    ALLOWED_AUDIO_EXTENSIONS: list = [".mp3", ".wav", ".m4a", ".flac", ".ogg"]
    ALLOWED_VIDEO_EXTENSIONS: list = [".mp4", ".webm", ".mkv", ".avi", ".mov"]
    
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    FAISS_INDEX_PATH: str = "faiss_index"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
