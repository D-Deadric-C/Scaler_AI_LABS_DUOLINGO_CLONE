"""Learner lookup, serialisation and settings."""
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import DailyActivity, User, XPEvent
from . import clock
from .hearts import next_heart_at, regenerate_hearts
from .streaks import effective_streak


def get_user(db: Session, user_id: int, now: datetime | None = None) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Learner not found")
    regenerate_hearts(user, now)
    return user


def weekly_xp_by_user(db: Session, now: datetime) -> dict[int, int]:
    rows = db.execute(
        select(XPEvent.user_id, func.coalesce(func.sum(XPEvent.amount), 0))
        .where(XPEvent.created_at >= clock.week_start(now))
        .group_by(XPEvent.user_id)
    ).all()
    return {user_id: int(total) for user_id, total in rows}


def today_xp_for(db: Session, user_id: int, today: date) -> int:
    return db.scalar(select(DailyActivity.xp_earned).where(DailyActivity.user_id == user_id, DailyActivity.activity_date == today)) or 0


def serialize_user(db: Session, user: User, now: datetime | None = None) -> dict[str, Any]:
    now = now or clock.current_time()
    today = clock.today_utc(now)
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_color": user.avatar_color,
        "total_xp": user.total_xp,
        "weekly_xp": weekly_xp_by_user(db, now).get(user.id, 0),
        "gems": user.gems,
        "hearts": user.hearts,
        "max_hearts": user.max_hearts,
        "current_streak": effective_streak(user, today),
        "longest_streak": user.longest_streak,
        "daily_goal": user.daily_goal,
        "today_xp": today_xp_for(db, user.id, today),
        "dark_mode": user.dark_mode,
        "next_heart_at": next_heart_at(user),
    }


def me_payload(db: Session, user_id: int) -> dict[str, Any]:
    user = get_user(db, user_id)
    payload = serialize_user(db, user)
    db.commit()  # persists lazily regenerated hearts
    return payload


def update_settings(db: Session, user_id: int, dark_mode: bool | None, daily_goal: int | None) -> dict[str, Any]:
    user = get_user(db, user_id)
    if dark_mode is not None:
        user.dark_mode = dark_mode
    if daily_goal is not None:
        user.daily_goal = daily_goal
    db.commit()
    return serialize_user(db, user)
