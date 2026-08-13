"""Isolated command-line worker for parsing untrusted resume bytes."""

from __future__ import annotations

import json
import sys

from app.services.resume.file_security import (
    ResumeFileComplexityError,
    ResumeFileError,
    ResumeFileTooLargeError,
)
from app.services.resume.parser import parse_resume


def _write(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))


def main() -> int:
    if len(sys.argv) != 2:
        _write({"ok": False, "error_type": "internal", "message": "Resume could not be parsed"})
        return 1

    try:
        document = parse_resume(sys.stdin.buffer.read(), sys.argv[1])
    except ResumeFileTooLargeError as exc:
        _write({"ok": False, "error_type": "too_large", "message": str(exc)})
        return 2
    except ResumeFileComplexityError as exc:
        _write({"ok": False, "error_type": "complexity", "message": str(exc)})
        return 2
    except ResumeFileError as exc:
        _write({"ok": False, "error_type": "validation", "message": str(exc)})
        return 2
    except Exception:
        _write({"ok": False, "error_type": "internal", "message": "Resume could not be parsed"})
        return 1

    _write({"ok": True, "document": document.model_dump(mode="json")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
