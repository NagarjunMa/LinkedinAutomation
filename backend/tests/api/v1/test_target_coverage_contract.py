from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.endpoints import career_targets
from app.application.career_service import CareerApplicationService
from app.application.errors import ResourceNotFoundError
from app.repositories.career_repository import CareerRepository
from app.schemas.career.sources import CareerTarget


@pytest.fixture
def coverage_http(monkeypatch):
    target = CareerTarget(
        schema_version=1, target_id="target", owner_id="owner", role_family="Platform Engineer",
        seniority="Entry level", status="active", desired_work=["Python"],
    )

    def identity(authorization: str | None = Header(default=None)):
        if authorization is None:
            raise HTTPException(status_code=401)
        return authorization.removeprefix("Bearer ")

    def get_target(service, target_id):
        if service.repo.user_id != target.owner_id or target_id != target.target_id:
            raise ResourceNotFoundError("Target not found")
        return target

    def ready_resume(repo, resume_document_id):
        if repo.user_id == "owner" and resume_document_id == "resume":
            return SimpleNamespace(parsed_json={"contact": {"name": "Fixture"}, "raw_text": ""})
        return None

    app = FastAPI()
    app.include_router(career_targets.router)
    app.dependency_overrides[career_targets.get_db] = object
    app.dependency_overrides[career_targets.get_current_user_id] = identity
    monkeypatch.setattr(CareerApplicationService, "get_target", get_target)
    monkeypatch.setattr(CareerApplicationService, "_coverage_evidence", lambda *_: [])
    monkeypatch.setattr(CareerRepository, "ready_resume", ready_resume)
    return TestClient(app)


@pytest.mark.parametrize("suffix", ["", "/resume/resume"])
def test_coverage_details_are_opt_in_under_the_existing_owned_routes(coverage_http, suffix):
    path = "/career/targets/target/coverage" + suffix
    headers = {"Authorization": "Bearer owner"}
    legacy = coverage_http.get(path, headers=headers)
    assert legacy.status_code == 200 and legacy.headers["Cache-Control"] == "no-store"
    legacy_view = legacy.json()["coverage"] if suffix else legacy.json()
    assert legacy_view == {
        "schema_version": 1, "target_id": "target", "policy_version": "target-coverage-v1",
        "positioning_reason": None, "focus": [{
            "label": "Python", "state": "experience_gap", "reason_code": "no_matching_confirmed_evidence",
            "evidence": None, "evidence_support": None,
        }],
    }

    detailed = coverage_http.get(path, headers=headers, params={"required_scope": "cross_team"})
    assert detailed.status_code == 200 and detailed.headers["Cache-Control"] == "no-store"
    view = detailed.json()["coverage"] if suffix else detailed.json()
    assert view["policy_version"] == "target-coverage-v2"
    assert view["details"]["target_level"] == "entry"
    assert view["details"]["required_scope"] == "cross_team"
    assert view["details"]["focus"][0]["scope"] == {"state": "unavailable", "observed_scope": None}

    assert coverage_http.get(path + "?explain=true").status_code == 401
    assert coverage_http.get(path + "?explain=true", headers={"Authorization": "Bearer other"}).status_code == 404
    assert coverage_http.get(path + "?required_scope=prestigious", headers=headers).status_code == 422
    if suffix:
        assert coverage_http.get(path + "-foreign?explain=true", headers=headers).status_code == 404
