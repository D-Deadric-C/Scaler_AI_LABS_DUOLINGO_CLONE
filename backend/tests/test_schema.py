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
