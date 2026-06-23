"""Hallucination guard for resume bullet rewrites.

This module detects when a rewritten bullet introduces numeric quantities that
were not present in the original text, which is a strong signal that the LLM
fabricated metrics.

Known limitation — written-number bypass:
    Numbers spelled out as words (e.g. "fifty percent", "a million users") are
    NOT caught by the regex here.  The LLM system prompts (evaluator, tailor,
    rewriter) include explicit instructions forbidding written-out numbers, so
    the primary defence for that class of hallucination must live at the prompt
    level rather than in this post-hoc regex check.
"""
import re
from typing import Iterable, List


class HallucinationError(Exception):
    pass


# Matches numeric tokens including:
#   - plain integers and decimals:  42, 3.14, 1,000
#   - scientific notation:          1e6, 2.5e7, 3E-2
#   - common metric suffixes:       5k, 10M, 2B, 30%
#   - multiplier suffix:            3x, 10X
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?(?:[eE][+-]?\d+)?[%xXkKmMbB]?\b")


def _extract_numbers(text: str) -> set:
    return set(m.group(0) for m in _NUMBER_RE.finditer(text))


def _contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def check_no_unprompted_numbers(
    original: str,
    rewritten: str,
    placeholders: List[dict],
) -> None:
    """Raise HallucinationError if rewritten introduces digits not in original
    and not protected by a placeholder token."""
    # Remove placeholder tokens from rewritten before number extraction.
    redacted = rewritten
    for ph in placeholders:
        redacted = redacted.replace(ph["token"], "")
    orig_nums = _extract_numbers(original)
    new_nums = _extract_numbers(redacted)
    leaked = new_nums - orig_nums
    if leaked:
        raise HallucinationError(
            f"Rewritten bullet introduced numbers not in original: {sorted(leaked)}"
        )


def analyze_rewrite_truth(
    *,
    original: str,
    rewritten: str,
    placeholders: List[dict],
    jd_skill_terms: Iterable[str] = (),
    resume_supported_skill_terms: Iterable[str] = (),
) -> dict:
    """Return truth-check metadata or raise on unsupported claims.

    This intentionally stays conservative. It proves only the things the app can
    verify cheaply at rewrite time: numeric claims and explicit JD skill names.
    Unsupported broader claims still rely on the LLM prompt and user review.
    """
    check_no_unprompted_numbers(
        original=original,
        rewritten=rewritten,
        placeholders=placeholders,
    )

    redacted = rewritten
    placeholder_tokens: list[str] = []
    for ph in placeholders:
        token = ph["token"]
        placeholder_tokens.append(token)
        redacted = redacted.replace(token, "")

    orig_nums = _extract_numbers(original)
    new_nums = _extract_numbers(redacted)
    verified_numbers = sorted(new_nums & orig_nums)
    numeric_claims = "placeholder_used" if placeholder_tokens else "verified"

    supported = {term for term in resume_supported_skill_terms if term}
    introduced_skills = [
        term
        for term in jd_skill_terms
        if term and _contains_phrase(rewritten, term) and not _contains_phrase(original, term)
    ]
    unsupported_skills = [
        term
        for term in introduced_skills
        if not any(_contains_phrase(supported_term, term) for supported_term in supported)
    ]
    if unsupported_skills:
        raise HallucinationError(
            f"Rewritten bullet introduced unsupported JD skills: {sorted(set(unsupported_skills))}"
        )

    return {
        "numeric_claims": numeric_claims,
        "new_skill_status": "resume_supported" if introduced_skills else "none",
        "unsupported_claims": [],
        "placeholders_used": placeholder_tokens,
        "source_evidence": [original] if original else [],
        "verified_numbers": verified_numbers,
        "verified_skills": sorted(set(introduced_skills)),
    }
