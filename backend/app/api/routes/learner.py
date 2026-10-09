from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ... import schemas
from ...services.daily import activity_payload
from ...services.profile import profile_payload
from ...services.users import me_payload, update_settings
from ..deps import current_user_id, get_db

router = APIRouter(prefix="/me", tags=["learner"])


@router.get("", response_model=schemas.UserOut)
def me(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return me_payload(db, user_id)


@router.patch("/settings", response_model=schemas.UserOut)
def patch_settings(body: schemas.SettingsRequest, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return update_settings(db, user_id, body.dark_mode, body.daily_goal)


@router.get("/profile", response_model=schemas.ProfileOut)
def profile(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return profile_payload(db, user_id)


@router.get("/activity", response_model=schemas.ActivityOut)
def activity(days: int = Query(default=14, ge=1, le=90), db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return activity_payload(db, user_id, days)
