"""Typed errors with safe, user-facing messages.

Each error carries a stable machine-readable `code` and an HTTP status. The message
must never contain document text, file paths or stack traces: it is shown to API callers.
"""

from __future__ import annotations


class RagError(Exception):
    code = "rag_error"
    http_status = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UnsupportedFileType(RagError):
    code = "unsupported_file_type"
    http_status = 415


class FileTooLarge(RagError):
    code = "file_too_large"
    http_status = 413


class TooManyPages(RagError):
    code = "too_many_pages"
    http_status = 413


class DocumentParseError(RagError):
    code = "document_parse_error"
    http_status = 422


class EncryptedPdfError(RagError):
    code = "encrypted_pdf"
    http_status = 422


class NoExtractableText(RagError):
    code = "no_extractable_text"
    http_status = 422


class InvalidDocumentId(RagError):
    code = "invalid_document_id"
    http_status = 422


class DocumentNotFound(RagError):
    code = "document_not_found"
    http_status = 404


class LLMUnavailable(RagError):
    code = "llm_unavailable"
    http_status = 503


class IndexMismatch(RagError):
    code = "index_mismatch"
    http_status = 500