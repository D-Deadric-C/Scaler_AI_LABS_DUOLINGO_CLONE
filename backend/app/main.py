from contextlib import asynccontextmanager
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import LessonAttempt, User
from .schemas import AnswerRequest, AttemptCreateRequest, SettingsRequest
from .seed import seed_database
from .service import (
    DEFAULT_USER_ID,
    achievements_payload,
    answer_attempt,
    attempt_payload,
    complete_attempt,
    get_user,
    leaderboard_payload,
    path_payload,
    serialize_user,
    start_attempt,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Duolingo API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "duolingo-api"}


@app.get("/api/v1/bootstrap")
async def bootstrap(db: Session = Depends(get_db)) -> dict:
    payload = path_payload(db)
    payload["leaderboard"] = leaderboard_payload(db)["entries"][:3]
    payload["achievements"] = achievements_payload(db)[:3]
    db.commit()
    return payload


@app.get("/api/v1/courses/1/path")
async def course_path(db: Session = Depends(get_db)) -> dict:
    payload = path_payload(db)
    db.commit()
    return payload


@app.get("/api/v1/me")
async def me(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    payload = serialize_user(db, user)
    db.commit()
    return payload


@app.patch("/api/v1/me/settings")
async def update_settings(body: SettingsRequest, db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    if body.dark_mode is not None:
        user.dark_mode = body.dark_mode
    if body.daily_goal is not None:
        user.daily_goal = body.daily_goal
    db.commit()
    return serialize_user(db, user)


@app.get("/api/v1/me/profile")
async def profile(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    return {"user": serialize_user(db, user), "achievements": achievements_payload(db), "league": leaderboard_payload(db)["league"]}


@app.post("/api/v1/lessons/{lesson_id}/attempts")
async def create_attempt(lesson_id: int, body: AttemptCreateRequest, db: Session = Depends(get_db)) -> dict:
    return start_attempt(db, lesson_id, body.mode)


@app.get("/api/v1/attempts/{attempt_id}")
async def get_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    return attempt_payload(db, attempt)


@app.post("/api/v1/attempts/{attempt_id}/answers")
async def submit_answer(attempt_id: int, body: AnswerRequest, db: Session = Depends(get_db)) -> dict:
    return answer_attempt(db, attempt_id, body.exercise_id, body.answer)


@app.post("/api/v1/attempts/{attempt_id}/complete")
async def finish_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict:
    return complete_attempt(db, attempt_id)


@app.post("/api/v1/attempts/{attempt_id}/abandon")
async def abandon_attempt(attempt_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    if attempt.status == "active":
        attempt.status = "abandoned"
        db.commit()
    return {"status": attempt.status}


@app.get("/api/v1/leaderboards/weekly")
async def weekly_leaderboard(db: Session = Depends(get_db)) -> dict:
    return leaderboard_payload(db)


@app.get("/api/v1/achievements")
async def achievements(db: Session = Depends(get_db)) -> list[dict]:
    return achievements_payload(db)


@app.get("/api/v1/hearts")
async def hearts(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    db.commit()
    return {"hearts": user.hearts, "max_hearts": user.max_hearts, "next_heart_at": serialize_user(db, user)["next_heart_at"]}


@app.post("/api/v1/hearts/practice-refill")
async def practice_refill(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    user.hearts = user.max_hearts
    db.commit()
    return {"hearts": user.hearts, "message": "Practice complete — hearts restored!"}


@app.post("/api/v1/hearts/gem-refill")
async def gem_refill(db: Session = Depends(get_db)) -> dict:
    user = get_user(db)
    cost = 350
    if user.gems < cost:
        raise HTTPException(409, "Not enough gems")
    if user.hearts == user.max_hearts:
        raise HTTPException(409, "Hearts are already full")
    user.gems -= cost
    user.hearts = user.max_hearts
    db.commit()
    return {"hearts": user.hearts, "gems": user.gems}


@app.post("/api/v1/dev/reset")
async def reset_demo(db: Session = Depends(get_db)) -> dict[str, str]:
    if db.scalar(select(User.id).where(User.id == DEFAULT_USER_ID)) is None:
        raise HTTPException(404, "Demo learner missing")
    return {"status": "available", "message": "Delete backend/duolingo.db and restart to fully reseed."}
