from io import BytesIO
from pydantic import BaseModel, Field
from typing import List
import pdfplumber
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from app.schemas.resume_v2 import FormatIssue


class ATSResult(BaseModel):
    parseability_score: int
    raw_text: str
    format_issues: List[FormatIssue]
    observed_format_issues: list[FormatIssue] = Field(default_factory=list)
    page_count: int | None = None


def simulate_ats(content: bytes, filename: str) -> ATSResult:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _simulate_pdf(content)
    if ext == "docx":
        return _simulate_docx(content)
    raise ValueError(f"Unsupported: {ext}")


def _simulate_pdf(content: bytes) -> ATSResult:
    issues: List[FormatIssue] = []
    observed: list[FormatIssue] = []
    score = 100
    with pdfplumber.open(BytesIO(content)) as pdf:
        page_count = len(pdf.pages)
        text_parts: list[str] = []
        for i, page in enumerate(pdf.pages):
            first_page_issue = len(issues)
            tables = [table for table in page.find_tables() if _is_true_table(table)]
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
            has_columns, interleaved = _detect_columns(page, text)
            if has_columns:
                column_issue = FormatIssue(
                    type="multi_column",
                    location=f"page {i + 1}",
                    fix_hint="Switch to single-column layout.",
                )
                issues.append(column_issue)
                if interleaved:
                    observed.append(column_issue)
                score -= 20
            if not text.strip():
                observed.extend(issue for issue in issues[first_page_issue:] if issue.type != "multi_column")
    raw = "\n".join(text_parts)
    score = max(0, min(100, score))
    return ATSResult(
        parseability_score=score, raw_text=raw, format_issues=issues,
        observed_format_issues=observed, page_count=page_count,
    )


def _is_true_table(table) -> bool:
    """Reject line-based false positives while preserving genuine data grids.

    Section divider rules can cause pdfplumber to infer a one-column "table"
    across an otherwise normal resume. A meaningful ATS-risk table needs at
    least two populated rows and two populated columns.
    """
    data = table.extract() or []
    populated_rows = [row for row in data if any((cell or "").strip() for cell in row or [])]
    if len(populated_rows) < 2:
        return False
    column_count = max((len(row or []) for row in populated_rows), default=0)
    return column_count >= 2


def _detect_columns(page, extracted_text: str) -> tuple[bool, bool]:
    """Detect stable columns and whether local extraction joins them across rows."""
    words = page.extract_words()
    if not words:
        return False, False
    width = page.width
    min_gutter = width * 0.18
    min_side_words = 2
    line_tolerance = 3

    lines: dict[int, list[dict]] = {}
    for word in words:
        key = round(float(word["top"]) / line_tolerance)
        lines.setdefault(key, []).append(word)

    split_lines = 0
    interleaved_lines = 0
    candidate_lines = 0
    gutters: list[tuple[float, float]] = []
    extracted_lines = {" ".join(line.split()) for line in extracted_text.splitlines()}
    for line_words in lines.values():
        if len(line_words) < min_side_words * 2:
            continue
        candidate_lines += 1
        ordered = sorted(line_words, key=lambda w: float(w["x0"]))
        gaps = [
            (float(right["x0"]) - float(left["x1"]), float(left["x1"]), float(right["x0"]))
            for left, right in zip(ordered, ordered[1:])
        ]
        if not gaps:
            continue
        gap, left_edge, right_edge = max(gaps, key=lambda item: item[0])
        if gap < min_gutter:
            continue
        left_count = sum(1 for word in ordered if float(word["x1"]) <= left_edge)
        right_count = sum(1 for word in ordered if float(word["x0"]) >= right_edge)
        if left_count >= min_side_words and right_count >= min_side_words:
            split_lines += 1
            gutters.append((left_edge, right_edge))
            if " ".join(word["text"] for word in ordered) in extracted_lines:
                interleaved_lines += 1

    if candidate_lines < 6 or split_lines < 4:
        return False, False

    gutter_centers = [(left + right) / 2 for left, right in gutters]
    center_avg = sum(gutter_centers) / len(gutter_centers)
    spread = max(abs(center - center_avg) for center in gutter_centers)
    stability = max(0.0, 1.0 - spread / (width * 0.15))
    prevalence = split_lines / candidate_lines
    has_columns = prevalence * 0.75 + stability * 0.25 >= 0.65
    return has_columns, has_columns and interleaved_lines >= 2


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
    cell_tag, paragraph_tag, text_tag = map(qn, ("w:tc", "w:p", "w:t"))
    # Visit physical cells once. Expanding the table grid follows vertical merges recursively.
    table_text = (
        "".join(run.text or "" for run in paragraph.iter(text_tag)).strip()
        for cell in doc.element.body.iter(cell_tag)
        for paragraph in cell.iterchildren(paragraph_tag)
    )
    missing_cell_text = any(paragraph and paragraph not in raw for paragraph in table_text)
    return ATSResult(
        parseability_score=max(0, min(100, score)), raw_text=raw, format_issues=issues,
        observed_format_issues=issues if missing_cell_text else [],
    )
