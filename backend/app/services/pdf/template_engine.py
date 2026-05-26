"""Jinja2 environment + template selection for Phase 2 PDF render."""
import re
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


def _read_shared_css() -> str:
    """Read and concatenate the three shared CSS files into one string."""
    css_files = ["_base.css", "_typography.css", "_print.css"]
    parts = []
    for name in css_files:
        path = TEMPLATES_DIR / "shared" / name
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def render_html_only(
    doc: ResumeDocumentJSON,
    country: Literal["US", "IN"],
    role: Literal["swe", "ds", "pm"],
) -> str:
    """Render a resume as a fully self-contained HTML string with inlined CSS.

    Unlike ``render_html``, this function:
    - Reads the three shared CSS files (_base.css, _typography.css, _print.css)
      and injects them as a single ``<style>`` block before ``</head>``.
    - Strips any ``<link>`` tags that reference ``file://`` URIs so the result
      can be used in a browser or converted to PDF without filesystem access.

    Args:
        doc: Structured resume document
        country: Country code (US or IN)
        role: Target role (swe, ds, or pm)

    Returns:
        Self-contained HTML string with all CSS inlined.

    Raises:
        ValueError: If country or role is not supported
        jinja2.TemplateNotFound: If the template file doesn't exist
    """
    # Render via the standard render_html first (which uses file:// links)
    raw_html = render_html(doc, country=country, role=role)

    # Strip all <link> tags that point to file:// URIs
    cleaned = re.sub(
        r'<link\b[^>]*href=["\']file://[^"\']*["\'][^>]*>',
        "",
        raw_html,
        flags=re.IGNORECASE,
    )

    # Build the inline <style> block
    css_content = _read_shared_css()
    style_block = f"<style>\n{css_content}\n</style>"

    # Inject before </head>; if no </head>, prepend at top
    if re.search(r"</head>", cleaned, re.IGNORECASE):
        cleaned = re.sub(
            r"(</head>)",
            f"{style_block}\n\\1",
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        cleaned = style_block + "\n" + cleaned

    return cleaned


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
