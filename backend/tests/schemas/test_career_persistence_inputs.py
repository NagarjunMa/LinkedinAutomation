import pytest
from pydantic import ValidationError

from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput


@pytest.mark.parametrize("change", [
    {"role_family": "Platform\x00"},
    {"seniority": "Senior\x00"},
    {"location": "Remote\x00"},
    {"desired_work": ["APIs\x00"]},
    {"exclusions": ["Travel\x00"]},
    {"role_family": "Platform\ud800"},
])
def test_target_labels_reject_text_postgres_cannot_store(change):
    data = {"role_family": "Platform", "seniority": "Senior"}
    with pytest.raises(ValidationError):
        CareerTargetInput.model_validate(data | change)


def test_untrusted_source_text_must_be_valid_utf8():
    with pytest.raises(ValidationError):
        CareerSourceCreate(kind="job_description", content="Synthetic\ud800")
