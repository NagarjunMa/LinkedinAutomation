import pytest
from unittest.mock import MagicMock, patch
from app.services.storage.supabase_storage import StorageClient


def test_upload_returns_path():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.upload.return_value = {"Key": "resume/u1/abc.pdf"}
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        path = client.upload(user_id="u1", file_id="abc", content=b"...", filename="r.pdf")
    assert path.startswith("u1/")
    assert path == "u1/abc.pdf"


def test_storage_path_does_not_include_user_controlled_filename():
    with patch("app.services.storage.supabase_storage.create_client"):
        client = StorageClient(bucket_name="resume")

    assert client.path_for("u1", "abc", "../../private resume.pdf") == "u1/abc.pdf"


def test_signed_url_returns_string():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.create_signed_url.return_value = {"signedURL": "https://x/y?token=z"}
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        url = client.signed_url("u1/abc.pdf", expires_in=3600)
    assert url.startswith("https://")


def test_download_returns_bytes():
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.download.return_value = b"file-bytes"
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        data = client.download("u1/abc.pdf")
    assert data == b"file-bytes"


def test_upload_raises_storage_upload_error_on_failure():
    from app.services.storage.exceptions import StorageUploadError
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.upload.side_effect = Exception("network error")
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        with pytest.raises(StorageUploadError):
            client.upload(user_id="u1", file_id="abc", content=b"data", filename="r.pdf")


def test_download_raises_storage_download_error_on_failure():
    from app.services.storage.exceptions import StorageDownloadError
    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.download.side_effect = Exception("not found")
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resumes")
        with pytest.raises(StorageDownloadError):
            client.download("u1/abc.pdf")


def test_delete_raises_typed_error_on_failure():
    from app.services.storage.exceptions import StorageDeleteError

    with patch("app.services.storage.supabase_storage.create_client") as mc:
        bucket = MagicMock()
        bucket.remove.side_effect = Exception("network error")
        mc.return_value.storage.from_.return_value = bucket
        client = StorageClient(bucket_name="resume")

        with pytest.raises(StorageDeleteError):
            client.delete("u1/abc.pdf")
