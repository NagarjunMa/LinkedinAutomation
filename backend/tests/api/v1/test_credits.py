"""Tests for credits balance endpoint (Task 19)."""
import os
os.environ.setdefault("OPENAI_API_KEY", "test")

from fastapi.testclient import TestClient


def test_balance_returns_zero_when_no_credits(client: TestClient, auth_headers):
    """GET /credits/balance returns 0 when user has no credit entries."""
    resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "balance" in data
    assert data["balance"] == 0


def test_balance_returns_granted_amount(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """After a grant, GET /credits/balance returns the granted balance."""
    from app.services.credits.ledger import grant_monthly
    grant_monthly(db_session, test_user_id, 20)
    db_session.commit()

    resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["balance"] == 20


def test_balance_reflects_debit(
    client: TestClient, auth_headers, db_session, test_user_id
):
    """After grant + debit, balance reflects the net amount."""
    from app.services.credits.ledger import grant_monthly, debit
    grant_monthly(db_session, test_user_id, 10)
    debit(db_session, test_user_id, amount=3, reason="evaluate")
    db_session.commit()

    resp = client.get("/api/v1/credits/balance", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["balance"] == 7
