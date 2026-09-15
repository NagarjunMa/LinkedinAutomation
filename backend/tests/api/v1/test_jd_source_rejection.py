"""Reject untrusted tailoring output before API display or evaluation storage."""

import pytest

from app.core.openai_client import ModelRuntime, get_model_runtime
from app.models.jd_evaluation import JDEvaluation
from app.schemas.jd import BulletDiff
from app.services.credits.ledger import get_balance
from tests.api.v1.test_error_contracts import assert_envelope
from tests.core.test_model_manifests import fake_provider, jd_fixture, plan_fixture, response


def test_unknown_model_bullet_is_rejected_and_refunded(
    client, auth_headers, uploaded_resume_doc, user_with_credits, db_session, caplog,
):
    plan = plan_fixture()
    plan.bullets = [BulletDiff(bullet_id="private-sentinel", old="9000 users",
                              new="9000 users", reason="private-sentinel")]
    fake, call = fake_provider(None)
    call.side_effect = [response(parsed=jd_fixture()), response(parsed=plan)]
    client.app.dependency_overrides[get_model_runtime] = lambda: ModelRuntime(client_factory=lambda: fake)
    before = get_balance(db_session, user_with_credits)
    try:
        result = client.post("/api/v1/jd/analyze", headers=auth_headers, json={
            "resume_document_id": uploaded_resume_doc.id,
            "jd_text": "Synthetic role: develop and maintain reliable Python services.",
        })
        assert_envelope(result, 422, "invalid_request")
        assert "private-sentinel" not in caplog.text
        assert db_session.query(JDEvaluation).count() == 0
        assert get_balance(db_session, user_with_credits) == before
        assert call.await_count == 2  # One extraction, one rejected tailoring call.
    finally:
        client.app.dependency_overrides.pop(get_model_runtime, None)


@pytest.mark.parametrize("returned_id", ["private-sentinel", "b2"])
def test_regeneration_rejects_wrong_model_target_without_mutating_evaluation(
    client, auth_headers, uploaded_resume_doc, user_with_credits, db_session, returned_id,
):
    original = uploaded_resume_doc.parsed_json["experience"][0]["bullets"][0]["text"]
    fake, call = fake_provider(None)
    call.side_effect = [response(parsed=jd_fixture()), response(parsed=plan_fixture()), response(parsed=BulletDiff(
        bullet_id=returned_id, old=original, new=original, reason="private-sentinel",
    ))]
    client.app.dependency_overrides[get_model_runtime] = lambda: ModelRuntime(client_factory=lambda: fake)
    try:
        analysis = client.post("/api/v1/jd/analyze", headers=auth_headers, json={
            "resume_document_id": uploaded_resume_doc.id,
            "jd_text": "Synthetic role: develop and maintain reliable Python services.",
        })
        assert analysis.status_code == 200
        evaluation_id = analysis.json()["jd_evaluation_id"]
        before = db_session.get(JDEvaluation, evaluation_id).diff_plan
        result = client.post(f"/api/v1/jd/{evaluation_id}/bullets/b1/options", headers=auth_headers)
        assert_envelope(result, 422, "invalid_request")
        db_session.expire_all()
        assert db_session.get(JDEvaluation, evaluation_id).diff_plan == before
        assert call.await_count == 3
    finally:
        client.app.dependency_overrides.pop(get_model_runtime, None)
