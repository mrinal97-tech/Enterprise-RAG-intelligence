"""Milestone 2: configuration, errors and models."""

import pytest
from pydantic import ValidationError

from ragintel.config import Settings
from ragintel.errors import FileTooLarge, RagError
from ragintel.logging_setup import fingerprint
from ragintel.models import Principal


def test_defaults_are_safe():
    s = Settings(_env_file=None)
    assert s.retrieval_mode == "vector"
    assert s.openai_api_key == ""  # no secret is ever defaulted
    assert s.max_upload_bytes == 20 * 1024 * 1024


def test_env_var_overrides(monkeypatch):
    monkeypatch.setenv("RAG_TOP_K", "7")
    assert Settings(_env_file=None).top_k == 7


def test_overlap_must_be_smaller_than_chunk():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, chunk_size_chars=500, chunk_overlap_chars=500)


def test_candidate_k_at_least_top_k():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, top_k=10, candidate_k=5)


def test_errors_carry_code_and_status():
    err = FileTooLarge("too big")
    assert isinstance(err, RagError)
    assert (err.code, err.http_status, err.message) == ("file_too_large", 413, "too big")


def test_fingerprint_is_stable_and_not_the_text(monkeypatch):
    monkeypatch.setenv("RAG_LOG_FINGERPRINT_KEY", "test-key")
    assert fingerprint("salary of G4") == fingerprint("salary of G4")
    assert "salary" not in fingerprint("salary of G4")


def test_fingerprint_depends_on_the_key(monkeypatch):
    monkeypatch.setenv("RAG_LOG_FINGERPRINT_KEY", "key-one")
    first = fingerprint("salary of G4")
    monkeypatch.setenv("RAG_LOG_FINGERPRINT_KEY", "key-two")
    assert fingerprint("salary of G4") != first


def test_fingerprint_without_key_fails_clearly(monkeypatch):
    monkeypatch.delenv("RAG_LOG_FINGERPRINT_KEY", raising=False)
    with pytest.raises(RuntimeError, match="RAG_LOG_FINGERPRINT_KEY"):
        fingerprint("anything")


def test_principal_is_immutable():
    p = Principal("alice", frozenset({"all_employees"}))
    with pytest.raises(AttributeError):
        p.user_id = "mallory"