def test_resume_export_columns():
    from app.models.resume_export import ResumeExport
    cols = {c.name for c in ResumeExport.__table__.columns}
    assert cols >= {
        "id", "user_id", "resume_document_id", "resume_version_id",
        "country", "role_template", "storage_path", "status",
        "render_ms", "file_size_bytes", "error_message", "created_at",
    }
