"""Text cleaning.

PDF extraction produces noise that hurts both retrieval and citations:
ligatures, words split across lines with hyphens, ragged whitespace, and the same
header/footer repeated on every page. We fix those here, conservatively: cleaning
must never change the meaning of the text, because answers cite it.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

from ragintel.models import PageText

_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")
_SPACES = re.compile(r"[ \t\u00a0\u2009\u202f]+")  # space, tab, non-breaking and thin spaces
_SPACE_AROUND_NEWLINE = re.compile(r" *\n *")
_MANY_NEWLINES = re.compile(r"\n{3,}")
_PAGE_NUMBER = re.compile(r"^[-\s]*(page\s*)?\d+(\s*(of|/)\s*\d+)?[-\s]*$")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)  # e.g. the "fi" ligature -> "fi"
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_BREAK.sub(r"\1\2", text)  # "reimburse-\nment" -> "reimbursement"
    text = _SPACES.sub(" ", text)
    text = _SPACE_AROUND_NEWLINE.sub("\n", text)
    text = _MANY_NEWLINES.sub("\n\n", text)
    return text.strip()


def _line_signature(line: str) -> str:
    # Page-number lines ("Page 3 of 12", "4", "- 7 -") are treated as one repeating footer.
    # All other lines must repeat EXACTLY; masking digits everywhere would wrongly delete body
    # lines such as "Clause 3 applies" / "Clause 4 applies".
    line = line.strip().lower()
    if _PAGE_NUMBER.match(line):
        return "<page-number>"
    return line


def remove_repeated_edge_lines(
    pages: list[PageText], *, min_pages: int = 3, min_ratio: float = 0.6, edge_lines: int = 2
) -> list[PageText]:
    """Drop header/footer lines that repeat at the top or bottom of most pages."""
    if len(pages) < min_pages:
        return pages

    counts: Counter[str] = Counter()
    for page in pages:
        lines = [ln for ln in page.text.split("\n") if ln.strip()]
        edges = lines[:edge_lines] + lines[-edge_lines:]
        counts.update({_line_signature(ln) for ln in edges})

    threshold = min_ratio * len(pages)
    repeated = {sig for sig, n in counts.items() if n >= threshold}
    if not repeated:
        return pages

    cleaned: list[PageText] = []
    for page in pages:
        lines = page.text.split("\n")
        non_empty_idx = [i for i, ln in enumerate(lines) if ln.strip()]
        edge_idx = set(non_empty_idx[:edge_lines] + non_empty_idx[-edge_lines:])
        kept = [ln for i, ln in enumerate(lines) if not (i in edge_idx and _line_signature(ln) in repeated)]
        cleaned.append(PageText(page.page_number, "\n".join(kept).strip()))
    return cleaned


def clean_pages(pages: list[PageText]) -> list[PageText]:
    normalised = [PageText(p.page_number, clean_text(p.text)) for p in pages]
    return remove_repeated_edge_lines(normalised)