"""Weekly league standings built from the XP ledger."""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import User, XPEvent
from . import clock
from .users import weekly_xp_by_user

LEAGUE_PROMOTION_SPOTS = 3
LEAGUE_DEMOTION_SPOTS = 2
# Simulated competitors: each earns this much XP every week (recorded in the XP ledger like real XP).
BOT_WEEKLY_XP = {"maya": 260, "leo": 210, "sam": 170, "nora": 125, "ari": 80}


def ensure_bot_weekly_xp(db: Session, now: datetime | None = None) -> None:
    """Give the simulated competitors this week's XP the first time the week is viewed."""
    now = now or clock.current_time()
    monday = clock.week_start(now)
    added = False
    for user in db.scalars(select(User).where(User.username.in_(BOT_WEEKLY_XP))).all():
        key = f"seed:weekly:{user.id}:{monday:%Y%m%d}"
        if not db.scalar(select(XPEvent.id).where(XPEvent.idempotency_key == key)):
            db.add(XPEvent(user_id=user.id, amount=BOT_WEEKLY_XP[user.username], source="seed", idempotency_key=key, created_at=monday))
            added = True
    if added:
        try:
            db.commit()
        except IntegrityError:  # another request seeded the same week first
            db.rollback()


def leaderboard_payload(db: Session, user_id: int) -> dict[str, Any]:
    now = clock.current_time()
    ensure_bot_weekly_xp(db, now)
    weekly = weekly_xp_by_user(db, now)
    users = sorted(db.scalars(select(User)).all(), key=lambda user: (-weekly.get(user.id, 0), user.id))
    total = len(users)
    entries = []
    for rank, user in enumerate(users, start=1):
        zone = "promotion" if rank <= LEAGUE_PROMOTION_SPOTS else "demotion" if rank > total - LEAGUE_DEMOTION_SPOTS else "safe"
        entries.append({"rank": rank, "id": user.id, "name": user.display_name, "username": user.username, "xp": weekly.get(user.id, 0), "avatar_color": user.avatar_color, "is_current": user.id == user_id, "zone": zone})
    ends_at = clock.week_start(now) + timedelta(days=7)
    return {"league": "Bronze", "ends_in": clock.format_remaining(ends_at - now), "ends_at": ends_at.isoformat(), "entries": entries}
