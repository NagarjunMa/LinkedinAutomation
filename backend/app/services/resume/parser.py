import uuid
import re
from io import BytesIO
import pdfplumber
from docx import Document as DocxDocument
from app.schemas.resume_v2 import (
    ResumeDocumentJSON, Contact, ExperienceEntry, EducationEntry,
    Skills, Bullet, ProjectEntry,
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
    projects = _extract_projects(sections.get("projects", ""))
    certifications = _extract_certifications(sections.get("certifications", ""))
    summary = sections.get("summary") or None
    return ResumeDocumentJSON(
        contact=contact, summary=summary, experience=experience,
        education=education, skills=skills, projects=projects,
        certifications=certifications, raw_text=raw_text,
    )


SECTION_HEADERS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills", "core competencies"],
    "summary": ["summary", "profile", "objective"],
    "projects": ["projects", "notable projects", "selected projects"],
    "certifications": ["certifications", "certification", "licenses", "licenses & certifications"],
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
    name = header_block.splitlines()[0].strip() if header_block else "Unknown"
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", header_block)
    email = email_match.group(0) if email_match else None
    phone_m = re.search(r"[\+\d][\d\s\-\(\)]{7,}", header_block)
    links = _extract_links(header_block)
    return Contact(name=name, email=email, phone=phone_m.group(0).strip() if phone_m else None, links=links)


_LINK_RE = re.compile(
    r"(?:(?:https?://|www\.)[^\s|,;]+|(?:linkedin\.com|github\.com)/[^\s|,;]+)",
    re.I,
)


def _extract_links(header_block: str) -> list[str]:
    """Return de-duplicated portfolio links without trailing sentence punctuation."""
    links: list[str] = []
    for match in _LINK_RE.finditer(header_block):
        link = match.group(0).rstrip(".])}")
        if link.lower().startswith("www."):
            link = f"https://{link}"
        elif "://" not in link:
            link = f"https://{link}"
        if link not in links:
            links.append(link)
    return links


MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
DATE_RANGE_RE = re.compile(
    rf"(?P<dates>(?:{MONTH}\s+)?\d{{4}}\s*[-–—]\s*(?:(?:{MONTH}\s+)?\d{{4}}|present|current|now))",
    re.I,
)
BULLET_RE = re.compile(r"^\s*[\u2022\u25cf\u25e6\u25aa\-\*]\s*[\u200b\ufeff]?\s*(?P<text>.+)")


def _extract_date(text: str) -> tuple[str, str | None]:
    match = DATE_RANGE_RE.search(text)
    if not match:
        return text.strip(), None
    dates = match.group("dates").strip()
    remaining = f"{text[:match.start()]} {text[match.end():]}".strip(" |,-")
    return re.sub(r"\s{2,}", " ", remaining).strip(), dates


def _split_pipe_parts(line: str) -> list[str]:
    return [p.strip() for p in re.split(r"\s+\|\s+", line) if p.strip()]


def _split_standard_parts(line: str) -> list[str]:
    """Split legacy pipe rows and canonical export rows without losing location text."""
    if re.search(r"\s+\|\s+", line):
        return _split_pipe_parts(line)
    return [part.strip() for part in re.split(r"\s+·\s+", line) if part.strip()]


def _split_name_location(value: str, *, allow_single_location: bool = False) -> tuple[str, str | None]:
    parts = [part.strip() for part in value.split(",") if part.strip()]
    if len(parts) >= 3:
        return ", ".join(parts[:-2]), ", ".join(parts[-2:])
    if allow_single_location and len(parts) == 2:
        return parts[0], parts[1]
    return value.strip(), None


def _parse_experience_header(line: str) -> ExperienceEntry:
    line_without_dates, dates = _extract_date(line)
    parts = _split_standard_parts(line_without_dates)
    if len(parts) >= 3:
        role, company, location = parts[0], parts[1], " | ".join(parts[2:])
    elif len(parts) == 2:
        role = parts[0]
        company, location = _split_name_location(parts[1])
    else:
        at_parts = re.split(r"\s+at\s+", line_without_dates, maxsplit=1, flags=re.I)
        role = at_parts[0].strip() if at_parts else line_without_dates
        company, location = _split_name_location(at_parts[1]) if len(at_parts) > 1 else ("Unknown", None)
    return ExperienceEntry(company=company, role=role, dates=dates, location=location, bullets=[])


def _extract_experience(block: str) -> list[ExperienceEntry]:
    """Each entry = role line + bullets that follow until next role line.
    Role line heuristic: contains ' at ', a legacy pipe, or the canonical dot separator."""
    entries: list[ExperienceEntry] = []
    if not block:
        return entries
    lines = [line for line in block.splitlines() if line.strip()]
    current_role: ExperienceEntry | None = None
    current_bullet: Bullet | None = None
    for line in lines:
        stripped = line.strip()
        bullet_match = BULLET_RE.match(stripped)
        is_role = bool(DATE_RANGE_RE.search(stripped)) and (
            " | " in stripped or " · " in stripped or " at " in stripped.lower()
        )
        if is_role:
            if current_role:
                entries.append(current_role)
            current_role = _parse_experience_header(stripped)
            current_bullet = None
        elif current_role is not None and bullet_match:
            text = bullet_match.group("text").strip()
            current_bullet = Bullet(id=str(uuid.uuid4())[:8], text=text, raw_text=text)
            current_role.bullets.append(current_bullet)
        elif current_role is not None and current_bullet is not None:
            continuation = stripped.strip()
            if continuation:
                current_bullet.text = f"{current_bullet.text} {continuation}"
                current_bullet.raw_text = f"{current_bullet.raw_text} {continuation}"
    if current_role:
        entries.append(current_role)
    return entries


def _extract_education(block: str) -> list[EducationEntry]:
    if not block:
        return []
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    out: list[EducationEntry] = []
    for line in lines:
        gpa_match = re.search(r"\b(?:CGPA|GPA)\s*:?\s*([\d.]+(?:\s*/\s*[\d.]+)?)", line, re.I)
        gpa = gpa_match.group(1).replace(" ", "") if gpa_match else None
        line_without_gpa = re.sub(
            r"\s*[·|,]?\s*\b(?:CGPA|GPA)\s*:?\s*[\d.]+(?:\s*/\s*[\d.]+)?",
            "",
            line,
            flags=re.I,
        ).strip()
        line_without_dates, dates = _extract_date(line_without_gpa)
        parts = _split_standard_parts(line_without_dates)
        if len(parts) >= 3:
            degree, school, location = parts[0], parts[1], " | ".join(parts[2:])
        elif len(parts) == 2:
            degree = parts[0]
            school, location = _split_name_location(parts[1], allow_single_location=True)
        else:
            comma_parts = [p.strip() for p in line_without_dates.split(",") if p.strip()]
            if len(comma_parts) >= 2:
                degree, school, location = comma_parts[0], comma_parts[1], None
            else:
                degree, school, location = None, line_without_dates, None
        out.append(EducationEntry(school=school, degree=degree, location=location, dates=dates, gpa=gpa))
    return out


def _extract_skills(block: str) -> Skills:
    if not block:
        return Skills()
    flat = block.replace("\n", ",")
    items = [s.strip() for s in flat.split(",") if s.strip()]
    return Skills(hard=items, soft=[])


def _extract_projects(block: str) -> list[ProjectEntry]:
    if not block:
        return []
    projects: list[ProjectEntry] = []
    current_project: ProjectEntry | None = None
    current_bullet: Bullet | None = None
    for line in [line.strip() for line in block.splitlines() if line.strip()]:
        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            text = bullet_match.group("text").strip()
            if current_project is None:
                current_project = ProjectEntry(name="Projects", bullets=[])
                projects.append(current_project)
            current_bullet = Bullet(id=str(uuid.uuid4())[:8], text=text, raw_text=text)
            current_project.bullets.append(current_bullet)
        elif current_bullet is not None:
            current_bullet.text = f"{current_bullet.text} {line}"
            current_bullet.raw_text = f"{current_bullet.raw_text} {line}"
        else:
            current_project = ProjectEntry(name=line, bullets=[])
            projects.append(current_project)
            current_bullet = None
    return projects


def _extract_certifications(block: str) -> list[str]:
    if not block:
        return []
    certifications: list[str] = []
    current: str | None = None
    for line in [line.strip() for line in block.splitlines() if line.strip()]:
        bullet_match = BULLET_RE.match(line)
        text = bullet_match.group("text").strip() if bullet_match else line
        if current and not bullet_match and not DATE_RANGE_RE.search(current):
            current = f"{current} {text}"
            certifications[-1] = current
        else:
            current = text
            certifications.append(current)
    return certifications
