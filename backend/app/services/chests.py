"""Unit reward chests: locked until every skill of the unit is complete, then claimable once."""
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import SkillStatus, Unit, UnitChestClaim
from . import clock
from .path import skill_states
from .users import get_user

CHEST_GEMS = 30


def chest_status(skill_statuses: list[str], claimed: bool) -> str:
    if claimed:
        return "opened"
    complete = bool(skill_statuses) and all(status == SkillStatus.COMPLETED for status in skill_statuses)
    return "ready" if complete else "locked"


def claimed_unit_ids(db: Session, user_id: int) -> set[int]:
    return set(db.scalars(select(UnitChestClaim.unit_id).where(UnitChestClaim.user_id == user_id)).all())


def claim_chest(db: Session, user_id: int, unit_id: int) -> dict[str, Any]:
    unit = db.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(404, "Unit not found")
    user = get_user(db, user_id, clock.current_time())
    states = [state for state in skill_states(db, user.id, unit.course_id) if state["skill"].unit_id == unit.id]
    if chest_status([state["status"] for state in states], unit.id in claimed_unit_ids(db, user.id)) != "ready":
        raise HTTPException(403, "Complete every skill in this unit to open its chest")
    db.add(UnitChestClaim(user_id=user.id, unit_id=unit.id, gems=CHEST_GEMS, claimed_at=clock.current_time()))
    user.gems += CHEST_GEMS
    db.commit()
    return {"gems_awarded": CHEST_GEMS, "gems": user.gems}
