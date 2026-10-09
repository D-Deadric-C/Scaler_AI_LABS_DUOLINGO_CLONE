from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import schemas
from ...services.path import path_payload
from ..deps import current_user_id, get_db

router = APIRouter(tags=["path"])


@router.get("/courses/{course_id}/path", response_model=schemas.PathOut)
def course_path(course_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    if course_id != 1:
        raise HTTPException(404, "Course not found")
    payload = path_payload(db, user_id)
    db.commit()  # persists lazily regenerated hearts
    return payload
