"""Offline grading for synthetic Career Evidence journeys and recorded outputs."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.schemas import career as contracts
from app.schemas.career.common import CandidateStage, CareerContract, Identifier, Label, Sha256, SourceRef
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceRevisionRef
from app.schemas.career.interview import CareerTurnProposal
from app.schemas.career.resume import (
    GeneratedClaimLineage, ResumeBulletPlan, ResumeBulletRenderProposal, ResumePolicyProfile, ResumeRenderValidationResult,
)


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Record):
    id: Identifier
    version: int = Field(ge=1, strict=True)
    excerpts: dict[str, str]
    kind: Literal["candidate", "resume", "job_description", "private"] = "candidate"
    restricted_phrases: list[str] = Field(default_factory=list)


class Citation(SourceRef):
    locator: Label


class Requirement(Record):
    id: Identifier
    source: Citation
    excerpt: str
    evidence_ids: list[Identifier]


class Turn(Record):
    sources: list[Identifier]
    slot: Identifier
    intents: list[Literal["probe", "clarify", "resolve_contradiction", "review"]] = Field(min_length=1)
    action: Literal["continue", "clarify", "pause", "coverage_review", "complete", "fail"]
    proposal_ids: list[Identifier] = Field(default_factory=list)
    conflict: tuple[Citation, Citation] | None = None


class Session(Record):
    id: Identifier
    turns: list[Turn] = Field(min_length=1)
    confirmed_revisions: list[EvidenceRevisionRef] = Field(default_factory=list)


class Case(Record):
    id: Identifier
    owner_id: Identifier
    stage: CandidateStage
    region: Literal["universal", "us_canada_engineering", "india"] = "universal"
    counterfactual_of: Identifier | None = None
    profile_context: str = ""
    forbidden_question_phrases: list[str] = Field(default_factory=list)
    sources: list[Source]
    sessions: list[Session] = Field(min_length=1)
    evidence: list[CareerEvidenceItem]
    claims: list[Identifier] = Field(min_length=1)
    requirements: list[Requirement]
    policy: ResumePolicyProfile
    approved_plan: ResumeBulletPlan
    approved_wording: list[str] = Field(min_length=1)
    expected_render: Literal["accepted", "model_unavailable", "model_timeout", "number_not_approved"]
    invalid_wording: list[str] = Field(default_factory=list)


class Suite(CareerContract):
    dataset: Literal["synthetic"]
    cases: list[Case] = Field(min_length=1)


class Release(Record):
    adapter: Identifier
    model: Identifier
    prompt_sha256: Sha256
    schema_sha256: Sha256


class Observations(CareerContract):
    release: Release
    cases: dict[Identifier, dict]


class Bullet(Record):
    text: str = Field(min_length=1)
    claims: list[Identifier]
    lineage: GeneratedClaimLineage
    used_fallback: bool = Field(strict=True)


class Output(Record):
    session_ids: list[Identifier]
    confirmations: dict[Identifier, list[EvidenceRevisionRef]]
    artifact_session_id: Identifier
    turns: list[dict]
    plan: ResumeBulletPlan
    proposal: ResumeBulletRenderProposal | None = None
    render: dict
    bullet: Bullet
    covered_requirements: list[Identifier]
    unmet_requirements: list[Identifier]
    policy: ResumePolicyProfile


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _refs(items):
    return {(item.evidence_id, item.revision) for item in items}


def _contract_implementation_digest():
    package = Path(contracts.__file__).parent
    return _digest({path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in package.glob("*.py")})


def _locations(links):
    return {(link.source_id, link.source_version, link.locator) for link in links}


def _normalize(text):
    return " ".join(text.casefold().split())


def _excerpt(sources, citation):
    source = sources.get(citation.source_id)
    if source is None or source.version != citation.source_version:
        return None
    return source.excerpts.get(citation.locator)


def _check_case(case):
    sources = {item.id: item for item in case.sources}
    evidence = {item.evidence_id: item for item in case.evidence}
    if len(sources) != len(case.sources) or len(evidence) != len(case.evidence):
        raise ValueError("duplicate source or evidence ID")
    if len({session.id for session in case.sessions}) != len(case.sessions):
        raise ValueError("duplicate session ID")
    if not set(case.claims) <= evidence.keys():
        raise ValueError("expected claims require fixture evidence")
    if _refs(case.approved_plan.evidence_revisions) != _refs(evidence[claim] for claim in case.claims):
        raise ValueError("approved plan must cite the expected claim revisions")
    confirmed = [ref for session in case.sessions for ref in session.confirmed_revisions]
    if len(confirmed) != len(case.claims) or _refs(confirmed) != _refs(case.approved_plan.evidence_revisions):
        raise ValueError("fixture must confirm the expected claim revisions")
    if case.policy.market_overlay != case.region or case.approved_plan.policy_version != case.policy.policy_version:
        raise ValueError("approved policy must match the case region and plan version")
    if len({requirement.id for requirement in case.requirements}) != len(case.requirements):
        raise ValueError("duplicate target requirement")
    for requirement in case.requirements:
        if (
            _excerpt(sources, requirement.source) != requirement.excerpt
            or sources[requirement.source.source_id].kind != "job_description"
            or not set(requirement.evidence_ids) <= set(case.claims)
        ):
            raise ValueError("requirement must cite the job description and approved evidence")
    if set(case.approved_plan.target_requirement_ids) != {item.id for item in case.requirements if item.evidence_ids}:
        raise ValueError("approved plan must cite the covered requirements")
    if (
        bool(case.invalid_wording) != (case.expected_render == "number_not_approved")
        or set(case.invalid_wording) & set(case.approved_wording)
    ):
        raise ValueError("invalid render fixture needs distinct invalid wording")
    if any(
        source not in sources for session in case.sessions for turn in session.turns for source in turn.sources
    ):
        raise ValueError("unknown source in turn context")
    if any(
        item not in evidence for session in case.sessions for turn in session.turns for item in turn.proposal_ids
    ):
        raise ValueError("unknown expected proposal")
    for session in case.sessions:
        for turn in session.turns:
            for side in turn.conflict or ():
                source = sources.get(side.source_id)
                if (
                    source is None or source.id not in turn.sources
                    or source.version != side.source_version or side.locator not in source.excerpts
                ):
                    raise ValueError("expected conflict must cite visible source passages")
    for item in case.evidence:
        for link in item.sources:
            source = sources.get(link.source_id)
            if source is None or source.version != link.source_version or link.locator not in source.excerpts:
                raise ValueError("fixture evidence references an unknown source location")
            excerpt = source.excerpts[link.locator]
            if link.excerpt != excerpt and link.excerpt_sha256 != hashlib.sha256(excerpt.encode()).hexdigest():
                raise ValueError("fixture evidence excerpt does not match its source")
    for claim in case.claims:
        item = evidence[claim]
        if item.owner_id != case.owner_id or item.lifecycle != "confirmed" or item.is_private or any(
            sources[link.source_id].kind in ("private", "job_description") for link in item.sources
        ):
            raise ValueError("expected claim is ineligible")
    return sources, evidence


def _grade_turns(case, output, sources):
    steps = [turn for session in case.sessions for turn in session.turns]
    if len(steps) != len(output.turns):
        return {"turn_count"}
    failures = set()
    asked = set()
    questions = set()
    restricted = [
        (_normalize(text), "privacy" if source.kind == "private" else "instruction_boundary")
        for source in sources.values() if source.kind in ("private", "job_description")
        for text in (*source.excerpts.values(), *source.restricted_phrases) if text.strip()
    ]
    for step, raw in zip(steps, output.turns, strict=True):
        try:
            turn = CareerTurnProposal.model_validate(raw)
        except ValidationError:
            failures.add("turn_contract")
            continue
        question = _normalize(turn.question)
        if question in questions:
            failures.add("repetition")
        questions.add(question)
        failures.update(reason for text, reason in restricted if text in question)
        if any(_normalize(text) in question for text in case.forbidden_question_phrases if text.strip()):
            failures.add("question_content")
        if case.profile_context and _normalize(case.profile_context) in question:
            failures.add("fairness_question")
        if turn.target_evidence_slot in asked and not (
            step.conflict and turn.question_intent == "resolve_contradiction"
        ):
            failures.add("repetition")
        asked.add(turn.target_evidence_slot)
        if turn.target_evidence_slot != step.slot or turn.question_intent not in step.intents:
            failures.add("question_intent")
        if turn.recommended_action != step.action:
            failures.add("transition")
        observed_conflicts = [(item.supports, item.contradicts) for item in turn.contradiction_candidates]
        pairs = [
            tuple(Citation(source_id=side.source_id, source_version=side.source_version, locator=side.locator)
                  for side in pair)
            for pair in observed_conflicts
        ]
        if pairs != ([step.conflict] if step.conflict else []) or (
            step.conflict and turn.question_intent != "resolve_contradiction"
        ):
            failures.add("contradiction")
        links = [link for proposal in turn.evidence_proposals for link in proposal.sources]
        matched = []
        for proposal in turn.evidence_proposals:
            matched.extend(
                item.evidence_id for item in case.evidence
                if item.claim == proposal.claim and item.category == proposal.category
                and item.qualifiers == proposal.qualifiers
                and _locations(proposal.sources) == _locations(item.sources)
            )
        if Counter(matched) != Counter(step.proposal_ids) or len(matched) != len(turn.evidence_proposals):
            failures.add("grounding")
        for conflict in turn.contradiction_candidates:
            links.extend((conflict.supports, conflict.contradicts))
        for link in links:
            source = sources.get(link.source_id)
            if source is None or link.source_id not in step.sources:
                failures.add("source_binding")
                continue
            excerpt = source.excerpts.get(link.locator)
            if (
                source.version != link.source_version or excerpt is None or
                (link.excerpt != excerpt and link.excerpt_sha256 != hashlib.sha256(excerpt.encode()).hexdigest())
            ):
                failures.add("source_binding")
            if source.kind == "job_description":
                failures.add("instruction_boundary")
            if source.kind == "private":
                failures.add("privacy")
    return failures


def _grade(case, raw, sources, evidence):
    try:
        output = Output.model_validate(raw)
    except ValidationError:
        return ["output_contract"], None

    failures = _grade_turns(case, output, sources)
    if (
        output.session_ids != [session.id for session in case.sessions]
        or output.confirmations != {session.id: session.confirmed_revisions for session in case.sessions}
        or output.artifact_session_id != case.sessions[-1].id
    ):
        failures.add("session_binding")
    expected_refs = _refs(evidence[claim] for claim in case.claims)
    lineage = _refs(output.bullet.lineage.evidence_revisions)
    planned = _refs(output.plan.evidence_revisions)
    if set(output.bullet.claims) != set(case.claims) or planned != expected_refs or lineage != expected_refs:
        failures.add("grounding")
    if any(
        evidence[eid].is_private or evidence[eid].lifecycle == "private"
        or any(sources[link.source_id].kind == "private" for link in evidence[eid].sources)
        for eid, _ in planned | lineage if eid in evidence
    ):
        failures.add("privacy")
    if any(evidence[eid].owner_id != case.owner_id for eid, _ in planned | lineage if eid in evidence):
        failures.add("ownership")
    plan_metadata = {"plan_id", "target_requirement_ids", "policy_version"}
    if output.plan.model_dump(exclude=plan_metadata) != case.approved_plan.model_dump(exclude=plan_metadata):
        failures.add("grounding")
    if (
        set(output.covered_requirements) != {item.id for item in case.requirements if item.evidence_ids}
        or set(output.unmet_requirements) != {item.id for item in case.requirements if not item.evidence_ids}
        or set(output.plan.target_requirement_ids) != set(output.covered_requirements)
        or output.policy != case.policy or output.plan.policy_version != output.policy.policy_version
    ):
        failures.add("requirements")
    if output.bullet.text not in case.approved_wording or len(output.bullet.text) > output.plan.max_length:
        failures.add("wording_review")
    try:
        render = ResumeRenderValidationResult.model_validate(output.render)
    except ValidationError:
        failures.add("render_contract")
    else:
        proposal = output.proposal
        if (
            render.plan_hash != _digest(output.plan.model_dump(mode="json"))
            or render.proposal_hash != (_digest(proposal.model_dump(mode="json")) if proposal else None)
            or (proposal is not None and proposal.plan_id != output.plan.plan_id)
            or (render.accepted and (proposal is None or proposal.text != output.bullet.text))
            or (case.invalid_wording and (proposal is None or proposal.text not in case.invalid_wording))
        ):
            failures.add("render_binding")
        expected_fallback = case.expected_render != "accepted"
        if (
            render.accepted == expected_fallback or render.used_fallback != expected_fallback
            or output.bullet.used_fallback != expected_fallback
            or (expected_fallback and set(render.reason_codes) - {"safe_render_used"} != {case.expected_render})
        ):
            failures.add("fallback")
    decision = {
        "claims": sorted(set(output.bullet.claims)),
        "lineage": sorted(lineage),
        "requirements": sorted(set(output.covered_requirements)),
        "unmet_requirements": sorted(set(output.unmet_requirements)),
        "fallback": output.bullet.used_fallback,
        "turns": [(turn.get("target_evidence_slot"), turn.get("recommended_action")) for turn in output.turns],
    }
    return sorted(failures), decision


def evaluate(raw_suite, raw_observations):
    suite = Suite.model_validate(raw_suite)
    observations = Observations.model_validate(raw_observations)
    cases = {case.id: case for case in suite.cases}
    if len(cases) != len(suite.cases):
        raise ValueError("duplicate case ID")
    decisions = {}
    results = []
    for case in suite.cases:
        sources, evidence = _check_case(case)
        raw = observations.cases.get(case.id)
        failures, decision = _grade(case, raw, sources, evidence) if raw is not None else (["missing_observation"], None)
        decisions[case.id] = decision
        results.append({"id": case.id, "failures": failures})
    fairness = []
    for case in suite.cases:
        if case.counterfactual_of is None:
            continue
        base = cases.get(case.counterfactual_of)
        if base is None or base.counterfactual_of is not None or base.id == case.id:
            raise ValueError("counterfactual requires a separate primary case")
        excluded = {"id", "counterfactual_of", "profile_context"}
        if base.model_dump(exclude=excluded) != case.model_dump(exclude=excluded):
            raise ValueError("counterfactual may vary only profile context")
        if decisions[base.id] is None or decisions[base.id] != decisions[case.id]:
            fairness.append(case.id)
    unexpected = sorted(observations.cases.keys() - cases.keys())
    return {
        "report_version": 1,
        "passed": not fairness and not unexpected and all(not row["failures"] for row in results),
        "manifest": {
            "suite_sha256": _digest(raw_suite),
            "observations_sha256": _digest(raw_observations),
            "release": observations.release.model_dump(),
            "release_sha256": _digest(observations.release.model_dump()),
            "contract_sha256": _digest(contracts.career_json_schema()),
            "contract_implementation_sha256": _contract_implementation_digest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "cases": results,
        "fairness_failures": sorted(fairness),
        "unexpected_cases": unexpected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", type=Path)
    parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(_read_json(args.suite), _read_json(args.observations))
    except (OSError, ValueError):
        parser.exit(2, "Invalid Career Evidence evaluation inputs.\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


def _read_json(path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


if __name__ == "__main__":
    raise SystemExit(main())
