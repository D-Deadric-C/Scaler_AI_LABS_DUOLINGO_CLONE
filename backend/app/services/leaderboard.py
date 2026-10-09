"""Weekly league standings built from the XP ledger."""
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User
from . import clock
from .users import weekly_xp_by_user

LEAGUE_PROMOTION_SPOTS = 3
LEAGUE_DEMOTION_SPOTS = 2


def leaderboard_payload(db: Session, user_id: int) -> dict[str, Any]:
    now = clock.current_time()
    weekly = weekly_xp_by_user(db, now)
    users = sorted(db.scalars(select(User)).all(), key=lambda user: (-weekly.get(user.id, 0), user.id))
    total = len(users)
    entries = []
    for rank, user in enumerate(users, start=1):
        zone = "promotion" if rank <= LEAGUE_PROMOTION_SPOTS else "demotion" if rank > total - LEAGUE_DEMOTION_SPOTS else "safe"
        entries.append({"rank": rank, "id": user.id, "name": user.display_name, "username": user.username, "xp": weekly.get(user.id, 0), "avatar_color": user.avatar_color, "is_current": user.id == user_id, "zone": zone})
    ends_at = clock.week_start(now) + timedelta(days=7)
    return {"league": "Bronze", "ends_in": clock.format_remaining(ends_at - now), "ends_at": ends_at.isoformat(), "entries": entries}
