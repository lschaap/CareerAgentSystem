"""PDF résumé text extraction."""

from io import BytesIO

from pypdf import PdfReader


class PDFExtractionError(ValueError):
    """Raised when a PDF cannot provide usable résumé text."""


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        raise PDFExtractionError("The uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)
    except Exception as exc:
        raise PDFExtractionError("The file could not be read as a PDF.") from exc

    cleaned = "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()
    if len(cleaned) < 40:
        raise PDFExtractionError(
            "No usable text was found. This may be a scanned PDF; "
            "export a text-based PDF and retry."
        )
    return cleaned
