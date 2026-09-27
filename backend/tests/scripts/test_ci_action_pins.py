"""Guard the release-critical CI action and secret-scan configuration."""

import re
from pathlib import Path

import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github/workflows/ci.yml"


def test_external_actions_use_full_shas_with_release_comments() -> None:
    source = WORKFLOW.read_text()
    jobs = yaml.safe_load(source)["jobs"]
    action_refs = [
        step["uses"]
        for job in jobs.values()
        for step in job["steps"]
        if "uses" in step
    ]
    action_lines = re.findall(
        r"^\s*(?:-\s*)?uses:\s*([^\s#]+)\s*#\s*(v\d+\.\d+\.\d+)\s*$",
        source,
        re.MULTILINE,
    )
    assert action_refs
    assert [action for action, _ in action_lines] == action_refs
    for action, release in action_lines:
        repository, separator, revision = action.partition("@")
        assert separator and "/" in repository
        assert re.fullmatch(r"[0-9a-f]{40}", revision), action
        assert re.fullmatch(r"v\d+\.\d+\.\d+", release), action


def test_secret_scan_uses_full_history_verified_results_and_pinned_image() -> None:
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"]["secret-scan"]["steps"]
    checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
    scanner = next(step for step in steps if step.get("name") == "TruffleHog verified scan")

    assert checkout["with"]["fetch-depth"] == 0
    assert all(not step.get("uses", "").startswith("trufflesecurity/trufflehog@") for step in steps)
    command = scanner["run"]
    assert re.search(
        r"ghcr\.io/trufflesecurity/trufflehog@sha256:[0-9a-f]{64}",
        command,
    )
    assert '"$PWD:/repo:ro"' in command
    assert "git file:///repo/" in command
    assert '--branch "$GITHUB_SHA"' in command
    assert "--since-commit" not in command
    for flag in ("--fail", "--fail-on-scan-errors", "--no-update", "--github-actions", "--only-verified"):
        assert flag in command.split()
