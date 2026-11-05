"""Milestone 3: loading and cleaning, including malicious / malformed inputs."""

import io

import pytest
from pypdf import PdfReader, PdfWriter

from ragintel.errors import DocumentParseError, EncryptedPdfError, TooManyPages, UnsupportedFileType
from ragintel.ingestion.cleaning import clean_pages, clean_text, remove_repeated_edge_lines
from ragintel.ingestion.loaders import load_document
from ragintel.models import PageText


def test_pdf_pages_and_numbers_preserved(make_pdf):
    data = make_pdf(["First page about leave.", "Second page about expenses.", "Third page."])
    pages = load_document("policy.pdf", data)
    assert [p.page_number for p in pages] == [1, 2, 3]
    assert "leave" in pages[0].text and "expenses" in pages[1].text


def test_text_and_markdown_are_single_page():
    pages = load_document("notes.md", "# Title\n\nHello".encode("utf-8"))
    assert len(pages) == 1 and pages[0].page_number == 1


def test_utf8_bom_is_stripped():
    pages = load_document("notes.txt", "\ufeffHello".encode("utf-8"))
    assert pages[0].text == "Hello"


@pytest.mark.parametrize("name", ["virus.exe", "sheet.xlsx", "noextension"])
def test_unsupported_extensions_rejected(name):
    with pytest.raises(UnsupportedFileType):
        load_document(name, b"data")


def test_fake_pdf_rejected():
    with pytest.raises(DocumentParseError):
        load_document("report.pdf", b"MZ\x90\x00 this is really an executable")


def test_truncated_pdf_rejected(make_pdf):
    data = make_pdf(["hello"])[:200]
    with pytest.raises(DocumentParseError):
        load_document("broken.pdf", data)


def test_encrypted_pdf_rejected(make_pdf):
    reader = PdfReader(io.BytesIO(make_pdf(["secret"])))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.encrypt("pw")
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(EncryptedPdfError):
        load_document("locked.pdf", buf.getvalue())


def test_page_limit_enforced(make_pdf):
    with pytest.raises(TooManyPages):
        load_document("long.pdf", make_pdf(["a", "b", "c"]), max_pages=2)


def test_non_utf8_text_rejected():
    with pytest.raises(DocumentParseError):
        load_document("legacy.txt", "caf\u00e9".encode("cp1252"))


def test_empty_file_rejected():
    with pytest.raises(DocumentParseError):
        load_document("empty.txt", b"")


def test_clean_text_fixes_hyphenation_ligatures_and_spaces():
    raw = "The reimburse-\nment  rule\u00a0applies to \ufb01nance.\r\n\r\n\r\n\r\nNext."
    assert clean_text(raw) == "The reimbursement rule applies to finance.\n\nNext."


def test_repeated_headers_and_footers_removed():
    pages = [
        PageText(i, f"NORTHWIND CONFIDENTIAL\nBody text number {i} is unique.\nPage {i} of 4")
        for i in range(1, 5)
    ]
    cleaned = remove_repeated_edge_lines(pages)
    for page in cleaned:
        assert "NORTHWIND CONFIDENTIAL" not in page.text
        assert "of 4" not in page.text
        assert "is unique" in page.text


def test_body_lines_differing_only_by_numbers_are_kept():
    pages = [PageText(i, f"Header\nClause {i} applies to drivers.\nMore text {i}.\nFooter") for i in range(1, 5)]
    cleaned = remove_repeated_edge_lines(pages)
    assert all(f"Clause {p.page_number} applies" in p.text for p in cleaned)
    assert all("Header" not in p.text and "Footer" not in p.text for p in cleaned)


def test_short_documents_keep_their_lines():
    pages = [PageText(1, "Header\nBody"), PageText(2, "Header\nBody 2")]
    assert remove_repeated_edge_lines(pages) == pages


def test_clean_pages_keeps_page_numbers():
    out = clean_pages([PageText(5, "  a  "), PageText(6, "b")])
    assert [p.page_number for p in out] == [5, 6]