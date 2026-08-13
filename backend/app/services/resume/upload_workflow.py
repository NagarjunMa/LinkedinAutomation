"""Consistency workflow for resume database rows and Storage objects."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.models.jd_evaluation import JDEvaluation
from app.models.resume_document import ResumeDocument, ResumeVersion
from app.models.resume_evaluation_v2 import ResumeEvaluationV2
from app.models.resume_export import ResumeExport
from app.schemas.resume_v2 import ResumeDocumentJSON
from app.services.storage.exceptions import StorageError
from app.services.storage.supabase_storage import StorageClient


logger = logging.getLogger(__name__)

STORAGE_PENDING = "pending"
STORAGE_READY = "ready"
STORAGE_DELETING = "deleting"


class ResumeStorageWorkflowError(RuntimeError):
    """Stable boundary error for recoverable persistence failures."""


def get_owned_ready_resume(
    db: Session,
    resume_document_id: str,
    user_id: str,
) -> ResumeDocument | None:
    row = db.get(ResumeDocument, resume_document_id)
    if not row or row.user_id != user_id or row.storage_status != STORAGE_READY:
        return None
    return row


def create_resume_document(
    *,
    db: Session,
    storage: StorageClient,
    user_id: str,
    filename: str,
    extension: str,
    content: bytes,
    document: ResumeDocumentJSON,
) -> ResumeDocument:
    """Persist an explicit pending state before mutating external Storage."""

    document_id = str(uuid.uuid4())
    storage_path = storage.path_for(user_id, document_id, filename)
    row = ResumeDocument(
        id=document_id,
        user_id=user_id,
        original_filename=filename,
        file_path=storage_path,
        storage_path=storage_path,
        storage_status=STORAGE_PENDING,
        file_type=extension,
        parsed_json=document.model_dump(),
        raw_text=document.raw_text,
    )

    try:
        db.add(row)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise ResumeStorageWorkflowError("Resume record could not be created") from exc

    try:
        uploaded_path = storage.upload(
            user_id=user_id,
            file_id=document_id,
            content=content,
            filename=filename,
        )
        if uploaded_path != storage_path:
            try:
                storage.delete(uploaded_path)
            except StorageError:
                logger.exception(
                    "Unexpected resume object path requires reconciliation",
                    extra={"storage_path": uploaded_path},
                )
            raise ResumeStorageWorkflowError("Storage returned an unexpected object path")
    except Exception as exc:
        _remove_pending_row(db, row)
        if isinstance(exc, ResumeStorageWorkflowError):
            raise
        raise ResumeStorageWorkflowError("Resume storage is temporarily unavailable") from exc

    try:
        row.storage_status = STORAGE_READY
        db.commit()
        db.refresh(row)
    except Exception as exc:
        # The committed pending row remains a durable reconciliation record for
        # the uploaded object and is excluded from every user-facing workflow.
        db.rollback()
        raise ResumeStorageWorkflowError("Resume upload could not be finalized") from exc
    return row


def delete_resume_document(
    *,
    db: Session,
    storage: StorageClient,
    row: ResumeDocument,
    user_id: str,
) -> None:
    """Hide the row before deletion so failures never expose a broken document."""

    if row.user_id != user_id:
        raise ValueError("Resume ownership mismatch")

    if row.storage_status != STORAGE_DELETING:
        try:
            row.storage_status = STORAGE_DELETING
            db.commit()
        except Exception as exc:
            db.rollback()
            raise ResumeStorageWorkflowError("Resume deletion could not be started") from exc

    storage_path = row.storage_path or row.file_path
    try:
        if storage_path:
            storage.delete(storage_path)
    except StorageError as exc:
        raise ResumeStorageWorkflowError("Resume storage deletion is temporarily unavailable") from exc

    try:
        db.query(ResumeExport).filter(
            ResumeExport.user_id == user_id,
            ResumeExport.resume_document_id == row.id,
        ).delete(synchronize_session=False)
        db.query(ResumeEvaluationV2).filter(
            ResumeEvaluationV2.user_id == user_id,
            ResumeEvaluationV2.resume_document_id == row.id,
        ).delete(synchronize_session=False)
        db.query(ResumeVersion).filter(
            ResumeVersion.resume_document_id == row.id,
        ).delete(synchronize_session=False)
        db.query(JDEvaluation).filter(
            JDEvaluation.user_id == user_id,
            JDEvaluation.resume_document_id == row.id,
        ).delete(synchronize_session=False)
        db.delete(row)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise ResumeStorageWorkflowError("Resume deletion could not be finalized") from exc


def _remove_pending_row(db: Session, row: ResumeDocument) -> None:
    try:
        db.delete(row)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Pending resume row requires reconciliation",
            extra={"resume_document_id": row.id},
        )
