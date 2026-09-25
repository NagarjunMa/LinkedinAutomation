"""Exercise the shell boundary between schema release and web startup."""

import os
import subprocess
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[2]


def _run_script(tmp_path: Path, script: str, alembic_exit: int = 0):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    trace = tmp_path / "commands"
    for command, exit_code in (("alembic", alembic_exit), ("uvicorn", 0)):
        executable = bin_dir / command
        executable.write_text(
            '#!/bin/sh\nprintf "%s %s\\n" "' + command + '" "$*" >> "$TRACE"\n'
            f"exit {exit_code}\n"
        )
        executable.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "TRACE": str(trace),
        "RUN_DB_MIGRATIONS": "true",  # Legacy setting must not restore startup writes.
        "PORT": "8080",
        "WEB_CONCURRENCY": "2",
    }
    result = subprocess.run(
        ["sh", str(BACKEND / "scripts" / script)],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    commands = trace.read_text().splitlines() if trace.exists() else []
    return result, commands


def test_web_start_checks_revision_without_upgrading(tmp_path):
    result, commands = _run_script(tmp_path, "start.sh")

    assert result.returncode == 0
    assert commands == [
        "alembic current --check-heads",
        "uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 2",
    ]


def test_web_start_fails_before_serving_when_schema_is_behind(tmp_path):
    result, commands = _run_script(tmp_path, "start.sh", alembic_exit=17)

    assert result.returncode == 17
    assert commands == ["alembic current --check-heads"]


def test_release_migration_succeeds_without_starting_web(tmp_path):
    result, commands = _run_script(tmp_path, "migrate.sh")

    assert result.returncode == 0
    assert commands == ["alembic upgrade head"]


def test_release_migration_failure_propagates(tmp_path):
    result, commands = _run_script(tmp_path, "migrate.sh", alembic_exit=23)

    assert result.returncode == 23
    assert commands == ["alembic upgrade head"]
