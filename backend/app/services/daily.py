"""Daily goal views: derived quests and the activity calendar."""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import AttemptStatus, DailyActivity, LessonAttempt
from . import clock
from .streaks import effective_streak
from .users import get_user


def quests_payload(db: Session, user_id: int) -> dict[str, Any]:
    now = clock.current_time()
    user = get_user(db, user_id, now)
    today = clock.today_utc(now)
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    xp = activity.xp_earned if activity else 0
    lessons = activity.lessons_completed if activity else 0
    day_start = datetime.combine(today, datetime.min.time())
    perfect = db.scalar(
        select(func.count()).select_from(LessonAttempt).where(
            LessonAttempt.user_id == user.id,
            LessonAttempt.status == AttemptStatus.COMPLETED,
            LessonAttempt.completed_at >= day_start,
            LessonAttempt.current_index > 0,
            LessonAttempt.correct_count == LessonAttempt.current_index,
        )
    ) or 0
    definitions = [
        ("daily-xp", f"Earn {user.daily_goal} XP", xp, user.daily_goal, 10),
        ("daily-lesson", "Complete a lesson", lessons, 1, 10),
        ("daily-perfect", "Finish a lesson with no mistakes", perfect, 1, 20),
    ]
    quests = [{"id": key, "title": title, "progress": min(progress, target), "target": target, "completed": progress >= target, "reward_gems": reward} for key, title, progress, target, reward in definitions]
    return {"ends_in": clock.format_remaining(day_start + timedelta(days=1) - now), "quests": quests}


def activity_payload(db: Session, user_id: int, days: int) -> dict[str, Any]:
    now = clock.current_time()
    user = get_user(db, user_id, now)
    today = clock.today_utc(now)
    start = today - timedelta(days=days - 1)
    rows = {row.activity_date: row for row in db.scalars(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date >= start)).all()}
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = rows.get(day)
        xp = row.xp_earned if row else 0
        result.append({"date": day.isoformat(), "xp": xp, "lessons": row.lessons_completed if row else 0, "goal_met": xp >= user.daily_goal})
    return {"days": result, "current_streak": effective_streak(user, today), "longest_streak": user.longest_streak}
