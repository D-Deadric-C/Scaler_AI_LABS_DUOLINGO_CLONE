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
    """Weekly league standings with promotion and demotion zones."""
    return leaderboard_payload(db, user_id)


@router.get("/achievements", response_model=list[schemas.AchievementOut])
def achievements(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> list[dict]:
    """All badges with progress and earned state."""
    return achievements_payload(db, user_id)


@router.get("/quests", response_model=schemas.QuestsOut)
def quests(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Derived daily quests and their progress."""
    return quests_payload(db, user_id)


@router.get("/hearts", response_model=schemas.HeartsOut)
def hearts(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Current hearts and the time the next one regenerates."""
    return hearts_payload(db, user_id)


@router.post("/hearts/practice-refill", response_model=schemas.RefillOut)
def hearts_practice_refill(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Mocked "practice" refill: restores hearts to full when below the maximum."""
    return practice_refill(db, user_id)


@router.post("/hearts/gem-refill", response_model=schemas.RefillOut)
def hearts_gem_refill(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Spend 350 gems to restore hearts to full."""
    return gem_refill(db, user_id)
