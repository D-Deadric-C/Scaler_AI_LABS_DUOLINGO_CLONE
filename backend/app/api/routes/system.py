from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ... import schemas
from ...services.achievements import achievements_payload
from ...services.leaderboard import leaderboard_payload
from ...services.path import path_payload
from ..deps import current_user_id, get_db

router = APIRouter()


@router.get("/health", tags=["system"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Liveness and database check used by deployments."""
    db.execute(text("SELECT 1"))  # fails (500) if the database is unreachable, so deploy checks are meaningful
    return {"status": "ok", "service": "duolingo-api"}


@router.get("/bootstrap", response_model=schemas.BootstrapOut, tags=["path"])
def bootstrap(db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Everything the home screen needs in one call: path, learner stats, top league entries and badges."""
    payload = path_payload(db, user_id)
    payload["leaderboard"] = leaderboard_payload(db, user_id)["entries"][:3]
    payload["achievements"] = achievements_payload(db, user_id)[:3]
    db.commit()
    return payload
