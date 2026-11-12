"""Turn uploaded bytes into per-page text.

Security posture: uploaded files are untrusted. We check the extension AND the
content signature, refuse encrypted PDFs, cap the page count, and never execute
anything embedded in the file. pypdf is pure Python, so a malformed PDF raises
an exception instead of crashing the process.
"""

import io
import logging
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ragintel.errors import (
    DocumentParseError,
    EncryptedPdfError,
    TooManyPages,
    UnsupportedFileType,
)
from ragintel.models import PageText

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def load_document(
    filename: str,
    data: bytes,
    *,
    max_pages: int = 500,
) -> list[PageText]:
    """Load a supported document and return its extracted pages."""

    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileType(
            f"Unsupported file type '{ext or '(none)'}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )

    if not data:
        raise DocumentParseError("The uploaded file is empty.")

    if ext == ".pdf":
        return _load_pdf(data, max_pages=max_pages)

    return _load_text(data)


def _load_pdf(data: bytes, *, max_pages: int) -> list[PageText]:
    """Extract PDF pages while enforcing document safety limits."""

    # Check that the file has a PDF signature near its beginning.
    if b"%PDF-" not in data[:1024]:
        raise DocumentParseError(
            "The file has a .pdf extension but is not a PDF."
        )

    try:
        reader = PdfReader(io.BytesIO(data), strict=False)

        # Reject password-protected PDFs.
        if reader.is_encrypted:
            raise EncryptedPdfError(
                "Encrypted or password-protected PDFs are not supported."
            )

        # Accessing the page tree can reveal malformed PDF structures.
        page_count = len(reader.pages)

    except EncryptedPdfError:
        raise

    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise DocumentParseError(
            "The PDF could not be read; it may be corrupt or incomplete."
        ) from exc

    if page_count == 0:
        raise DocumentParseError("The PDF has no pages.")

    if page_count > max_pages:
        raise TooManyPages(
            f"The PDF has {page_count} pages; the limit is {max_pages}."
        )

    pages: list[PageText] = []

    for number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""

        except Exception:
            # A failure on one page should not lose the entire document.
            logger.warning(
                "Text extraction failed on page %d",
                number,
            )
            text = ""

        pages.append(
            PageText(
                page_number=number,
                text=text,
            )
        )

    return pages


def _load_text(data: bytes) -> list[PageText]:
    """Decode UTF-8 text and Markdown as a single page."""

    try:
        text = data.decode("utf-8-sig")

    except UnicodeDecodeError as exc:
        raise DocumentParseError(
            "Text files must be UTF-8 encoded."
        ) from exc

    return [
        PageText(
            page_number=1,
            text=text,
        )
    ]
