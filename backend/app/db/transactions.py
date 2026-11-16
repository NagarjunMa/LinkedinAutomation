"""Checks shared by writes that read fresh PostgreSQL state after taking a lock."""

from sqlalchemy.engine import Connection


def is_transactional_read_committed(connection: Connection) -> bool:
    # SQLAlchemy's isolation level does not report DBAPI autocommit.
    driver = connection.connection.dbapi_connection
    return not driver.autocommit and connection.get_isolation_level() == "READ COMMITTED"
