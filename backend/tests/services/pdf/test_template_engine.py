"""Tests for Jinja2 template engine and rendering."""
import pytest
from tests.fixtures.resume_doc_json import make_resume


def test_pick_template_returns_path_for_known_combo():
    """pick_template should return valid template paths for known country/role combinations."""
    from app.services.pdf.template_engine import pick_template

    assert pick_template("US", "swe").endswith("us/swe.html")
    assert pick_template("IN", "pm").endswith("in/pm.html")


def test_pick_template_raises_on_unknown():
    """pick_template should reject unknown countries and roles."""
    from app.services.pdf.template_engine import pick_template

    with pytest.raises(ValueError):
        pick_template("UK", "swe")
    with pytest.raises(ValueError):
        pick_template("US", "designer")


def test_render_html_contains_contact_name_and_bullets():
    """render_html should produce HTML containing user content and bullets."""
    from app.services.pdf.template_engine import render_html

    doc = make_resume(name="Jane Doe")
    html = render_html(doc, country="US", role="swe")
    assert "Jane Doe" in html
    assert "Cut p99 latency 38%" in html
    assert "<html" in html.lower()


def test_render_html_escapes_html_in_user_content():
    """render_html should escape HTML entities in user content to prevent XSS."""
    from app.services.pdf.template_engine import render_html

    doc = make_resume(name="<script>alert(1)</script>")
    html = render_html(doc, country="US", role="swe")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
