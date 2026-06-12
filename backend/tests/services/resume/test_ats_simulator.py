from pathlib import Path
import fitz
from app.services.resume.ats_simulator import simulate_ats

PDF = Path(__file__).parent.parent.parent / "fixtures/resumes/simple.pdf"
TABLE_PDF = Path(__file__).parent.parent.parent / "fixtures/resumes/with_table.pdf"


def test_ats_simulator_returns_score_and_raw_text():
    with PDF.open("rb") as f:
        result = simulate_ats(f.read(), filename="simple.pdf")
    assert 0 <= result.parseability_score <= 100
    assert "Acme" in result.raw_text
    assert isinstance(result.format_issues, list)


def test_ats_simulator_penalizes_tables():
    with TABLE_PDF.open("rb") as f:
        result = simulate_ats(f.read(), filename="with_table.pdf")
    assert result.parseability_score < 90
    assert any(i.type == "table" for i in result.format_issues)


def _pdf_with_lines(lines: list[tuple[float, float, str]]) -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for x, y, text in lines:
        page.insert_text((x, y), text, fontsize=10)
    return doc.tobytes()


def test_ats_simulator_does_not_flag_single_column_text_spanning_page_halves():
    content = _pdf_with_lines([
        (
            72,
            72 + i * 18,
            "Built backend automation systems using Python FastAPI AWS Terraform Docker and PostgreSQL "
            "for production engineering workflows.",
        )
        for i in range(12)
    ])

    result = simulate_ats(content, filename="single-column.pdf")

    assert result.parseability_score == 100
    assert not any(issue.type == "multi_column" for issue in result.format_issues)


def test_ats_simulator_flags_true_two_column_layout():
    lines: list[tuple[float, float, str]] = []
    for i in range(12):
        y = 72 + i * 18
        lines.append((72, y, "Built APIs with Python and FastAPI"))
        lines.append((340, y, "Managed AWS Terraform Docker systems"))
    content = _pdf_with_lines(lines)

    result = simulate_ats(content, filename="two-column.pdf")

    assert result.parseability_score == 80
    assert any(issue.type == "multi_column" for issue in result.format_issues)
