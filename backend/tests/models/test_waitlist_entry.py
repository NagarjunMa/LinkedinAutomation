from datetime import datetime, timedelta, timezone

from app.models.waitlist_entry import WaitlistEntry
from scripts.purge_expired_waitlist import purge_expired


def _entry(email: str, expires_at: datetime) -> WaitlistEntry:
    return WaitlistEntry(
        normalized_email=email,
        consent_granted=True,
        consent_version="test",
        consented_at=datetime.now(timezone.utc),
        retention_expires_at=expires_at,
    )


def test_retention_purge_deletes_only_expired_entries(db_session):
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            _entry("expired@example.com", now - timedelta(days=1)),
            _entry("active@example.com", now + timedelta(days=1)),
        ]
    )
    db_session.commit()

    assert purge_expired(db_session, dry_run=True) == 1
    assert db_session.query(WaitlistEntry).count() == 2

    assert purge_expired(db_session, dry_run=False) == 1
    assert [row.normalized_email for row in db_session.query(WaitlistEntry).all()] == [
        "active@example.com"
    ]
