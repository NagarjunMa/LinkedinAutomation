"""Optional authentication is enforced before either logging route writes."""

import time
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.exceptions import PyJWKClientConnectionError

from app.core import auth
from app.core.rate_limiter import RateLimiter
from app.api.v1.endpoints import logs


@pytest.fixture(params=["/api/v1/logs/frontend", "/api/v1/logs/frontend/batch"])
def log_request(request, client, monkeypatch):
    logger = Mock()
    monkeypatch.setattr(logs, "get_logger", lambda: logger)
    monkeypatch.setattr(logs, "rate_limiter", RateLimiter())
    monkeypatch.delitem(client.app.dependency_overrides, auth.get_current_user_id, raising=False)
    monkeypatch.delitem(client.app.dependency_overrides, auth.get_authenticated_user_id, raising=False)
    entry = {"errorId": "auth-contract", "message": "synthetic event", "level": "info",
             "url": "https://example.test", "userAgent": "test", "userId": "spoofed-user"}
    payload = {"logs": [entry, dict(entry, errorId="second")]} if request.param.endswith("/batch") else entry

    def post(headers=None):
        return client.post(request.param, json=payload, headers=headers)

    return post, logger, 2 if request.param.endswith("/batch") else 1


@pytest.fixture
def signed_token(monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    client = Mock()
    client.get_signing_key_from_jwt.return_value = SimpleNamespace(key=key.public_key())
    monkeypatch.setattr(auth, "_jwks_client", lambda: client)

    def make(fault=None):
        claims = {"sub": "verified-user", "aud": "authenticated",
                  "iss": "https://test.supabase.co/auth/v1", "exp": int(time.time()) + 120}
        signing_key = key
        if fault == "expired":
            claims["exp"] = int(time.time()) - 120
        elif fault == "issuer":
            claims["iss"] = "https://foreign.example/auth/v1"
        elif fault == "audience":
            claims["aud"] = "another-app"
        elif fault == "missing-sub":
            del claims["sub"]
        elif fault == "empty-sub":
            claims["sub"] = ""
        elif fault == "invalid-sub":
            claims["sub"] = ["verified-user"]
        elif fault == "signature":
            signing_key = ec.generate_private_key(ec.SECP256R1())
        return jwt.encode(claims, signing_key, algorithm="ES256", headers={"kid": "synthetic"})

    return make


def test_absent_credentials_allow_anonymous_logs_without_provider_access(log_request, monkeypatch):
    provider = Mock(side_effect=AssertionError("anonymous request accessed provider"))
    monkeypatch.setattr(auth, "_jwks_client", provider)
    post, logger, count = log_request
    response = post()
    assert response.status_code == 200
    assert response.json()["processed"] == count
    provider.assert_not_called()
    assert logger.info.call_count == count
    for call in logger.info.call_args_list:
        assert call.kwargs["extra"]["user_id"] is None
        assert "authenticated" not in call.kwargs["extra"]


@pytest.mark.parametrize("scheme", ["Bearer", "bearer"])
def test_signed_identity_overrides_caller_supplied_attribution(log_request, signed_token, scheme):
    post, logger, count = log_request
    response = post({"Authorization": f"{scheme} {signed_token()}"})
    assert response.status_code == 200
    assert response.json()["processed"] == count
    assert logger.info.call_count == count
    for call in logger.info.call_args_list:
        assert call.kwargs["extra"]["user_id"] == "verified-user"
        assert call.kwargs["extra"]["authenticated"] is True


@pytest.mark.parametrize("authorization", ["", "Bearer", "Bearer ", "Basic abc", "not-bearer", "Bearer malformed"])
def test_present_invalid_credentials_never_become_anonymous(log_request, authorization):
    post, logger, _ = log_request
    response = post({"Authorization": authorization})
    assert response.status_code == 401
    assert logger.mock_calls == []


@pytest.mark.parametrize("fault", ["expired", "issuer", "audience", "signature", "missing-sub", "empty-sub", "invalid-sub"])
def test_rejected_signed_tokens_do_not_write_logs(log_request, signed_token, fault):
    post, logger, _ = log_request
    response = post({"Authorization": f"Bearer {signed_token(fault)}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired authentication token"
    assert logger.mock_calls == []


def test_provider_outage_stays_503_and_does_not_write_logs(log_request, monkeypatch):
    client = Mock()
    client.get_signing_key_from_jwt.side_effect = PyJWKClientConnectionError("private provider details")
    monkeypatch.setattr(auth, "_jwks_client", lambda: client)
    post, logger, _ = log_request
    response = post({"Authorization": "Bearer unavailable"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Authentication service unavailable"
    assert "private provider" not in response.text
    assert logger.mock_calls == []


@pytest.mark.parametrize("failure_status", [401, 503])
def test_rotating_rejected_credentials_consume_ip_budget_before_authentication(
    log_request, monkeypatch, failure_status,
):
    from fastapi import HTTPException

    post, logger, batch_cost = log_request
    # Two single requests or two batches fit; varying credentials must not
    # create a fresh IP budget or reach the provider after it is exhausted.
    monkeypatch.setattr(logs, "rate_limiter", RateLimiter(max_requests=2 * batch_cost))
    verify = Mock(side_effect=HTTPException(status_code=failure_status, detail="synthetic denial"))
    monkeypatch.setattr(auth, "decode_supabase_jwt", verify)
    responses = [post({"Authorization": f"Bearer rotated-{i}"}) for i in range(3)]
    assert [r.status_code for r in responses] == [failure_status, failure_status, 429]
    assert verify.call_count == 2
    assert logger.mock_calls == []
