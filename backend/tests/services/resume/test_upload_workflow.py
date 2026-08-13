from unittest.mock import MagicMock

import pytest

from app.models.resume_document import ResumeDocument
from app.schemas.resume_v2 import Contact, ResumeDocumentJSON
from app.services.resume.upload_workflow import (
    STORAGE_DELETING,
    STORAGE_PENDING,
    STORAGE_READY,
    ResumeStorageWorkflowError,
    create_resume_document,
    delete_resume_document,
)
from app.services.storage.exceptions import StorageDeleteError, StorageUploadError


def _document() -> ResumeDocumentJSON:
    return ResumeDocumentJSON(
        contact=Contact(name="Test User", email="test@example.com"),
        raw_text="Test User\ntest@example.com",
    )


def _storage() -> MagicMock:
    storage = MagicMock()
    storage.path_for.side_effect = (
        lambda user_id, file_id, filename: f"{user_id}/{file_id}.{filename.rsplit('.', 1)[-1]}"
    )
    storage.upload.side_effect = (
        lambda user_id, file_id, content, filename: storage.path_for(user_id, file_id, filename)
    )
    return storage


def test_upload_transitions_from_pending_to_ready(db_session, test_user_id):
    storage = _storage()

    row = create_resume_document(
        db=db_session,
        storage=storage,
        user_id=test_user_id,
        filename="resume.pdf",
        extension="pdf",
        content=b"%PDF-1.4",
        document=_document(),
    )

    assert row.storage_status == STORAGE_READY
    assert row.storage_path == f"{test_user_id}/{row.id}.pdf"
    storage.upload.assert_called_once()


def test_storage_failure_removes_pending_database_row(db_session, test_user_id):
    storage = _storage()
    storage.upload.side_effect = StorageUploadError("offline")

    with pytest.raises(ResumeStorageWorkflowError, match="temporarily unavailable"):
        create_resume_document(
            db=db_session,
            storage=storage,
            user_id=test_user_id,
            filename="resume.pdf",
            extension="pdf",
            content=b"%PDF-1.4",
            document=_document(),
        )

    assert db_session.query(ResumeDocument).filter_by(user_id=test_user_id).count() == 0


def test_unexpected_storage_path_is_removed_and_pending_row_is_compensated(
    db_session,
    test_user_id,
):
    storage = _storage()
    storage.upload.side_effect = None
    storage.upload.return_value = f"{test_user_id}/unexpected.pdf"

    with pytest.raises(ResumeStorageWorkflowError, match="unexpected object path"):
        create_resume_document(
            db=db_session,
            storage=storage,
            user_id=test_user_id,
            filename="resume.pdf",
            extension="pdf",
            content=b"%PDF-1.4",
            document=_document(),
        )

    storage.delete.assert_called_once_with(f"{test_user_id}/unexpected.pdf")
    assert db_session.query(ResumeDocument).filter_by(user_id=test_user_id).count() == 0


def test_finalize_failure_keeps_durable_pending_row(
    db_session,
    test_user_id,
    monkeypatch,
):
    storage = _storage()
    original_commit = db_session.commit
    commit_count = 0

    def fail_second_commit():
        nonlocal commit_count
        commit_count += 1
        if commit_count == 2:
            raise RuntimeError("database unavailable")
        return original_commit()

    monkeypatch.setattr(db_session, "commit", fail_second_commit)

    with pytest.raises(ResumeStorageWorkflowError, match="finalized"):
        create_resume_document(
            db=db_session,
            storage=storage,
            user_id=test_user_id,
            filename="resume.pdf",
            extension="pdf",
            content=b"%PDF-1.4",
            document=_document(),
        )

    row = db_session.query(ResumeDocument).filter_by(user_id=test_user_id).one()
    assert row.storage_status == STORAGE_PENDING
    storage.upload.assert_called_once()


def test_delete_failure_leaves_hidden_retryable_state(db_session, test_user_id):
    storage = _storage()
    row = create_resume_document(
        db=db_session,
        storage=storage,
        user_id=test_user_id,
        filename="resume.pdf",
        extension="pdf",
        content=b"%PDF-1.4",
        document=_document(),
    )
    storage.delete.side_effect = StorageDeleteError("offline")

    with pytest.raises(ResumeStorageWorkflowError, match="temporarily unavailable"):
        delete_resume_document(
            db=db_session,
            storage=storage,
            row=row,
            user_id=test_user_id,
        )

    db_session.refresh(row)
    assert row.storage_status == STORAGE_DELETING
