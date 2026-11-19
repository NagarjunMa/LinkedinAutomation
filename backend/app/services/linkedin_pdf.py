"""Deterministically interpret sections explicitly present in a profile export."""

import re
from pydantic import HttpUrl, TypeAdapter, ValidationError

from app.core.config import settings
from app.schemas.career.common import SourceRef
from app.schemas.career.sources import LinkedInDocument, LinkedInExperience, LinkedInSection
from app.services.resume.file_security import ResumeFileError, run_parser_worker

HEADINGS = {
    "contact": "contact", "headline": "headline", "about": "about", "summary": "about",
    "experience": "experience", "education": "education", "projects": "projects",
    "skills": "skills", "top skills": "skills", "certifications": "certifications",
    "licenses & certifications": "certifications", "licenses": "licenses",
    "publications": "publications", "volunteering": "volunteering", "honors": "honors",
    "honors & awards": "honors", "languages": "languages", "featured": "featured",
}
MAIN = {"headline", "about", "experience", "education", "projects"}
SIDEBAR_LOCATOR_SUFFIX = ":sidebar"
EXPLICIT_HEADLINE_LOCATOR_SUFFIX = ":headline"
COVERAGE = ("identity", "headline", "about", "experience", "education", "projects", "skills", "certifications")
LINK = re.compile(r"(?:https?://|www\.|linkedin\.com/in/)[^\s<>]+", re.I)
MONTH_YEAR = r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\d{4}"
DATE = re.compile(rf"({MONTH_YEAR})\s*[-–—]\s*({MONTH_YEAR}|Present)(?:\s*\(\d+\s+[a-z]+(?:\s+\d+\s+[a-z]+)?\))?", re.I)
PROFILE_URL = TypeAdapter(HttpUrl)
EMPLOYMENT_TYPES = {"full-time", "part-time", "self-employed", "freelance", "contract", "internship",
                    "apprenticeship", "seasonal"}
LOCATION = re.compile(r"(?:Location:\s*)?[A-Za-z][A-Za-z .'-]{1,70},\s*[A-Za-z][A-Za-z .'-]{1,70}(?:,\s*[A-Za-z][A-Za-z .'-]{1,70})?", re.I)
CLAIM = re.compile(
    r"^(?:[•*-]\s*)?(?:I\s+)?(?:built|created|designed|developed|implemented|led|"
    r"shipped|deployed|maintained|wrote|improved|reduced|managed|delivered|tested)\b",
    re.I,
)


async def read_profile_pages(content: bytes) -> tuple[list[str], list[int | None]]:
    chars = min(settings.MAX_EXTRACTED_TEXT_CHARS, 100_000)
    result = await run_parser_worker(
        content, "app.services.linkedin_pdf_worker", str(settings.MAX_UPLOAD_SIZE),
        str(settings.MAX_PDF_PAGES), str(chars), env={"PYTHON_DOTENV_DISABLED": "1"},
    )
    pages = result.get("pages")
    if not isinstance(pages, list) or not 0 < len(pages) <= settings.MAX_PDF_PAGES or not all(
        isinstance(page, str) for page in pages
    ) or len("\n".join(pages)) > chars:
        raise ResumeFileError("PDF could not be parsed")
    sidebar_lines = result.get("sidebar_lines")
    if not isinstance(sidebar_lines, list) or len(sidebar_lines) != len(pages) or any(
        count is not None and (type(count) is not int or not 0 < count < len(page.splitlines()))
        for page, count in zip(pages, sidebar_lines)
    ):
        raise ResumeFileError("PDF layout could not be parsed")
    return pages, sidebar_lines


