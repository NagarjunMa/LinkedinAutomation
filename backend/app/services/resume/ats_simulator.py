from io import BytesIO
from pydantic import BaseModel
from typing import List
import pdfplumber
from docx import Document as DocxDocument
from app.schemas.resume import FormatIssue


class ATSResult(BaseModel):
    parseability_score: int
    raw_text: str
    format_issues: List[FormatIssue]


def simulate_ats(content: bytes, filename: str) -> ATSResult:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _simulate_pdf(content)
    if ext == "docx":
        return _simulate_docx(content)
    raise ValueError(f"Unsupported: {ext}")


def _simulate_pdf(content: bytes) -> ATSResult:
    issues: List[FormatIssue] = []
    score = 100
    with pdfplumber.open(BytesIO(content)) as pdf:
        text_parts: list[str] = []
        for i, page in enumerate(pdf.pages):
            tables = page.find_tables()
            if tables:
                issues.append(FormatIssue(
                    type="table",
                    location=f"page {i + 1}",
                    fix_hint="ATS parsers misread tables. Use bullet lists instead.",
                ))
                score -= 15
            if page.images:
                issues.append(FormatIssue(
                    type="image",
                    location=f"page {i + 1}",
                    fix_hint="Remove images. ATS ignores them but they shift layout.",
                ))
                score -= 5
            text = page.extract_text() or ""
            text_parts.append(text)
            cols = _detect_columns(page)
            if cols > 1:
                issues.append(FormatIssue(
                    type="multi_column",
                    location=f"page {i + 1}",
                    fix_hint="Switch to single-column layout.",
                ))
                score -= 20
    raw = "\n".join(text_parts)
    score = max(0, min(100, score))
    return ATSResult(parseability_score=score, raw_text=raw, format_issues=issues)


def _detect_columns(page) -> int:
    """Cluster word x-positions into bins. >1 cluster = multi-column."""
    words = page.extract_words()
    if not words:
        return 1
    xs = sorted(w["x0"] for w in words)
    if not xs:
        return 1
    width = page.width
    half = width / 2
    left = sum(1 for x in xs if x < half)
    right = sum(1 for x in xs if x >= half)
    # If both halves have ≥30% of words, it's two-column
    total = len(xs)
    if left / total > 0.3 and right / total > 0.3:
        return 2
    return 1


def _simulate_docx(content: bytes) -> ATSResult:
    doc = DocxDocument(BytesIO(content))
    issues: List[FormatIssue] = []
    score = 100
    if doc.tables:
        issues.append(FormatIssue(
            type="table",
            location="document",
            fix_hint="ATS parsers misread tables. Use bullet lists.",
        ))
        score -= 15
    raw = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ATSResult(parseability_score=max(0, min(100, score)), raw_text=raw, format_issues=issues)
