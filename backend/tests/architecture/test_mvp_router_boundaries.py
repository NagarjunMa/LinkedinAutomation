"""Guard the application boundary introduced for mounted MVP resume flows."""

import ast
from pathlib import Path


ENDPOINT_ROOT = Path(__file__).parents[2] / "app/api/v1/endpoints"
MIGRATED_ROUTERS = (
    "resumes_v2.py",
    "jd.py",
    "exports.py",
    "tailored_resumes.py",
    "jobs.py",
    "user_profiles.py",
)


def test_migrated_routers_do_not_import_other_endpoint_modules():
    for filename in MIGRATED_ROUTERS:
        source = (ENDPOINT_ROOT / filename).read_text()
        assert "app.api.v1.endpoints" not in source, filename


def test_migrated_routers_do_not_own_sqlalchemy_or_transactions():
    for filename in MIGRATED_ROUTERS:
        tree = ast.parse((ENDPOINT_ROOT / filename).read_text())
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert not any(module.startswith("sqlalchemy") for module in imports), filename
        assert "db" not in names, filename
        assert "Session" not in names, filename
        assert "credit_transaction" not in names, filename


def test_migrated_routers_depend_on_application_services():
    for filename in MIGRATED_ROUTERS:
        tree = ast.parse((ENDPOINT_ROOT / filename).read_text())
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        assert any(module.startswith("app.application") for module in imports), filename
