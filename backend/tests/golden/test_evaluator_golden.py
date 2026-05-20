"""Golden snapshot tests for the evaluator service.

These tests use REAL OpenAI calls and are gated by:
    RUN_GOLDEN=1 pytest backend/tests/golden -v

To regenerate snapshots (e.g. after prompt changes):
    RUN_GOLDEN=1 pytest backend/tests/golden -v --snapshot-update
"""
import os
import pytest
from pathlib import Path
from app.services.resume.parser import parse_resume
from app.services.resume.evaluator import evaluate_resume


FIXTURES = sorted((Path(__file__).parent.parent / "fixtures/resumes").glob("*.pdf"))


@pytest.mark.skipif(
    not os.getenv("RUN_GOLDEN"),
    reason="requires RUN_GOLDEN=1 (nightly only — uses real OpenAI)",
)
@pytest.mark.asyncio
@pytest.mark.parametrize("fixture", FIXTURES, ids=[f.name for f in FIXTURES])
async def test_evaluator_snapshot(fixture, snapshot):
    with fixture.open("rb") as f:
        doc = parse_resume(f.read(), filename=fixture.name)
    report = await evaluate_resume(doc, target_role="SWE")
    # Snapshot only structural fields — not LLM-variable free-text reasons
    assert {
        "overall_score_band": report.overall_score // 10 * 10,
        "flag_count_by_severity": {
            s: sum(1 for fl in report.bullet_flags if fl.severity == s)
            for s in ("critical", "warning", "info")
        },
    } == snapshot
