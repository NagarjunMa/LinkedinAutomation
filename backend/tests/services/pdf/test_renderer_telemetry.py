import logging
import json
from tests.fixtures.resume_doc_json import make_resume


def test_render_pdf_emits_structured_log(caplog, monkeypatch):
    from app.services.pdf import renderer
    caplog.set_level(logging.INFO, logger="pdf_render")

    # Mock _render_html_to_pdf_bytes to avoid needing Playwright installed
    def fake_render_bytes(html, timeout_s):
        return b"%PDF-test-pdf-content"

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", fake_render_bytes)

    renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")
    records = [r for r in caplog.records if r.name == "pdf_render"]
    assert records, "expected at least one pdf_render log record"
    # We attach structured fields via record.__dict__; verify shape.
    last = records[-1]
    payload = getattr(last, "structured", None)
    assert payload, "expected 'structured' field on log record"
    assert payload["event"] == "pdf_render"
    assert payload["country"] == "US"
    assert payload["role"] == "swe"
    assert isinstance(payload["render_ms"], int)
    assert payload["render_ms"] >= 0
    assert isinstance(payload["file_size_bytes"], int)
    assert payload["file_size_bytes"] > 0
    assert payload["status"] == "succeeded"


def test_render_pdf_emits_telemetry_on_timeout(caplog, monkeypatch):
    """Verify telemetry is emitted even when timeout occurs."""
    from app.services.pdf import renderer
    from playwright.sync_api import TimeoutError as PWTimeout
    import pytest

    caplog.set_level(logging.INFO, logger="pdf_render")

    def always_timeout(html, timeout_s):
        raise PWTimeout("simulated")

    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", always_timeout)

    with pytest.raises(renderer.PdfRenderTimeout):
        renderer.render_pdf_from_doc(make_resume(), country="US", role="swe")

    records = [r for r in caplog.records if r.name == "pdf_render"]
    assert records, "expected telemetry even on timeout"
    last = records[-1]
    payload = getattr(last, "structured", None)
    assert payload["status"] == "timed_out"
    assert payload["file_size_bytes"] == 0


def test_render_pdf_emits_telemetry_with_fallback(caplog, monkeypatch):
    """Verify fallback_used flag is set when template error occurs."""
    from app.services.pdf import renderer
    from app.services.pdf import template_engine

    caplog.set_level(logging.INFO, logger="pdf_render")

    calls = {"templates": []}
    original_render_html = template_engine.render_html

    def flaky_render_html(doc, country, role):
        calls["templates"].append((country, role))
        if (country, role) == ("IN", "ds"):
            raise RuntimeError("simulated template fail")
        return original_render_html(doc, country, role)

    def fake_render_bytes(html, timeout_s):
        return b"%PDF-test"

    monkeypatch.setattr(template_engine, "render_html", flaky_render_html)
    monkeypatch.setattr(renderer, "render_html", flaky_render_html)
    monkeypatch.setattr(renderer, "_render_html_to_pdf_bytes", fake_render_bytes)

    renderer.render_pdf_from_doc(make_resume(), country="IN", role="ds")

    records = [r for r in caplog.records if r.name == "pdf_render"]
    assert records
    last = records[-1]
    payload = getattr(last, "structured", None)
    assert payload["fallback_used"] is True
    assert payload["status"] == "succeeded"
