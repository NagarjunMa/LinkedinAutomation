import uuid
from io import BytesIO
import pdfplumber
from docx import Document as DocxDocument
from app.schemas.resume_v2 import (
    ResumeDocumentJSON, Contact, ExperienceEntry, EducationEntry,
    Skills, Bullet,
)


def parse_resume(content: bytes, filename: str) -> ResumeDocumentJSON:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return _parse_pdf(content)
    if ext == "docx":
        return _parse_docx(content)
    raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(content: bytes) -> ResumeDocumentJSON:
    with pdfplumber.open(BytesIO(content)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    raw_text = "\n".join(pages)
    return _structure_from_text(raw_text)


def _parse_docx(content: bytes) -> ResumeDocumentJSON:
    doc = DocxDocument(BytesIO(content))
    lines: list[str] = []
    for p in doc.paragraphs:
        if not p.text.strip():
            continue
        if "list" in (p.style.name or "").lower() or "bullet" in (p.style.name or "").lower():
            lines.append(f"• {p.text}")
        else:
            lines.append(p.text)
    raw_text = "\n".join(lines)
    return _structure_from_text(raw_text)


def _structure_from_text(raw_text: str) -> ResumeDocumentJSON:
    """Heuristic section splitter. Good enough for v1; LLM-augmented later."""
    sections = _split_sections(raw_text)
    contact = _extract_contact(sections.get("header", raw_text[:500]))
    experience = _extract_experience(sections.get("experience", ""))
    education = _extract_education(sections.get("education", ""))
    skills = _extract_skills(sections.get("skills", ""))
    summary = sections.get("summary") or None
    return ResumeDocumentJSON(
        contact=contact, summary=summary, experience=experience,
        education=education, skills=skills, raw_text=raw_text,
    )


SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills", "core competencies"],
    "summary": ["summary", "profile", "objective"],
}


def _split_sections(raw: str) -> dict[str, str]:
    lines = raw.splitlines()
    out: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in lines:
        norm = line.strip().lower()
        matched = None
        for sect, aliases in SECTION_HEADERS.items():
            if norm in aliases or any(norm.startswith(a + ":") for a in aliases):
                matched = sect
                break
        if matched:
            current = matched
            out.setdefault(current, [])
            continue
        out.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _extract_contact(header_block: str) -> Contact:
    import re
    name = header_block.splitlines()[0].strip() if header_block else "Unknown"
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", header_block)
    email = email_match.group(0) if email_match else None
    phone_m = re.search(r"[\+\d][\d\s\-\(\)]{7,}", header_block)
    return Contact(name=name, email=email, phone=phone_m.group(0).strip() if phone_m else None, links=[])


def _extract_experience(block: str) -> list[ExperienceEntry]:
    """Each entry = role line + bullets that follow until next role line.
    Role line heuristic: contains ' at ' or ' | ' or year range pattern."""
    import re
    entries: list[ExperienceEntry] = []
    if not block:
        return entries
    lines = [l for l in block.splitlines() if l.strip()]
    current_role: ExperienceEntry | None = None
    role_pattern = re.compile(r"(\d{4})\s*[-–—]\s*(\d{4}|present|now)", re.I)
    for line in lines:
        is_role = bool(role_pattern.search(line)) or " at " in line.lower() or " | " in line
        if is_role:
            if current_role:
                entries.append(current_role)
            parts = re.split(r"\s+at\s+|\s+\|\s+", line, maxsplit=1, flags=re.I)
            role = parts[0].strip() if parts else line.strip()
            company = parts[1].strip() if len(parts) > 1 else "Unknown"
            current_role = ExperienceEntry(company=company, role=role, dates=None, location=None, bullets=[])
        elif current_role is not None and line.strip().startswith(("•", "-", "*")):
            text = line.lstrip("•-*").strip()
            current_role.bullets.append(Bullet(id=str(uuid.uuid4())[:8], text=text, raw_text=text))
    if current_role:
        entries.append(current_role)
    return entries


def _extract_education(block: str) -> list[EducationEntry]:
    if not block:
        return []
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    out: list[EducationEntry] = []
    for line in lines:
        out.append(EducationEntry(school=line, degree=None, dates=None))
    return out


def _extract_skills(block: str) -> Skills:
    if not block:
        return Skills()
    flat = block.replace("\n", ",")
    items = [s.strip() for s in flat.split(",") if s.strip()]
    return Skills(hard=items, soft=[])
