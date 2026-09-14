"""HTTP envelopes for JD analysis and its supporting credit-balance view."""

from pydantic import BaseModel

from app.schemas.jd import DiffPlan, JDExtraction


class JDAnalysisResponse(BaseModel):
    jd_evaluation_id: str
    extracted_requirements: JDExtraction
    diff_plan: DiffPlan


class CreditBalanceResponse(BaseModel):
    # Preserve the ledger's integer result; transport validation must not clamp it.
    balance: int
