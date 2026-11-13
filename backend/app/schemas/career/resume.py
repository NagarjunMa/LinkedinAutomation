"""Application-owned résumé plans, model wording and generated claim lineage."""

from typing import Annotated, Literal, Self, get_args

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, FiniteFloat, StrictBool, StrictInt, model_validator

from .common import CareerContract, Identifier, Label, Ownership, Revision, Sha256, SourceRef, Text
from .evidence import EvidenceRevisionRef


RankingCriterion = Literal[
    "must_have_relevance", "ownership_clearer", "outcome_more_defensible",
    "technical_depth_stronger", "level_better_aligned", "more_recent", "redundant_evidence",
    "page_budget_excluded", "stable_id_tiebreak",
]
GroundingViolation = Literal[
    "number_not_approved", "skill_not_approved",
    "employer_not_approved", "outcome_not_approved", "ownership_upgrade", "qualifier_removed",
    "entity_not_approved",
]
IneligibleEvidence = Literal[
    "evidence_not_confirmed", "evidence_private", "evidence_rejected", "evidence_unavailable",
    "evidence_contradicted", "evidence_revision_stale",
]
AbsentProposal = Literal["model_unavailable", "model_timeout"]
ProposalRejection = GroundingViolation | IneligibleEvidence | Literal["schema_invalid", "proposal_rejected"]
RenderReason = AbsentProposal | ProposalRejection | Literal["safe_render_used"]
SELECTION_EXCLUSIONS = (*get_args(IneligibleEvidence), "redundant_evidence", "page_budget_excluded")
ResumeReasonCode = RankingCriterion | RenderReason | Literal[
    "reading_order_failed", "parser_field_missing",
    "layout_overflow", "minimum_font_violated", "link_invalid", "document_limit",
]


class ResumePolicyProfile(CareerContract):
    profile_id: Identifier
    policy_version: Identifier
    universal_rules_version: Identifier
    market_overlay: Literal["us_canada_engineering", "india", "universal"]
    page_limit: Revision


class ResumeRequirementFinding(CareerContract):
    model_config = ConfigDict(json_schema_extra={"oneOf": [
        {
            "required": ["source", "source_locator"],
            "properties": {"source": {"type": "object"}, "source_locator": {"type": "string"}},
        },
        {
            "required": ["evidence_revisions"],
            "properties": {
                "source": {"type": "null"}, "source_locator": {"type": "null"},
                "evidence_revisions": {"minItems": 1},
            },
        },
    ]})

    finding_id: Identifier
    category: Literal["evidence", "communication", "role_clarity", "formatting", "parseability", "defensibility", "document_limit"]
    severity: Literal["info", "warning", "error"]
    blocking: StrictBool
    reason_code: ResumeReasonCode
    policy_profile_id: Identifier
    rule_version: Identifier
    source: SourceRef | None = None
    source_locator: Label | None = None
    evidence_revisions: list[EvidenceRevisionRef] = Field(default_factory=list)
    explanation: Text
    next_action: Text

    @model_validator(mode="after")
    def validate_citation(self) -> Self:
        if (self.source is None) != (self.source_locator is None):
            raise ValueError("finding source and source locator must be supplied together")
        if self.source is None and not self.evidence_revisions:
            raise ValueError("finding requires a source locator or evidence revisions")
        return self


class EvidenceSelectionDecision(CareerContract):
    model_config = ConfigDict(json_schema_extra={
        "if": {"properties": {"decision": {"const": "selected"}}},
        "then": {
            "required": ["winning_evidence"],
            "properties": {
                "winning_evidence": {"type": "object"},
                "reason_codes": {"items": {"not": {"enum": list(SELECTION_EXCLUSIONS)}}},
            },
        },
    })

    target_id: Identifier
    artifact_id: Identifier
    evidence: EvidenceRevisionRef
    decision: Literal["selected", "excluded", "deferred", "blocked"]
    ordered_criteria: list[RankingCriterion] = Field(min_length=1)
    winning_evidence: EvidenceRevisionRef | None = None
    competing_evidence: list[EvidenceRevisionRef] = Field(default_factory=list)
    page_budget_effect: StrictInt = 0
    reason_codes: list[ResumeReasonCode] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_winner(self) -> Self:
        if self.decision == "selected":
            if self.winning_evidence != self.evidence:
                raise ValueError("selected evidence must match the winning revision")
            if any(reason in SELECTION_EXCLUSIONS for reason in self.reason_codes):
                raise ValueError("selected evidence cannot have an ineligible or exclusion reason")
        elif self.winning_evidence is not None and self.winning_evidence.evidence_id == self.evidence.evidence_id:
            raise ValueError("a non-selected evidence item cannot be its own winner")
        return self


def _one_revision_per_evidence(revisions: list[EvidenceRevisionRef]) -> list[EvidenceRevisionRef]:
    if len({ref.evidence_id for ref in revisions}) != len(revisions):
        raise ValueError("use exactly one revision per evidence item")
    return revisions


ClaimEvidence = Annotated[list[EvidenceRevisionRef], Field(min_length=1), AfterValidator(_one_revision_per_evidence)]


class ResumeMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    value: StrictInt | Annotated[FiniteFloat, Field(strict=True)]
    unit: Label
    estimated: StrictBool
    evidence: EvidenceRevisionRef


class ResumeOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    description: Text
    measurement_method: Label | None = None
    measurement_scope: Label | None = None


