from unittest.mock import MagicMock

import pytest

from app.application.errors import ApplicationError
from app.application.job_service import JobApplicationService
from app.schemas.job import JobListingCreate


def test_write_failure_rolls_back_and_returns_stable_error(db_session, monkeypatch):
    rollback = MagicMock(wraps=db_session.rollback)
    monkeypatch.setattr(db_session, "rollback", rollback)
    monkeypatch.setattr(
        db_session,
        "commit",
        MagicMock(side_effect=RuntimeError("database-secret-detail")),
    )
    service = JobApplicationService(db_session)

    with pytest.raises(ApplicationError) as raised:
        service.create(
            "test-user-1",
            JobListingCreate(title="Engineer", company="Prism"),
        )

    assert str(raised.value) == "Unable to update job applications"
    assert "database-secret-detail" not in str(raised.value)
    rollback.assert_called_once()
