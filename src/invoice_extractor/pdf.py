"""Read text out of PDF files. The only module that touches PDFs."""

from __future__ import annotations

from pathlib import Path

import pdfplumber


class NoTextError(ValueError):
    """The PDF has no text layer (probably a scan): it needs OCR first."""


def pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    if not text.strip():
        raise NoTextError("no text layer (scanned image?): needs OCR first")
    return text
