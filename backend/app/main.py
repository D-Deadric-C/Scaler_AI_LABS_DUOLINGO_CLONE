from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import schemas
from .database import SessionLocal, ensure_schema, get_db
from .seed import reset_learner, seed_database, simulate_next_day
from .service import (
    abandon_attempt,
    achievements_payload,
    activity_payload,
    answer_attempt,
    attempt_payload,
    complete_attempt,
    gem_refill,
    get_attempt,
    get_user,
    hearts_payload,
    leaderboard_payload,
    path_payload,
    practice_refill,
    profile_payload,
    quests_payload,
    serialize_user,
    start_attempt,
)

API = "/api/v1"


def dev_endpoints_enabled() -> bool:
    return os.getenv("ENABLE_DEV_ENDPOINTS", "1").lower() not in {"0", "false", "no", "off"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema()
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Duolingo API",
    version="1.1.0",
    description="Server-authoritative API for the Duolingo clone: path, lesson attempts, hearts, XP, streaks and leagues.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------ system
@app.get(f"{API}/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "duolingo-api"}


@app.get(f"{API}/bootstrap", response_model=schemas.BootstrapOut, tags=["path"])
def bootstrap(db: Session = Depends(get_db)) -> dict:
    payload = path_payload(db)
    payload["leaderboard"] = leaderboard_payload(db)["entries"][:3]
    payload["achievements"] = achievements_payload(db)[:3]
    db.commit()
    return payload


@app.get(f"{API}/courses/{{course_id}}/path", response_model=schemas.PathOut, tags=["path"])
def course_path(course_id: int, db: Session = Depends(get_db)) -> dict:
    if course_id != 1:
        raise HTTPException(404, "Course not found")
    payload = path_payload(db)
    db.commit()
    return payload


# ----------------------------------------------------------------- learner
@app.get(f"{API}/me", response_model=schemas.UserOut, tags=["learner"])
def me(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    payload = serialize_user(db, user)
    db.commit()
    return payload


@app.patch(f"{API}/me/settings", response_model=schemas.UserOut, tags=["learner"])
def update_settings(body: schemas.SettingsRequest, db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    if body.dark_mode is not None:
        user.dark_mode = body.dark_mode
    if body.daily_goal is not None:
        user.daily_goal = body.daily_goal
    db.commit()
    return serialize_user(db, user)


@app.get(f"{API}/me/profile", response_model=schemas.ProfileOut, tags=["learner"])
def profile(db: Session = Depends(get_db)) -> dict:
    payload = profile_payload(db)
    db.commit()
    return payload


@app.get(f"{API}/me/activity", response_model=schemas.ActivityOut, tags=["learner"])
def activity(days: int = Query(default=14, ge=1, le=90), db: Session = Depends(get_db)) -> dict:
    return activity_payload(db, days)


# ---------------------------------------------------------- lesson attempts
@app.post(f"{API}/lessons/{{lesson_id}}/attempts", response_model=schemas.AttemptOut, tags=["attempts"])
def create_attempt(lesson_id: int, body: schemas.AttemptCreateRequest | None = None, db: Session = Depends(get_db)) -> dict:
    return start_attempt(db, lesson_id, (body or schemas.AttemptCreateRequest()).mode)


@app.get(f"{API}/attempts/{{attempt_id}}", response_model=schemas.AttemptOut, tags=["attempts"])
def read_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict:
    return attempt_payload(db, get_attempt(db, attempt_id))


@app.post(f"{API}/attempts/{{attempt_id}}/answers", response_model=schemas.AnswerOut, tags=["attempts"])
def submit_answer(attempt_id: int, body: schemas.AnswerRequest, db: Session = Depends(get_db)) -> dict:
    return answer_attempt(db, attempt_id, body.exercise_id, body.answer)


@app.post(f"{API}/attempts/{{attempt_id}}/complete", response_model=schemas.CompletionOut, tags=["attempts"])
def finish_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict:
    return complete_attempt(db, attempt_id)


@app.post(f"{API}/attempts/{{attempt_id}}/abandon", response_model=schemas.StatusOut, tags=["attempts"])
def leave_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict:
    return abandon_attempt(db, attempt_id)


# ------------------------------------------------------------- gamification
@app.get(f"{API}/leaderboards/weekly", response_model=schemas.LeaderboardOut, tags=["gamification"])
def weekly_leaderboard(db: Session = Depends(get_db)) -> dict:
    return leaderboard_payload(db)


@app.get(f"{API}/achievements", response_model=list[schemas.AchievementOut], tags=["gamification"])
def achievements(db: Session = Depends(get_db)) -> list[dict]:
    return achievements_payload(db)


@app.get(f"{API}/quests", response_model=schemas.QuestsOut, tags=["gamification"])
def quests(db: Session = Depends(get_db)) -> dict:
    return quests_payload(db)


@app.get(f"{API}/hearts", response_model=schemas.HeartsOut, tags=["gamification"])
def hearts(db: Session = Depends(get_db)) -> dict:
    return hearts_payload(db)


@app.post(f"{API}/hearts/practice-refill", response_model=schemas.RefillOut, tags=["gamification"])
def hearts_practice_refill(db: Session = Depends(get_db)) -> dict:
    return practice_refill(db)


@app.post(f"{API}/hearts/gem-refill", response_model=schemas.RefillOut, tags=["gamification"])
def hearts_gem_refill(db: Session = Depends(get_db)) -> dict:
    return gem_refill(db)


# --------------------------------------------------------------------- dev
def require_dev_endpoints() -> None:
    if not dev_endpoints_enabled():
        raise HTTPException(404, "Not found")


@app.post(f"{API}/dev/reset", response_model=schemas.DevActionOut, tags=["dev"], dependencies=[Depends(require_dev_endpoints)])
def reset_demo(db: Session = Depends(get_db)) -> dict:
    """Restore the sample learner to the seeded starting state."""
    reset_learner(db)
    return {"status": "ok", "message": "Demo learner restored to the seeded starting state."}


@app.post(f"{API}/dev/simulate-day", response_model=schemas.DevActionOut, tags=["dev"], dependencies=[Depends(require_dev_endpoints)])
def simulate_day(db: Session = Depends(get_db)) -> dict:
    """Pretend one day has passed (streak, daily goal and heart regeneration can then be observed)."""
    simulate_next_day(db)
    return {"status": "ok", "message": "One day has passed for the demo learner."}
