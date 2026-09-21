"""PRI-19 offline evaluation; not imported by application code."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time

BACKEND = Path(__file__).resolve().parents[1]
CORPUS = BACKEND / "tests/fixtures/anydoc"


def parser_budgets():
    from app.core.config import settings
    return {name: getattr(settings, name) for name in (
        "MAX_UPLOAD_SIZE", "MAX_PDF_PAGES", "MAX_EXTRACTED_TEXT_CHARS",
        "MAX_DOCX_ENTRIES", "MAX_DOCX_UNCOMPRESSED_SIZE", "MAX_DOCX_COMPRESSION_RATIO")}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in value.items() if k != "id"}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value


def grade(document, case):
    fields = {}
    for path, expected in case["fields"].items():
        value = document
        try:
            for key in path.split("."):
                value = value[int(key)] if isinstance(value, list) else value[key]
        except (KeyError, IndexError, TypeError):
            value = None
        fields[path] = value == expected
    text = " ".join(document.get("raw_text", "").split())
    positions = [text.find(anchor) for anchor in case["order"]]
    return {"fields": fields, "text_values_found": sum(str(v) in text for v in case["fields"].values()),
            "reading_order": bool(positions) and
            all(p >= 0 for p in positions) and positions == sorted(set(positions))}


def worker(engine, filename, content):
    started = time.perf_counter()
    from io import BytesIO
    import pdfplumber
    from app.core.config import settings
    from app.services.resume.file_security import validate_resume_bytes, ResumeFileComplexityError
    from app.services.resume.parser import parse_resume, _structure_from_text

    try:
        extension = filename.rsplit(".", 1)[-1]
        validate_resume_bytes(content, extension)
        if extension == "pdf":
            with pdfplumber.open(BytesIO(content)) as pdf:
                if len(pdf.pages) > settings.MAX_PDF_PAGES:
                    raise ResumeFileComplexityError("page budget")
        if engine == "existing":
            document = parse_resume(content, filename).model_dump(mode="json")
        else:
            if importlib.metadata.version("firecrawl-anydoc") != "0.2.4":
                raise RuntimeError("Unreviewed AnyDoc version")
            import anydoc
            text = anydoc.to_markdown_bytes(content, extension, ocr="reject")
            if len(text) > settings.MAX_EXTRACTED_TEXT_CHARS:
                raise ResumeFileComplexityError("text budget")
            document = _structure_from_text(text).model_dump(mode="json")
        result = {"status": "ok", "document": document}
    except Exception as exc:
        result = {"status": type(exc).__name__}  # Never persist exception content.
    result["budgets"] = parser_budgets()
    result["parse_ms"] = round((time.perf_counter() - started) * 1000, 3)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["peak_rss_bytes"] = rss if sys.platform == "darwin" else rss * 1024
    return result


def run(engine, path, timeout=15):
    # Empty cwd prevents dotenv loading; allowlist excludes real credentials.
    env = {"PATH": os.defpath, "PYTHONPATH": str(BACKEND), "OPENAI_API_KEY": "test",
           "SUPABASE_URL": "https://test.supabase.co", "SUPABASE_ANON_KEY": "test",
           "SUPABASE_SERVICE_ROLE_KEY": "test", "DATABASE_URL": "sqlite:///:memory:",
           "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    from app.core.config import settings
    env.update({name: str(value) for name, value in parser_budgets().items()})
    with path.open("rb") as stream:
        content = stream.read(settings.MAX_UPLOAD_SIZE + 1)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as cwd:
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                                      "--worker", engine, path.name], input=content,
                                     capture_output=True, cwd=cwd, env=env, timeout=timeout)
            result = json.loads(process.stdout) if process.returncode == 0 else {"status": "worker_failed"}
        except subprocess.TimeoutExpired:
            result = {"status": "timeout"}  # subprocess.run kills and waits.
    result["wall_ms"] = round((time.perf_counter() - started) * 1000, 3)
    result["timeout_seconds"] = timeout
    return result


def main():
    from app.core.config import settings
    cases = json.loads((CORPUS / "manifest.json").read_text())
    rows = []
    for case in cases:
        path = CORPUS / case["file"]
        if path.parent != CORPUS or digest(path.read_bytes()) != case["sha256"]:
            raise ValueError("Corpus identity mismatch")
        for engine in ("existing", "anydoc"):
            samples = []
            for _ in range(3):
                result = run(engine, path, settings.RESUME_PARSE_TIMEOUT_SECONDS)
                document = result.pop("document", {})
                result.update(grade(document, case))
                result["content_hash"] = digest(json.dumps(canonical(document), sort_keys=True).encode())
                samples.append(result)
            rows.append({"case": case["file"], "engine": engine, "samples": samples,
                         "deterministic": len({(s["status"], s["content_hash"]) for s in samples}) == 1})
    print(json.dumps({"platform": platform.platform(), "python": platform.python_version(),
                      "versions": {p: importlib.metadata.version(p) for p in
                                   ("firecrawl-anydoc", "pdfplumber", "python-docx")},
                      "manifest_sha256": digest((CORPUS / "manifest.json").read_bytes()),
                      "results": rows}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], sys.argv[3], sys.stdin.buffer.read())))
    else:
        main()
