import os
os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest
from app.services.resume.hallucination_guard import check_no_unprompted_numbers


def test_passes_when_numbers_match():
    original = "Improved API latency by 30%"
    rewritten = "Reduced API latency by 30% via caching layer"
    check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_raises_when_new_number_introduced():
    original = "Built a thing"
    rewritten = "Built a thing serving 5M users"
    from app.services.resume.hallucination_guard import HallucinationError
    with pytest.raises(HallucinationError):
        check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_allows_placeholders():
    original = "Built a thing"
    rewritten = "Built a thing serving [N users]"
    check_no_unprompted_numbers(original=original, rewritten=rewritten,
                                placeholders=[{"token": "[N users]", "what": "scale"}])


def test_raises_on_scientific_notation():
    """Rewrite that introduces a scientific-notation number should raise."""
    from app.services.resume.hallucination_guard import HallucinationError
    original = "Built thing"
    rewritten = "Built thing serving 1e6 users"
    with pytest.raises(HallucinationError):
        check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_raises_on_x_multiplier():
    """Rewrite that introduces an x-multiplier number should raise."""
    from app.services.resume.hallucination_guard import HallucinationError
    original = "Improved latency"
    rewritten = "Improved latency 10x"
    with pytest.raises(HallucinationError):
        check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])


def test_allows_x_when_in_original():
    """When the x-multiplier value already appears in the original, no raise expected."""
    original = "10x faster than before"
    rewritten = "Achieved 10x speedup in response time"
    # Should NOT raise because "10x" is already in the original
    check_no_unprompted_numbers(original=original, rewritten=rewritten, placeholders=[])
