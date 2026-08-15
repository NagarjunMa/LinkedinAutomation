"""Pure validation and naming helpers shared by PDF workflows."""

import re


_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]")
_DEFAULT_FILENAME = "resume.pdf"


def sanitize_pdf_filename(name: str | None, default: str = _DEFAULT_FILENAME) -> str:
    if not name:
        return default if default.endswith(".pdf") else default + ".pdf"
    filename = name.replace("\\", "/").split("/")[-1]
    filename = re.sub(r"[\x00-\x1f]", "", filename)
    filename = _SAFE_CHARS.sub("-", filename).strip("-")
    if not filename:
        filename = default.removesuffix(".pdf") if default.endswith(".pdf") else default
    return filename if filename.lower().endswith(".pdf") else filename + ".pdf"


def parse_template_id(template_id: str) -> tuple[str, str]:
    parts = template_id.replace("/", "-").split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid template_id: {template_id}")
    country, role = parts[0].upper(), parts[1].lower()
    if country not in ("US", "IN") or role not in ("swe", "ds", "pm"):
        raise ValueError(f"Invalid template_id: {template_id}")
    return country, role


def slugify_filename_part(text: str) -> str:
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")
    slug = (slug or "user")[:100].strip("-")
    return slug or "user"
