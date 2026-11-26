"""Verify saved résumé findings and their privacy boundary against PostgreSQL."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.evidence_service import EvidenceService
from app.core import auth
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.resume_document import ResumeDocument
from app.models.user import User
from app.schemas.career.evidence import EvidenceDecisionInput, EvidenceProposal
from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput
from app.schemas.resume_v2 import EvaluationReport
from app.services.credits.ledger import grant_monthly

pytestmark = pytest.mark.postgres
PREVIOUS_HEAD = "2026_11_19_linkedin_pdf"
COLUMN = "grounded_review_ciphertext"
TABLE = "resume_evaluations_v2"
PDF = Path(__file__).parents[1] / "fixtures" / "resumes" / "simple.pdf"


def resume(owner, document_id):
    body = {"contact": {"name": "Synthetic"}, "raw_text": "", "experience": [{
        "company": "Synthetic", "role": "Engineer", "bullets": [{
            "id": "b1", "text": "Built a synthetic checker.", "raw_text": "Built a synthetic checker.",
        }],
    }]}
    return ResumeDocument(
        id=document_id, user_id=owner, original_filename="review.pdf",
        file_path=f"{owner}/review.pdf", storage_status="ready", file_type="pdf",
        parsed_json=body, raw_text="",
    )


def test_existing_rows_and_policy_survive_additive_upgrade_and_rollback(migrated_database):
    engine, config = migrated_database
    command.upgrade(config, PREVIOUS_HEAD)
    with Session(engine) as db:
        db.add(User(user_id="legacy-owner"))
        db.flush()
        db.add(resume("legacy-owner", "legacy-document"))
        db.flush()
        db.execute(text("""
            INSERT INTO resume_evaluations_v2
                (id, resume_document_id, user_id, overall_score, bullet_flags, format_issues,
                 ats_parseability, ats_raw_text, model_version)
            VALUES ('legacy-evaluation', 'legacy-document', 'legacy-owner', 62, '[]', '[]', 90, '', 'legacy')
        """))
        db.commit()

    def access_state():
        with engine.connect() as conn:
            return conn.execute(text("""
                SELECT relrowsecurity,
                       has_table_privilege('authenticated', :table, 'SELECT'),
                       has_table_privilege('authenticated', :table, 'UPDATE')
                FROM pg_class WHERE oid = CAST(:table AS regclass)
            """), {"table": f"public.{TABLE}"}).one()

    original = access_state()
    assert original[0]
    for target in ("head", PREVIOUS_HEAD, "head"):
        if target == "head":
            command.upgrade(config, target)
        else:
            command.downgrade(config, target)
        columns = {column["name"] for column in inspect(engine).get_columns(TABLE)}
        assert (COLUMN in columns) == (target == "head")
        assert access_state() == original
        with engine.connect() as conn:
            assert conn.execute(text(
                "SELECT overall_score FROM resume_evaluations_v2 WHERE id = 'legacy-evaluation'"
            )).scalar_one() == 62
            if target == "head":
                assert conn.execute(text(
                    "SELECT grounded_review_ciphertext FROM resume_evaluations_v2 WHERE id = 'legacy-evaluation'"
                )).scalar_one() is None
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE resume_evaluations_v2 SET grounded_review_ciphertext = 'fixture' WHERE id = 'legacy-evaluation'"
        ))
    with pytest.raises(DBAPIError, match="Cannot downgrade while grounded résumé reviews exist"):
        command.downgrade(config, PREVIOUS_HEAD)
    with engine.connect() as conn:
        assert conn.execute(text(
            "SELECT grounded_review_ciphertext FROM resume_evaluations_v2 WHERE id = 'legacy-evaluation'"
        )).scalar_one() == "fixture"


def test_review_is_owner_scoped_encrypted_and_rechecked_after_evidence_revocation(migrated_database, monkeypatch):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owners = (str(uuid4()), str(uuid4()))
    owner, peer = owners
    own_doc, peer_doc = (str(uuid4()), str(uuid4()))
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(Fernet.generate_key().decode()))
    evidence_text = "I used Python to verify a synthetic release with my team."
    with Session(engine) as db:
        db.add_all(User(user_id=identity) for identity in owners)
        db.flush()
        db.add_all([resume(owner, own_doc), resume(peer, peer_doc)])
        for identity in owners:
            grant_monthly(db, identity, 20)
        db.commit()
        targets = [
            CareerApplicationService(db, identity).create_target(CareerTargetInput(
                role_family="Software Engineer", seniority="mid", desired_work=["Python"],
            )).target_id for identity in owners
        ]
        source = CareerApplicationService(db, owner).add_source(CareerSourceCreate(
            kind="candidate_introduction", content=evidence_text,
        )).source
        ledger = EvidenceService(db, owner)
        draft = ledger.propose(EvidenceProposal(
            claim=evidence_text, category="action", ownership="team",
            sources=[{**source.model_dump(), "relationship": "supports", "locator": "test",
                      "excerpt": evidence_text, "extraction": "candidate"}],
        ))
        confirmed = ledger.decide(draft.evidence_id, EvidenceDecisionInput(revision=1, action="confirm"))

    evaluator = AsyncMock(return_value=EvaluationReport(
        overall_score=40, readiness_label="needs_work",
        score_breakdown={"content_quality": 40, "role_fit": 40, "evidence_strength": 40, "recruiter_readability": 40},
        score_explanation=[], parser_confidence="high", bullet_flags=[], format_issues=[],
    ))
    pdf = PDF.read_bytes()
    monkeypatch.setattr("app.application.resume_service.evaluate_resume", evaluator)
    monkeypatch.setattr("app.application.resume_service.get_storage", lambda: SimpleNamespace(download=lambda _: pdf))
    monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": owners[int(token)]})

    def session():
        with Session(engine) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, session)
    own_headers, peer_headers = ({"Authorization": f"Bearer {i}"} for i in range(2))
    path = f"/api/v1/resumes/{own_doc}"
    body = {"target_role": "Software Engineer", "target_id": targets[0], "grounded_review": True}
    with TestClient(app) as client:
        assert client.post(path + "/evaluate", headers=peer_headers, json=body).status_code == 404
        assert client.post(f"/api/v1/resumes/{peer_doc}/evaluate", headers=peer_headers, json=body).status_code == 404
        assert evaluator.await_count == 0
        response = client.post(path + "/evaluate", headers=own_headers, json=body)
        assert response.status_code == 200, response.text
        data = response.json()
        review = data["grounded_review"]
        assert review["mode"] == "evidence_grounded"
        assert {
            (ref["evidence_id"], ref["revision"])
            for finding in review["findings"] for ref in finding["evidence_revisions"]
        } == {(confirmed.evidence_id, confirmed.revision)}
        assert response.headers["Cache-Control"] == "no-store"
        assert evidence_text not in response.text
        assert client.get(path, headers=peer_headers).status_code == 404
        assert client.get(path, headers=own_headers).json()["grounded_review"] == review
        legacy = client.post(path + "/evaluate", headers=own_headers, json={"target_role": "Platform Engineer"})
        assert legacy.status_code == 200
        with Session(engine) as db:
            db.execute(text("""
                UPDATE resume_evaluations_v2 SET score_explanation = CAST(:explanation AS jsonb) WHERE id = :id
            """), {
                "id": legacy.json()["evaluation_id"],
                "explanation": '[{"category":"role_fit","score":40,"reason":"Legacy","before_applying_action":"Review"}]',
            })
            db.commit()
        details = client.get(path, headers=own_headers).json()
        assert details["evaluation"]["id"] == legacy.json()["evaluation_id"]
        assert details["evaluation"]["score_explanation"][0]["evidence"] == []
        assert details["resume"]["evaluation_result"]["score_explanation"][0]["evidence"] == []
        assert details["grounded_review"] == review
        assert details["grounded_evaluation_id"] == data["evaluation_id"]
        exact = f"{path}?grounded_evaluation_id={data['evaluation_id']}"
        assert client.get(exact, headers=own_headers).json()["grounded_review"] == review
        foreign = f"/api/v1/resumes/{peer_doc}?grounded_evaluation_id={data['evaluation_id']}"
        assert client.get(foreign, headers=peer_headers).status_code == 404
        with Session(engine) as db:
            cipher = db.execute(text(
                "SELECT grounded_review_ciphertext FROM resume_evaluations_v2 WHERE id = :id"
            ), {"id": data["evaluation_id"]}).scalar_one()
            assert cipher and confirmed.evidence_id not in cipher and evidence_text not in cipher
            EvidenceService(db, owner).decide(confirmed.evidence_id, EvidenceDecisionInput(
                revision=confirmed.revision, action="mark_private",
            ))
        saved = client.get(path, headers=own_headers)
        assert saved.headers["Cache-Control"] == "no-store"
        updated = saved.json()["grounded_review"]
        assert updated["needs_refresh"] and updated["mode"] == "document_only"
        assert all(not finding["evidence_revisions"] for finding in updated["findings"])
        assert confirmed.evidence_id not in saved.text
        assert evaluator.await_count == 2
