"""Deterministic projection of a saved JD extraction onto an owned target."""

import json
import re
from bisect import bisect_right
from collections.abc import Iterable
from hashlib import sha256
from itertools import accumulate
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
_SLASHES = ("/", "／")
_SLASH_PATTERN = f"[{''.join(_SLASHES)}]"
_LIST_PREFIX = re.compile(BULLET_PREFIX.pattern + r"|^(?:\+|\d{1,9}[.)])\s+")
_LITERAL_SLASH_SKILLS = {"a/b testing", "ci/cd", "i/o", "tcp/ip"}
_LEADING_WRAPPERS = " \t*_~`([{"
_TRAILING_WRAPPERS = " \t\r*_~`)]}"
_TERM_WRAPPERS = _LEADING_WRAPPERS + _TRAILING_WRAPPERS
_VERSION_BEFORE_SLASH = re.compile(
    r"(?:with[ \t]+)?(?:versions?[ \t]+)?(?:[<>=!~^≤≥]{1,3}[ \t]*)?v?\d{1,8}"
    r"(?:[.\-–—+][0-9a-z*]{1,12}){0,8}(?:[a-z]{1,6}\d{0,6})?\+?"
    r"(?:[ \t]+(?:lts|\([^()\r\n]{1,40}\)))?"
    rf"[{re.escape(_TERM_WRAPPERS)}]*{_SLASH_PATTERN}",
    re.I,
)
_OPEN_MARKUP = f"[{re.escape(_LEADING_WRAPPERS.lstrip())}]*"
_CONTROL_MARKUP = str.maketrans("", "", "*_~`")
_NON_AFFIRMATIVE = re.compile(
    rf"[?？]|(?<!\S){_OPEN_MARKUP}{_SLASH_PATTERN}|\b{_CONDITIONAL}|"
    r"\b(?:no|not|never|without|either|or|whether|if|cannot|exclude[ds]?|except)\b|"
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
    rf"^(?:{_SLASH_PATTERN}|{_CONDITIONAL}|(?:is|are|was|were|and|or|with|without|not|for|if|except)\b|\w+n['’]t\b)", re.I,
)
_NEW_SENTENCE = re.compile(r"^and (?:you|we|candidates?|applicants?|the)\b", re.I)
_MARKDOWN_HEADING = re.compile(r"(#{1,6})(?:[ \t]+|$)")
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
    markdown_ancestors: tuple[str, ...]
    continuation: str
    slash_alternative: bool


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
    lines = jd_text.splitlines(keepends=True)
    line_ends = tuple(accumulate(map(len, lines)))
    nested_lines = _list_continuations(lines)
    entries = []
    for priority, requirements in groups:
        for index, requirement in enumerate(requirements, 1):
            label = requirement.skill.strip()
            if (
                not label or len(label) > _MAX_SKILL_LABEL_LENGTH or "\x00" in label
                or (full_description and full_description in normalized_phrase(label))
            ):
                raise InvalidOperationError("Saved job analysis has an invalid requirement label")
            context = _source_context(jd_text, requirement, lines, line_ends, nested_lines)
            entries.append((priority, index, requirement, context))

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


