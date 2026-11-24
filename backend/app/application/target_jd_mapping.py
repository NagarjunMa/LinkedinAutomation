"""Deterministic projection of a saved JD extraction onto an owned target."""

import json
import re
from collections.abc import Iterable
from hashlib import sha256
from typing import NamedTuple

from app.application.errors import InvalidOperationError
from app.application.evidence_terms import BULLET_PREFIX, normalized_phrase
from app.application.target_coverage import project_target_resume_coverage
from app.schemas.career.evidence import CareerEvidenceItem
from app.schemas.career.jd_mapping import (
    JDRequirementMapping, JDRequirementRef, RequirementPriority, RequirementReason,
    RequirementState, TargetJDMapping,
)
from app.schemas.career.sources import CareerTarget
from app.schemas.career.target_coverage import TargetFocusCoverage
from app.schemas.jd import JDExtraction, Requirement
from app.schemas.resume_v2 import ResumeDocumentJSON

_CONDITIONAL = r"(?:unless|alternatively|provided that|subject to|in lieu of)\b"
_NON_AFFIRMATIVE = re.compile(
    rf"[?？]|(?<!\S)/|\b{_CONDITIONAL}|\b(?:no|not|never|without|either|or|whether|if|cannot|exclude[ds]?|except)\b|"
    r"\b\w+n['’]t\b|\b(?:one|any|some) of\b|"
    r"\b(?:choose|select|pick) (?:\d+|one|two|three|any)\b",
    re.I,
)
_REQUIREMENT_LINE = re.compile(
    r"^(?:at least|minimum|\d+\s*\+?\s*(?:years?|months?)|must|have to|require[ds]?|requirements?|"
    r"preferred|need(?:ed)?|experience (?:with|using|in)|proficiency in|knowledge of|certification|"
    r"degree)\b"
)
_WRAPPED_PREFIX = re.compile(r"\b(?:of|in|with|using|require|need|include)$", re.I)
_WRAPPED_SUFFIX = re.compile(
    rf"^(?:/|{_CONDITIONAL}|(?:is|are|was|were|and|or|with|without|not|for|if|except)\b|\w+n['’]t\b)", re.I,
)
_NEW_SENTENCE = re.compile(r"^and (?:you|we|candidates?|applicants?|the)\b", re.I)
_GENERIC_HEADINGS = {
    "skills", "technical skills", "required skills", "preferred skills", "requirements",
    "minimum requirements", "qualifications", "required qualifications", "minimum qualifications",
    "preferred qualifications", "must have", "good to have", "nice to have",
}
_MAX_REQUIREMENTS = 80
_MAX_SKILL_LABEL_LENGTH = 200


class _SourceContext(NamedTuple):
    start: int
    end: int
    line: str
    preceding: tuple[str, ...]
    continuation: str


def project_target_jd_mapping(
    target: CareerTarget, evidence: Iterable[CareerEvidenceItem], *,
    evaluation_id: str, jd_text: str, jd_text_sha256: str, extraction: JDExtraction,
    resume_document_id: str, resume: ResumeDocumentJSON | None,
) -> TargetJDMapping:
    groups: tuple[tuple[RequirementPriority, list[Requirement]], ...] = (
        ("must_have", extraction.must_have), ("preferred", extraction.good_to_have),
    )
    if sum(len(requirements) for _, requirements in groups) > _MAX_REQUIREMENTS:
        raise InvalidOperationError("Saved job analysis has too many requirements")

    # Saved extractions can mistake a short job description for a requirement label.
    full_description = normalized_phrase(jd_text) if len(jd_text) >= 50 else ""
    entries = []
    for priority, requirements in groups:
        for index, requirement in enumerate(requirements, 1):
            label = requirement.skill.strip()
            if (
                not label or len(label) > _MAX_SKILL_LABEL_LENGTH or "\x00" in label
                or (full_description and full_description in normalized_phrase(label))
            ):
                raise InvalidOperationError("Saved job analysis has an invalid requirement label")
            entries.append((priority, index, requirement, _source_context(jd_text, requirement)))

    focus = [requirement.skill for _, _, requirement, context in entries if context is not None]
    comparison = project_target_resume_coverage(
        target.model_copy(update={"desired_work": focus}), evidence, resume_document_id, resume,
    )
    covered = {normalized_phrase(item.label): item for item in comparison.coverage.focus}
    missing = {
        normalized_phrase(finding.focus_label)
        for finding in comparison.findings
        if finding.kind == "communication_gap" and finding.focus_label is not None
    }
    return TargetJDMapping(
        schema_version=1, policy_version="jd-mapping-v1", target_id=target.target_id,
        jd_evaluation_id=evaluation_id, jd_source=target.job_description, jd_text_sha256=jd_text_sha256,
        resume_document_id=resume_document_id,
        resume_comparable=not any(item.kind == "document_limit" for item in comparison.findings),
        requirements=[
            _mapping(
                priority, index, requirement, context, jd_text_sha256,
                covered.get(normalized_phrase(requirement.skill)), normalized_phrase(requirement.skill) in missing,
            )
            for priority, index, requirement, context in entries
        ],
    )


