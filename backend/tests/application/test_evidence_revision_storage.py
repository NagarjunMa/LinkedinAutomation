"""Verify the owner edit contract and the encrypted evidence payload boundary."""
import json
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.application.errors import ExternalServiceError
from app.application.evidence_service import EvidenceService
from app.models.career_evidence import EvidenceRow
from app.schemas.career.evidence import CareerEvidenceItem, EvidenceDecisionInput


MEASUREMENT = {"method": "Median of synthetic runs", "scope": "Local fixture", "estimated": True}


@pytest.mark.parametrize("changes", [
    {"claim": "Built tests"},
    {"ownership": "shared"},
    {"scope": None, "measurement": None},
    {"measurement": MEASUREMENT},
])
def test_edit_body_preserves_omission_and_explicit_clearing(changes):
    decision = EvidenceDecisionInput.model_validate({"revision": 1, "action": "edit", **changes})
    assert decision.edit_values() == changes


@pytest.mark.parametrize("body", [
    {"action": "edit"},
    {"action": "edit", "ownership": None, "scope": "Local fixture"},
    {"action": "edit", "claim": None},
    {"action": "confirm", "measurement": None},
    {"action": "resolve_contradiction", "ownership": "team"},
])
def test_edit_body_rejects_ambiguous_or_non_edit_updates(body):
    with pytest.raises(ValidationError):
        EvidenceDecisionInput.model_validate({"revision": 1, **body})


@pytest.mark.parametrize("measurement", [None, MEASUREMENT])
def test_measurement_is_stored_apart_from_the_legacy_evidence_payload(measurement):
    item = CareerEvidenceItem(
        schema_version=1, evidence_id="synthetic-evidence", revision=1, owner_id="owner",
        claim="Built tests", category="action", ownership="individual", lifecycle="proposed",
        support="candidate_statement", measurement=measurement,
        sources=[{
            "source_id": "synthetic-source", "source_version": 1, "relationship": "supports",
            "locator": "chars:0-11", "excerpt_sha256": "a" * 64, "extraction": "candidate",
        }],
    )
    db = MagicMock(spec=Session)
    service = EvidenceService(db, "owner")
    cipher = Fernet(Fernet.generate_key())

    service._insert(item, cipher)

    row = db.add.call_args.args[0]
    assert json.loads(cipher.decrypt(row.ciphertext.encode())) == item.model_dump(exclude={"measurement"})
    if measurement is None:
        assert row.measurement_ciphertext is None
    else:
        assert json.loads(cipher.decrypt(row.measurement_ciphertext.encode())) == measurement
    assert service._view(row, cipher) == item


def test_malformed_stored_evidence_error_omits_private_content():
    cipher = Fernet(Fernet.generate_key())
    row = EvidenceRow(ciphertext=cipher.encrypt(b'{"claim":"synthetic private claim"}').decode())
    service = EvidenceService(MagicMock(spec=Session), "owner")
    with pytest.raises(ExternalServiceError, match="Career evidence could not be opened") as failure:
        service._view(row, cipher)
    assert "synthetic private claim" not in str(failure.value)
