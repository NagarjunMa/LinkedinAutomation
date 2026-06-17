import pytest
from unittest.mock import MagicMock, patch
from tests.fixtures.resume_doc_json import make_resume


def test_render_pdf_returns_bytes_starting_with_pdf_magic(tmp_path):
    from app.services.pdf.renderer import render_pdf_from_doc
    pdf = render_pdf_from_doc(make_resume(), country="US", role="swe")
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000   # not an empty stub


def test_render_pdf_retries_once_on_timeout(monkeypatch):
    """First call raises TimeoutError, second call succeeds, render returns bytes."""
    from app.services.pdf import renderer
    calls = {"n": 0}

    def fake_render_bytes(html, timeout_s):
        calls["n"] += 1
        if calls["n"] == 1:
            from playwright.sync_api import TimeoutError as PWTimeout
            raise PWTimeout("simulated")
        return b"%PDF-retry-success"

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", fake_render_bytes)
    monkeypatch.setattr(renderer, "_assert_pdf_has_visible_content", lambda pdf: None)
    pdf = renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
    assert pdf.startswith(b"%PDF-")
    assert calls["n"] == 2


def test_render_pdf_falls_back_to_us_swe_on_template_error(monkeypatch):
    """If the requested template raises, we fall back to us/swe and still return a PDF."""
    from app.services.pdf import renderer
    from app.services.pdf import template_engine

    calls = {"templates": []}
    original_render_html = template_engine.render_html_only

    def flaky_render_html(doc, country, role):
        calls["templates"].append((country, role))
        if (country, role) == ("IN", "ds"):
            raise RuntimeError("simulated template fail")
        return original_render_html(doc, country, role)

    monkeypatch.setattr(template_engine, "render_html_only", flaky_render_html)
    monkeypatch.setattr(renderer, "render_html_only", flaky_render_html)
    monkeypatch.setattr(renderer, "_assert_pdf_has_visible_content", lambda pdf: None)
    pdf = renderer.render_pdf_from_doc(make_resume(), country="IN", role="ds")
    assert pdf.startswith(b"%PDF-")
    assert ("IN", "ds") in calls["templates"]
    assert ("US", "swe") in calls["templates"]


def test_render_pdf_raises_after_second_timeout(monkeypatch):
    from app.services.pdf import renderer
    from playwright.sync_api import TimeoutError as PWTimeout

    def always_timeout(html, timeout_s):
        raise PWTimeout("simulated")

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", always_timeout)
    with pytest.raises(renderer.PdfRenderTimeout):
        renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")


def test_render_pdf_rejects_suspiciously_small_blank_output(monkeypatch):
    from app.services.pdf import renderer

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", lambda html, timeout_s: b"%PDF-blank")

    with pytest.raises(renderer.BlankPdfError):
        renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
