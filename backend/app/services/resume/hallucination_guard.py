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
from typing import List


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
