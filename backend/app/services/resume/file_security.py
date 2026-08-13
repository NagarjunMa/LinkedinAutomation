"""Bounded file ingestion for untrusted resume documents."""

from __future__ import annotations

import asyncio
import json
import re
import stat
import sys
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath

from fastapi import UploadFile

from app.core.config import settings


_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
_DOCX_REQUIRED_ENTRIES = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
}
_READ_CHUNK_SIZE = 64 * 1024
_PARSER_SEMAPHORE = asyncio.Semaphore(settings.MAX_CONCURRENT_RESUME_PARSERS)


class ResumeFileError(ValueError):
    """Safe validation error suitable for returning to an API caller."""

    status_code = 400


class ResumeFileTooLargeError(ResumeFileError):
    status_code = 413


class ResumeFileComplexityError(ResumeFileError):
    status_code = 422


class ResumeParseTimeoutError(ResumeFileError):
    status_code = 408


class ResumeParseCapacityError(ResumeFileError):
    status_code = 429


@dataclass(frozen=True)
class ValidatedResumeFile:
    filename: str
    extension: str
    media_type: str
    content: bytes


def _safe_filename(filename: str | None) -> str:
    value = (filename or "").replace("\\", "/")
    name = PurePosixPath(value).name.strip()
    if not name or len(name) > 255 or name in {".", ".."}:
        raise ResumeFileError("Invalid resume filename")
    if any(ord(character) < 32 for character in name):
        raise ResumeFileError("Invalid resume filename")
    return name


async def read_resume_upload(file: UploadFile) -> ValidatedResumeFile:
    """Read a spooled upload in bounded chunks and validate its declared type."""

    filename = _safe_filename(file.filename)
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    expected_media_type = _MEDIA_TYPES.get(extension)
    if expected_media_type is None:
        raise ResumeFileError("Only PDF and DOCX files are supported")

    media_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    if media_type != expected_media_type:
        raise ResumeFileError("File media type does not match its extension")

    content = bytearray()
    while chunk := await file.read(_READ_CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise ResumeFileTooLargeError("File exceeds maximum upload size")

    file_bytes = bytes(content)
    validate_resume_bytes(file_bytes, extension)
    return ValidatedResumeFile(
        filename=filename,
        extension=extension,
        media_type=expected_media_type,
        content=file_bytes,
    )


def validate_resume_bytes(content: bytes, extension: str) -> None:
    """Validate magic bytes and container budgets without trusting a filename."""

    if not content:
        raise ResumeFileError("Resume file is empty")
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise ResumeFileTooLargeError("File exceeds maximum upload size")

    if extension == "pdf":
        if b"%PDF-" not in content[:1024]:
            raise ResumeFileError("File content is not a valid PDF")
        return
    if extension == "docx":
        _validate_docx_archive(content)
        return
    raise ResumeFileError("Only PDF and DOCX files are supported")


def _validate_docx_archive(content: bytes) -> None:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > settings.MAX_DOCX_ENTRIES:
                raise ResumeFileComplexityError("DOCX contains too many archive entries")

            names: set[str] = set()
            total_compressed = 0
            total_uncompressed = 0
            for entry in entries:
                name = entry.filename
                normalized = PurePosixPath(name.replace("\\", "/"))
                if normalized.is_absolute() or ".." in normalized.parts:
                    raise ResumeFileError("DOCX contains an unsafe archive path")
                if name in names:
                    raise ResumeFileError("DOCX contains duplicate archive entries")
                names.add(name)

                if entry.flag_bits & 0x1:
                    raise ResumeFileError("Encrypted DOCX files are not supported")
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ResumeFileError("DOCX symbolic links are not supported")

                total_compressed += entry.compress_size
                total_uncompressed += entry.file_size

            if not _DOCX_REQUIRED_ENTRIES.issubset(names):
                raise ResumeFileError("File content is not a valid DOCX document")
            if "word/vbaProject.bin" in names:
                raise ResumeFileError("Macro-enabled Word documents are not supported")
            if total_uncompressed > settings.MAX_DOCX_UNCOMPRESSED_SIZE:
                raise ResumeFileComplexityError("DOCX expands beyond the processing limit")
            if total_uncompressed / max(total_compressed, 1) > settings.MAX_DOCX_COMPRESSION_RATIO:
                raise ResumeFileComplexityError("DOCX compression ratio exceeds the processing limit")

            content_types = archive.read("[Content_Types].xml", pwd=None)
            if re.search(br"macroEnabled", content_types, flags=re.IGNORECASE):
                raise ResumeFileError("Macro-enabled Word documents are not supported")
    except ResumeFileError:
        raise
    except (zipfile.BadZipFile, OSError, RuntimeError, KeyError) as exc:
        raise ResumeFileError("File content is not a valid DOCX document") from exc


async def parse_resume_with_timeout(content: bytes, filename: str):
    """Parse in a killable subprocess so the timeout is a hard boundary."""

    try:
        await asyncio.wait_for(
            _PARSER_SEMAPHORE.acquire(),
            timeout=settings.RESUME_PARSE_QUEUE_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise ResumeParseCapacityError("Resume parser is busy; retry shortly") from exc

    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "app.services.resume.parser_worker",
            filename,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(input=content),
                timeout=settings.RESUME_PARSE_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            await _terminate_process(process)
            raise ResumeParseTimeoutError("Resume parsing timed out") from exc
        except asyncio.CancelledError:
            await _terminate_process(process)
            raise
    finally:
        _PARSER_SEMAPHORE.release()

    try:
        payload = json.loads(stdout)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ResumeFileError("Resume could not be parsed") from exc

    if process.returncode != 0 or not payload.get("ok"):
        error_type = payload.get("error_type")
        message = payload.get("message", "Resume could not be parsed")
        error_class = {
            "complexity": ResumeFileComplexityError,
            "too_large": ResumeFileTooLargeError,
            "validation": ResumeFileError,
        }.get(error_type, ResumeFileError)
        raise error_class(message)

    from app.schemas.resume_v2 import ResumeDocumentJSON

    try:
        return ResumeDocumentJSON.model_validate(payload["document"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ResumeFileError("Resume could not be parsed") from exc


async def _terminate_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    await process.wait()
