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


@pytest.mark.parametrize("country,role", [
    ("US", "swe"),
    ("US", "ds"),
    ("US", "pm"),
    ("IN", "swe"),
    ("IN", "ds"),
    ("IN", "pm"),
])
def test_canonical_exports_do_not_trigger_false_table_warnings(country, role):
    """Section divider rules must not be treated as ATS-risk tables."""
    from app.services.pdf.renderer import render_pdf_from_doc
    from app.services.resume.ats_simulator import simulate_ats

    pdf = render_pdf_from_doc(make_resume(), country=country, role=role)
    result = simulate_ats(pdf, filename="generated-resume.pdf")

    assert result.parseability_score == 100
    assert not any(issue.type == "table" for issue in result.format_issues)
    assert not any(issue.type == "multi_column" for issue in result.format_issues)


def test_canonical_export_keeps_contact_links_clickable():
    """Exported portfolio links must remain real PDF links, not plain text."""
    from app.services.pdf.renderer import render_pdf_from_doc

    pdf = render_pdf_from_doc(make_resume(), country="US", role="swe")
    page = PdfReader(BytesIO(pdf)).pages[0]
    annotations = page.get("/Annots", [])
    uris = {
        str(annotation.get_object()["/A"].get("/URI"))
        for annotation in annotations
        if annotation.get_object().get("/A")
        and annotation.get_object()["/A"].get("/URI")
    }

    assert "https://github.com/janedoe" in uris


def test_canonical_template_does_not_repeat_generic_project_heading():
    from app.schemas.resume_v2 import Bullet, ProjectEntry
    from app.services.pdf.template_engine import render_html_only

    doc = make_resume()
    doc.projects = [
        ProjectEntry(
            name="Projects",
            bullets=[Bullet(id="project-1", text="Built a resume parser.", raw_text="Built a resume parser.")],
        )
    ]

    html = render_html_only(doc, country="US", role="swe")

    assert html.count(">Projects<") == 1
    assert "Built a resume parser." in html


def test_canonical_export_can_be_parsed_again_without_losing_sections():
    """A saved Prism Pro export must remain evaluable after a user re-uploads it."""
    from app.services.pdf.renderer import render_pdf_from_doc
    from app.services.resume.parser import parse_resume

    pdf = render_pdf_from_doc(make_resume(), country="US", role="swe")
    parsed = parse_resume(pdf, filename="reuploaded.pdf")

    assert parsed.contact.links == ["https://github.com/janedoe"]
    assert parsed.experience[0].role == "Senior SWE"
    assert parsed.experience[0].company == "Acme"
    assert parsed.experience[0].dates == "2022-2026"
    assert [bullet.text for bullet in parsed.experience[0].bullets] == [
        "Cut p99 latency 38% by rewriting the auth path.",
        "Mentored 4 engineers; 3 promoted within 12 months.",
    ]
    assert parsed.projects[0].name == "OSS lib"
    assert parsed.projects[0].bullets[0].text == "500+ GitHub stars."
    assert parsed.education[0].degree == "BS CS"
    assert parsed.education[0].school == "State U"
    assert parsed.education[0].gpa == "3.8"
