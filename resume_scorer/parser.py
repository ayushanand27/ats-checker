"""Resume and job-description text extraction — no API calls."""

from __future__ import annotations

import io
import re
from typing import Optional

import fitz  # PyMuPDF
from docx import Document


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def extract_text_from_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts).strip()


def extract_text_from_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    return "\n".join(parts).strip()


def extract_text_from_txt(data: bytes) -> str:
    return _decode_text(data).strip()


def extract_text(data: bytes, filename: str) -> str:
    """Extract plain text from uploaded file bytes based on extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if lower.endswith(".docx"):
        return extract_text_from_docx(data)
    if lower.endswith(".txt"):
        return extract_text_from_txt(data)
    raise ValueError(f"Unsupported file type: {filename}")


def alphanumeric_ratio(text: str) -> float:
    if not text:
        return 0.0
    alnum = sum(1 for c in text if c.isalnum())
    return alnum / len(text)


def validate_extracted_text(text: str) -> Optional[str]:
    """Return a warning message if text looks unreadable, else None."""
    if len(text) < 50:
        return (
            "Extracted text is very short (< 50 characters). "
            "The file may be image-based or unreadable by text extraction."
        )
    if alphanumeric_ratio(text) < 0.4:
        return (
            "Extracted text contains mostly non-alphanumeric characters. "
            "The file may be a scanned/image PDF without OCR."
        )
    return None