class ResumeBulletPlan(CareerContract):
    model_config = ConfigDict(json_schema_extra={"allOf": [
        {"properties": {"ownership": {"not": {"const": "unknown"}}}},
        {
            "if": {"properties": {"structure": {"const": "achievement"}}},
            "then": {"required": ["outcome"], "properties": {"outcome": {"type": "object"}, "ownership": {"const": "individual"}}},
        },
        {
            "if": {"properties": {"structure": {"const": "team_contribution"}}},
            "then": {"properties": {"ownership": {"enum": ["shared", "team"]}}},
        },
        {
            "if": {"properties": {"ownership": {"enum": ["shared", "team"]}}},
            "then": {"required": ["ownership_scope"], "properties": {"ownership_scope": {"type": "string"}}},
        },
        {
            "if": {"required": ["permitted_numbers"], "properties": {"permitted_numbers": {"minItems": 1}}},
            "then": {"required": ["outcome"], "properties": {"outcome": {
                "type": "object", "required": ["measurement_method", "measurement_scope"],
                "properties": {"measurement_method": {"type": "string"}, "measurement_scope": {"type": "string"}},
            }}},
        },
    ]})

    plan_id: Identifier
    target_requirement_ids: list[Identifier] = Field(default_factory=list)
    evidence_revisions: ClaimEvidence
    problem: Text | None = None
    context: Text | None = None
    action: Text
    ownership: Ownership
    ownership_scope: Label | None = None
    method: Text
    technologies: list[Label] = Field(default_factory=list)
    technical_depth: Text | None = None
    outcome: ResumeOutcome | None = None
    permitted_entities: list[Label] = Field(default_factory=list)
    permitted_numbers: list[ResumeMetric] = Field(default_factory=list)
    skills: list[Label] = Field(default_factory=list)
    ownership_verbs: list[Label] = Field(min_length=1)
    qualifiers: list[Label] = Field(default_factory=list)
    structure: Literal["achievement", "technical_contribution", "team_contribution"]
    max_length: Revision
    policy_version: Identifier
    renderer_version: Identifier

    @model_validator(mode="after")
    def validate_facts(self) -> Self:
        if self.ownership == "unknown":
            raise ValueError("bullet plan requires clarified ownership")
        if self.structure == "achievement" and self.outcome is None:
            raise ValueError("achievement plans require a supported outcome")
        if self.structure == "team_contribution" and self.ownership not in ("shared", "team"):
            raise ValueError("team contribution requires shared or team ownership")
        if self.structure == "achievement" and self.ownership in ("shared", "team"):
            raise ValueError("shared or team achievements require the team contribution structure")
        if self.ownership in ("shared", "team") and not self.ownership_scope:
            raise ValueError("shared or team work requires a personal ownership scope")
        if self.permitted_numbers and (
            self.outcome is None or not self.outcome.measurement_method or not self.outcome.measurement_scope
        ):
            raise ValueError("permitted numbers require an outcome with a measurement method and scope")
        approved = {(ref.evidence_id, ref.revision) for ref in self.evidence_revisions}
        if any((metric.evidence.evidence_id, metric.evidence.revision) not in approved for metric in self.permitted_numbers):
            raise ValueError("each metric must cite an approved evidence revision")
        return self


class ResumeBulletRenderProposal(CareerContract):
    plan_id: Identifier
    text: Text


class ResumeRenderValidationResult(CareerContract):
    model_config = ConfigDict(json_schema_extra={"oneOf": [
        {
            "required": ["proposal_hash"],
            "properties": {
                "accepted": {"const": True}, "used_fallback": {"const": False},
                "proposal_hash": {"type": "string"},
                "reason_codes": {"maxItems": 0}, "disallowed_additions": {"maxItems": 0},
            },
        },
        *[
            {
                "required": ["reason_codes"],
                "properties": {
                    "accepted": {"const": False}, "used_fallback": {"const": True},
                    "proposal_hash": {"type": "null"}, "disallowed_additions": {"maxItems": 0},
                    "reason_codes": {"contains": {"const": reason}, "items": {"enum": [reason, "safe_render_used"]}},
                },
            }
            for reason in get_args(AbsentProposal)
        ],
        {
            "required": ["proposal_hash", "reason_codes"],
            "properties": {
                "accepted": {"const": False}, "used_fallback": {"const": True},
                "proposal_hash": {"type": "string"},
                "reason_codes": {
                    "contains": {"not": {"const": "safe_render_used"}},
                    "items": {"not": {"enum": list(get_args(AbsentProposal))}},
                },
            },
        },
    ]})

    accepted: StrictBool
    rule_version: Identifier
    reason_codes: list[RenderReason] = Field(default_factory=list)
    disallowed_additions: list[Label] = Field(default_factory=list)
    plan_hash: Sha256
    proposal_hash: Sha256 | None = None
    used_fallback: StrictBool

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        reasons = set(self.reason_codes) - {"safe_render_used"}
        if self.accepted:
            if self.used_fallback or self.disallowed_additions or self.reason_codes or self.proposal_hash is None:
                raise ValueError("accepted proposal requires a hash and no rejection or fallback details")
        elif not self.used_fallback or not reasons:
            raise ValueError("rejected or absent proposal requires a reason and fallback")
        elif reasons.intersection(get_args(AbsentProposal)):
            if self.proposal_hash is not None or self.disallowed_additions or len(reasons) != 1:
                raise ValueError("absent proposal cannot carry a proposal hash, additions or another failure reason")
        elif self.proposal_hash is None:
            raise ValueError("rejected proposal requires a proposal hash")
        return self


class GeneratedClaimLineage(CareerContract):
    claim_id: Identifier
    artifact_id: Identifier
    artifact_version: Revision
    evidence_revisions: ClaimEvidence
