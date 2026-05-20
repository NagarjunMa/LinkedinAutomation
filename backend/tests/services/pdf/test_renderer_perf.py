import os
import time
import pytest
from tests.fixtures.resume_doc_json import make_resume

# Skip in CI environments that can't run headless Chromium reliably.
pytestmark = pytest.mark.skipif(
    os.environ.get("PDF_PERF_SKIP") == "1",
    reason="PDF_PERF_SKIP=1 set",
)


def test_single_render_under_8s_after_warmup():
    from app.services.pdf.renderer import render_pdf_from_doc

    # Warmup: launching Chromium dominates the first call; perf budget is per render
    # after browser is hot.
    render_pdf_from_doc(make_resume(), country="US", role="swe")

    started = time.monotonic()
    render_pdf_from_doc(make_resume(), country="US", role="swe")
    elapsed = time.monotonic() - started
    assert elapsed < 8.0, f"warm render took {elapsed:.2f}s (budget 8.0s)"
