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


def guess_name_from_pdf(data: bytes) -> Optional[str]:
    """
    Guess candidate name from largest font-size text near the top of page 1.
    Uses PyMuPDF span-level font data; returns None if unavailable or inconclusive.
    """
    doc = fitz.open(stream=data, filetype="pdf")
    candidates: list[dict[str, float | str]] = []
    try:
        page = doc[0]
        page_height = page.rect.height
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                y = line["bbox"][1]
                if y > page_height * 0.35:
                    continue
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    candidates.append({
                        "text": text,
                        "size": float(span.get("size", 0)),
                        "x0": float(span["bbox"][0]),
                        "y": float(y),
                    })
    finally:
        doc.close()

    if not candidates:
        return None

    max_size = max(c["size"] for c in candidates)
    top_size = [c for c in candidates if c["size"] >= max_size - 0.5]
    by_line: dict[float, list[dict[str, float | str]]] = {}
    for c in top_size:
        by_line.setdefault(round(c["y"], 1), []).append(c)

    best_y = max(by_line, key=lambda y: max(c["size"] for c in by_line[y]))
    line_spans = sorted(by_line[best_y], key=lambda c: c["x0"])
    return " ".join(str(c["text"]) for c in line_spans).strip() or None
