import pytest
from pathlib import Path
from app.services.resume.parser import parse_resume

FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"
DOCX_FIXTURE = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.docx"


def test_parser_pdf_returns_resume_document_json():
    with FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.pdf")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert doc.experience[0].company.lower().startswith("acme")
    assert len(doc.experience[0].bullets) == 2
    # Bullet IDs are stable & non-empty
    assert all(b.id for b in doc.experience[0].bullets)
    # raw_text populated
    assert "Acme" in doc.raw_text


def test_parser_docx_returns_resume_document_json():
    with DOCX_FIXTURE.open("rb") as f:
        doc = parse_resume(f.read(), filename="simple.docx")
    assert doc.contact.name == "Test User"
    assert len(doc.experience) >= 1
    assert len(doc.experience[0].bullets) == 2
