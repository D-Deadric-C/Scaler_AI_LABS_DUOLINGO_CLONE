"""Heart refills: the mocked practice refill and the gem purchase."""
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import HeartEventKind
from .hearts import GEM_REFILL_COST, log_heart_event, next_heart_at
from .users import get_user


def hearts_payload(db: Session, user_id: int) -> dict[str, Any]:
    user = get_user(db, user_id)
    db.commit()
    return {"hearts": user.hearts, "max_hearts": user.max_hearts, "next_heart_at": next_heart_at(user)}


def practice_refill(db: Session, user_id: int) -> dict[str, Any]:
    user = get_user(db, user_id)
    if user.hearts >= user.max_hearts:
        raise HTTPException(409, "Hearts are already full")
    gained = user.max_hearts - user.hearts
    user.hearts = user.max_hearts
    log_heart_event(db, user, HeartEventKind.PRACTICE_REFILL, gained)
    db.commit()
    return {"hearts": user.hearts, "gems": user.gems, "message": "Practice complete — hearts restored!"}


def gem_refill(db: Session, user_id: int) -> dict[str, Any]:
    user = get_user(db, user_id)
    if user.hearts >= user.max_hearts:
        raise HTTPException(409, "Hearts are already full")
    if user.gems < GEM_REFILL_COST:
        raise HTTPException(409, "Not enough gems")
    gained = user.max_hearts - user.hearts
    user.gems -= GEM_REFILL_COST
    user.hearts = user.max_hearts
    log_heart_event(db, user, HeartEventKind.GEM_REFILL, gained, gems_spent=GEM_REFILL_COST)
    db.commit()
    return {"hearts": user.hearts, "gems": user.gems, "message": "Hearts refilled!"}
