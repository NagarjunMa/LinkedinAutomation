"""Versioned Career Evidence contracts and an offline JSON Schema bundle."""

from pydantic.json_schema import models_json_schema

from .evidence import CareerEvidenceDecision, CareerEvidenceItem
from .interview import CareerCoverage, CareerSessionState, CareerTurnProposal
from .resume import (
    EvidenceSelectionDecision,
    GeneratedClaimLineage,
    ResumeBulletPlan,
    ResumeBulletRenderProposal,
    ResumePolicyProfile,
    ResumeRenderValidationResult,
    ResumeRequirementFinding,
)
from .sources import CareerSource, CareerTarget, LinkedInDocument, LinkedInReview


def career_json_schema(contract_name: str | None = None) -> dict:
    """Export definitions or a named wire validator. Use Pydantic for domain checks."""
    contracts = (
        CareerSource, CareerTarget, CareerSessionState, CareerCoverage, CareerTurnProposal,
        CareerEvidenceItem, CareerEvidenceDecision, LinkedInDocument, LinkedInReview,
        GeneratedClaimLineage, ResumePolicyProfile, ResumeRequirementFinding, EvidenceSelectionDecision,
        ResumeBulletPlan, ResumeBulletRenderProposal, ResumeRenderValidationResult,
    )
    _, bundle = models_json_schema([(contract, "validation") for contract in contracts], title="Career Evidence v1")
    if contract_name is None:
        entry = {"not": {}, "description": "Definition bundle. Select a named contract to validate an instance."}
    elif contract_name in bundle["$defs"]:
        entry = {"$ref": f"#/$defs/{contract_name}"}
    else:
        raise ValueError(f"unknown Career Evidence contract: {contract_name}")
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **entry, **bundle}
