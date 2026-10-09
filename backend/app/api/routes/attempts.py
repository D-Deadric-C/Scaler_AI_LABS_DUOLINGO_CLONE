from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ... import schemas
from ...services import attempts as service
from ..deps import current_user_id, get_db

router = APIRouter(tags=["attempts"])


@router.post("/lessons/{lesson_id}/attempts", response_model=schemas.AttemptOut)
def create_attempt(lesson_id: int, body: schemas.AttemptCreateRequest | None = None, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Start a lesson, practice or legendary attempt, or resume the active one. Answers are never included."""
    return service.start_attempt(db, user_id, lesson_id, (body or schemas.AttemptCreateRequest()).mode)


@router.get("/attempts/{attempt_id}", response_model=schemas.AttemptOut)
def read_attempt(attempt_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Reload an attempt (for example after a page refresh)."""
    return service.read_attempt(db, user_id, attempt_id)


@router.post("/attempts/{attempt_id}/answers", response_model=schemas.AnswerOut)
def submit_answer(attempt_id: int, body: schemas.AnswerRequest, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Check the current exercise server-side; a wrong answer in a lesson costs one heart."""
    return service.answer_attempt(db, user_id, attempt_id, body.exercise_id, body.answer)


@router.post("/attempts/{attempt_id}/complete", response_model=schemas.CompletionOut)
def complete_attempt(attempt_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Finish an attempt. Idempotent: XP, streak and unlocks are applied exactly once."""
    return service.complete_attempt(db, user_id, attempt_id)


@router.post("/attempts/{attempt_id}/abandon", response_model=schemas.StatusOut)
def abandon_attempt(attempt_id: int, db: Session = Depends(get_db), user_id: int = Depends(current_user_id)) -> dict:
    """Leave an attempt without rewards."""
    return service.abandon_attempt(db, user_id, attempt_id)
