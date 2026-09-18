import subprocess
import pytest
from scripts.benchmark_anydoc import CORPUS, canonical, grade, run


def test_independent_fields_and_order_do_not_reward_missing_content():
    case = {"fields": {"contact.name": "Example", "experience.0.company": "Acme"},
            "order": ["Experience", "Education"]}
    result = grade({"contact": {"name": "Example"}, "raw_text": "Education Experience"}, case)
    assert result == {"fields": {"contact.name": True, "experience.0.company": False},
                      "reading_order": False, "text_values_found": 0}


def test_correct_order_and_literal_content():
    assert grade({"raw_text": "Example Experience Education"},
                 {"fields": {"contact.name": "Example"}, "order": ["Experience", "Education"]}) == {
        "fields": {"contact.name": False}, "reading_order": True, "text_values_found": 1}


def test_hash_normalization_preserves_claims_but_excludes_generated_ids():
    assert canonical({"id": "random", "bullets": [{"id": "random", "text": "Truth"}]}) == {
        "bullets": [{"text": "Truth"}]}


@pytest.mark.parametrize("filename,status", [("malformed.pdf", "PdfminerException"),
    ("unsafe.docx", "ResumeFileError"), ("over-page-limit.pdf", "ResumeFileComplexityError")])
def test_real_worker_rejects_unsafe_corpus(filename, status):
    result = run("existing", CORPUS / filename)
    assert result["status"] == status
    assert "document" not in result


def test_timeout_and_credential_isolation(monkeypatch):
    def timeout(command, **kwargs):
        assert kwargs["env"].get("PRIVATE_TEST_SECRET") is None
        assert kwargs["env"]["OPENAI_API_KEY"] == "test"
        assert kwargs["timeout"] == 0.01
        raise subprocess.TimeoutExpired(command, 0.01)
    monkeypatch.setenv("PRIVATE_TEST_SECRET", "must-not-inherit")
    monkeypatch.setattr(subprocess, "run", timeout)
    assert run("existing", CORPUS / "simple.pdf", 0.01)["status"] == "timeout"
