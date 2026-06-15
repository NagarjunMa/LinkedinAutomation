"""Supabase Storage client + PDF helpers for Phase 2 exports."""
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def upload_pdf(pdf_bytes: bytes, storage_path: str) -> str:
    """Upload PDF bytes to the configured bucket. Returns the storage path."""
    bucket = _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
    bucket.upload(
        storage_path,
        pdf_bytes,
        {"content-type": "application/pdf", "upsert": "true"},
    )
    return storage_path


def download_pdf(storage_path: str) -> bytes:
    """Download PDF bytes from the configured bucket."""
    bucket = _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
    return bucket.download(storage_path)


def signed_url(storage_path: str, ttl_seconds: Optional[int] = None) -> str:
    """Return a signed download URL for the stored PDF."""
    ttl = ttl_seconds if ttl_seconds is not None else settings.SUPABASE_SIGNED_URL_TTL_SECONDS
    bucket = _get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET)
    resp = bucket.create_signed_url(storage_path, ttl)
    # supabase-py returns the URL under either "signedURL" or "signed_url" depending on version.
    return resp.get("signedURL") or resp["signed_url"]
