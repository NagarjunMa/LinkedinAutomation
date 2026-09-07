"""Delete waitlist records whose configured retention deadline has passed."""

import argparse
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.waitlist_entry import WaitlistEntry


def purge_expired(db: Session, *, dry_run: bool) -> int:
    query = db.query(WaitlistEntry).filter(
        WaitlistEntry.retention_expires_at <= datetime.now(timezone.utc)
    )
    count = query.count()
    if not dry_run and count:
        query.delete(synchronize_session=False)
        db.commit()
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Purge PrismPro waitlist entries after their retention deadline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the number eligible for deletion without deleting records.",
    )
    args = parser.parse_args()
    with SessionLocal() as database:
        affected = purge_expired(database, dry_run=args.dry_run)
    action = "eligible" if args.dry_run else "deleted"
    print(f"Waitlist records {action}: {affected}")
