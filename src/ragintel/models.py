"""Core data structures shared by each component
Plain dataclasses (not ORM Models) keep each pipeline stage easy to test in isolation"""

from __future__ import annotations

from dataclasses import dataclass,field


@dataclass(frozen=True)
class PageText:
     """Text extracted from one page. 
     Text and Markdown files are treated as a single page 1."""
     
     page_number:int
     text:str
     
@dataclass(frozen=True)
class Chunk:
    chunk_id : str #document<id>:str+ordinal:int
    doc_id:str
    ordinal:int
    text:str
    page_start:int
    page_end:int
    section: str | None
    content_hash: str
    title: str = ""
    
@dataclass(frozen=True)
class DocumentRecord:
    doc_id:str
    title:str
    source_name:str
    department:str
    version:str    
    allowed_groups: tuple[str, ...]
    content_hash: str
    page_count: int
    chunk_count: int
    ingested_at: str
    status: str = "current"
    
    
@dataclass(frozen=True)
class Pricipal:
     """Who is asking. Every retrieval call requires one; there is no 'unfiltered' path."""
     
     user_id:str
     groups: frozenset[str]
     is_admin: bool = False
     
@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float  # score from the active retriever (cosine, bm25, rrf or reranker)
    rank: int  # 1-based
    vector_score: float  # cosine similarity to the question, always computed (used by the evidence gate)
    retriever: str
 
 
@dataclass(frozen=True)
class Citation:
    label: str  # e.g. "E2" as written in the answer
    chunk_id: str
    doc_id: str
    title: str
    page_start: int
    page_end: int
 
 
@dataclass
class AnswerResult:
    answer: str
    abstained: bool
    abstain_reason: str | None
    citations: list[Citation] = field(default_factory=list)
    invalid_citation_labels: list[str] = field(default_factory=list)
    evidence: list[ScoredChunk] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    guard_flagged_chunks: list[str] = field(default_factory=list)  # chunks the evidence guard cleaned
    
    
    
    
    