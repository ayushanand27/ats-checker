"""Resume and job-description text extraction — no API calls."""

from __future__ import annotations

import io
import os
import re
import shutil
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


def _page_text_column_ordered(page: fitz.Page) -> str:
    """
    Reassemble page text with left-column blocks before right-column blocks.
    Helps multi-column resumes (e.g. Jake's template) keep sidebar headers like
    Skills near their content instead of interleaved with main-column text.
    """
    blocks = page.get_text("blocks")
    if not blocks:
        return page.get_text()

    typed: list[tuple[float, float, str]] = []
    for block in blocks:
        if len(block) < 5:
            continue
        text = str(block[4]).strip()
        if not text:
            continue
        typed.append((float(block[0]), float(block[1]), text))

    if not typed:
        return page.get_text()

    page_width = page.rect.width
    # Jake's-style sidebar is ~30–38% from the left; use adaptive split when possible
    x0_values = sorted(b[0] for b in typed)
    split_x = page_width * 0.38
    if len(x0_values) >= 4:
        mid = len(x0_values) // 2
        gap = x0_values[mid] - x0_values[mid - 1]
        if gap > page_width * 0.08:
            split_x = (x0_values[mid - 1] + x0_values[mid]) / 2.0

    left = sorted((y, t) for x, y, t in typed if x < split_x)
    right = sorted((y, t) for x, y, t in typed if x >= split_x)
    ordered = [t for _, t in left] + [t for _, t in right]
    return "\n".join(ordered)


# Bullet glyphs that PDF exporters emit, including Word's Symbol-font bullets
# (U+F0B7, U+F0A7 …, private-use code points) that look like "•" on screen.
_BULLET_GLYPHS = "\uf0b7\uf0a7\uf076\uf0d8\uf0fc\uf0e0\uf0a8\uf06e\uf0a1\u25e6\u2023\u2043\u2219\u00b7\u25cb\u25aa\u25ab\u25a0\u25a1\u27a2\u27a4\u2713\u2714\u25cf\u25b8\u25ba\u2022"
_GLYPH_LINE_RE = re.compile(rf"^\s*[{_BULLET_GLYPHS}]\s*")
_DATE_HINT_RE = re.compile(r"\b(?:19|20)\d{2}\b|\bpresent\b", re.I)


def normalize_bullets(text: str) -> str:
    """Make bullets parseable: unify glyphs to "• ", join a lone glyph with the
    next line, and re-join bullet text that the PDF wrapped onto a new line."""
    out: list[str] = []
    pending_bullet = False
    for raw_line in (text or "").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if _GLYPH_LINE_RE.match(line):
            rest = _GLYPH_LINE_RE.sub("", line).strip()
            if not rest:
                pending_bullet = True
                continue
            out.append(f"\u2022 {rest}")
            pending_bullet = False
            continue
        if pending_bullet and stripped:
            out.append(f"\u2022 {stripped}")
            pending_bullet = False
            continue
        prev = out[-1] if out else ""
        if (
            stripped
            and prev.startswith("\u2022 ")
            and (stripped[0].islower() or stripped[0] in "(&%")
            and not _DATE_HINT_RE.search(stripped)
        ):
            out[-1] = f"{prev.rstrip()} {stripped}"
            continue
        out.append(line)
    return "\n".join(out)


def extract_text_from_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    parts: list[str] = []
    for page in doc:
        parts.append(_page_text_column_ordered(page))
    doc.close()
    return normalize_bullets("\n".join(parts)).strip()


def _configure_tesseract() -> bool:
    """Point pytesseract at the Tesseract binary (Windows often lacks PATH entry)."""
    try:
        import pytesseract
    except ImportError:
        return False

    if shutil.which("tesseract"):
        return True

    candidates = [
        os.environ.get("TESSERACT_CMD", ""),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


def extract_text_from_pdf_with_ocr(data: bytes) -> tuple[str, bool]:
    """
    Extract PDF text; attempt OCR when native extraction is sparse (scanned PDFs).
    Requires pytesseract + Tesseract binary — falls back gracefully.
    """
    text = extract_text_from_pdf(data)
    warning = validate_extracted_text(text)
    if warning is None:
        return text, False

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return text, False

    if not _configure_tesseract():
        return text, False

    doc = fitz.open(stream=data, filetype="pdf")
    ocr_parts: list[str] = []
    try:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_parts.append(pytesseract.image_to_string(img))
    except Exception:
        return text, False
    finally:
        doc.close()

    ocr_text = "\n".join(ocr_parts).strip()
    if len(ocr_text) > len(text.strip()) + 40:
        return ocr_text, True
    return text, False


def extract_text_from_docx(data: bytes) -> str:
    doc = Document(io.BytesIO(data))
    parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            # Word list paragraphs (List Bullet style or numbering) carry no bullet
            # character in their text — add one so bullets are detected.
            is_list = "list" in (para.style.name or "").lower() or para._p.pPr is not None and para._p.pPr.numPr is not None
            parts.append(f"\u2022 {para.text.strip()}" if is_list and not para.text.lstrip().startswith(("\u2022", "-", "*")) else para.text)
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
        text, _ = extract_text_from_pdf_with_ocr(data)
        return text
    if lower.endswith(".docx"):
        return extract_text_from_docx(data)
    if lower.endswith(".txt"):
        return normalize_bullets(extract_text_from_txt(data))
    raise ValueError(f"Unsupported file type: {filename}")


def detect_multi_column_pdf(data: bytes) -> bool:
    """True when PDF blocks suggest a multi-column layout."""
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        for page in doc:
            blocks = page.get_text("blocks")
            x0_values = sorted(
                float(b[0]) for b in blocks if len(b) >= 5 and str(b[4]).strip()
            )
            if len(x0_values) < 4:
                continue
            page_width = page.rect.width
            mid = len(x0_values) // 2
            gap = x0_values[mid] - x0_values[mid - 1]
            if gap > page_width * 0.08:
                return True
    finally:
        doc.close()
    return False


def docx_has_tables(data: bytes) -> bool:
    """True when DOCX contains table structures."""
    doc = Document(io.BytesIO(data))
    return len(doc.tables) > 0


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
                        "x1": float(span["bbox"][2]),
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
    # Letter-spaced headings split one word into several spans ("Ri" "y" "a");
    # insert a space only where the visual gap looks like a real word gap.
    out = ""
    for prev, cur in zip([None] + line_spans[:-1], line_spans):
        if prev is None:
            out = str(cur["text"])
            continue
        gap = float(cur["x0"]) - float(prev.get("x1", prev["x0"]))
        out += (" " if gap > 0.18 * float(cur["size"]) else "") + str(cur["text"])
    return " ".join(out.split()) or None
