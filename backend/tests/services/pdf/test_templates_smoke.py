"""Smoke tests for the locked, recruiter-readable PDF templates."""
from io import BytesIO

import pytest
from pypdf import PdfReader
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
    """Each template renders a visible one-page baseline resume."""
    from app.services.pdf.renderer import get_pdf_page_count, render_pdf_from_doc

    pdf = render_pdf_from_doc(make_resume(), country=country, role=role)
    assert pdf.startswith(b"%PDF-"), f"{country}/{role} did not produce a PDF magic header"
    assert len(pdf) > 2000, f"{country}/{role} PDF suspiciously small ({len(pdf)} bytes)"
    assert get_pdf_page_count(pdf) == 1


@pytest.mark.parametrize(
    ("country", "role", "width", "height"),
    [
        ("US", "swe", 612, 792),
        ("IN", "swe", 595, 842),
    ],
)
def test_template_uses_the_expected_page_size(country, role, width, height):
    """US exports use Letter while Indian exports use A4 without browser scaling."""
    from app.services.pdf.renderer import render_pdf_from_doc

    pdf = render_pdf_from_doc(make_resume(), country=country, role=role)
    page = PdfReader(BytesIO(pdf)).pages[0]

    assert round(float(page.mediabox.width)) == width
    assert round(float(page.mediabox.height)) == height


def test_template_embeds_a_supported_sans_font_family():
    """Exports use the locked sans profile or the platform's approved fallback."""
    from app.services.pdf.renderer import render_pdf_from_doc

    pdf = render_pdf_from_doc(make_resume(), country="US", role="swe")
    page = PdfReader(BytesIO(pdf)).pages[0]
    fonts = page["/Resources"]["/Font"]
    font_names = {
        str(font.get_object().get("/BaseFont", "")).lower()
        for font in fonts.values()
    }

    assert any(
        family in name
        for name in font_names
        for family in ("liberationsans", "arial")
    ), font_names
