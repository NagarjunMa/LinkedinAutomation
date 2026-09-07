import pytest

from scripts.verify_public_preview_release import (
    GateFailure,
    _origin,
    verify_supabase_auth,
)


class FakeResponse:
    def __init__(self, *, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


@pytest.mark.parametrize(
    "value",
    [
        "http://www.prismpro.live",
        "https://*.prismpro.live",
        "https://user:password@www.prismpro.live",
        "https://www.prismpro.live/api",
        "https://www.prismpro.live?preview=true",
        "https://WWW.prismpro.live",
        "https://www.prismpro.live:443",
        "https://www.prism pro.live",
    ],
)
def test_origin_rejects_values_that_are_not_exact_https_origins(value):
    with pytest.raises(GateFailure):
        _origin(value)


def test_origin_allows_local_http_only_when_explicitly_requested():
    assert _origin("http://localhost:8000/", allow_http=True) == "http://localhost:8000"

    with pytest.raises(GateFailure):
        _origin("http://localhost:8000/")


def test_supabase_auth_gate_requires_signup_and_anonymous_access_disabled():
    session = FakeSession(
        FakeResponse(
            payload={
                "disable_signup": True,
                "external_anonymous_users_enabled": False,
            }
        )
    )

    verify_supabase_auth(
        session,
        project_ref="abcdefghijklmnopqrst",
        access_token="not-logged",
    )

    url, kwargs = session.calls[0]
    assert url.endswith("/projects/abcdefghijklmnopqrst/config/auth")
    assert kwargs["headers"]["Authorization"] == "Bearer not-logged"
    assert kwargs["timeout"] == 15


@pytest.mark.parametrize(
    "payload, expected",
    [
        (
            {"disable_signup": False, "external_anonymous_users_enabled": False},
            "public signup is still enabled",
        ),
        (
            {"disable_signup": True, "external_anonymous_users_enabled": True},
            "anonymous sign-in is still enabled",
        ),
    ],
)
def test_supabase_auth_gate_fails_closed(payload, expected):
    session = FakeSession(FakeResponse(payload=payload))

    with pytest.raises(GateFailure, match=expected):
        verify_supabase_auth(
            session,
            project_ref="abcdefghijklmnopqrst",
            access_token="not-logged",
        )


def test_supabase_auth_gate_rejects_unexpected_project_ref():
    session = FakeSession(FakeResponse())

    with pytest.raises(GateFailure, match="project ref"):
        verify_supabase_auth(
            session,
            project_ref="wrong-project",
            access_token="not-logged",
        )

    assert session.calls == []
