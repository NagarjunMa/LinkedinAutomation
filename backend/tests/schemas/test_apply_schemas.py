import pytest
from pydantic import ValidationError
from app.schemas.resume_v2 import ApplyTailorRequest, ApplyTailorResponse, ChangeItem


def test_apply_request_accepts_changes_with_optional_template():
    req = ApplyTailorRequest(
        accepted_changes=[ChangeItem(type="bullet_update", bullet_id="b1", new_text="x")],
        template_id="us-swe",
    )
    assert req.template_id == "us-swe"


def test_apply_request_template_id_optional():
    req = ApplyTailorRequest(
        accepted_changes=[ChangeItem(type="bullet_update", bullet_id="b1", new_text="x")],
    )
    assert req.template_id is None


def test_apply_response_minimal():
    resp = ApplyTailorResponse(
        version_id="v1",
        preview_html="<html>...</html>",
        company_name="Stripe",
        suggested_template="us-swe",
        filename_hint="test-user-stripe.pdf",
    )
    assert resp.warning is None


def test_apply_response_with_warning():
    resp = ApplyTailorResponse(
        version_id="v1",
        preview_html="",
        company_name=None,
        suggested_template="us-swe",
        filename_hint="test-user-resume.pdf",
        warning="Preview unavailable",
    )
    assert resp.preview_html == ""
    assert resp.warning == "Preview unavailable"
