from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...services.path import path_payload
from ..deps import current_user_id, get_db

router = APIRouter(tags=["path"])


@router.get("/courses/{course_id}/path", response_model=schemas.PathOut)
def course_path(course_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Units and skills with lock state, progress and the next lesson to take."""
    payload = path_payload(db, user_id, course_id)
    db.commit()  # persists lazily regenerated hearts
    return payload
