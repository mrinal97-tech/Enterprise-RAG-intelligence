"""Logging configuration.

Rule for this project: logs carry ids, counts, scores, timings and hashes.
They do NOT carry document text or the full question at INFO level, because both
can contain confidential information. Use `fingerprint()` to correlate a question
across log lines without storing it.
"""

from __future__ import annotations

import hashlib
import logging
import sys

_configured = False


def configure_logging(level: str = "INFO") -> None:
    global _configured
    root = logging.getLogger()
    root.setLevel(level.upper())
    if _configured:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s"))
    root.addHandler(handler)
    _configured = True


def fingerprint(text: str) -> str:
    """Short, non-reversible id for a piece of text (for log correlation only)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]