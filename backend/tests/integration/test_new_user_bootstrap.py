"""Integration tests: new-user bootstrap — freemium credits + empty profile.

These tests verify that:
1. bootstrap_account creates a users row + grants 90 monthly credits on
   first call, and is idempotent on subsequent calls.
2. GET /api/v1/user-profiles/{user_id} returns 200 with exists=False for
   a user that has no UserProfile row yet.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.credits.ledger import grant_monthly, get_balance
from app.application.bootstrap import bootstrap_account


# ---------------------------------------------------------------------------
# Unit-level: bootstrap_account
# ---------------------------------------------------------------------------


def testbootstrap_account_creates_user_and_grants_monthly_credits(db_session: Session):
    """First call should insert users row and grant 90 monthly credits."""
    user_id = "new-user-bootstrap-1"
    email = "bootstrap1@example.com"

    assert db_session.query(User).filter(User.user_id == user_id).first() is None

    bootstrap_account(db_session, user_id=user_id, email=email)

    user = db_session.query(User).filter(User.user_id == user_id).first()
    assert user is not None
    assert user.email == email

    balance = get_balance(db_session, user_id)
    assert balance == 90, f"Expected 90 monthly freemium credits, got {balance}"


def testbootstrap_account_is_idempotent(db_session: Session):
    """Calling bootstrap_account twice must NOT double-grant credits."""
    user_id = "new-user-bootstrap-2"
    email = "bootstrap2@example.com"

    bootstrap_account(db_session, user_id=user_id, email=email)
    bootstrap_account(db_session, user_id=user_id, email=email)  # second call — must be no-op

    balance = get_balance(db_session, user_id)
    assert balance == 90, f"Expected 90 credits after idempotent call, got {balance}"


def testbootstrap_account_backfills_existing_user_current_month(db_session: Session):
    """An existing account is never a first-sign-in grant recipient."""
    user_id = "existing-user-no-grant"
    email = "existing@example.com"

    # Pre-insert the user row with 5 credits already.
    db_session.add(User(user_id=user_id, email=email))
    db_session.commit()
    grant_monthly(db_session, user_id=user_id, amount=5)
    db_session.commit()

    bootstrap_account(db_session, user_id=user_id, email=email)
    bootstrap_account(db_session, user_id=user_id, email=email)

    balance = get_balance(db_session, user_id)
    assert balance == 5


# ---------------------------------------------------------------------------
# HTTP-level: empty profile for new users
# ---------------------------------------------------------------------------


def test_get_profile_returns_empty_for_new_user(client, db_session: Session, test_user_id: str):
    """GET /api/v1/user-profiles/{user_id} returns 200 with exists=False."""
    response = client.get(f"/api/v1/user-profiles/{test_user_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == test_user_id
    assert data["exists"] is False
    assert data["full_name"] == ""
    assert data["programming_languages"] == []
    assert data["total_applications"] == 0


def test_get_profile_derives_from_latest_resume_document(client, db_session: Session, test_user_id: str):
    """Profile endpoint uses resume v2 data when the legacy profile row is absent."""
    from app.models.resume_document import ResumeDocument

    db_session.add(
        ResumeDocument(
            id="resume-doc-1",
            user_id=test_user_id,
            original_filename="resume.pdf",
            file_path="u/resume.pdf",
            storage_path="u/resume.pdf",
            file_type="pdf",
            raw_text="Nagarjun Mallesh",
            parsed_json={
                "contact": {
                    "name": "Nagarjun Mallesh",
                    "email": "nagarjun@example.com",
                    "phone": "+1 555 123 4567",
                    "links": [],
                },
                "summary": "Backend engineer building AI systems.",
                "experience": [
                    {
                        "company": "ML Technologies LLC",
                        "role": "Systems Analyst / Software Engineer",
                        "location": "Boston, MA",
                        "dates": "Jul 2025 - Present",
                        "bullets": [
                            {"id": "b1", "text": "Built RAG systems.", "raw_text": "Built RAG systems."}
                        ],
                    }
                ],
                "education": [
                    {
                        "school": "Northeastern University",
                        "degree": "MS Information Systems",
                        "location": "Boston, MA",
                        "dates": "2022-2024",
                    }
                ],
                "skills": {"hard": ["Python", "FastAPI"], "soft": []},
                "projects": [],
                "certifications": [],
                "raw_text": "Nagarjun Mallesh",
            },
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/user-profiles/{test_user_id}")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["full_name"] == "Nagarjun Mallesh"
    assert data["email"] == "nagarjun@example.com"
    assert data["location"] == "Boston, MA"
    assert data["total_resumes"] == 1
    assert data["job_titles"] == ["Systems Analyst / Software Engineer"]
    assert data["companies"] == ["ML Technologies LLC"]
    assert len(data["work_experiences"]) == 1
    assert data["degrees"] == ["MS Information Systems"]
    assert data["institutions"] == ["Northeastern University"]
    assert data["programming_languages"] == ["Python", "FastAPI"]


def test_get_profile_ignores_non_ready_resume_documents(
    client,
    db_session: Session,
    test_user_id: str,
):
    from app.models.resume_document import ResumeDocument

    db_session.add(
        ResumeDocument(
            id="pending-resume",
            user_id=test_user_id,
            original_filename="pending.pdf",
            file_path=f"{test_user_id}/pending-resume.pdf",
            storage_path=f"{test_user_id}/pending-resume.pdf",
            storage_status="pending",
            file_type="pdf",
            raw_text="Pending Candidate",
            parsed_json={"contact": {"name": "Pending Candidate"}, "raw_text": "Pending Candidate"},
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/user-profiles/{test_user_id}")

    assert response.status_code == 200
    assert response.json()["exists"] is False
