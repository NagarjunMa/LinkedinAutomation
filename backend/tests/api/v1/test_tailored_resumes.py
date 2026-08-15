import uuid
from unittest.mock import patch


def _seed_tailored_resume(db_session, user_id: str):
    from app.models.jd_evaluation import JDEvaluation
    from app.models.resume_document import ResumeDocument, ResumeVersion
    from app.models.user import User
    from tests.fixtures.resume_doc_json import make_resume

    if db_session.query(User).filter(User.user_id == user_id).first() is None:
        db_session.add(User(user_id=user_id, email=f"{user_id}@example.com"))
        db_session.commit()

    doc_json = make_resume()
    doc_id = str(uuid.uuid4())
    doc = ResumeDocument(
        id=doc_id,
        user_id=user_id,
        original_filename="base.pdf",
        file_path="/tmp/base.pdf",
        storage_path="/tmp/base.pdf",
        file_type="pdf",
        parsed_json=doc_json.model_dump(),
        raw_text=doc_json.raw_text,
    )
    db_session.add(doc)
    db_session.commit()

    jd_id = str(uuid.uuid4())
    extracted = {
        "must_have": [],
        "good_to_have": [],
        "soft_skills": [],
        "seniority": "senior",
        "primary_role_category": "SWE",
        "country_hint": "US",
        "red_flags": [],
        "company_name": "Acme",
        "job_title": "Senior Backend Engineer",
    }
    jd = JDEvaluation(
        id=jd_id,
        user_id=user_id,
        resume_document_id=doc_id,
        jd_text="Senior backend engineer role at Acme.",
        extracted_requirements=extracted,
        diff_plan={
            "match_score": 82,
            "must_have_coverage_found": [],
            "must_have_coverage_missing": [],
            "good_to_have_coverage_found": [],
            "good_to_have_coverage_missing": [],
            "bullets": [],
            "skills_reorder": None,
            "summary_rewrite": None,
            "suggested_additions": [],
        },
        match_score=82,
    )
    db_session.add(jd)
    db_session.commit()

    version_id = str(uuid.uuid4())
    change_set = [{"type": "bullet_update", "bullet_id": "b1", "new_text": "Edited pointer."}]
    version = ResumeVersion(
        id=version_id,
        resume_document_id=doc_id,
        parent_version_id=None,
        change_set=change_set,
        parsed_json=doc_json.model_dump(),
        jd_evaluation_id=jd_id,
        template_id="us-swe",
        company_name="Acme",
        target_role_title="Senior Backend Engineer",
        role_category="SWE",
        seniority="senior",
        country_hint="US",
        match_score=82,
        source_jd_text=jd.jd_text,
    )
    db_session.add(version)
    db_session.commit()
    return version


def test_tailored_resume_list_and_detail_are_user_scoped(
    client, auth_headers, db_session, test_user_id
):
    version = _seed_tailored_resume(db_session, test_user_id)
    _seed_tailored_resume(db_session, "other-user")

    list_resp = client.get("/api/v1/tailored-resumes", headers=auth_headers)
    assert list_resp.status_code == 200, list_resp.text
    rows = list_resp.json()
    assert len(rows) == 1
    assert rows[0]["version_id"] == version.id
    assert rows[0]["company_name"] == "Acme"
    assert rows[0]["target_role_title"] == "Senior Backend Engineer"
    assert rows[0]["accepted_change_count"] == 1

    detail_resp = client.get(f"/api/v1/tailored-resumes/{version.id}", headers=auth_headers)
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert detail["resume_json"]["contact"]["name"]
    assert detail["source_jd_text"] == "Senior backend engineer role at Acme."
    assert detail["extracted_requirements"]["company_name"] == "Acme"
    assert detail["accepted_changes"][0]["new_text"] == "Edited pointer."


def test_tailored_resume_download_renders_json_debits_and_does_not_store_pdf(
    client, auth_headers, db_session, test_user_id, user_with_credits
):
    from app.models.resume_export import ResumeExport
    from app.services.credits.ledger import get_balance

    version = _seed_tailored_resume(db_session, test_user_id)
    before = get_balance(db_session, test_user_id)

    with patch(
        "app.application.tailored_resume_service.render_pdf_from_doc",
        return_value=b"%PDF-tailored",
    ), patch(
        "app.application.tailored_resume_service.get_pdf_page_count",
        return_value=1,
    ):
        resp = client.post(
            f"/api/v1/tailored-resumes/{version.id}/download",
            json={"template_id": "us-swe", "filename": "acme.pdf"},
            headers=auth_headers,
        )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.headers["x-resume-page-count"] == "1"
    assert resp.content == b"%PDF-tailored"
    assert get_balance(db_session, test_user_id) == before - 1

    export = (
        db_session.query(ResumeExport)
        .filter(ResumeExport.resume_version_id == version.id)
        .one()
    )
    assert export.storage_path is None
    assert export.status == "succeeded"
    assert export.file_size_bytes == len(b"%PDF-tailored")


def test_tailored_resume_download_refunds_on_blank_pdf(
    client, auth_headers, db_session, test_user_id, user_with_credits
):
    from app.models.resume_export import ResumeExport
    from app.services.credits.ledger import get_balance
    from app.services.pdf.renderer import BlankPdfError

    version = _seed_tailored_resume(db_session, test_user_id)
    before = get_balance(db_session, test_user_id)

    with patch(
        "app.application.tailored_resume_service.render_pdf_from_doc",
        side_effect=BlankPdfError("blank output"),
    ):
        resp = client.post(
            f"/api/v1/tailored-resumes/{version.id}/download",
            json={"template_id": "us-swe", "filename": "acme.pdf"},
            headers=auth_headers,
        )

    assert resp.status_code == 500
    assert "blank" in resp.json()["detail"].lower()
    assert get_balance(db_session, test_user_id) == before
    export = (
        db_session.query(ResumeExport)
        .filter(ResumeExport.resume_version_id == version.id)
        .one()
    )
    assert export.status == "errored"
    assert export.storage_path is None
    assert "blank" in export.error_message
