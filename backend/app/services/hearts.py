"""Heart rules: lazy regeneration, losing hearts and the heart ledger."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import HeartEvent, User
from . import clock

HEART_REGEN_MINUTES = 30
GEM_REFILL_COST = 350
PRACTICE_HEART_REWARD = 1


def regenerate_hearts(user: User, now: datetime | None = None) -> None:
    """Lazily add the hearts earned since ``hearts_updated_at`` (one per 30 minutes)."""
    if user.hearts >= user.max_hearts:
        return
    current = now or clock.current_time()
    elapsed = (current - user.hearts_updated_at).total_seconds()
    regenerated = int(elapsed // (HEART_REGEN_MINUTES * 60))
    if regenerated > 0:
        user.hearts = min(user.max_hearts, user.hearts + regenerated)
        user.hearts_updated_at += timedelta(minutes=regenerated * HEART_REGEN_MINUTES)


def lose_heart(user: User, now: datetime) -> bool:
    """Remove one heart; the regeneration clock only starts when leaving a full heart bar."""
    regenerate_hearts(user, now)
    if user.hearts <= 0:
        return False
    if user.hearts >= user.max_hearts:
        user.hearts_updated_at = now
    user.hearts -= 1
    return True


def next_heart_at(user: User) -> str | None:
    if user.hearts >= user.max_hearts:
        return None
    return (user.hearts_updated_at + timedelta(minutes=HEART_REGEN_MINUTES)).isoformat()


def log_heart_event(db: Session, user: User, kind: str, delta: int, attempt_id: int | None = None, gems_spent: int = 0) -> None:
    db.add(HeartEvent(user_id=user.id, attempt_id=attempt_id, kind=kind, delta=delta, hearts_after=user.hearts, gems_spent=gems_spent, created_at=clock.current_time()))
