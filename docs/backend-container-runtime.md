# PRI-24 backend container runtime

Status: implemented locally on `security/pri-24-backend-non-root`; the backend
image smoke passed, while the combined image and clean-PostgreSQL startup remain
unverified. The [PrismPro issue](https://linear.app/prismpro/issue/PRI-24/run-the-backend-container-as-a-non-root-user)
is the durable plan and progress record.

## Contract and design

Both backend image definitions, `backend/Dockerfile` (CI and Compose) and the
repository-root `Dockerfile` (combined Railway image), select the fixed
`prism:prism` runtime identity (UID/GID 10001). Python packages, application
source and the Playwright browser remain root-owned. The runtime account owns
only its home/cache, `/app/logs` and `/app/uploads`; `/tmp` retains the base
image's normal temporary-file permissions. The browser is installed at
`/ms-playwright`, readable and executable but not writable by the runtime user.
The local Compose source bind mount masks image permissions, so Compose mounts
the two data directories as UID/GID 10001 temporary filesystems.

The existing startup command still runs Alembic before Uvicorn when
`RUN_DB_MIGRATIONS=true`; the health endpoint still checks database
connectivity. Supabase Storage credentials and API contracts are unchanged.
Both image health probes use a dedicated User-Agent because request validation
blocks curl's default User-Agent. The probe path and request validation policy
are otherwise unchanged.
The root build context now excludes `.env` files, local logs, uploads, caches
and dependencies so a developer's private files cannot be copied by the
combined Dockerfile. No secret build arguments were added.

The PDF renderer currently starts Chromium with `--no-sandbox`. Running the
container as a non-root user does **not** enable the Chromium sandbox. Playwright's
[Docker guidance](https://playwright.dev/python/docs/docker) recommends a
non-root user plus a permissive seccomp profile for sandboxed crawling, while
Docker's [image guidance](https://docs.docker.com/build/building/best-practices/)
recommends `USER` for services that need no privilege (checked 2026-09-23).
This issue reduces the API/browser process's OS privileges; it does not claim
browser-process sandboxing or permission to alter Railway seccomp policy.

## Evaluations

| Criterion | Check | Current evidence |
| --- | --- | --- |
| Non-root API and browser process | Dockerfile regression test and built-image `id`/write-denial smoke | Static test red before change, green after; backend image smoke passed as UID 10001; combined image pending |
| Health and PDF | CI runs `/health` and the real `render_pdf_from_doc` path in both backend-capable images | Backend image rendered a visible one-page PDF and Docker reported healthy; combined image pending |
| Writable paths | Built-image smoke checks home, logs and uploads writable; app and browser paths denied | Backend image passed; combined image pending; Compose config parses |
| No image-layer production secret | Root `.dockerignore` excludes `.env*`; Dockerfiles use no secret build arguments | Source inspection; built-image inspection pending |
| Startup migrations | CI starts each image with migrations enabled against its own clean disposable PostgreSQL database, then checks health and `alembic_version` | Pending hosted CI execution |

The backend native gate passed with 694 tests, 26 skips, 88.82% coverage and no
known dependency vulnerabilities. Docker Desktop initially had no usable daemon;
a force-stop/start recovered it. On the locally built backend image, the first
file-path smoke invocation failed because `/app` was absent from Python's import
path; the corrected module invocation passed. The first image health probe was
rejected with HTTP 400 because it used curl's blocked default User-Agent, and
Docker marked the container unhealthy. After setting a dedicated health
User-Agent in both images and CI, a rebuilt backend image passed the UID,
write-permission and real PDF smoke; `/health` returned healthy and Docker's
health state became healthy. The test container and temporary image were removed
afterward because available disk fell below 200 MB.

The combined root image and clean-PostgreSQL migration/startup remain not run
locally because disk space is insufficient for another large image and a new
PostgreSQL image. Hosted CI must execute both before PRI-24 can be verified.

## Delivery limits

Build-time compiler and Git packages remain in the final Python stage. Removing
them would require a separately verified dependency/runtime-stage change and
does not affect the non-root runtime invariant. Deployment must use the newly
built image; green CI is not deployed evidence. Reverting to the previous image
would restore a root API/browser process, so investigate a failed rollout and
prefer a scoped forward correction.
