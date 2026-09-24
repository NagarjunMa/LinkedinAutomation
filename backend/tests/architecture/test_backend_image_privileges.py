"""Keep both backend image entry points unprivileged at runtime."""

from pathlib import Path

import pytest


REPOSITORY = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("dockerfile", ["backend/Dockerfile", "Dockerfile"])
def test_backend_image_selects_a_non_root_runtime_user(dockerfile):
    instructions = (REPOSITORY / dockerfile).read_text().splitlines()
    users = [line.split(maxsplit=1)[1].strip() for line in instructions
             if line.lstrip().upper().startswith("USER ")]

    assert users, f"{dockerfile} must select a runtime user"
    assert users[-1].split(":", maxsplit=1)[0] not in {"root", "0"}
