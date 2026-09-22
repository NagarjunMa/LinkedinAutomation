"""Exercise real PyJWT/JWKS transport through the mounted optional-auth routes."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core import auth
from app.api.v1.endpoints import logs


@pytest.mark.parametrize("path", ["/api/v1/logs/frontend", "/api/v1/logs/frontend/batch"])
def test_jwks_outage_then_recovery_preserves_identity(client, monkeypatch, path):
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = jwt.algorithms.ECAlgorithm.to_jwk(key.public_key(), as_dict=True)
    jwk.update(kid="local-fixture", use="sig", alg="ES256")
    state = {"available": False, "requests": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            state["requests"] += 1
            self.send_response(200 if state["available"] else 503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"keys": [jwk]}).encode() if state["available"] else b"unavailable")

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        jwks = jwt.PyJWKClient(f"http://127.0.0.1:{server.server_port}/jwks", timeout=1)
        monkeypatch.setattr(auth, "_jwks_client", lambda: jwks)
        logger = Mock()
        monkeypatch.setattr(logs, "get_logger", lambda: logger)
        monkeypatch.delitem(client.app.dependency_overrides, auth.get_current_user_id, raising=False)
        monkeypatch.delitem(client.app.dependency_overrides, auth.get_authenticated_user_id, raising=False)
        token = jwt.encode({"sub": "transport-user", "aud": "authenticated",
                            "iss": "https://test.supabase.co/auth/v1", "exp": int(time.time()) + 120},
                           key, algorithm="ES256", headers={"kid": "local-fixture"})
        entry = {"errorId": "transport", "message": "synthetic", "level": "info",
                 "url": "https://example.test", "userAgent": "test", "userId": "spoofed"}
        payload = {"logs": [entry]} if path.endswith("/batch") else entry
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 503
        assert response.json()["detail"] == "Authentication service unavailable"
        assert logger.mock_calls == []
        state["available"] = True
        response = client.post(path, json=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["processed"] == 1
        logger.info.assert_called_once()
        assert logger.info.call_args.kwargs["extra"]["user_id"] == "transport-user"
        assert state["requests"] == 2
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
