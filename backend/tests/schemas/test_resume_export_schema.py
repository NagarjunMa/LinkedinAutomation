import pytest
from pydantic import ValidationError


def test_export_request_accepts_known_country_and_role():
    from app.schemas.resume_export import ExportRequest
    r = ExportRequest(
        resume_document_id="doc-1",
        country="US",
        role_template="swe",
    )
    assert r.country == "US"
    assert r.role_template == "swe"
    assert r.resume_version_id is None


def test_export_request_rejects_unknown_country():
    from app.schemas.resume_export import ExportRequest
    with pytest.raises(ValidationError):
        ExportRequest(resume_document_id="doc-1", country="UK", role_template="swe")


def test_export_request_rejects_unknown_role():
    from app.schemas.resume_export import ExportRequest
    with pytest.raises(ValidationError):
        ExportRequest(resume_document_id="doc-1", country="US", role_template="designer")


def test_export_response_shape():
    from app.schemas.resume_export import ExportResponse
    r = ExportResponse(
        export_id="exp-1",
        download_url="https://x/y.pdf",
        expires_at="2026-05-27T00:00:00Z",
        country="IN",
        role_template="ds",
    )
    assert r.export_id == "exp-1"
