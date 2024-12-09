from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # OpenAI Settings (from .env)
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str
    OPENAI_COMPLETION_MODEL: str
    
    # Service URLs (from .env)
    GROBID_URL: str
    BACKEND_CORS_ORIGINS: str
    
    # Storage Paths (from .env)
    UPLOAD_DIR: str
    METADATA_DIR: str
    VECTOR_DIR: str
    
    # Vector Search Settings (application constants)
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    # Model Settings (application constants)
    TEMPERATURE: float = 0.7  # randomness in generation
    MAX_TOKENS: int = 1000  # maximum response length
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    # Computed paths
    @property
    def upload_dir_path(self) -> str:
        """Full path to upload directory."""
        return os.path.join(os.path.dirname(__file__), self.UPLOAD_DIR)
    
    @property
    def metadata_dir_path(self) -> str:
        """Full path to metadata directory."""
        return os.path.join(os.path.dirname(__file__), self.METADATA_DIR)
    
    @property
    def vector_dir_path(self) -> str:
        """Full path to vector store directory."""
        return os.path.join(os.path.dirname(__file__), self.VECTOR_DIR)

settings = Settings() 