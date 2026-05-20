"""Smoke test — all 6 country/role templates render valid PDFs."""
import pytest
from tests.fixtures.resume_doc_json import make_resume


@pytest.mark.parametrize("country,role", [
    ("US", "swe"),
    ("US", "ds"),
    ("US", "pm"),
    ("IN", "swe"),
    ("IN", "ds"),
    ("IN", "pm"),
])
def test_each_template_renders_valid_pdf(country, role):
    """Each of 6 templates renders a valid PDF with magic header and reasonable size."""
    from app.services.pdf.renderer import render_pdf_from_doc

    pdf = render_pdf_from_doc(make_resume(), country=country, role=role)
    assert pdf.startswith(b"%PDF-"), f"{country}/{role} did not produce a PDF magic header"
    assert len(pdf) > 2000, f"{country}/{role} PDF suspiciously small ({len(pdf)} bytes)"
