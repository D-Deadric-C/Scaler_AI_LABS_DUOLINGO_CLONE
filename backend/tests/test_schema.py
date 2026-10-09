import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError

from app.database import ensure_schema
from app.models import Exercise, ExerciseAttempt, LessonAttempt, User


@pytest.mark.parametrize(
    ("changes", "constraint"),
    [
        ({"hearts": 6}, "ck_users_hearts_range"),
        ({"hearts": -1}, "ck_users_hearts_range"),
        ({"gems": -5}, "ck_users_gems"),
        ({"total_xp": -1}, "ck_users_total_xp"),
        ({"daily_goal": 0}, "ck_users_daily_goal"),
        ({"current_streak": 20}, "ck_users_streaks"),
    ],
)
def test_database_rejects_invalid_learner_state(seeded_session, changes, constraint) -> None:
    user = seeded_session.scalar(select(User).where(User.username == "learner"))
    for field, value in changes.items():
        setattr(user, field, value)
    with pytest.raises(IntegrityError, match=constraint):
        seeded_session.commit()
    seeded_session.rollback()


def test_database_rejects_invalid_attempt_and_exercise_values(seeded_session) -> None:
    attempt = seeded_session.scalar(select(LessonAttempt))
    attempt.status = "paused"
    with pytest.raises(IntegrityError, match="ck_lesson_attempts_status"):
        seeded_session.commit()
    seeded_session.rollback()
    attempt = seeded_session.scalar(select(LessonAttempt))
    attempt.correct_count = attempt.current_index + 1
    with pytest.raises(IntegrityError, match="ck_lesson_attempts_progress"):
        seeded_session.commit()
    seeded_session.rollback()
    exercise = seeded_session.scalar(select(Exercise))
    exercise.type = "essay"
    with pytest.raises(IntegrityError, match="ck_exercises_type"):
        seeded_session.commit()
    seeded_session.rollback()


def test_deleting_an_attempt_removes_its_answers(seeded_session) -> None:
    attempt = seeded_session.scalar(select(LessonAttempt))
    assert seeded_session.scalar(select(func.count()).select_from(ExerciseAttempt)) == 5
    seeded_session.delete(attempt)
    seeded_session.commit()
    assert seeded_session.scalar(select(func.count()).select_from(ExerciseAttempt)) == 0


def test_ensure_schema_creates_missing_indexes_on_existing_tables(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'noindex.db'}")
    ensure_schema(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP INDEX ix_xp_events_user_created")
    ensure_schema(engine)
    with engine.connect() as connection:
        names = {row[1] for row in connection.exec_driver_sql("PRAGMA index_list('xp_events')")}
    assert "ix_xp_events_user_created" in names
    engine.dispose()


def test_legacy_exercise_attempts_table_is_rebuilt_with_turns(tmp_path) -> None:
    from sqlalchemy import text

    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql(
            "CREATE TABLE exercise_attempts (id INTEGER PRIMARY KEY, attempt_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, "
            "submitted_answer JSON NOT NULL, correct BOOLEAN NOT NULL, created_at DATETIME, UNIQUE (attempt_id, exercise_id))"
        )
        for row_id, (attempt_id, exercise_id) in enumerate([(1, 10), (1, 11), (2, 10)], start=1):
            connection.exec_driver_sql(f"INSERT INTO exercise_attempts VALUES ({row_id}, {attempt_id}, {exercise_id}, '{{}}', 1, NULL)")
    ensure_schema(engine)
    ensure_schema(engine)  # idempotent
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT attempt_id, exercise_id, turn FROM exercise_attempts ORDER BY id")).all()
        assert [tuple(row) for row in rows] == [(1, 10, 1), (1, 11, 2), (2, 10, 1)]
        connection.exec_driver_sql("INSERT INTO exercise_attempts (attempt_id, exercise_id, turn, submitted_answer, correct, created_at) VALUES (1, 10, 3, '{}', 0, CURRENT_TIMESTAMP)")  # a retry is now allowed
    engine.dispose()
