from __future__ import annotations
 
from functools import lru_cache
from pathlib import Path
from typing import Literal
 
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
 
RetrievalMode = Literal["vector", "bm25", "hybrid"]
 
 
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAG_", extra="ignore")
 
    # Storage
    db_path: Path = Path("data/runtime/ragintel.db")
    users_file: Path = Path("config/users.json")
 
    # Upload limits (defence against oversized / abusive files)
    max_upload_mb: int = Field(20, ge=1, le=200)
    max_pages: int = Field(500, ge=1)
 
    # Chunking, measured in characters (~4 characters per English token)
    chunk_size_chars: int = Field(1800, ge=200)
    chunk_overlap_chars: int = Field(200, ge=0)
 
    # Embeddings
    embedder: Literal["sentence-transformers", "hashing"] = "sentence-transformers"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
 
    # Retrieval
    retrieval_mode: RetrievalMode = "vector"
    top_k: int = Field(5, ge=1, le=20)
    candidate_k: int = Field(20, ge=1, le=200)
    rrf_k: int = Field(60, ge=1)
    min_evidence_score: float = Field(0.45, ge=-1.0, le=1.0)
    reranker: Literal["none", "cross-encoder"] = "none"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
 
    # Generation
    llm_provider: Literal["ollama", "openai_compatible", "extractive"] = "ollama"
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"
    openai_base_url: str = ""
    openai_api_key: str = ""
    llm_timeout_s: float = Field(120.0, gt=0)
    max_question_chars: int = Field(1000, ge=10)
 
    log_level: str = "INFO"
 
    @model_validator(mode="after")
    def _check_consistency(self) -> "Settings":
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be >= top_k")
        return self
 
    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024
 
 
@lru_cache
def get_settings() -> Settings:
    return Settings()