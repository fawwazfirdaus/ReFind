from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
    completion_model: str = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4o-mini")
    
    # GROBID settings
    grobid_url: str = os.getenv("GROBID_URL", "http://localhost:8070")
    
    # Server settings
    backend_cors_origins: list = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # File storage settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    metadata_dir: str = os.getenv("METADATA_DIR", "metadata")
    vector_dir: str = os.getenv("VECTOR_DIR", "vectors")
    
    # Vector search settings
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "512"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    top_k_results: int = int(os.getenv("TOP_K_RESULTS", "5"))

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 