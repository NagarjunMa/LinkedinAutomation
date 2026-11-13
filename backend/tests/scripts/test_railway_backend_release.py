from pathlib import Path
from unittest.mock import Mock, call

import pytest

from scripts import railway_backend_release as release


def test_migration_failure_never_uploads_web():
    railway = Mock()
    railway.upload.return_value = "migration-deployment"
    railway.wait.side_effect = release.ReleaseError("FAILED")
    with pytest.raises(release.ReleaseError, match="FAILED"):
        release.deploy(railway, Path("/archive"), "migrator", "web")
    assert railway.mock_calls == [
        call.require_idle("migrator"),
        call.require_idle("web"),
        call.upload(Path("/archive"), "migrator"),
        call.wait("migrator", "migration-deployment"),
    ]


def test_only_success_of_uploaded_migration_allows_same_archive_to_reach_web():
    railway = Mock()
    railway.upload.side_effect = ["migration-deployment", "web-deployment"]
    release.deploy(railway, Path("/archive"), "migrator", "web")
    assert railway.mock_calls == [
        call.require_idle("migrator"),
        call.require_idle("web"),
        call.upload(Path("/archive"), "migrator"),
        call.wait("migrator", "migration-deployment"),
        call.verify_migration("migrator", "migration-deployment"),
        call.upload(Path("/archive"), "web"),
        call.wait("web", "web-deployment"),
    ]


def test_wait_rejects_uploaded_migration_failure_even_with_unrelated_success(monkeypatch):
    railway = release.Railway("project", "environment", 10)
    monkeypatch.setattr(railway, "run", Mock(return_value=[
        {"id": "other-deployment", "status": "SUCCESS"},
        {"id": "submitted-deployment", "status": "FAILED"},
    ]))
    with pytest.raises(release.ReleaseError, match="submitted-deployment ended in FAILED"):
        railway.wait("migrator", "submitted-deployment")


def test_success_without_alembic_marker_never_uploads_web():
    railway = Mock()
    railway.upload.return_value = "migration-deployment"
    railway.verify_migration.side_effect = release.ReleaseError("Missing Alembic completion marker")
    with pytest.raises(release.ReleaseError, match="Missing Alembic"):
        release.deploy(railway, Path("/archive"), "migrator", "web")
    railway.upload.assert_called_once_with(Path("/archive"), "migrator")


def test_snapshot_reads_git_tree_and_excludes_worktree_edits(tmp_path):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    backend = repo / "backend"
    backend.mkdir()
    (backend / "Dockerfile").write_text("reviewed")
    subprocess.run(["git", "add", "backend"], cwd=repo, check=True)
    tree = subprocess.check_output(["git", "write-tree"], cwd=repo, text=True).strip()
    revision = subprocess.check_output(
        ["git", "-c", "user.name=Release Test", "-c", "user.email=release@example.com",
         "commit-tree", tree, "-m", "Fixture"], cwd=repo, text=True,
    ).strip()
    (backend / "Dockerfile").write_text("unreviewed")
    (backend / ".env").write_text("synthetic-private")
    archive = tmp_path / "archive"
    release.snapshot(repo, archive, revision)
    assert (archive / "Dockerfile").read_text() == "reviewed"
    assert sorted(p.name for p in archive.iterdir()) == ["Dockerfile"]


def test_separate_migration_environment_routes_only_migration_service():
    railway = release.Railway("project", "web-env", 10, "migration-env", "migration")
    assert railway.target("migration") == ["--project", "project", "--environment", "migration-env", "--service", "migration"]
    assert railway.target("web") == ["--project", "project", "--environment", "web-env", "--service", "web"]


def test_verify_migration_reads_marker_for_exact_deployment(monkeypatch):
    railway = release.Railway("project", "env", 10)
    run = Mock(return_value=Mock(stdout='{"message":"PRISMPRO_ALEMBIC_UPGRADE_SUCCEEDED"}\n'))
    monkeypatch.setattr(release.subprocess, "run", run)
    railway.verify_migration("migrator", "migration-deployment")
    assert run.call_args.args[0] == [
        "railway", "logs", "migration-deployment", "--deployment", "--lines", "100", "--json",
        "--project", "project", "--environment", "env", "--service", "migrator",
    ]


def test_existing_deployment_stops_release_before_any_upload():
    railway = Mock()
    railway.require_idle.side_effect = release.ReleaseError("deployment in progress")
    with pytest.raises(release.ReleaseError, match="deployment in progress"):
        release.deploy(railway, Path("/archive"), "migrator", "web")
    railway.upload.assert_not_called()


def test_cli_receives_only_destination_project_token(monkeypatch):
    railway = release.Railway("project", "web-env", 10, "migration-env", "migration")
    monkeypatch.setenv("RELEASE_WEB_TOKEN", "web-fixture")
    monkeypatch.setenv("RELEASE_MIGRATION_TOKEN", "migration-fixture")
    monkeypatch.setenv("RAILWAY_API_TOKEN", "workspace-fixture")
    command = Mock()
    monkeypatch.setattr(release.subprocess, "run", command)
    for service, token in (("migration", "migration-fixture"), ("web", "web-fixture")):
        railway.command(["deployment", "list"], 10, service)
        env = command.call_args.kwargs["env"]
        assert env["RAILWAY_TOKEN"] == token
        assert {"RELEASE_WEB_TOKEN", "RELEASE_MIGRATION_TOKEN", "RAILWAY_API_TOKEN"}.isdisjoint(env)
