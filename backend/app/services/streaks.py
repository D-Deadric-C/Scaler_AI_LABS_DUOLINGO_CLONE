"""Daily streak rules (calendar-day based, date passed in for testability)."""
from datetime import date, timedelta

from ..models import User


def effective_streak(user: User, today: date) -> int:
    """Displayed streak: a streak is lost once a full day passes with no lesson."""
    if user.last_active_date not in {today, today - timedelta(days=1)}:
        return 0
    return user.current_streak


def update_streak(user: User, today: date) -> None:
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_active_date = today
