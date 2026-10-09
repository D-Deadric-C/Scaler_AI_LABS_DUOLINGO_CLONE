from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...services.achievements import achievements_payload
from ...services.daily import quests_payload
from ...services.leaderboard import leaderboard_payload
from ...services.refills import gem_refill, hearts_payload, practice_refill
from ..deps import current_user_id, get_db

router = APIRouter(tags=["gamification"])


@router.get("/leaderboards/weekly", response_model=schemas.LeaderboardOut)
def weekly_leaderboard(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return leaderboard_payload(db, user_id)


@router.get("/achievements", response_model=list[schemas.AchievementOut])
def achievements(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> list[dict]:
    return achievements_payload(db, user_id)


@router.get("/quests", response_model=schemas.QuestsOut)
def quests(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return quests_payload(db, user_id)


@router.get("/hearts", response_model=schemas.HeartsOut)
def hearts(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return hearts_payload(db, user_id)


@router.post("/hearts/practice-refill", response_model=schemas.RefillOut)
def hearts_practice_refill(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return practice_refill(db, user_id)


@router.post("/hearts/gem-refill", response_model=schemas.RefillOut)
def hearts_gem_refill(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    return gem_refill(db, user_id)
