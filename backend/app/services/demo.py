"""Demo tooling: restore the sample learner or fast-forward time (used by the dev endpoints)."""
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import DailyActivity, ExerciseAttempt, HeartEvent, Lesson, LessonAttempt, Skill, SkillProgress, Unit, UnitChestClaim, User, UserAchievement, XPEvent
from ..seed import LEARNER_BASELINE, LEARNER_USERNAME, seed_learner_week, seed_sample_completion
from . import clock
from .achievements import evaluate_achievements


def reset_learner(db: Session) -> None:
    """Restore the sample learner to the seeded starting state (other learners are untouched)."""
    user = db.scalar(select(User).where(User.username == LEARNER_USERNAME))
    first_skill = db.scalar(select(Skill).join(Unit).order_by(Unit.position, Skill.position).limit(1))
    if user is None or first_skill is None:
        raise LookupError("Seed data is missing")
    attempt_ids = select(LessonAttempt.id).where(LessonAttempt.user_id == user.id)
    db.execute(delete(HeartEvent).where(HeartEvent.user_id == user.id))
    db.execute(delete(ExerciseAttempt).where(ExerciseAttempt.attempt_id.in_(attempt_ids)))
    for model in (LessonAttempt, XPEvent, SkillProgress, DailyActivity, UserAchievement, UnitChestClaim):
        db.execute(delete(model).where(model.user_id == user.id))
    now = clock.current_time()
    for field, value in LEARNER_BASELINE.items():
        setattr(user, field, value)
    user.hearts_updated_at = now
    today = clock.learner_today(user.tz_offset_minutes, now)
    user.last_active_date = today - timedelta(days=1)
    db.add(SkillProgress(user_id=user.id, skill_id=first_skill.id, completed_lessons=1, crowns=1))
    lesson = db.scalar(select(Lesson).where(Lesson.skill_id == first_skill.id).order_by(Lesson.position).limit(1))
    seed_sample_completion(db, user, lesson)
    db.add(DailyActivity(user_id=user.id, activity_date=today, xp_earned=15, lessons_completed=0))
    seed_learner_week(db, user)
    evaluate_achievements(db, user, today)
    db.commit()


def simulate_next_day(db: Session) -> None:
    """Shift the learner's history one day into the past, as if a day had elapsed (streak/goal/heart demo)."""
    user = db.scalar(select(User).where(User.username == LEARNER_USERNAME))
    if user is None:
        raise LookupError("Seed data is missing")
    day = timedelta(days=1)
    for row in db.scalars(select(DailyActivity).where(DailyActivity.user_id == user.id).order_by(DailyActivity.activity_date)).all():
        row.activity_date -= day  # oldest first so the unique (user, date) constraint is never violated
        db.flush()
    for event in db.scalars(select(XPEvent).where(XPEvent.user_id == user.id)).all():
        event.created_at -= day
    for attempt in db.scalars(select(LessonAttempt).where(LessonAttempt.user_id == user.id)).all():
        attempt.started_at -= day
        if attempt.completed_at:
            attempt.completed_at -= day
    if user.last_active_date:
        user.last_active_date -= day
    user.hearts_updated_at -= day
    db.commit()
