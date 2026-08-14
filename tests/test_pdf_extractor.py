from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from career_agent.pdf_extractor import PDFExtractionError, extract_pdf_text


def test_extract_pdf_text_joins_pages() -> None:
    reader = Mock()
    reader.pages = [Mock(), Mock()]
    reader.pages[0].extract_text.return_value = "Fictional Candidate\nPython engineer"
    reader.pages[1].extract_text.return_value = "Delivered AI implementation projects for clients."
    with patch("career_agent.pdf_extractor.PdfReader", return_value=reader):
        text = extract_pdf_text(b"%PDF fictional fixture")
    assert "Python engineer" in text
    assert "AI implementation" in text


def test_pdf_without_extractable_text_is_rejected() -> None:
    reader = Mock()
    reader.pages = [Mock()]
    reader.pages[0].extract_text.return_value = ""
    with patch("career_agent.pdf_extractor.PdfReader", return_value=reader):
        with pytest.raises(PDFExtractionError, match="No usable text"):
            extract_pdf_text(BytesIO().getvalue() or b"fake")
