"""Run all PDF renderer tests on a dedicated worker thread.

Sync Playwright is greenlet-affinity: once `sync_playwright().start()` runs on
a thread, that thread's asyncio event-loop policy is fixed in a way pytest-asyncio
cannot recover from. If a PDF test executes on the main test thread, every later
async test in the same pytest process fails with "coroutine was never awaited".

This autouse fixture wraps the renderer call so Playwright always runs on a
dedicated background thread, keeping the main thread's asyncio policy clean.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pdf-test-worker")


@pytest.fixture(autouse=True)
def _run_renderer_on_worker_thread(monkeypatch):
    """Patch `render_pdf_from_doc` so every direct call from a PDF test
    runs on a single, persistent background thread."""
    from app.services.pdf import renderer as _renderer

    original = _renderer.render_pdf_from_doc

    def via_worker(*args, **kwargs):
        future = _executor.submit(original, *args, **kwargs)
        return future.result()

    monkeypatch.setattr(_renderer, "render_pdf_from_doc", via_worker)
    yield
