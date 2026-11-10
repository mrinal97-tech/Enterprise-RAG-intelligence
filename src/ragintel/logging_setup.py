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
import hmac
import os

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
    secret = os.environ["RAG_LOG_FINGERPRINT_KEY"].encode("utf-8")

    return hmac.new(
        secret,
        text.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()[:16]