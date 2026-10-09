"""Single time seam: every calendar rule reads time here so tests can inject a clock."""
from datetime import date, datetime, timedelta

from ..models import utc_now


def current_time() -> datetime:
    """Naive UTC "now"."""
    return utc_now()


def today_utc(now: datetime | None = None) -> date:
    return (now or current_time()).date()


def learner_today(offset_minutes: int, now: datetime | None = None) -> date:
    """The learner's calendar date (their timezone), which streaks and the daily goal are measured in."""
    return ((now or current_time()) + timedelta(minutes=offset_minutes)).date()


def local_day_start_utc(day: date, offset_minutes: int) -> datetime:
    """UTC instant at which the learner's calendar ``day`` begins."""
    return datetime.combine(day, datetime.min.time()) - timedelta(minutes=offset_minutes)


def week_start(now: datetime) -> datetime:
    """Monday 00:00 UTC of the week containing ``now``."""
    midnight = datetime.combine(now.date(), datetime.min.time())
    return midnight - timedelta(days=now.weekday())


def format_remaining(delta: timedelta) -> str:
    total = max(0, int(delta.total_seconds()))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
