"""Literal matching shared by evidence-backed career views."""

import re

BULLET_PREFIX = re.compile(r"^[•*-]\s+")
CONTRIBUTION_CATEGORIES = {"action", "outcome", "decision", "validation"}
_EXPLICIT_SKILL_USE = re.compile(r"^(?:i )?used (.{1,50}?) to \S")


def normalized_phrase(text: str) -> str:
    return " ".join(BULLET_PREFIX.sub("", text.strip()).casefold().split()).rstrip(".!?")


def applied_skill(claim: str) -> str:
    # shortcut: require a direct "Used <skill> to ..." claim until the ledger stores applied skill links.
    match = _EXPLICIT_SKILL_USE.match(normalized_phrase(claim))
    return match[1] if match is not None else ""
