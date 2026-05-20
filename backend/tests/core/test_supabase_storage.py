from unittest.mock import MagicMock, patch


def test_upload_pdf_calls_supabase_storage(monkeypatch):
    from app.core import supabase_storage as ss
    fake_client = MagicMock()
    fake_bucket = MagicMock()
    fake_client.storage.from_.return_value = fake_bucket
    monkeypatch.setattr(ss, "_get_client", lambda: fake_client)

    path = ss.upload_pdf(b"%PDF-fake", "user-1/exp-1.pdf")
    fake_client.storage.from_.assert_called_once_with(ss.settings.SUPABASE_STORAGE_BUCKET)
    fake_bucket.upload.assert_called_once()
    args, kwargs = fake_bucket.upload.call_args
    # path is first positional; file is second; options carry content-type
    assert "user-1/exp-1.pdf" in args
    assert path == "user-1/exp-1.pdf"


def test_signed_url_returns_url(monkeypatch):
    from app.core import supabase_storage as ss
    fake_client = MagicMock()
    fake_bucket = MagicMock()
    fake_bucket.create_signed_url.return_value = {"signedURL": "https://x/file.pdf?token=abc"}
    fake_client.storage.from_.return_value = fake_bucket
    monkeypatch.setattr(ss, "_get_client", lambda: fake_client)

    url = ss.signed_url("user-1/exp-1.pdf", ttl_seconds=3600)
    assert url == "https://x/file.pdf?token=abc"
    fake_bucket.create_signed_url.assert_called_once_with("user-1/exp-1.pdf", 3600)
