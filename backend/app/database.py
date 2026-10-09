from collections.abc import Iterator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .core.config import database_url




class Base(DeclarativeBase):
    pass


engine = create_engine(
    database_url(),
    connect_args={"check_same_thread": False, "timeout": 15},
)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=15000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _rebuild_legacy_exercise_attempts(connection) -> None:
    """Databases from before wrong answers were retried allowed one answer per exercise; rebuild that table."""
    inspector = inspect(connection)
    if "exercise_attempts" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("exercise_attempts")}
    legacy_unique = any(set(constraint["column_names"]) == {"attempt_id", "exercise_id"} for constraint in inspector.get_unique_constraints("exercise_attempts"))
    if "turn" in columns and not legacy_unique:
        return
    connection.exec_driver_sql(
        "CREATE TABLE exercise_attempts_old AS SELECT id, attempt_id, exercise_id, submitted_answer, correct, COALESCE(created_at, CURRENT_TIMESTAMP) AS created_at, "
        "ROW_NUMBER() OVER (PARTITION BY attempt_id ORDER BY id) AS turn FROM exercise_attempts"
    )
    connection.exec_driver_sql("DROP TABLE exercise_attempts")
    Base.metadata.tables["exercise_attempts"].create(connection)
    connection.exec_driver_sql(
        "INSERT INTO exercise_attempts (id, attempt_id, exercise_id, submitted_answer, correct, created_at, turn) "
        "SELECT id, attempt_id, exercise_id, submitted_answer, correct, created_at, turn FROM exercise_attempts_old"
    )
    connection.exec_driver_sql("DROP TABLE exercise_attempts_old")


def ensure_schema(bind=None) -> None:
    """Create missing tables, columns and indexes (lightweight stand-in for migrations).

    CHECK constraints are enforced on freshly created databases; SQLite cannot add them to existing tables.
    """
    target = bind or engine
    Base.metadata.create_all(bind=target)
    with target.begin() as connection:
        _rebuild_legacy_exercise_attempts(connection)
    inspector = inspect(target)
    with target.begin() as connection:
        for table in Base.metadata.sorted_tables:
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                if not column.nullable and column.default is None and column.server_default is None:
                    raise RuntimeError(f"Cannot auto-add required column {table.name}.{column.name}")
                ddl_type = column.type.compile(dialect=target.dialect)
                connection.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {ddl_type}'))
            for column in table.columns:  # required columns added earlier (or by a failed upgrade) may hold NULLs: give them their default
                if not column.nullable and column.default is not None and column.default.is_scalar:
                    connection.execute(text(f'UPDATE "{table.name}" SET "{column.name}" = :value WHERE "{column.name}" IS NULL'), {"value": column.default.arg})
            for index in table.indexes:
                index.create(connection, checkfirst=True)
