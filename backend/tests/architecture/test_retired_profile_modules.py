"""Keep retired profile code absent without breaking supported app configurations."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.export_openapi import EXPORT_ENV


BACKEND_ROOT = Path(__file__).resolve().parents[2]
RETIRED_MODULES = (
    "app.api.v1.endpoints.profiles",
    "app.services.resume_parser",
    "app.services.job_scorer",
)
CONFIGURATIONS = (
    {},
    {"ENABLE_LEGACY_JOB_EXTRACTION": "true"},
    {"ENABLE_BILLING": "true"},
    {"ENABLE_LEGACY_JOB_EXTRACTION": "true", "ENABLE_BILLING": "true",
     "PRISM_PRO_PUBLIC_PREVIEW_ONLY": "true"},
)

# A fresh interpreter avoids passing because an earlier test cached app.main.
# Fail on a retired import even if the caller would swallow ImportError.
APP_PROBE = """
import asyncio, contextlib, importlib.abc, json, sys
sys.path.insert(0, sys.argv[1])
from scripts.export_openapi import deny_network
sys.addaudithook(deny_network)
retired = set(json.loads(sys.argv[2]))
class RetiredImportBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in retired:
            raise AssertionError(f'Retired module imported: {fullname}')
sys.meta_path.insert(0, RetiredImportBlocker())
with contextlib.redirect_stdout(sys.stderr):
    from app.main import app
    async def startup_and_shutdown():
        async with app.router.lifespan_context(app):
            pass
    asyncio.run(startup_and_shutdown())
    document = app.openapi()
print(json.dumps({'openapi': document, 'loaded': sorted(sys.modules)}))
"""


def inspect_app(directory: Path, flags: dict[str, str]) -> dict:
    """Return the full schema under dummy settings, with all network I/O denied."""
    result = subprocess.run(
        [sys.executable, "-I", "-c", APP_PROBE, str(BACKEND_ROOT),
         json.dumps(RETIRED_MODULES)],
        cwd=directory, env={**EXPORT_ENV, **flags},
        capture_output=True, text=True, timeout=30, check=True,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("module", RETIRED_MODULES)
def test_retired_profile_modules_are_not_importable(module):
    assert importlib.util.find_spec(module) is None, module


@pytest.mark.parametrize("flags", CONFIGURATIONS,
                         ids=("mvp", "legacy-extraction", "billing", "preview-all-flags"))
def test_application_starts_without_retired_modules(tmp_path, flags):
    result = inspect_app(tmp_path, flags)
    paths = result["openapi"]["paths"]
    assert not any(path.startswith("/api/v1/profiles/") for path in paths)
    assert "/api/v1/user-profiles/{user_id}" in paths
    assert "/api/v1/resumes/upload" in paths
    assert "/api/v1/jd/analyze" in paths
    assert "/api/v1/exports" in paths
    assert "/api/v1/admin/metrics/cost-per-user" in paths
    assert ("/api/v1/webhooks/stripe" in paths) == (flags.get("ENABLE_BILLING") == "true")
    legacy_enabled = flags.get("ENABLE_LEGACY_JOB_EXTRACTION") == "true"
    assert ("/api/v1/jobs/extract-from-url" in paths) == legacy_enabled
    assert ("app.services.smart_job_scorer" in result["loaded"]) == legacy_enabled
    assert "app.schemas.profile" in result["loaded"]
