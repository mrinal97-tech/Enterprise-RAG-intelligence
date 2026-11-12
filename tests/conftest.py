"""Shared test fixtures.

Tests never download models or call an LLM: they use HashingEmbedder (deterministic, offline)
and ExtractiveLLM / scripted fake LLMs. Imports of later-milestone modules happen inside the
fixtures, so early milestones' tests run before those modules exist.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "data" / "sample_docs"
DATASET = REPO_ROOT / "eval" / "datasets" / "eval_v1.jsonl"


@pytest.fixture
def make_pdf():
    """Return a function that builds a text PDF in memory: make_pdf(["page 1 text", "page 2 text"])."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    def _make(pages: list[str]) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        for text in pages:
            y = 800
            for line in text.split("\n"):
                c.drawString(60, y, line)
                y -= 16
            c.showPage()
        c.save()
        return buf.getvalue()

    return _make


@pytest.fixture
def settings(tmp_path):
    from ragintel.config import Settings

    return Settings(
        _env_file=None,
        db_path=tmp_path / "test.db",
        users_file=tmp_path / "users.json",
        embedder="hashing",
        llm_provider="extractive",
        min_evidence_score=0.10,
        chunk_size_chars=900,
        chunk_overlap_chars=120,
    )


@pytest.fixture
def store(settings):
    from ragintel.store.sqlite_store import SQLiteStore

    s = SQLiteStore(settings.db_path)
    yield s
    s.close()


def ingest_manifest(ingestion) -> None:
    manifest = json.loads((SAMPLE_DIR / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["documents"]:
        path = SAMPLE_DIR / entry["file"]
        ingestion.ingest(
            path.name,
            path.read_bytes(),
            doc_id=entry["doc_id"],
            title=entry["title"],
            department=entry["department"],
            version=entry["version"],
            allowed_groups=entry["allowed_groups"],
            status=entry.get("status", "current"),
        )


@pytest.fixture
def services(settings):
    """Fully wired services with the sample corpus ingested and demo users created."""
    from ragintel.auth import UserDirectory, create_users_file
    from ragintel.services import build_services

    keys = create_users_file(settings.users_file)
    svc = build_services(settings, users=UserDirectory.load(settings.users_file))
    ingest_manifest(svc.ingestion)
    svc.api_keys = keys  # test convenience only
    yield svc
    svc.store.close()