def _source_context(
    jd_text: str, requirement: Requirement, lines: list[str], line_ends: tuple[int, ...], nested_lines: set[int],
) -> _SourceContext | None:
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
    term_pattern = re.compile(r"(?<![\w+#.])" + term + r"(?![\w+#]|\.[\w-])", re.I)
    match = term_pattern.search(jd_text, start)
    if match is None or match.end() > end:
        return None

    line_start = jd_text.rfind("\n", 0, start) + 1
    line_end = jd_text.find("\n", end)
    line_end = len(jd_text) if line_end == -1 else line_end
    line = jd_text[line_start:line_end]
    preceding, ancestors = _preceding_context(line, lines, bisect_right(line_ends, line_start), nested_lines)
    continuation = _following_context(line, jd_text[line_end + 1:])
    term_line_start = jd_text.rfind("\n", 0, match.start()) + 1
    term_line_end = jd_text.find("\n", match.end())
    term_line = jd_text[term_line_start:term_line_end if term_line_end != -1 else len(jd_text)]
    previous_line = jd_text[:term_line_start].removesuffix("\n").rsplit("\n", 1)[-1].rstrip(_TRAILING_WRAPPERS)
    term_prefix = _LIST_PREFIX.sub("", term_line[:match.start() - term_line_start].lstrip()).strip(_TERM_WRAPPERS)
    wrapped_slash = (
        (not term_prefix or _WRAPPED_PREFIX.search(term_prefix) is not None)
        and previous_line.endswith(_SLASHES)
        and "://" not in previous_line.rsplit(maxsplit=1)[-1]
    )
    if wrapped_slash and _LIST_PREFIX.match(term_line.strip()):
        marker = _LIST_PREFIX.match(previous_line.strip())
        wrapped_slash = (
            _list_content_indent(previous_line, marker) <= _indentation(term_line)
            if marker else _REQUIREMENT_LINE.match(normalized_phrase(previous_line)) is not None
        )
    canonical_skill = skill.replace("／", "/")
    slash_alternative = (
        ("/" in canonical_skill and canonical_skill not in _LITERAL_SLASH_SKILLS)
        or wrapped_slash
        or _slash_borders_term(term_line, match.start() - term_line_start, match.end() - term_line_start)
        or _VERSION_BEFORE_SLASH.match(continuation.lstrip(_TERM_WRAPPERS)) is not None
        or any(
            _slash_borders_term(part, occurrence.start(), occurrence.end())
            for part in (*preceding, *ancestors, continuation)
            if any(slash in part for slash in _SLASHES)
            for occurrence in term_pattern.finditer(part)
        )
    )
    return _SourceContext(start, end, line, preceding, ancestors, continuation, slash_alternative)


def _slash_borders_term(text: str, start: int, end: int) -> bool:
    # Formatting around the verified term does not change the separator's meaning.
    prefix = text[:start].rstrip(_TERM_WRAPPERS)
    _, separator, cue = prefix.replace("／", "/").rpartition("/")
    if separator:
        cue = normalized_phrase(cue.lstrip(_LEADING_WRAPPERS))
        if not cue or (_REQUIREMENT_LINE.match(cue) and _WRAPPED_PREFIX.search(cue)):
            return True
    suffix = text[end:].lstrip(_TERM_WRAPPERS)
    return suffix.startswith(_SLASHES) or _VERSION_BEFORE_SLASH.match(suffix) is not None


def _indentation(line: str) -> int:
    return len(_leading_whitespace(line).expandtabs(4))


def _leading_whitespace(line: str) -> str:
    return line[:len(line) - len(line.lstrip())]


def _list_content_indent(line: str, marker: re.Match[str]) -> int:
    return len((_leading_whitespace(line) + marker[0]).expandtabs(4))


def _list_continuations(lines: list[str]) -> set[int]:
    # A lightly indented heading can also be inside a list item that ended before the requirement.
    nested = set()
    content_indent = None
    for index, raw in enumerate(lines):
        text = raw.strip()
        if not text:
            continue
        indentation = _indentation(raw)
        if content_indent is not None and indentation >= content_indent:
            nested.add(index)
        else:
            marker = _LIST_PREFIX.match(text)
            content_indent = _list_content_indent(raw, marker) if marker else None
    return nested


def _is_non_affirmative(text: str) -> bool:
    return bool(_NON_AFFIRMATIVE.search(text) or _NON_AFFIRMATIVE.search(text.translate(_CONTROL_MARKUP)))


