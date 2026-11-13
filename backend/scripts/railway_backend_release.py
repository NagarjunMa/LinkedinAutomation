"""Release a reviewed backend snapshot through separate Railway services."""

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
import time
from uuid import UUID


ACTIVE_STATUSES = {"QUEUED", "WAITING", "INITIALIZING", "BUILDING", "DEPLOYING", "NEEDS_APPROVAL"}


class ReleaseError(RuntimeError):
    """Railway could not confirm the release."""


def uuid_arg(value):
    return str(UUID(value))


def snapshot(repository, destination, revision):
    tar_path = destination.with_suffix(".tar")
    subprocess.run(
        ["git", "archive", "--format=tar", f"--output={tar_path}", f"{revision}^{{commit}}:backend"],
        cwd=repository, capture_output=True, check=True, timeout=30,
    )
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise ReleaseError("Backend archive contains an unsupported path or file type")
        archive.extractall(destination)
    tar_path.unlink()


class Railway:
    def __init__(self, project, environment, timeout, migration_environment=None, migrator=None):
        self.project = project
        self.environment = environment
        self.migration_environment = migration_environment or environment
        self.migrator = migrator
        self.timeout = timeout

    def target(self, service):
        environment = self.migration_environment if service == self.migrator else self.environment
        return ["--project", self.project, "--environment", environment, "--service", service]

    def command(self, args, timeout, service):
        env = os.environ.copy()
        env.pop("RAILWAY_API_TOKEN", None)
        web_token = env.pop("RELEASE_WEB_TOKEN", None)
        migration_token = env.pop("RELEASE_MIGRATION_TOKEN", None)
        if web_token:
            env["RAILWAY_TOKEN"] = (migration_token or web_token) if service == self.migrator else web_token
        return subprocess.run(
            ["railway", *args, *self.target(service)],
            capture_output=True, text=True, check=True, timeout=timeout, env=env,
        )

    def run(self, args, timeout, service):
        try:
            return json.loads(self.command(args, timeout, service).stdout)
        except (OSError, subprocess.SubprocessError, ValueError):
            raise ReleaseError("Railway command failed or returned an unreadable response") from None

    def upload(self, backend, service):
        result = self.run(
            ["up", str(backend), "--path-as-root", "--no-gitignore", "--detach", "--json"], 180, service,
        )
        try:
            deployment = uuid_arg(result["deploymentId"])
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ReleaseError("Railway did not return a deployment ID") from None
        print(f"Queued Railway deployment {deployment} for {service}", flush=True)
        return deployment

    def wait(self, service, deployment):
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            deployments = self.run(["deployment", "list", "--json", "--limit", "20"], 30, service)
            result = next((item for item in deployments if item["id"] == deployment), None)
            if result:
                status = result["status"]
                if status == "SUCCESS":
                    print(f"Railway deployment {deployment} succeeded", flush=True)
                    return
                if status in {"FAILED", "CRASHED", "REMOVED", "SKIPPED", "CANCELED", "CANCELLED"}:
                    raise ReleaseError(f"Railway deployment {deployment} ended in {status}")
            time.sleep(5)
        raise ReleaseError(f"Timed out waiting for Railway deployment {deployment}")

    def require_idle(self, service):
        deployments = self.run(["deployment", "list", "--json", "--limit", "20"], 30, service)
        if any(item["status"] in ACTIVE_STATUSES for item in deployments):
            raise ReleaseError(f"Railway service {service} already has a deployment in progress")

    def verify_migration(self, service, deployment):
        # A Railway deployment can succeed with an unset pre-deploy command.
        for _ in range(6):
            try:
                result = self.command(["logs", deployment, "--deployment", "--lines", "100", "--json"], 20, service)
                if any(json.loads(line).get("message") == "PRISMPRO_ALEMBIC_UPGRADE_SUCCEEDED"
                       for line in result.stdout.splitlines() if line.strip()):
                    return
            except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
                pass
            time.sleep(2)
        raise ReleaseError(f"Missing Alembic completion marker for {deployment}")


def deploy(railway, backend, migrator, web):
    railway.require_idle(migrator)
    railway.require_idle(web)
    migration = railway.upload(backend, migrator)
    railway.wait(migrator, migration)
    railway.verify_migration(migrator, migration)
    deployment = railway.upload(backend, web)
    railway.wait(web, deployment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=uuid_arg, required=True)
    parser.add_argument("--environment", type=uuid_arg, required=True)
    parser.add_argument("--migration-environment", type=uuid_arg)
    parser.add_argument("--migrator", type=uuid_arg, required=True)
    parser.add_argument("--web", type=uuid_arg, required=True)
    parser.add_argument("--revision", required=True, help="Full reviewed Git commit SHA")
    parser.add_argument("--timeout", type=int, default=900, help="Seconds to wait per deployment")
    args = parser.parse_args()
    if args.migrator == args.web or args.timeout <= 0:
        parser.error("Use distinct services and a positive timeout")
    if os.environ.get("RELEASE_WEB_TOKEN") and args.migration_environment not in (None, args.environment):
        if not os.environ.get("RELEASE_MIGRATION_TOKEN"):
            parser.error("A separate migration environment requires its own Railway project token")
    if len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
        parser.error("Provide a full lowercase Git commit SHA")
    repository = Path(__file__).resolve().parents[2]
    try:
        with TemporaryDirectory(prefix="prismpro-backend-release-") as directory:
            archive = Path(directory) / "backend"
            snapshot(repository, archive, args.revision)
            railway = Railway(args.project, args.environment, args.timeout, args.migration_environment, args.migrator)
            deploy(railway, archive, args.migrator, args.web)
    except ReleaseError as error:
        print(error, file=sys.stderr)
        return 1
    except (OSError, subprocess.SubprocessError, tarfile.TarError):
        print("Could not package the reviewed backend commit", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
