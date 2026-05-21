"""Supabase Storage client for Phase 4 — class-based interface.

This module provides StorageClient with upload/download/signed_url/delete.
It intentionally does not reuse app.core.supabase_storage (Phase 2 helper)
to keep services/ decoupled from core/; both co-exist for one release.
"""
import os
from supabase import create_client, Client
from app.services.storage.exceptions import StorageUploadError, StorageDownloadError


class StorageClient:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("SUPABASE_STORAGE_BUCKET", "resumes")
        self._client: Client = create_client(
            os.getenv("SUPABASE_URL", "https://placeholder.supabase.co"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "placeholder"),
        )

    def _bucket(self):
        return self._client.storage.from_(self.bucket_name)

    def upload(self, user_id: str, file_id: str, content: bytes, filename: str) -> str:
        """Upload bytes to <user_id>/<file_id>_<filename>. Returns the storage path."""
        path = f"{user_id}/{file_id}_{filename}"
        try:
            self._bucket().upload(
                path,
                content,
                file_options={"content-type": "application/octet-stream"},
            )
        except Exception as e:
            raise StorageUploadError(str(e)) from e
        return path

    def signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Return a short-lived signed download URL for the given storage path."""
        try:
            resp = self._bucket().create_signed_url(path, expires_in)
        except Exception as e:
            raise StorageDownloadError(str(e)) from e
        return resp.get("signedURL") or resp.get("signed_url") or ""

    def download(self, path: str) -> bytes:
        """Download raw bytes from the given storage path."""
        try:
            return self._bucket().download(path)
        except Exception as e:
            raise StorageDownloadError(str(e)) from e

    def delete(self, path: str) -> None:
        """Delete a stored object."""
        self._bucket().remove([path])


# Module-level singleton — lazy-initialised on first call
_client_instance: StorageClient | None = None


def get_storage() -> StorageClient:
    """Return the shared StorageClient singleton."""
    global _client_instance
    if _client_instance is None:
        _client_instance = StorageClient()
    return _client_instance
