def test_resume_version_has_jd_link_columns():
    from app.models.resume_document import ResumeVersion
    cols = {c.name for c in ResumeVersion.__table__.columns}
    assert "jd_evaluation_id" in cols
    assert "accepted_at" in cols
    assert "template_id" in cols
    assert "company_name" in cols
    assert "target_role_title" in cols
    assert "role_category" in cols
    assert "seniority" in cols
    assert "country_hint" in cols
    assert "match_score" in cols
    assert "source_jd_text" in cols
