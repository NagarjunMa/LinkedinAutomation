# PRI-19 — AnyDoc benchmark

## Execution context / problem / goal

2026-09-20; [approved issue](https://linear.app/prismpro/issue/PRI-19/benchmark-anydoc-against-the-existing-bounded-resume-parser); base `1600901`, implementation `5cd9fea` plus local audit corrections on `chore/pri-19-anydoc-benchmark`. Evaluate replacement suitability, not a production integration. Full evidence record for Significant risk (native parser/resource boundary and shared AnyIO patch). Issue remains open pending final review and merge gates.
PrismPro's current FastAPI/Python parser produces resume JSON for the Next.js client; target grounded-evidence architecture remains [separate](architecture.md). Verified `backend/app/services/resume/{parser,file_security,parser_worker}.py`, parser tests, PDF renderer/templates, Makefile and CI. Other subsystems were not reviewed for this benchmark.

## Contract / implementation plan / design

Create a synthetic corpus, independent labels, regression-first grader, bounded subprocess comparison and evidence-backed decision. AC1: reproducible corpus/results; AC2: privacy/license/resources documented; AC3: fallback/rollback recommendation; AC4: production parser untouched. Acceptance does not require AnyDoc to win.
Created `backend/scripts/benchmark_anydoc.py` (runner, worker, grader), `anydoc-requirements.txt` (evaluation-only pin), `backend/tests/scripts/test_benchmark_anydoc.py` and `backend/tests/fixtures/anydoc/` (builder, manifest, nine documents). No application imports this tooling; no API/schema changes. Owner separately authorized the AnyIO security patch in requirements.in/lock and a small increase above the original 300-line budget for the subprocess correction and regression tests. Single sequential child per sample; existing validation owns upload/archive policy, not a copied implementation.
Corpus: single-column PDF/DOCX, columns, synthetic LinkedIn-style layout, image-only scan, actual PrismPro renderer output, malformed PDF, unsafe DOCX and eleven-page PDF. LinkedIn-style is NOT a real LinkedIn export; generalization needs separately consented holdout data. Fixture expectations are authored independently; generated fixtures are not training data.
Grading separates literal source-value presence from exact eight-field resume-JSON compatibility and ordered anchors. AnyDoc Markdown goes through the unchanged heuristic splitter: this measures direct compatibility, NOT AnyDoc's standalone semantic accuracy. No adapter is proposed for adoption. Canonical replay hashes omit generated IDs only; raw text remains included. No aggregate ATS/candidate score.

## Security / privacy / limits

Only checked-in synthetic fixtures run. SHA-256 manifest verification precedes execution; workers use empty cwd and credential-free allowlisted environment. Existing limits: 10 MiB upload, 10 PDF pages, 100k extracted characters, 2,000 ZIP entries, 25 MiB expansion, ratio 100, 15-second kill-and-wait timeout. PDF preflight runs for both engines, so malformed/page-limit rejection is shared-policy evidence, not an AnyDoc advantage. No hard RSS cap exists in the current boundary; RSS is measured, not guaranteed bounded.
AnyDoc `ocr="reject"` is explicit. Source inspection confirms hosted OCR is opt-in and sends the whole document; never enable it implicitly. No hosted calls/real secrets were used. This is not an OS network-isolation or transitive native-code audit. Output contains metrics/hashes and exception class names, not raw documents or exception messages. No logs or generated measurement files belong in Git.
[Pinned source](https://github.com/firecrawl/anydoc/tree/261fc257d17c3eab0f673be31c408fd9fdc2171a), Python wrapper, Cargo manifest and MIT license reviewed 2026-09-18; installed wrapper matched source. MIT requires notice preservation; transitive license/security review remains necessary before adoption. Python >=3.10; source builds require Rust >=1.88. Tested macOS arm64 wheel: 3,262,365 bytes download, about 6.9 MiB installed package. Linux x86_64 wheel hash also pinned but not executed. Existing pdfplumber/python-docx cannot be removed by this experiment.

## Reproduction / verification

From `backend`, with Python 3.11 and the repository's supported dependencies:
```sh
BENCH_ENV=$(mktemp -d /tmp/prism-anydoc.XXXXXX)
python3.11 -m venv --system-site-packages "$BENCH_ENV"
"$BENCH_ENV/bin/python" -m pip install --only-binary=:all: --no-deps --require-hashes -r scripts/anydoc-requirements.txt
export OPENAI_API_KEY=test SUPABASE_URL=https://test.supabase.co SUPABASE_ANON_KEY=test SUPABASE_SERVICE_ROLE_KEY=test DATABASE_URL=sqlite:///:memory: SQLALCHEMY_DATABASE_URI=sqlite:///:memory: PYTHONPATH=.
"$BENCH_ENV/bin/python" scripts/benchmark_anydoc.py > "$BENCH_ENV/results.json"
python3.11 -m pytest tests/scripts/test_benchmark_anydoc.py tests/services/resume/test_parser.py -q -o addopts=''
```
Use shipped fixture bytes for comparisons. Optional regeneration: `python3.11 tests/fixtures/anydoc/build.py` needs ReportLab 4.4.3, Pillow and repository Chromium; PDF/ZIP metadata may change hashes, so review the new manifest. The executed fixture build used Pillow 12.2.0. Visual inspection covered simple, columns, LinkedIn-style, scan and export; malformed and blank extra pages are intentional. A page-count test caught and corrected the builder's initial ten-versus-eleven-page mistake.
TDD: observed the runnable grader fail its missing-field/reversed-order assertion, then pass; subsequent boundary coverage added. Passed: 12 scoped tests and Ruff for all three new Python files. `make verify-backend-ci`: 603 passed, 12 existing skips, 88.42% coverage; FAILED dependency audit on unchanged anyio 4.14.0 (GHSA-82r6-8w77-94w6, GHSA-5p39-cfhj-2xmp, GHSA-3w57-8xmc-8v26; fix listed 4.14.2). No skip/control weakened. Hosted CI, Docker/Linux execution and human review pending; frontend not rerun (no UI/runtime change).

## Results / decisions / remaining risks

Final run: three fresh processes per engine/case (54 total), all canonical outputs/statuses repeatable. Manifest SHA-256 `699c936a18b992aabe55dfb0c9a7d00a51eb2e04ada7b776192d0179eaa62bc1`. All eight literal values survived in both engines on the five readable cases below. Field compatibility is a separate result. Times are median wall milliseconds, including interpreter/imports, shared preflight and structuring; memory is maximum child RSS MiB. No throughput/p95 or speedup claim. Environment: macOS 26.6.2 arm64, Python 3.11.1, AnyDoc 0.2.4, pdfplumber 0.11.10, python-docx 1.2.0.

| Fixture | Exact fields existing / AnyDoc | Order existing / AnyDoc | Wall ms existing / AnyDoc | RSS MiB existing / AnyDoc |
| --- | --- | --- | --- | --- |
| simple PDF | 8/8 / 1/8 | pass / pass | 401 / 1032 | 63.5 / 66.9 |
| columns PDF | 1/8 / 1/8 | fail / fail | 422 / 522 | 63.4 / 67.2 |
| LinkedIn-style PDF | 2/8 / 1/8 | pass / pass | 397 / 370 | 63.2 / 66.8 |
| simple DOCX | 8/8 / 7/8 | pass / pass | 397 / 383 | 68.8 / 69.2 |
| PrismPro export | 8/8 / 1/8 | pass / pass | 365 / 450 | 63.2 / 68.3 |

Both safely rejected the image-only scan (existing ResumeFileError, AnyDoc NeedsOcrError); both rejected eleven pages (ResumeFileComplexityError), malformed PDF (PdfminerException) and unsafe ZIP path (ResumeFileError) before conversion. No crash or timeout occurred in this small corpus. Timeout reporting/environment isolation are regression-tested with a simulated timeout, not a native-parser hang. Readable text without compatible structure is the demonstrated lesson; preserve both graders in future adapter evaluations.

## Compatibility / rollout / rollback

Recommendation: reject a drop-in replacement on this corpus; retain the bounded existing parser. Both need further work for columns/LinkedIn semantic fields and neither provides local OCR here. A future adapter requires a separately approved issue, larger consent-safe holdout corpus, unchanged safety boundaries and no regression in expected fields/order. On unreadable scans, return a clear failure/request text-based PDF or DOCX; do not silently send to hosted OCR or fabricate fields. Evaluation rollback removes the tooling; preserve patched AnyIO instead of restoring vulnerable 4.14.0. Deploy the rebuilt backend dependency environment only after release gates; no API/data migration is required.

## Audit correction / retained lesson — 2026-09-20

PRI19-R1 (medium, introduced): credential isolation also dropped configured parsing limits. Six real-process regressions first failed for the intended wrong acceptance/error behavior. The runner now explicitly transports six validated non-secret budgets; workers report their effective budgets and the parent reports its timeout. Settings remains the validation owner; no ambient credentials or dotenv files are restored. Tests cover stricter upload/text/archive limits and accepting eleven pages with a configured twelve-page limit. When isolating workers, test legitimate configuration separately from secret isolation, including both sides of defaults.
AnyIO 4.14.2 replaces 4.14.0; no other locked version changed. Pre-correction backend gate passed 603 tests/12 existing skips, 88.42% coverage, and zero known dependency vulnerabilities; API contract gate passed. This supersedes the historical dependency blocker above. Final correction validation and independent-review evidence are recorded in Linear. Docker daemon is unavailable; hosted CI, PostgreSQL/Linux checks and human review remain pending. Local validation uses a temporary system-site venv with the complete lock installed; unrelated inherited pip-check conflicts mean clean-install consistency is not established here.
