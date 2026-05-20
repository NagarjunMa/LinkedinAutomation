"""Playwright-backed HTML→PDF renderer.

Public API: render_pdf_from_doc(doc, country, role) -> bytes

Behavior:
- Single shared Playwright + browser instance (lazy, process-global).
- 15s timeout per render (configurable via settings.PDF_RENDER_TIMEOUT_S).
- One retry on Playwright TimeoutError.
- If the template engine raises, fall back to us/swe and try again.
- After fallback, a second timeout raises PdfRenderTimeout; callers refund the credit.
"""
from __future__ import annotations

import threading
from typing import Optional

from playwright.sync_api import (
    Browser,
    Playwright,
    TimeoutError as PWTimeout,
    sync_playwright,
)

from app.core.config import settings
from app.schemas.resume import ResumeDocumentJSON
from app.services.pdf.template_engine import render_html


class PdfRenderTimeout(Exception):
    pass


_lock = threading.Lock()
_pw: Optional[Playwright] = None
_browser: Optional[Browser] = None


def _get_browser() -> Browser:
    global _pw, _browser
    with _lock:
        if _browser is None or not _browser.is_connected():
            _pw = sync_playwright().start()
            _browser = _pw.chromium.launch(args=["--no-sandbox"])
        return _browser


def _render_html_to_pdf_bytes(html: str, timeout_s: int) -> bytes:
    """Render HTML to PDF bytes via a fresh page. Raises Playwright TimeoutError on miss."""
    browser = _get_browser()
    context = browser.new_context()
    try:
        page = context.new_page()
        page.set_default_timeout(timeout_s * 1000)
        page.set_content(html, wait_until="networkidle")
        return page.pdf(
            print_background=True,
            prefer_css_page_size=True,
        )
    finally:
        context.close()


def render_pdf_from_doc(
    doc: ResumeDocumentJSON,
    country: str,
    role: str,
    timeout_s: Optional[int] = None,
) -> bytes:
    """Render a resume doc to PDF bytes. One retry on timeout. Template fallback on render error."""
    t = timeout_s or settings.PDF_RENDER_TIMEOUT_S

    # Stage 1: template
    try:
        html = render_html(doc, country, role)
    except Exception:
        # Template-engine failure → fall back to a known-good template.
        html = render_html(doc, "US", "swe")

    # Stage 2: PDF render with one retry on timeout.
    try:
        return _render_html_to_pdf_bytes(html, timeout_s=t)
    except PWTimeout:
        try:
            return _render_html_to_pdf_bytes(html, timeout_s=t)
        except PWTimeout as exc:
            raise PdfRenderTimeout(f"PDF render timed out after retry (>{t}s)") from exc
