import re
from typing import List


class HallucinationError(Exception):
    pass


_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?[%kKmMbB]?\b")


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
