"""Retired infrastructure must not become an implicit runtime dependency again."""

import ast
from pathlib import Path

from packaging.requirements import Requirement
import pytest
import yaml

from app.core.config import Settings
from tests.architecture.test_retired_profile_modules import CONFIGURATIONS, inspect_app


BACKEND = Path(__file__).resolve().parents[2]
RETIRED_PACKAGES = {
    "google-auth", "google-auth-oauthlib", "google-auth-httplib2",
    "google-api-python-client", "google-api-core", "googleapis-common-protos",
    "httplib2", "pyasn1", "pyasn1-modules", "oauthlib", "requests-oauthlib",
    "proto-plus", "protobuf", "pyparsing", "uritemplate", "celery", "redis",
}
RETIRED_IMPORTS = (
    "google", "googleapiclient", "google_auth_oauthlib", "google_auth_httplib2",
    "httplib2", "pyasn1", "pyasn1_modules", "oauthlib", "requests_oauthlib",
    "proto", "pyparsing", "uritemplate", "celery", "redis",
)
RETIRED_SETTINGS = {
    "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_SCOPES",
    "EMAIL_CLASSIFICATION_MODEL", "EMAIL_SYNC_FREQUENCY_MINUTES",
    "EMAIL_CONFIDENCE_THRESHOLD", "AUTO_UPDATE_THRESHOLD", "ENABLE_EMAIL_SCANNING",
}


def test_compose_has_no_unimplemented_workers_or_brokers():
    source = (BACKEND.parent / "docker-compose.yml").read_text()
    compose = yaml.safe_load(source)
    assert set(compose["services"]) == {"frontend", "backend", "db"}
    assert set(compose["volumes"]) == {"postgres_data"}
    assert "redis" not in source.lower()
    assert "celery" not in source.lower()
    for service in compose["services"].values():
        assert set(service.get("depends_on", [])) <= set(compose["services"])


@pytest.mark.parametrize("filename", ["requirements.in", "requirements.lock"])
def test_dependencies_exclude_retired_family_but_preserve_active_integrations(filename):
    names = {
        Requirement(line).name.lower()
        for line in (BACKEND / filename).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert not names & RETIRED_PACKAGES
    assert {"stripe", "supabase", "pyjwt", "cryptography", "beautifulsoup4"} <= names


def test_compatibility_install_uses_the_canonical_dependency_declarations():
    lines = [line for line in (BACKEND / "requirements.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    assert lines == ["-r requirements.in"]


@pytest.mark.parametrize("filename", ["requirements.in", "requirements.lock"])
def test_soupsieve_security_floor_excludes_vulnerable_releases(filename):
    requirements = [
        Requirement(line)
        for line in (BACKEND / filename).read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    requirement = next((item for item in requirements if item.name == "soupsieve"), None)
    assert requirement is not None
    assert "2.8.4" not in requirement.specifier
    assert "2.9.0" in requirement.specifier
    assert "3.0.0" not in requirement.specifier


@pytest.mark.parametrize("filename, prefix", [("Dockerfile", "backend/"),
                                             ("backend/Dockerfile", "")])
def test_docker_installs_the_lock_after_copying_it(filename, prefix):
    source = (BACKEND.parent / filename).read_text()
    install = "RUN pip install --no-cache-dir -r requirements.lock"
    copy = f"COPY {prefix}requirements.in {prefix}requirements.lock ./"
    assert copy in source
    assert install in source
    assert source.index(copy) < source.index(install)
    assert "-r requirements.txt" not in source


def test_retired_gmail_environment_is_ignored_without_enabling_billing(monkeypatch):
    for name in RETIRED_SETTINGS:
        monkeypatch.setenv(name, "retired-placeholder")
    settings = Settings(_env_file=None, ENVIRONMENT="test", ENABLE_BILLING=False,
                        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    assert not RETIRED_SETTINGS & Settings.model_fields.keys()
    assert Settings.model_fields["ENABLE_BILLING"].default is False
    assert settings.ENABLE_BILLING is False


def test_no_runtime_source_imports_retired_dependencies():
    for directory in ("app", "scripts", "migrations"):
        for path in (BACKEND / directory).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                imports = []
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    imports = [node.module or ""]
                assert not any(name.split(".")[0] in RETIRED_IMPORTS for name in imports), path


@pytest.mark.parametrize("flags", CONFIGURATIONS)
def test_optional_routes_start_without_retired_integration_imports(tmp_path, flags):
    result = inspect_app(tmp_path, flags, blocked_modules=RETIRED_IMPORTS)
    assert ("/api/v1/webhooks/stripe" in result["openapi"]["paths"]) == (
        flags.get("ENABLE_BILLING") == "true"
    )
    assert "app.core.auth" in result["loaded"]
