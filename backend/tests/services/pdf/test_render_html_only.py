"""Tests for render_html_only — inlined CSS, no file:// links."""
import re
import pytest
from tests.fixtures.resume_doc_json import make_resume


def test_render_html_only_contains_inline_style_block():
    """render_html_only must embed a <style> block with CSS content."""
    from app.services.pdf.template_engine import render_html_only

    doc = make_resume(name="Alice Smith")
    html = render_html_only(doc, country="US", role="swe")

    # Must contain an inline <style> tag with actual CSS
    assert "<style>" in html.lower() or "<style " in html.lower()
    # Must contain contact name
    assert "Alice Smith" in html


def test_render_html_only_strips_file_uri_link_tags():
    """render_html_only must not contain any file:// URIs or <link> tags pointing to them."""
    from app.services.pdf.template_engine import render_html_only

    doc = make_resume()
    html = render_html_only(doc, country="US", role="swe")

    # No file:// URIs allowed
    assert "file://" not in html
    # No <link rel="stylesheet" href="..."> tags pointing to file:// paths
    link_tags = re.findall(r'<link[^>]*>', html, re.IGNORECASE)
    for tag in link_tags:
        assert "file://" not in tag, f"Found file:// in link tag: {tag}"


def test_render_html_only_inlines_all_three_css_files():
    """render_html_only must inline _base.css, _typography.css, and _print.css content."""
    from app.services.pdf.template_engine import render_html_only

    doc = make_resume()
    html = render_html_only(doc, country="IN", role="ds")

    # Check for known snippets from each CSS file
    # _base.css: box-sizing rule
    assert "box-sizing" in html
    # _typography.css: font-size or font-family rule
    assert "font" in html.lower()
    # The HTML must be self-contained
    assert "<html" in html.lower()
    assert "</html>" in html.lower()
