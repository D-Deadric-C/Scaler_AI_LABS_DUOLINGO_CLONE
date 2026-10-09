"""Badge metrics, awarding and progress."""
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Achievement, AttemptMode, AttemptStatus, LessonAttempt, User, UserAchievement
from . import clock
from .streaks import effective_streak
from .users import get_user


def learner_metrics(db: Session, user: User, today: date) -> dict[str, int]:
    completed = (LessonAttempt.user_id == user.id, LessonAttempt.status == AttemptStatus.COMPLETED)
    lessons = db.scalar(select(func.count(func.distinct(LessonAttempt.lesson_id))).where(*completed, LessonAttempt.mode == AttemptMode.LESSON)) or 0
    perfect = db.scalar(select(func.count()).select_from(LessonAttempt).where(*completed, LessonAttempt.current_index > 0, LessonAttempt.correct_count == LessonAttempt.current_index)) or 0
    return {"lessons": lessons, "perfect": perfect, "xp": user.total_xp, "streak": effective_streak(user, today)}


def evaluate_achievements(db: Session, user: User, today: date | None = None) -> list[dict[str, Any]]:
    """Award every badge whose threshold is met and return the newly earned ones."""
    metrics = learner_metrics(db, user, today or clock.today_utc())
    awarded_ids = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    newly_awarded = []
    for achievement in db.scalars(select(Achievement).order_by(Achievement.id)).all():
        if achievement.id not in awarded_ids and metrics.get(achievement.metric, 0) >= achievement.threshold:
            db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
            newly_awarded.append({"title": achievement.title, "icon": achievement.icon})
    return newly_awarded


def achievements_payload(db: Session, user_id: int) -> list[dict[str, Any]]:
    user = get_user(db, user_id)
    metrics = learner_metrics(db, user, clock.today_utc())
    earned = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    return [
        {"id": item.id, "title": item.title, "description": item.description, "icon": item.icon, "earned": item.id in earned, "progress": min(metrics.get(item.metric, 0), item.threshold), "threshold": item.threshold}
        for item in db.scalars(select(Achievement).order_by(Achievement.id)).all()
    ]