def parse_profile_pages(
    pages: list[str], source: SourceRef, *, role_first: bool = False, sidebar_lines: list[int | None] | None = None,
) -> LinkedInDocument:
    sections: list[LinkedInSection] = []
    name = location = None
    current = "unclassified"
    explicit_headline = False
    for page_number, page in enumerate(pages, 1):
        lines = [(number, line.strip()) for number, line in enumerate(page.splitlines(), 1) if line.strip()]
        previous = current
        previous_explicit_headline = explicit_headline
        boundary = sidebar_lines[page_number - 1] if sidebar_lines else None
        main_index = next((i for i, (number, _) in enumerate(lines) if number > boundary), None) if boundary else None
        if main_index is not None:
            current = "unclassified"
            explicit_headline = False
            role_first = True
        identity_index = (main_index if main_index is not None else _identity_index(lines)) if page_number == 1 else None
        header = page_number == 1 and main_index is not None
        for index, (line_number, line) in enumerate(lines):
            in_sidebar = main_index is not None and index < main_index
            if index == main_index:
                current = "identity" if header else previous
                explicit_headline = not header and previous_explicit_headline
            heading = HEADINGS.get(line.casefold().rstrip(":"))
            if heading:
                if not in_sidebar:
                    header = False
                current = "unclassified" if in_sidebar and heading in MAIN else heading
                explicit_headline = current == "headline"
                continue
            if identity_index is not None and index == identity_index:
                current = "identity"
                name = line if len(line) <= 200 else None
            elif identity_index is not None and index == identity_index + 1 and (header or main_index is None):
                current = "headline"
                explicit_headline = False
            elif header and not in_sidebar:
                current = "identity"
                location = location or _location(line)
            elif (main_index is None and not explicit_headline and identity_index is not None
                  and index == identity_index + 2 and LOCATION.fullmatch(line)):
                current = "identity"
                location = _location(line)
            for start in range(0, len(line), 4000):
                segment = line[start:start + 4000].strip()
                if not segment:
                    continue
                locator = f"page:{page_number}:line:{line_number}"
                if len(line) > 4000:
                    locator += f":column:{start + 1}"
                if in_sidebar:
                    locator += SIDEBAR_LOCATOR_SUFFIX
                elif current == "headline" and explicit_headline:
                    locator += EXPLICIT_HEADLINE_LOCATOR_SUFFIX
                sections.append(LinkedInSection(name=current, page=page_number, locator=locator, text=segment))

    raw_text = "\n".join(pages)
    coverage = {section.name for section in sections}
    links = list(dict.fromkeys(
        ("https://" if not candidate.lower().startswith(("http://", "https://")) else "") + candidate
        for match in LINK.finditer(raw_text) if len(candidate := match[0].rstrip(".,)]}")) <= 192
    ))
    profile_url = next((profile for link in links if (profile := _profile_link(link))), None)
    experience = _experience(sections, role_first)
    return LinkedInDocument(
        schema_version=1, source=source, raw_text=raw_text, name=name,
        profile_url=profile_url, location=location, contact_links=links, sections=sections, experience=experience,
        coverage="uploaded_export_only", not_found_in_export=[key for key in COVERAGE if key not in coverage],
        parse_status="unreadable" if not raw_text.strip() else "parsed" if name and experience else "partial",
    )


def _identity_index(lines: list[tuple[int, str]]) -> int | None:
    first_main = next((i for i, (_, line) in enumerate(lines) if HEADINGS.get(line.casefold()) in MAIN), None)
    if first_main is None:
        return None
    explicit_headline = lines[first_main][1].casefold() == "headline"
    has_sidebar = any(HEADINGS.get(line.casefold()) in {"contact", "skills", "certifications"}
                      for _, line in lines[:first_main])
    location = first_main > 0 and LOCATION.fullmatch(lines[first_main - 1][1])
    index = first_main - (1 if explicit_headline else 2) - bool(location) if has_sidebar or explicit_headline else 0
    if 0 <= index < first_main:
        candidate = lines[index][1]
        if len(candidate.split()) >= 2 and len(candidate) <= 200 and not re.search(r"[:@/0-9]", candidate):
            return index
    return None


def _profile_link(value: str) -> HttpUrl | None:
    if "linkedin.com" not in value.casefold():
        return None
    try:
        url = PROFILE_URL.validate_python(value)
    except ValidationError:
        return None
    if url.host in {"linkedin.com", "www.linkedin.com"} and url.path.startswith("/in/") and not url.username:
        return url
    return None


def _location(value: str) -> str | None:
    value = re.sub(r"^Location:\s*", "", value, flags=re.I)
    return value if len(value) <= 200 and LOCATION.fullmatch(value) else None


def _experience(sections: list[LinkedInSection], role_first: bool) -> list[LinkedInExperience]:
    entries = []
    for index, section in enumerate(sections):
        dates = DATE.fullmatch(section.text)
        if section.name != "experience" or dates is None or index < 2:
            continue
        first, second = sections[index - 2:index]
        if first.name != "experience" or second.name != "experience":
            continue
        company, separator, employment_type = second.text.rpartition(" · ")
        if separator and employment_type.casefold() in EMPLOYMENT_TYPES:
            title = first
        elif role_first:
            title, company, employment_type = first, second.text, None
        else:
            title, company, employment_type = second, first.text, None
        entries.append((index, title, company, employment_type, dates))

    result = []
    for position, (index, title, company, employment_type, dates) in enumerate(entries):
        end = entries[position + 1][0] - 2 if position + 1 < len(entries) else len(sections)
        location = None
        description = []
        for section in sections[index + 1:end]:
            if section.name != "experience":
                break
            if not description and location is None and (location := _location(section.text)):
                continue
            description.append(section.text)
        result.append(LinkedInExperience(
            page=title.page, locator=title.locator, title=title.text[:200], company=company[:200],
            employment_type=employment_type, start_date=dates[1], end_date=dates[2],
            location=location, description="\n".join(description)[:4000].rstrip() or None,
        ))
    return result
