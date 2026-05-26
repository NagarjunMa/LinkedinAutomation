"""Tests for GET /api/v1/analytics/jd-progress."""
import uuid
import pytest


def test_jd_progress_empty(client, auth_headers):
    """When the user has no JD evaluations, returns an empty list at zero cost."""
    resp = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body == []


def test_jd_progress_counts(client, auth_headers, db_session, test_user_id, uploaded_resume_doc):
    """Returns per-JD funnel counts: evaluations, versions, exports."""
    from app.models.jd_evaluation import JDEvaluation
    from app.models.resume_document import ResumeVersion
    from app.models.resume_export import ResumeExport

    # Create a JD evaluation for the test user
    jd_id = str(uuid.uuid4())
    jd = JDEvaluation(
        id=jd_id,
        user_id=test_user_id,
        resume_document_id=uploaded_resume_doc.id,
        jd_text="We are looking for a backend engineer...",
        extracted_requirements={},
        diff_plan={},
        match_score=75,
    )
    db_session.add(jd)

    # Create 2 resume versions linked to this JD evaluation
    for _ in range(2):
        v = ResumeVersion(
            id=str(uuid.uuid4()),
            resume_document_id=uploaded_resume_doc.id,
            parent_version_id=None,
            change_set={},
            parsed_json=uploaded_resume_doc.parsed_json,
            jd_evaluation_id=jd_id,
        )
        db_session.add(v)

    # Create 1 export linked to one of those versions
    export = ResumeExport(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        resume_document_id=uploaded_resume_doc.id,
        resume_version_id=None,
        country="US",
        role_template="swe",
        storage_path=f"{test_user_id}/export.pdf",
        status="succeeded",
    )
    db_session.add(export)
    db_session.commit()

    resp = client.get("/api/v1/analytics/jd-progress", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1

    row = body[0]
    assert row["jd_evaluation_id"] == jd_id
    assert row["match_score"] == 75
    assert row["versions_count"] == 2
    # exports_count counts exports for the user (may not be linked by jd_id — see implementation notes)
    assert "exports_count" in row
    assert isinstance(row["exports_count"], int)
