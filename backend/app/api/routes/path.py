from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...services.chests import claim_chest
from ...services.path import path_payload
from ..deps import current_user_id, get_db

router = APIRouter(tags=["path"])


@router.get("/courses/{course_id}/path", response_model=schemas.PathOut)
def course_path(course_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Units and skills with lock state, progress and the next lesson to take."""
    payload = path_payload(db, user_id, course_id)
    db.commit()  # persists lazily regenerated hearts
    return payload


@router.post("/units/{unit_id}/chest", response_model=schemas.ChestClaimOut)
def open_unit_chest(unit_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Open the unit's reward chest once the first three skills are complete."""
    return claim_chest(db, user_id, unit_id)