def _source_context(jd_text: str, requirement: Requirement) -> _SourceContext | None:
    excerpt = requirement.evidence_from_jd.strip()
    skill = normalized_phrase(requirement.skill)
    if not excerpt or len(excerpt) > 4000 or not skill:
        return None
    start = jd_text.find(excerpt)
    if start == -1 or jd_text.find(excerpt, start + 1) != -1:
        return None
    end = start + len(excerpt)
    # Search against the original text so the quote cannot hide an adjacent character.
    term = r"\s+".join(re.escape(word) for word in skill.split())
    match = re.compile(r"(?<![\w+#.])" + term + r"(?![\w+#]|\.[\w-])", re.I).search(jd_text, start)
    if match is None or match.end() > end:
        return None

    line_start = jd_text.rfind("\n", 0, start) + 1
    line_end = jd_text.find("\n", end)
    line = jd_text[line_start:line_end if line_end != -1 else len(jd_text)]
    preceding = _preceding_context(line, jd_text[:line_start])
    continuation = _following_context(line, jd_text[line_end + 1:]) if line_end != -1 else ""
    return _SourceContext(start, end, line, preceding, continuation)


def _indentation(line: str) -> int:
    return len(line) - len(line.lstrip())


def _preceding_context(line: str, preceding: str) -> tuple[str, ...]:
    indentation = _indentation(line)
    is_list_item = bool(BULLET_PREFIX.match(line.strip()))
    same_block = True
    inside_section = False
    scopes = []
    for raw in reversed(preceding.splitlines()):
        text = raw.strip()
        if not text:
            same_block = False
            continue

        previous_indentation = _indentation(raw)
        if BULLET_PREFIX.match(text):
            # A shallower list item can introduce its descendants. Peers are independent.
            if previous_indentation < indentation:
                scopes.append(BULLET_PREFIX.sub("", text))
                indentation = previous_indentation
                inside_section = False
            continue
        if previous_indentation > indentation or (inside_section and previous_indentation == indentation):
            continue

        if text.endswith(":") or text.startswith("#") or (is_list_item and same_block):
            scopes.append(text.lstrip("#").strip())
            if previous_indentation == 0:
                break
            indentation = previous_indentation
            inside_section = True
            continue
        if _NON_AFFIRMATIVE.search(text) or (same_block and _WRAPPED_PREFIX.search(text)):
            scopes.append(text)
    return tuple(scopes)


def _following_context(line: str, following: str) -> str:
    parts = []
    indentation = _indentation(line)
    paragraph_break = False
    for raw in following.splitlines():
        text = raw.strip()
        if not text:
            paragraph_break = True
            continue

        # Indented content is part of the requirement across blanks and subheadings.
        if _indentation(raw) > indentation:
            parts.append(text)
            paragraph_break = False
            continue
        if paragraph_break or text.startswith("#") or BULLET_PREFIX.match(text):
            break

        suffix = text.lstrip("([—– \t")
        if not _WRAPPED_SUFFIX.match(suffix):
            break
        if line.rstrip().endswith((".", "!", "?")) and _NEW_SENTENCE.match(suffix):
            break
        parts.append(text)
    return " ".join(parts)


def _mapping(
    priority: RequirementPriority, index: int, entry: Requirement,
    context: _SourceContext | None, jd_text_sha256: str,
    coverage: TargetFocusCoverage | None, resume_gap: bool,
) -> JDRequirementMapping:
    requirement_id = f"{priority}-{index}"
    revision = sha256(json.dumps(
        [jd_text_sha256, requirement_id, entry.skill, entry.type, entry.evidence_from_jd],
        ensure_ascii=True, separators=(",", ":"),
    ).encode()).hexdigest()
    state, reason, follow_up = _classify(entry, context, coverage, resume_gap)
    return JDRequirementMapping(
        requirement=JDRequirementRef(
            requirement_id=requirement_id, revision=revision,
            source_start=context.start if context else None, source_end=context.end if context else None,
        ),
        priority=priority, kind=entry.type, state=state, reason_code=reason,
        evidence=coverage.evidence if coverage and state != "unresolved" else None, follow_up=follow_up,
    )


def _classify(
    entry: Requirement, context: _SourceContext | None,
    coverage: TargetFocusCoverage | None, resume_gap: bool,
) -> tuple[RequirementState, RequirementReason, str | None]:
    if context is None or coverage is None:
        return "unresolved", "requirement_not_grounded", None
    if any(_NON_AFFIRMATIVE.search(part) for part in (context.line, *context.preceding, context.continuation)):
        return "unresolved", "requirement_not_affirmative", None

    skill = normalized_phrase(entry.skill)
    line = normalized_phrase(context.line)
    headings = [normalized_phrase(text.rstrip(":").replace("-", " ")) for text in context.preceding]
    simple_line = line in {skill, f"{skill} required", f"experience with {skill}", f"proficiency in {skill}"}
    generic_heading = all(not heading or heading in _GENERIC_HEADINGS for heading in headings)
    heading_cue = any(
        _REQUIREMENT_LINE.search(heading)
        or any(cue in heading for cue in ("experience with", "proficiency in", "years of", "months of"))
        for heading in headings
    )
    if line == skill and not (generic_heading or heading_cue):
        return "unresolved", "requirement_not_affirmative", None
    skill_tail = line.removeprefix(skill + " ") if line.startswith(skill + " ") else ""
    if not (simple_line or _REQUIREMENT_LINE.match(line) or _REQUIREMENT_LINE.match(skill_tail)):
        return "unresolved", "requirement_not_affirmative", None
    # shortcut: qualify only complete literal skill lines until JD constraints are structured.
    simple = entry.type == "technical" and simple_line and generic_heading and not context.continuation
    if not simple:
        question = "What evidence can you cite for the specific qualification or scope this requirement asks for?"
        if coverage.state == "supported":
            return "partial", "additional_qualification_unverified", question
        return "unresolved", "qualification_unresolved", question
    if coverage.state == "supported" and resume_gap:
        return "communication_gap", "confirmed_application_not_found_in_resume", None
    question = "When have you applied this skill, and what did you personally do?"
    return coverage.state, coverage.reason_code, None if coverage.state == "supported" else question
