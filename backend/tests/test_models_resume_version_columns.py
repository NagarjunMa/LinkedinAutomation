def test_resume_version_has_jd_link_columns():
    from app.models.resume_document import ResumeVersion
    cols = {c.name for c in ResumeVersion.__table__.columns}
    assert "jd_evaluation_id" in cols
    assert "accepted_at" in cols
    assert "template_id" in cols
