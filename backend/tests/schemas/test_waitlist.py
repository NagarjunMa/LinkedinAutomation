import pytest
from pydantic import ValidationError

from app.schemas.waitlist import WaitlistCreate


def test_waitlist_schema_accepts_and_strips_valid_input():
    payload = WaitlistCreate(
        email="  Candidate@Example.com ",
        career_stage="experienced_ic",
        target_role="  Staff Engineer  ",
        communication_challenge="  Explaining cross-team impact  ",
        consent=True,
    )

    assert str(payload.email) == "Candidate@example.com"
    assert payload.target_role == "Staff Engineer"
    assert payload.communication_challenge == "Explaining cross-team impact"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"consent": False},
        {"career_stage": "executive_rockstar"},
        {"target_role": "x" * 121},
        {"communication_challenge": "x" * 1001},
        {"unexpected": "field"},
    ],
)
def test_waitlist_schema_rejects_invalid_or_oversized_input(overrides):
    data = {"email": "candidate@example.com", "consent": True, **overrides}

    with pytest.raises(ValidationError):
        WaitlistCreate.model_validate(data)
