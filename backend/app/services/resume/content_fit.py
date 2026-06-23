"""Deterministic resume content-fit signals for JD tailoring.

The LLM proposes rewrites, but page discipline and noise reduction should not
depend only on prompt behavior. These helpers add explainable, testable signals
that tell the UI which bullets are strongest for a specific JD and whether a
tailored resume is likely to exceed the intended page budget.
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable

from app.schemas.jd import (
    BulletFitSignal,
    ContentBudget,
    DiffPlan,
    JDExtraction,
    Requirement,
)
from app.schemas.resume_v2 import Bullet, ResumeDocumentJSON

_STOP_WORDS = {
    "and",
    "are",
    "for",
    "from",
    "have",
    "into",
    "that",
    "the",
    "this",
    "with",
    "you",
    "your",
    "using",
    "work",
    "will",
    "role",
    "team",
    "teams",
    "candidate",
    "experience",
}

_RESPONSIBILITY_ONLY_PREFIXES = (
    "assisted",
    "contributed",
    "helped",
    "participated",
    "responsible for",
    "supported",
    "worked on",
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{2,}", text.lower())
        if token not in _STOP_WORDS
    }


def _requirement_terms(requirements: Iterable[Requirement]) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = {}
    for req in requirements:
        text = f"{req.skill} {req.evidence_from_jd}"
        req_tokens = _tokens(text)
        if req_tokens:
            terms[req.skill] = req_tokens
    return terms


def _all_bullets(doc: ResumeDocumentJSON) -> list[Bullet]:
    return [
        bullet
        for section in [*doc.experience, *doc.projects]
        for bullet in section.bullets
    ]


def _page_cost(text: str) -> str:
    words = len(text.split())
    if words > 34:
        return "high"
    if words > 24:
        return "medium"
    return "low"


def _truth_risk(
    *,
    matched_requirements: list[str],
    noise_flags: list[str],
    recommendation: str,
) -> str:
    if not matched_requirements or "responsibility_only" in noise_flags:
        return "high"
    if recommendation == "rewrite" or noise_flags:
        return "medium"
    return "low"


def _why_stronger(
    *,
    matched_requirements: list[str],
    recommendation: str,
    noise_flags: list[str],
) -> str:
    if recommendation == "keep":
        return (
            "Strong pointer because it directly supports "
            f"{', '.join(matched_requirements)} with resume-backed evidence."
        )
    if recommendation == "rewrite":
        return (
            "Useful pointer, but it needs tighter wording to make the JD match "
            "and resume evidence obvious."
        )
    if "no_jd_requirement_match" in noise_flags:
        return (
            "Weak pointer for this JD because it does not clearly support a listed requirement."
        )
    return "Lower-priority pointer for this JD; keep it only if it supports the role narrative."


def _source_page_estimate(doc: ResumeDocumentJSON, bullet_count: int) -> float:
    """Estimate whether the source is closer to one page or two pages.

    This intentionally uses text density instead of the generated PDF because
    the tailor endpoint needs the signal before export. The threshold is loose:
    a normal one-page SWE resume generally lands around 3.5k-4.8k extracted
    characters, while 1.5+ pages tends to exceed that or carry many bullets.
    """

    char_pages = max(1.0, len(doc.raw_text or "") / 4200)
    bullet_pages = max(1.0, bullet_count / 14)
    return round(max(char_pages, bullet_pages), 2)


def build_content_budget(doc: ResumeDocumentJSON) -> ContentBudget:
    bullet_count = len(_all_bullets(doc))
    source_pages = _source_page_estimate(doc, bullet_count)
    target_pages = 2 if source_pages >= 1.5 else 1
    budget = 22 if target_pages == 2 else 12
    overage = bullet_count - budget

    if overage <= 0:
        risk = "low"
    elif overage <= 4:
        risk = "medium"
    else:
        risk = "high"

    if target_pages == 1:
        guidance = (
            "Source resume appears one-page sized; keep only the strongest "
            "JD-matched bullets and trim low-relevance noise."
        )
    else:
        guidance = (
            "Source resume appears long enough to justify a two-page target, "
            "but low-relevance bullets should still be trimmed."
        )

    return ContentBudget(
        source_page_estimate=source_pages,
        target_max_pages=target_pages,
        recommended_bullet_budget=budget,
        current_bullet_count=bullet_count,
        page_fit_risk=risk,
        guidance=guidance,
    )


def score_bullet_fit(doc: ResumeDocumentJSON, jd: JDExtraction) -> list[BulletFitSignal]:
    must_terms = _requirement_terms(jd.must_have)
    good_terms = _requirement_terms(jd.good_to_have)
    all_requirements = {**must_terms, **good_terms}
    jd_vocab = set().union(*all_requirements.values()) if all_requirements else set()
    signals: list[BulletFitSignal] = []

    for bullet in _all_bullets(doc):
        text = bullet.text.strip()
        bullet_tokens = _tokens(text)
        matched_must = [
            name
            for name, terms in must_terms.items()
            if bullet_tokens & terms
        ]
        matched_good = [
            name
            for name, terms in good_terms.items()
            if bullet_tokens & terms
        ]
        matched = [*matched_must, *matched_good]
        matched_jd_phrases = [
            req.evidence_from_jd
            for req in [*jd.must_have, *jd.good_to_have]
            if req.skill in matched and req.evidence_from_jd
        ]

        requirement_score = 0
        if all_requirements:
            weighted_matches = (len(matched_must) * 1.4) + len(matched_good)
            weighted_total = max(1.0, (len(must_terms) * 1.4) + len(good_terms))
            requirement_score = min(72, math.ceil((weighted_matches / weighted_total) * 72))

        token_score = 0
        if jd_vocab:
            token_score = min(18, math.ceil((len(bullet_tokens & jd_vocab) / max(1, len(jd_vocab))) * 54))

        quality_score = 10 if re.search(r"\d|%|\$|minutes?|hours?|users?|transactions?", text, re.I) else 4
        score = max(10, min(100, requirement_score + token_score + quality_score))

        noise_flags: list[str] = []
        if not matched:
            noise_flags.append("no_jd_requirement_match")
        if len(text.split()) > 34:
            noise_flags.append("long_bullet")
        if text.lower().startswith(_RESPONSIBILITY_ONLY_PREFIXES):
            noise_flags.append("responsibility_only")

        if score >= 68:
            recommendation = "keep"
            evidence = "high"
            rationale = "Strong overlap with this JD's requirements."
        elif score >= 42:
            recommendation = "rewrite"
            evidence = "medium"
            rationale = "Some JD overlap exists, but the pointer should be tightened."
        else:
            recommendation = "consider_trim"
            evidence = "low"
            rationale = "Limited JD overlap; trim unless it supports a critical narrative."

        page_cost = _page_cost(text)
        truth_risk = _truth_risk(
            matched_requirements=matched,
            noise_flags=noise_flags,
            recommendation=recommendation,
        )

        signals.append(
            BulletFitSignal(
                bullet_id=bullet.id,
                relevance_score=score,
                evidence_level=evidence,
                recommendation=recommendation,
                matched_requirements=matched,
                noise_flags=noise_flags,
                rationale=rationale,
                why_stronger=_why_stronger(
                    matched_requirements=matched,
                    recommendation=recommendation,
                    noise_flags=noise_flags,
                ),
                matched_jd_phrases=matched_jd_phrases,
                source_resume_evidence=[text] if text else [],
                page_cost=page_cost,
                truth_risk=truth_risk,
            )
        )

    return signals


def enrich_diff_plan_with_content_fit(
    doc: ResumeDocumentJSON,
    jd: JDExtraction,
    plan: DiffPlan,
) -> DiffPlan:
    plan.bullet_fit = score_bullet_fit(doc, jd)
    plan.content_budget = build_content_budget(doc)
    return plan
