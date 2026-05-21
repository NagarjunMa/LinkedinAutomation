"""Jinja2 environment + template selection for Phase 2 PDF render."""
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas.resume_v2 import ResumeDocumentJSON

TEMPLATES_DIR = Path(__file__).parent / "templates"

_VALID_COUNTRIES = {"US", "IN"}
_VALID_ROLES = {"swe", "ds", "pm"}

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def pick_template(country: str, role: str) -> str:
    """Return the template path relative to TEMPLATES_DIR, e.g. 'us/swe.html'."""
    if country not in _VALID_COUNTRIES:
        raise ValueError(f"Unknown country: {country}")
    if role not in _VALID_ROLES:
        raise ValueError(f"Unknown role: {role}")
    return f"{country.lower()}/{role}.html"


def _shared_css_url(filename: str) -> str:
    return (TEMPLATES_DIR / "shared" / filename).as_uri()


def render_html(
    doc: ResumeDocumentJSON,
    country: Literal["US", "IN"],
    role: Literal["swe", "ds", "pm"],
) -> str:
    """Render a resume document as HTML using the appropriate template.

    Args:
        doc: Structured resume document
        country: Country code (US or IN)
        role: Target role (swe, ds, or pm)

    Returns:
        Rendered HTML string with autoescape enabled (XSS-safe)

    Raises:
        ValueError: If country or role is not supported
        jinja2.TemplateNotFound: If the template file doesn't exist
    """
    template_path = pick_template(country, role)
    template = _env.get_template(template_path)
    return template.render(
        doc=doc,
        country=country,
        role=role,
        base_css=_shared_css_url("_base.css"),
        type_css=_shared_css_url("_typography.css"),
        print_css=_shared_css_url("_print.css"),
    )
