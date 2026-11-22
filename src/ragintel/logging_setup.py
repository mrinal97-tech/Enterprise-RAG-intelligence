"""Logging configuration.

Rule for this project: logs carry ids, counts, scores, timings and hashes.
They do NOT carry document text or the full question at INFO level, because both
can contain confidential information. Use `fingerprint()` to correlate a question
across log lines without storing it.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys

_configured = False



def configure_logging(level: str = "INFO") -> None:
    global _configured

    # 1. Validate logging level
    valid_levels = {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }

    normalized_level = level.upper()

    if normalized_level not in valid_levels:
        raise ValueError(f"Invalid logging level: {level}")

    # 2. Get root logger
    root = logging.getLogger()

    # 3. Apply logging level
    root.setLevel(normalized_level)

    # 4. Avoid duplicate handlers
    if _configured:
        return

    # 5. Create terminal logging handler
    handler = logging.StreamHandler(sys.stderr)

    # 6. Define log format
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s | %(message)s"
        )
    )

    # 7. Attach handler to root logger
    root.addHandler(handler)

    # 8. Mark logging as configured
    _configured = True


def fingerprint(text: str) -> str:
    """Short, non-reversible id for a piece of text (for log correlation only).

    Uses an HMAC with a secret key so short, guessable text (for example
    "salary of G4") cannot be matched by hashing guesses.
    """
    key = os.environ.get("RAG_LOG_FINGERPRINT_KEY")
    if not key:
        raise RuntimeError(
            "RAG_LOG_FINGERPRINT_KEY is not set. Set it in your terminal or deployment environment."
        )

    return hmac.new(
        key.encode("utf-8"),
        text.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16]