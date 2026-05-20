from pathlib import Path
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
