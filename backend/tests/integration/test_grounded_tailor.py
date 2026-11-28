"""Exercise the provider-free Tailor preview against the real evidence ledger."""

import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from unittest.mock import Mock
from uuid import uuid4

import pytest
from alembic import command
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr
from pypdf import PdfReader
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.application.career_service import CareerApplicationService
from app.application.errors import ResourceConflictError, ResourceNotFoundError
from app.application.evidence_service import EvidenceService
from app.application.jd_service import JDTailoringApplicationService
from app.application.resume_service import ResumeApplicationService
from app.core import auth
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.models.user import User
from app.schemas.career.evidence import EvidenceDecisionInput, EvidenceProposal
from app.schemas.career.persistence import CareerSourceCreate, CareerTargetInput
from app.services.credits.ledger import get_balance, grant_monthly

pytestmark = pytest.mark.postgres


def test_tailor_preview_cites_exact_sources_without_the_model(migrated_database, monkeypatch):
    engine, config = migrated_database
    command.upgrade(config, "head")
    owner, peer, document_id, version_id, review_id, jd_id = (str(uuid4()) for _ in range(6))
    original_review_id = str(uuid4())
    key = Fernet.generate_key()
    cipher = Fernet(key)
    monkeypatch.setattr(settings, "CAREER_TRANSCRIPT_KEY", SecretStr(key.decode()))
    resume = {"contact": {"name": "Synthetic candidate"}, "raw_text": "", "experience": [{
        "company": "Synthetic Company", "role": "Engineer",
        "bullets": [{"id": "b1", "text": "Checked deployments.", "raw_text": "Checked deployments."}],
    }]}
    jd_text = "Python\nDocker\nRust\nRuby\nElixir\nKotlin"
    extraction = {
        "must_have": [
            {"skill": skill, "evidence_from_jd": skill, "type": "technical"} for skill in jd_text.splitlines()
        ],
        "good_to_have": [], "seniority": "mid", "primary_role_category": "SWE", "country_hint": "US",
    }

    with Session(engine) as db:
        db.add_all([User(user_id=owner), User(user_id=peer)])
        db.flush()
        db.add(ResumeDocument(
            id=document_id, user_id=owner, original_filename="synthetic.pdf", file_path="synthetic",
            file_type="pdf", raw_text="", parsed_json=resume,
        ))
        db.flush()
        db.add_all([
            ResumeVersion(id=version_id, resume_document_id=document_id, change_set=[], parsed_json=resume),
            JDEvaluation(id=jd_id, user_id=owner, resume_document_id=document_id, jd_text=jd_text,
                         extracted_requirements=extraction, diff_plan={}, match_score=0),
        ])
        jd_source = CareerApplicationService(db, owner).add_source(
            CareerSourceCreate(kind="job_description", content=jd_text),
        ).source
        target = CareerApplicationService(db, owner).create_target(CareerTargetInput(
            role_family="Platform Engineer", seniority="mid", job_description=jd_source,
        ))
        with monkeypatch.context() as fixed_id:
            fixed_id.setattr("app.application.evidence_service.uuid4", lambda: "earlier")
            _contribution(db, owner, "I used Python to verify two synthetic releases.")
        with monkeypatch.context() as fixed_id:
            fixed_id.setattr("app.application.evidence_service.uuid4", lambda: "later")
            confirmed = _contribution(db, owner, "• I used Python to double-check a synthetic release。")
        _contribution(db, owner, "I used Rust to verify two synthetic releases.")
        _contribution(db, owner, "I used Ruby to verify a synthetic release?")
        _contribution(db, owner, "I used Elixir to quadruple release throughput.")
        _contribution(db, owner, "I used Kotlin to split the traffic into thirds.")
        _contribution(db, peer, "I used Python to validate a peer-only synthetic release.")
        _contribution(db, owner, "I used Docker to run a private synthetic release.", private=True)
        _contribution(db, owner, "I used Go to build a synthetic tool.")
        other_target = CareerApplicationService(db, owner).create_target(CareerTargetInput(
            role_family="Platform Engineer", seniority="mid", job_description=jd_source,
        ))
        report = json.dumps({
            "schema_version": 1, "mode": "document_only", "target_id": target.target_id,
            "target_role": "Platform Engineer", "resume_version_id": version_id, "findings": [],
            "policy": {
                "schema_version": 1, "profile_id": "universal", "policy_version": "resume-review-v1",
                "universal_rules_version": "resume-review-v1", "market_overlay": "universal", "page_limit": 2,
            },
        })
        db.add(ResumeEvaluationV2(
            id=review_id, user_id=owner, resume_document_id=document_id, overall_score=0,
            bullet_flags=[], format_issues=[], ats_parseability=0, ats_raw_text="", model_version="fixture",
            grounded_review_ciphertext=cipher.encrypt(report.encode()).decode(),
        ))
        original_review = json.loads(report)
        original_review["resume_version_id"] = None
        db.add(ResumeEvaluationV2(
            id=original_review_id, user_id=owner, resume_document_id=document_id, overall_score=0,
            bullet_flags=[], format_issues=[], ats_parseability=0, ats_raw_text="", model_version="fixture",
            grounded_review_ciphertext=cipher.encrypt(json.dumps(original_review).encode()).decode(),
        ))
        db.commit()

        runtime = Mock(spec_set=[])
        service = JDTailoringApplicationService(db, runtime=runtime)
        request = dict(evaluation_id=jd_id, target_id=target.target_id,
                       resume_version_id=version_id, review_id=review_id)
        preview = service.preview_grounded(**request, user_id=owner)
        list_eligible = EvidenceService.list_eligible

        def reverse_eligible(ledger, **kwargs):
            return list_eligible(ledger, **kwargs)[::-1]

        monkeypatch.setattr(EvidenceService, "list_eligible", reverse_eligible)
        assert preview == service.preview_grounded(**request, user_id=owner)
        assert preview.resume_version_id == version_id
        assert preview.jd_source == jd_source
        [bullet] = preview.bullets
        assert (bullet.requirements[0].requirement_id, bullet.requirements[0].source_start, bullet.requirements[0].source_end) == (
            "must_have-1", 0, 6,
        )
        assert [(ref.evidence_id, ref.revision) for ref in bullet.plan.evidence_revisions] == [
            (confirmed.evidence_id, confirmed.revision),
        ]
        assert bullet.plan.policy_version == "resume-review-v1"
        assert bullet.plan.outcome is None
        assert bullet.text == "Used Python to double-check a synthetic release (team contribution: release checker)。"
        with pytest.raises(ResourceNotFoundError):
            service.preview_grounded(**request, user_id=peer)
        with pytest.raises(ResourceConflictError):
            service.preview_grounded(**{**request, "target_id": other_target.target_id}, user_id=owner)
        assert get_balance(db, owner) == 0
        db.rollback()

        def request_session():
            with Session(engine) as session:
                yield session

        monkeypatch.setitem(app.dependency_overrides, get_db, request_session)
        monkeypatch.setattr(auth, "decode_supabase_jwt", lambda token: {"sub": {"0": owner, "1": peer}[token]})
        owner_headers, peer_headers = ({"Authorization": f"Bearer {number}"} for number in (0, 1))
        body = {**request, "document_id": document_id}
        client = TestClient(app)
        with client:
            endpoint = "/api/v1/jd/grounded"
            assert client.post(endpoint + "/preview", json=body, headers=peer_headers).status_code == 404
            assert client.post(endpoint + "/preview", json=body).status_code == 401
            saved_context = {key: value for key, value in body.items() if key != "evaluation_id"}
            draft = client.post(endpoint + "/preview", json=saved_context, headers=owner_headers)
            assert draft.status_code == 200, draft.text
            assert draft.headers["cache-control"] == "no-store"
            assert draft.json()["evaluation_id"] == jd_id
            original = client.post(endpoint + "/preview", json={
                **saved_context, "resume_version_id": None, "review_id": original_review_id,
            }, headers=owner_headers)
            assert original.status_code == 200 and original.json()["resume_version_id"] is None
            [choice] = draft.json()["choices"]
            assert choice["plan_id"] == bullet.plan.plan_id
            request_body = {**body, "selections": {choice["plan_id"]: "safe"}}

            def apply():
                return client.post(endpoint + "/apply", json=request_body, headers=owner_headers)

            with ThreadPoolExecutor(max_workers=2) as workers:
                applied, repeat = [task.result(timeout=20) for task in (workers.submit(apply), workers.submit(apply))]
            assert applied.status_code == repeat.status_code == 200, (applied.text, repeat.text)
            version = applied.json()
            assert version["version_id"] == repeat.json()["version_id"]
            assert "double-check a synthetic release" in version["preview_html"]
            assert get_balance(db, owner) == 0
            library = f'/api/v1/tailored-resumes/{version["version_id"]}'
            detail = client.get(library, headers=owner_headers).json()
            assert detail["accepted_change_count"] == 1
            assert detail["grounded_claims"][0]["evidence_revisions"] == choice["evidence"]
            assert client.get(library, headers=peer_headers).status_code == 404
            grant_monthly(db, owner, 3)
            db.commit()
            downloaded = client.post(library + "/download", headers=owner_headers, json={})
            assert downloaded.status_code == 200, downloaded.text
            assert downloaded.headers["content-type"] == "application/pdf"
            pdf_text = " ".join((page.extract_text() or "") for page in PdfReader(BytesIO(downloaded.content)).pages)
            assert "double-check a synthetic release" in pdf_text
            assert "quadruple" not in pdf_text and "private synthetic release" not in pdf_text
            assert get_balance(db, owner) == 2

            async def replay_pdf(*_):
                return downloaded.content

            with monkeypatch.context() as crowded:
                crowded.setattr("app.application.tailored_resume_service._render_pdf", replay_pdf)
                crowded.setattr("app.application.tailored_resume_service.get_pdf_page_count", lambda _: 3)
                with ThreadPoolExecutor(max_workers=2) as workers:
                    requests = [workers.submit(client.post, library + "/download", headers=owner_headers, json={})
                                for _ in range(2)]
                    assert [request.result(timeout=20).status_code for request in requests] == [422, 422]
                assert get_balance(db, owner) == 2

            async def delete_during_render(*_):
                with Session(engine) as writer:
                    writer.execute(update(ResumeDocument).where(ResumeDocument.id == document_id)
                                   .values(storage_status="deleting"))
                    writer.commit()
                return downloaded.content

            with monkeypatch.context() as concurrent:
                concurrent.setattr("app.application.tailored_resume_service._render_pdf", delete_during_render)
                assert client.post(library + "/download", headers=owner_headers, json={}).status_code == 409
            assert get_balance(db, owner) == 2
            db.execute(update(ResumeDocument).where(ResumeDocument.id == document_id).values(storage_status="ready"))
            db.commit()

        read_review = ResumeApplicationService.get_grounded_review

        def revoke_during_preview(review_service, *args):
            review = read_review(review_service, *args)
            with Session(engine) as writer:
                EvidenceService(writer, owner).decide(confirmed.evidence_id, EvidenceDecisionInput(
                    revision=confirmed.revision, action="mark_private",
                ))
            return review

        with monkeypatch.context() as concurrent:
            concurrent.setattr(ResumeApplicationService, "get_grounded_review", revoke_during_preview)
            with pytest.raises(ResourceConflictError, match="Evidence changed"):
                service.preview_grounded(**request, user_id=owner)

        assert not service.preview_grounded(**request, user_id=owner).bullets
        db.rollback()
        with client:
            assert client.get(library, headers=owner_headers).status_code == 409
            assert client.post(library + "/download", headers=owner_headers, json={}).status_code == 409
            assert client.post(endpoint + "/apply", headers=owner_headers, json=request_body).status_code == 409
        assert get_balance(db, owner) == 2
        runtime.assert_not_called()


def _contribution(db, owner, claim, *, private=False):
    source = CareerApplicationService(db, owner).add_source(
        CareerSourceCreate(kind="candidate_introduction", content=claim),
    ).source
    ledger = EvidenceService(db, owner)
    proposal = ledger.propose(EvidenceProposal(
        claim=claim, category="action", ownership="team", scope="release checker",
        sources=[{**source.model_dump(), "relationship": "supports", "locator": "fixture",
                  "excerpt": claim, "extraction": "candidate"}],
    ))
    return ledger.decide(proposal.evidence_id, EvidenceDecisionInput(
        revision=proposal.revision, action="mark_private" if private else "confirm",
    ))
