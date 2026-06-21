from fastapi.security import HTTPAuthorizationCredentials


def test_frontend_log_user_id_is_derived_from_jwt(monkeypatch):
    from app.api.v1.endpoints import logs

    monkeypatch.setattr(logs, "decode_supabase_jwt", lambda token: {"sub": "verified-user"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    assert logs.get_verified_log_user_id(credentials) == "verified-user"


def test_frontend_log_user_id_ignores_missing_or_invalid_jwt(monkeypatch):
    from app.api.v1.endpoints import logs

    def raise_invalid(_token):
        raise ValueError("invalid")

    monkeypatch.setattr(logs, "decode_supabase_jwt", raise_invalid)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")

    assert logs.get_verified_log_user_id(None) is None
    assert logs.get_verified_log_user_id(credentials) is None