def _preceding_context(
    line: str, lines: list[str], line_index: int, nested_lines: set[int],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    indentation = _indentation(line)
    is_list_item = bool(_LIST_PREFIX.match(line.strip()))
    same_block = True
    inside_section = False
    plain_scope_closed = False
    markdown_level = 7
    seen_markdown = False
    scopes = []
    ancestors = []
    list_preamble = []
    for index in range(line_index - 1, -1, -1):
        raw = lines[index]
        text = raw.strip()
        if not text:
            same_block = False
            continue

        previous_indentation = _indentation(raw)
        top_level_heading = previous_indentation <= 3 and index not in nested_lines
        if (previous_indentation <= indentation or top_level_heading) and (
            heading := _MARKDOWN_HEADING.match(text)
        ):
            level = len(heading[1])
            # Only progressively shallower Markdown headings can govern this section.
            if level < markdown_level:
                heading_text = text[heading.end():]
                without_closing_hashes = heading_text.rstrip("#")
                if without_closing_hashes.endswith((" ", "\t")):
                    heading_text = without_closing_hashes.rstrip()
                ancestors.extend(list_preamble)
                if not seen_markdown and not plain_scope_closed:
                    scopes.append(heading_text)
                else:
                    ancestors.append(heading_text)
                seen_markdown = True
                markdown_level = level
                indentation = 0 if top_level_heading else min(indentation, previous_indentation)
                inside_section = True
                if top_level_heading:
                    plain_scope_closed = True
                    if level == 1:
                        break
            list_preamble.clear()
            continue
        if plain_scope_closed:
            continue

        if marker := _LIST_PREFIX.match(text):
            # A shallower list item can introduce its descendants. Peers are independent.
            if _list_content_indent(raw, marker) <= indentation:
                ancestors.extend(list_preamble)
                scopes.append(text[marker.end():])
                indentation = previous_indentation
                inside_section = False
                # Nested Markdown headings do not close a section outside their list container.
                markdown_level = 7
            list_preamble.clear()
            continue
        if previous_indentation > indentation:
            continue
        if inside_section and previous_indentation == indentation:
            if seen_markdown and index in nested_lines and _is_non_affirmative(text):
                # An earlier sibling heading can separate this text from the current requirement.
                list_preamble.append(text)
            continue

        if text.endswith(":") or text.startswith("#") or (is_list_item and same_block):
            scopes.append(text.lstrip("#").strip())
            if previous_indentation == 0:
                plain_scope_closed = True
            indentation = previous_indentation
            inside_section = True
            continue
        if _is_non_affirmative(text) or (same_block and _WRAPPED_PREFIX.search(text)):
            scopes.append(text)
    return tuple(scopes), tuple(ancestors)


def _following_context(line: str, following: str) -> str:
    parts = []
    indentation = _indentation(line)
    paragraph_break = False
    lines = following.splitlines()
    for index, raw in enumerate(lines):
        text = raw.strip()
        if not text:
            paragraph_break = True
            continue

        # Indented content is part of the requirement across blanks and subheadings.
        if _indentation(raw) > indentation:
            parts.append(text)
            paragraph_break = False
            continue
        if paragraph_break or text.startswith("#") or _LIST_PREFIX.match(text):
            break

        suffix = text.lstrip(_LEADING_WRAPPERS + "—–")
        if not (_WRAPPED_SUFFIX.match(suffix) or _VERSION_BEFORE_SLASH.match(suffix)):
            next_line = lines[index + 1].lstrip(_LEADING_WRAPPERS) if index + 1 < len(lines) else ""
            if not _VERSION_BEFORE_SLASH.match(f"{suffix} {next_line}"):
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
    if context.slash_alternative or any(
        _is_non_affirmative(part)
        for part in (context.line, *context.preceding, *context.markdown_ancestors, context.continuation)
    ):
        return "unresolved", "requirement_not_affirmative", None

    skill = normalized_phrase(entry.skill)
    line = normalized_phrase(_LIST_PREFIX.sub("", context.line.lstrip()))
    headings = [normalized_phrase(text.rstrip(":").replace("-", " ")) for text in context.preceding]
    # Ordinary ancestor titles are context, while explicit qualifications still constrain the requirement.
    ancestor_headings = [normalized_phrase(text.rstrip(":").replace("-", " ")) for text in context.markdown_ancestors]
    headings.extend(heading for heading in ancestor_headings if _heading_has_requirement_cue(heading))
    simple_line = line in {skill, f"{skill} required", f"experience with {skill}", f"proficiency in {skill}"}
    generic_heading = all(not heading or heading in _GENERIC_HEADINGS for heading in headings)
    heading_cue = any(_heading_has_requirement_cue(heading) for heading in headings)
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


def _heading_has_requirement_cue(heading: str) -> bool:
    return heading.endswith((" required", " mandatory", " only")) or bool(_REQUIREMENT_LINE.search(heading)) or any(
        cue in heading for cue in ("experience with", "proficiency in", "years of", "months of")
    )
