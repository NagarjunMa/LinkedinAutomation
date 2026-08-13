import asyncio
import zipfile
import json
import sys
from io import BytesIO
from io import StringIO

import pytest
from fastapi import UploadFile
from pypdf import PdfWriter

from app.core.config import settings
from app.services.resume.file_security import (
    ResumeFileComplexityError,
    ResumeFileError,
    ResumeFileTooLargeError,
    ResumeParseCapacityError,
    ResumeParseTimeoutError,
    parse_resume_with_timeout,
    read_resume_upload,
    validate_resume_bytes,
)
from app.services.resume.parser import parse_resume
from app.services.resume import parser_worker


DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx_archive(extra_entries: dict[str, bytes] | None = None) -> bytes:
    buffer = BytesIO()
    entries = {
        "[Content_Types].xml": b"<Types />",
        "_rels/.rels": b"<Relationships />",
        "word/document.xml": b"<document />",
        **(extra_entries or {}),
    }
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_upload_rejects_declared_media_type_mismatch():
    upload = UploadFile(
        filename="resume.pdf",
        file=BytesIO(b"%PDF-1.4\n%%EOF"),
        headers={"content-type": "application/octet-stream"},
    )

    with pytest.raises(ResumeFileError, match="media type"):
        await read_resume_upload(upload)


@pytest.mark.asyncio
async def test_upload_stops_when_stream_exceeds_limit(monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 16)
    upload = UploadFile(
        filename="resume.pdf",
        file=BytesIO(b"%PDF-1.4\n" + b"x" * 32),
        headers={"content-type": "application/pdf"},
    )

    with pytest.raises(ResumeFileTooLargeError):
        await read_resume_upload(upload)


def test_pdf_extension_requires_pdf_signature():
    with pytest.raises(ResumeFileError, match="valid PDF"):
        validate_resume_bytes(b"PK\x03\x04not-a-pdf", "pdf")


def test_docx_rejects_archive_traversal():
    content = _docx_archive({"../outside.xml": b"unsafe"})

    with pytest.raises(ResumeFileError, match="unsafe archive path"):
        validate_resume_bytes(content, "docx")


def test_rejects_docx_archive_with_high_expansion():
    content = _docx_archive({"word/large.xml": b"0" * 1_000_000})

    with pytest.raises(ResumeFileComplexityError, match="compression ratio"):
        validate_resume_bytes(content, "docx")


def test_pdf_parser_rejects_excessive_page_count(monkeypatch):
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    monkeypatch.setattr(settings, "MAX_PDF_PAGES", 2)

    with pytest.raises(ResumeFileComplexityError, match="page count"):
        parse_resume(buffer.getvalue(), "resume.pdf")


def test_parser_rejects_extracted_text_over_budget(monkeypatch):
    from pathlib import Path

    fixture = Path(__file__).parents[2] / "fixtures/resumes/simple.pdf"
    monkeypatch.setattr(settings, "MAX_EXTRACTED_TEXT_CHARS", 10)

    with pytest.raises(ResumeFileComplexityError, match="text exceeds"):
        parse_resume(fixture.read_bytes(), "resume.pdf")


@pytest.mark.asyncio
async def test_parser_timeout_terminates_worker_with_stable_error(monkeypatch):
    monkeypatch.setattr(settings, "RESUME_PARSE_TIMEOUT_SECONDS", 0.001)

    with pytest.raises(ResumeParseTimeoutError, match="timed out"):
        await parse_resume_with_timeout(b"%PDF-1.4", "resume.pdf")


@pytest.mark.asyncio
async def test_parser_capacity_returns_retryable_error(monkeypatch):
    import app.services.resume.file_security as file_security

    monkeypatch.setattr(file_security, "_PARSER_SEMAPHORE", asyncio.Semaphore(0))
    monkeypatch.setattr(settings, "RESUME_PARSE_QUEUE_TIMEOUT_SECONDS", 0.001)

    with pytest.raises(ResumeParseCapacityError, match="retry shortly"):
        await parse_resume_with_timeout(b"%PDF-1.4", "resume.pdf")


def test_parser_worker_serializes_a_valid_document(monkeypatch):
    from pathlib import Path

    fixture = Path(__file__).parents[2] / "fixtures/resumes/simple.pdf"
    stdin = type("BinaryStdin", (), {"buffer": BytesIO(fixture.read_bytes())})()
    stdout = StringIO()
    monkeypatch.setattr(sys, "argv", ["parser_worker", "resume.pdf"])
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    assert parser_worker.main() == 0
    payload = json.loads(stdout.getvalue())
    assert payload["ok"] is True
    assert payload["document"]["contact"]["name"]


def test_parser_worker_returns_only_stable_validation_errors(monkeypatch):
    stdin = type("BinaryStdin", (), {"buffer": BytesIO(b"%PDF-1.4\nbroken")})()
    stdout = StringIO()
    monkeypatch.setattr(sys, "argv", ["parser_worker", "resume.pdf"])
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)

    assert parser_worker.main() == 2
    payload = json.loads(stdout.getvalue())
    assert payload == {
        "ok": False,
        "error_type": "validation",
        "message": "Resume could not be parsed",
    }
