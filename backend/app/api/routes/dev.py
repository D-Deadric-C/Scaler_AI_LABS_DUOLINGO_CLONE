from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...seed import reset_learner, simulate_next_day
from ..deps import get_db, require_dev_endpoints

router = APIRouter(prefix="/dev", tags=["dev"], dependencies=[Depends(require_dev_endpoints)])


@router.post("/reset", response_model=schemas.DevActionOut)
def reset_demo(db: Session = Depends(get_db)) -> dict:
    """Restore the sample learner to the seeded starting state."""
    reset_learner(db)
    return {"status": "ok", "message": "Demo learner restored to the seeded starting state."}


@router.post("/simulate-day", response_model=schemas.DevActionOut)
def simulate_day(db: Session = Depends(get_db)) -> dict:
    """Pretend one day has passed (streak, daily goal and heart regeneration can then be observed)."""
    simulate_next_day(db)
    return {"status": "ok", "message": "One day has passed for the demo learner."}
