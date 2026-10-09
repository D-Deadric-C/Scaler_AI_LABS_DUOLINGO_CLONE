"""Server-authoritative learning rules: path state, attempts, hearts, XP, streaks, achievements.

Every rule that depends on the calendar reads time through ``current_time`` so tests can
inject a clock (``monkeypatch.setattr(service, "current_time", ...)``) instead of sleeping.
"""
from __future__ import annotations

import random
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import (
    Achievement,
    DailyActivity,
    Exercise,
    ExerciseAttempt,
    HeartEvent,
    Lesson,
    LessonAttempt,
    Skill,
    SkillProgress,
    Unit,
    User,
    UserAchievement,
    XPEvent,
    utc_now,
)

DEFAULT_USER_ID = 1
HEART_REGEN_MINUTES = 30
GEM_REFILL_COST = 350
PRACTICE_HEART_REWARD = 1
LEGENDARY_SECONDS = 75
LEGENDARY_GRACE_SECONDS = 3
XP_PER_CORRECT_ANSWER = 2
LEAGUE_PROMOTION_SPOTS = 3
LEAGUE_DEMOTION_SPOTS = 2


def current_time() -> datetime:
    """Naive UTC "now"; the single seam used by tests to control time."""
    return utc_now()


def today_utc(now: datetime | None = None) -> date:
    return (now or current_time()).date()


# ---------------------------------------------------------------- hearts
def regenerate_hearts(user: User, now: datetime | None = None) -> None:
    """Lazily add the hearts earned since ``hearts_updated_at`` (one per 30 minutes)."""
    if user.hearts >= user.max_hearts:
        return
    current = now or current_time()
    elapsed = (current - user.hearts_updated_at).total_seconds()
    regenerated = int(elapsed // (HEART_REGEN_MINUTES * 60))
    if regenerated > 0:
        user.hearts = min(user.max_hearts, user.hearts + regenerated)
        user.hearts_updated_at += timedelta(minutes=regenerated * HEART_REGEN_MINUTES)


def lose_heart(user: User, now: datetime) -> bool:
    """Remove one heart; the regeneration clock only starts when leaving a full heart bar."""
    regenerate_hearts(user, now)
    if user.hearts <= 0:
        return False
    if user.hearts >= user.max_hearts:
        user.hearts_updated_at = now
    user.hearts -= 1
    return True


def log_heart_event(db: Session, user: User, kind: str, delta: int, attempt_id: int | None = None, gems_spent: int = 0) -> None:
    db.add(HeartEvent(user_id=user.id, attempt_id=attempt_id, kind=kind, delta=delta, hearts_after=user.hearts, gems_spent=gems_spent, created_at=current_time()))


def get_user(db: Session, user_id: int = DEFAULT_USER_ID, now: datetime | None = None) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Learner not found")
    regenerate_hearts(user, now)
    return user


def practice_refill(db: Session) -> dict[str, Any]:
    user = get_user(db)
    if user.hearts >= user.max_hearts:
        raise HTTPException(409, "Hearts are already full")
    gained = user.max_hearts - user.hearts
    user.hearts = user.max_hearts
    log_heart_event(db, user, "practice_refill", gained)
    db.commit()
    return {"hearts": user.hearts, "gems": user.gems, "message": "Practice complete — hearts restored!"}


def gem_refill(db: Session) -> dict[str, Any]:
    user = get_user(db)
    if user.hearts >= user.max_hearts:
        raise HTTPException(409, "Hearts are already full")
    if user.gems < GEM_REFILL_COST:
        raise HTTPException(409, "Not enough gems")
    gained = user.max_hearts - user.hearts
    user.gems -= GEM_REFILL_COST
    user.hearts = user.max_hearts
    log_heart_event(db, user, "gem_refill", gained, gems_spent=GEM_REFILL_COST)
    db.commit()
    return {"hearts": user.hearts, "gems": user.gems, "message": "Hearts refilled!"}


def hearts_payload(db: Session) -> dict[str, Any]:
    user = get_user(db)
    db.commit()
    return {"hearts": user.hearts, "max_hearts": user.max_hearts, "next_heart_at": next_heart_at(user)}


def next_heart_at(user: User) -> str | None:
    if user.hearts >= user.max_hearts:
        return None
    return (user.hearts_updated_at + timedelta(minutes=HEART_REGEN_MINUTES)).isoformat()


# ---------------------------------------------------------------- streaks & weeks
def effective_streak(user: User, today: date) -> int:
    """Displayed streak: a streak is lost once a full day passes with no lesson."""
    if user.last_active_date not in {today, today - timedelta(days=1)}:
        return 0
    return user.current_streak


def update_streak(user: User, today: date) -> None:
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_active_date = today


def week_start(now: datetime) -> datetime:
    """Monday 00:00 UTC of the week containing ``now``."""
    midnight = datetime.combine(now.date(), datetime.min.time())
    return midnight - timedelta(days=now.weekday())


def format_remaining(delta: timedelta) -> str:
    total = max(0, int(delta.total_seconds()))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def weekly_xp_by_user(db: Session, now: datetime) -> dict[int, int]:
    rows = db.execute(
        select(XPEvent.user_id, func.coalesce(func.sum(XPEvent.amount), 0))
        .where(XPEvent.created_at >= week_start(now))
        .group_by(XPEvent.user_id)
    ).all()
    return {user_id: int(total) for user_id, total in rows}


def today_xp_for(db: Session, user_id: int, today: date) -> int:
    return db.scalar(select(DailyActivity.xp_earned).where(DailyActivity.user_id == user_id, DailyActivity.activity_date == today)) or 0


def serialize_user(db: Session, user: User, now: datetime | None = None) -> dict[str, Any]:
    now = now or current_time()
    today = today_utc(now)
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_color": user.avatar_color,
        "total_xp": user.total_xp,
        "weekly_xp": weekly_xp_by_user(db, now).get(user.id, 0),
        "gems": user.gems,
        "hearts": user.hearts,
        "max_hearts": user.max_hearts,
        "current_streak": effective_streak(user, today),
        "longest_streak": user.longest_streak,
        "daily_goal": user.daily_goal,
        "today_xp": today_xp_for(db, user.id, today),
        "dark_mode": user.dark_mode,
        "next_heart_at": next_heart_at(user),
    }


# ---------------------------------------------------------------- path
def ordered_skills(db: Session) -> list[Skill]:
    return list(db.scalars(select(Skill).join(Unit).order_by(Unit.position, Skill.position)).all())


def skill_states(db: Session, user_id: int) -> list[dict[str, Any]]:
    """Ordered skills with derived lock state; unlocking is computed, never stored."""
    skills = ordered_skills(db)
    lessons_by_skill: dict[int, list[Lesson]] = {}
    for lesson in db.scalars(select(Lesson).order_by(Lesson.skill_id, Lesson.position)).all():
        lessons_by_skill.setdefault(lesson.skill_id, []).append(lesson)
    progress = {row.skill_id: row for row in db.scalars(select(SkillProgress).where(SkillProgress.user_id == user_id)).all()}
    states: list[dict[str, Any]] = []
    previous_complete = True
    for skill in skills:
        lessons = lessons_by_skill.get(skill.id, [])
        row = progress.get(skill.id)
        done = min(row.completed_lessons, len(lessons)) if row else 0
        complete = bool(lessons) and done >= len(lessons)
        status = "completed" if complete else "available" if previous_complete and lessons else "locked"
        states.append({"skill": skill, "lessons": lessons, "completed_lessons": done, "crowns": row.crowns if row else 0, "status": status})
        previous_complete = complete
    return states


def next_lesson(state: dict[str, Any]) -> Lesson | None:
    lessons: list[Lesson] = state["lessons"]
    if not lessons:
        return None
    return lessons[state["completed_lessons"]] if state["completed_lessons"] < len(lessons) else lessons[0]


def practice_lesson_id(states: list[dict[str, Any]]) -> int | None:
    """Lesson used for generic practice: the latest finished skill, else the first unlocked one."""
    for status in ("completed", "available"):
        candidates = [state for state in states if state["status"] == status]
        if candidates:
            lesson = next_lesson(candidates[-1] if status == "completed" else candidates[0])
            return lesson.id if lesson else None
    return None


def path_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    now = current_time()
    user = get_user(db, user_id, now)
    states = skill_states(db, user.id)
    states_by_unit: dict[int, list[dict[str, Any]]] = {}
    for state in states:
        states_by_unit.setdefault(state["skill"].unit_id, []).append(state)
    units = []
    for unit in db.scalars(select(Unit).order_by(Unit.position)).all():
        skills = []
        for state in states_by_unit.get(unit.id, []):
            skill: Skill = state["skill"]
            lesson = next_lesson(state)
            skills.append({
                "id": skill.id,
                "title": skill.title,
                "description": skill.description,
                "icon": skill.icon,
                "status": state["status"],
                "progress": state["completed_lessons"],
                "total_lessons": len(state["lessons"]),
                "crowns": state["crowns"],
                "lesson_id": lesson.id if lesson else None,
                "xp_reward": lesson.xp_reward if lesson else 0,
            })
        units.append({"id": unit.id, "position": unit.position, "title": unit.title, "objective": unit.objective, "color": unit.color, "skills": skills})
    return {
        "course": {"id": 1, "title": "Spanish", "flag": "ES"},
        "user": serialize_user(db, user, now),
        "units": units,
        "practice_lesson_id": practice_lesson_id(states),
    }


# ---------------------------------------------------------------- attempts
def attempt_expired(attempt: LessonAttempt, now: datetime) -> bool:
    return attempt.expires_at is not None and now > attempt.expires_at + timedelta(seconds=LEGENDARY_GRACE_SECONDS)


def seconds_left(attempt: LessonAttempt, now: datetime) -> int | None:
    if attempt.expires_at is None or attempt.status != "active":
        return None
    return max(0, int((attempt.expires_at - now).total_seconds()))


def start_attempt(db: Session, lesson_id: int, mode: str, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    now = current_time()
    user = get_user(db, user_id, now)
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    state = next((item for item in skill_states(db, user.id) if item["skill"].id == lesson.skill_id), None)
    if state is None or state["status"] == "locked":
        raise HTTPException(403, "Complete the previous skill to unlock this lesson")
    if mode == "lesson" and lesson.position > state["completed_lessons"] + 1:
        raise HTTPException(403, "Finish the earlier lessons in this skill first")
    if mode == "legendary" and state["status"] != "completed":
        raise HTTPException(403, "Complete this skill to unlock the legendary challenge")
    if mode == "lesson" and user.hearts <= 0:
        raise HTTPException(409, "You need a heart to start this lesson")
    active = db.scalar(
        select(LessonAttempt).where(
            LessonAttempt.user_id == user.id,
            LessonAttempt.lesson_id == lesson.id,
            LessonAttempt.mode == mode,
            LessonAttempt.status == "active",
        )
    )
    if active and attempt_expired(active, now):
        active.status = "abandoned"
        active.completed_at = now
        active = None
    attempt = active
    if attempt is None:
        attempt = LessonAttempt(
            user_id=user.id,
            lesson_id=lesson.id,
            mode=mode,
            started_at=now,
            expires_at=now + timedelta(seconds=LEGENDARY_SECONDS) if mode == "legendary" else None,
        )
        db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt_payload(db, attempt, now)


def lesson_exercises(db: Session, lesson_id: int) -> list[Exercise]:
    return list(db.scalars(select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.position)).all())


def public_exercise(exercise: Exercise, attempt_id: int) -> dict[str, Any]:
    """Exercise as shown to the learner: no canonical answer, and no answer hidden in the option order."""
    rng = random.Random(attempt_id * 100_003 + exercise.id)  # stable across refreshes of one attempt
    payload = dict(exercise.payload)
    if exercise.type == "match_pairs":
        pairs = payload["pairs"]
        right = [pair[1] for pair in pairs]
        rng.shuffle(right)
        payload = {"left": [pair[0] for pair in pairs], "right": right}
    else:
        for key in ("options", "tokens"):
            if key in payload:
                payload[key] = rng.sample(payload[key], len(payload[key]))
    return {"id": exercise.id, "type": exercise.type, "prompt": exercise.prompt, "hint": exercise.hint, "payload": payload}


def attempt_payload(db: Session, attempt: LessonAttempt, now: datetime | None = None) -> dict[str, Any]:
    now = now or current_time()
    lesson = db.get(Lesson, attempt.lesson_id)
    user = get_user(db, attempt.user_id, now)
    return {
        "attempt_id": attempt.id,
        "mode": attempt.mode,
        "lesson": {"id": lesson.id, "title": lesson.title, "xp_reward": lesson.xp_reward},
        "status": attempt.status,
        "current_index": attempt.current_index,
        "hearts": user.hearts,
        "seconds_left": seconds_left(attempt, now),
        "exercises": [public_exercise(exercise, attempt.id) for exercise in lesson_exercises(db, attempt.lesson_id)],
    }


def get_attempt(db: Session, attempt_id: int) -> LessonAttempt:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt or attempt.user_id != DEFAULT_USER_ID:
        raise HTTPException(404, "Attempt not found")
    return attempt


def abandon_attempt(db: Session, attempt_id: int) -> dict[str, str]:
    attempt = get_attempt(db, attempt_id)
    if attempt.status == "active":
        attempt.status = "abandoned"
        attempt.completed_at = current_time()
        db.commit()
    return {"status": attempt.status}


# ---------------------------------------------------------------- answer checking
_PUNCTUATION = re.compile(r"[¿¡!?.,;:\"“”]")


def normalize_text(value: Any, fold_accents: bool = False) -> str:
    text = unicodedata.normalize("NFC", str(value)).casefold()
    text = _PUNCTUATION.sub("", text)
    if fold_accents:
        text = "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))
    return " ".join(text.split())


def _pair_key(pair: Any) -> tuple[str, str]:
    return tuple(sorted(normalize_text(word) for word in pair))  # type: ignore[return-value]


def check_answer(exercise: Exercise, submitted: Any) -> bool:
    answer = exercise.answer
    if exercise.type == "word_bank":
        if not isinstance(submitted, list) or not all(isinstance(token, str) for token in submitted):
            return False
        return [normalize_text(item) for item in submitted] == [normalize_text(item) for item in answer["tokens"]]
    if exercise.type == "match_pairs":
        if not isinstance(submitted, list):
            return False
        if any(not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(word, str) for word in pair) for pair in submitted):
            return False
        return Counter(_pair_key(pair) for pair in submitted) == Counter(_pair_key(pair) for pair in answer["pairs"])
    if not isinstance(submitted, str):
        return False
    if exercise.type == "type_answer":
        return normalize_text(submitted, True) in {normalize_text(item, True) for item in answer["accepted"]}
    return normalize_text(submitted) == normalize_text(answer["value"])


def display_answer(exercise: Exercise) -> Any:
    answer = exercise.answer
    if exercise.type == "word_bank":
        return answer["tokens"]
    if exercise.type == "match_pairs":
        return answer["pairs"]
    if exercise.type == "type_answer":
        return answer["accepted"][0]
    return answer["value"]


def answer_attempt(db: Session, attempt_id: int, exercise_id: int, submitted: Any) -> dict[str, Any]:
    now = current_time()
    attempt = get_attempt(db, attempt_id)
    if attempt.status != "active":
        raise HTTPException(409, "Attempt is not active")
    if attempt_expired(attempt, now):
        attempt.status = "abandoned"
        attempt.completed_at = now
        db.commit()
        raise HTTPException(409, "Time is up")
    exercises = lesson_exercises(db, attempt.lesson_id)
    if attempt.current_index >= len(exercises):
        raise HTTPException(409, "All exercises are already answered")
    exercise = exercises[attempt.current_index]
    if exercise.id != exercise_id:
        raise HTTPException(409, "Exercises must be answered in order")
    user = get_user(db, attempt.user_id, now)
    correct = check_answer(exercise, submitted)
    db.add(ExerciseAttempt(attempt_id=attempt.id, exercise_id=exercise.id, submitted_answer={"value": submitted}, correct=correct, created_at=now))
    if correct:
        attempt.correct_count += 1
    elif attempt.mode == "lesson" and lose_heart(user, now):
        attempt.hearts_lost += 1
        log_heart_event(db, user, "mistake", -1, attempt.id)
    attempt.current_index += 1
    failed = attempt.mode == "lesson" and user.hearts == 0 and not correct
    if failed:
        attempt.status = "failed"
        attempt.completed_at = now
    try:
        db.commit()
    except IntegrityError:  # the same exercise was submitted twice concurrently
        db.rollback()
        raise HTTPException(409, "Exercise already answered") from None
    return {
        "correct": correct,
        "explanation": exercise.explanation,
        "correct_answer": display_answer(exercise),
        "hearts": user.hearts,
        "next_index": attempt.current_index,
        "ready_to_complete": attempt.current_index == len(exercises) and not failed,
        "failed": failed,
    }


# ---------------------------------------------------------------- achievements
def learner_metrics(db: Session, user: User, today: date) -> dict[str, int]:
    completed = (LessonAttempt.user_id == user.id, LessonAttempt.status == "completed")
    lessons = db.scalar(select(func.count(func.distinct(LessonAttempt.lesson_id))).where(*completed, LessonAttempt.mode == "lesson")) or 0
    perfect = db.scalar(select(func.count()).select_from(LessonAttempt).where(*completed, LessonAttempt.current_index > 0, LessonAttempt.correct_count == LessonAttempt.current_index)) or 0
    return {"lessons": lessons, "perfect": perfect, "xp": user.total_xp, "streak": effective_streak(user, today)}


def evaluate_achievements(db: Session, user: User, today: date | None = None) -> list[dict[str, Any]]:
    metrics = learner_metrics(db, user, today or today_utc())
    awarded_ids = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    newly_awarded = []
    for achievement in db.scalars(select(Achievement).order_by(Achievement.id)).all():
        if achievement.id not in awarded_ids and metrics.get(achievement.metric, 0) >= achievement.threshold:
            db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
            newly_awarded.append({"title": achievement.title, "icon": achievement.icon})
    return newly_awarded


def achievements_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> list[dict[str, Any]]:
    user = get_user(db, user_id)
    metrics = learner_metrics(db, user, today_utc())
    earned = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    return [
        {"id": item.id, "title": item.title, "description": item.description, "icon": item.icon, "earned": item.id in earned, "progress": min(metrics.get(item.metric, 0), item.threshold), "threshold": item.threshold}
        for item in db.scalars(select(Achievement).order_by(Achievement.id)).all()
    ]


# ---------------------------------------------------------------- completion
def complete_attempt(db: Session, attempt_id: int) -> dict[str, Any]:
    now = current_time()
    attempt = get_attempt(db, attempt_id)
    user = get_user(db, attempt.user_id, now)
    if attempt.status == "completed":
        return completion_payload(db, attempt, user, [])
    lesson = db.get(Lesson, attempt.lesson_id)
    exercise_count = db.scalar(select(func.count()).select_from(Exercise).where(Exercise.lesson_id == lesson.id)) or 0
    if attempt.status != "active" or attempt.current_index < exercise_count:
        raise HTTPException(409, "Attempt is not ready to complete")
    earned = lesson.xp_reward + attempt.correct_count * XP_PER_CORRECT_ANSWER
    if attempt.mode == "legendary":
        earned *= 2
    # Atomically claim the completion: exactly one concurrent request wins and applies the rewards.
    claimed = db.execute(
        update(LessonAttempt).where(LessonAttempt.id == attempt.id, LessonAttempt.status == "active").values(status="completed", completed_at=now)
    ).rowcount
    if claimed == 0:
        db.rollback()
        db.refresh(attempt)
        if attempt.status == "completed":
            return completion_payload(db, attempt, get_user(db, attempt.user_id), [])
        raise HTTPException(409, "Attempt is not ready to complete")
    db.refresh(attempt)
    today = today_utc(now)
    key = f"attempt:{attempt.id}:completion"
    if not db.scalar(select(XPEvent.id).where(XPEvent.idempotency_key == key)):
        db.add(XPEvent(user_id=user.id, amount=earned, source=attempt.mode, idempotency_key=key, created_at=now))
        user.total_xp += earned
        attempt.xp_awarded = earned
    update_streak(user, today)
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    if not activity:
        activity = DailyActivity(user_id=user.id, activity_date=today, xp_earned=0, lessons_completed=0)
        db.add(activity)
    activity.xp_earned += attempt.xp_awarded
    activity.lessons_completed += 1
    progress = db.scalar(select(SkillProgress).where(SkillProgress.user_id == user.id, SkillProgress.skill_id == lesson.skill_id))
    if not progress:
        progress = SkillProgress(user_id=user.id, skill_id=lesson.skill_id, completed_lessons=0, crowns=0, legendary=False)
        db.add(progress)
    if attempt.mode == "lesson":
        progress.completed_lessons = max(progress.completed_lessons, lesson.position)
        progress.crowns = max(progress.crowns, progress.completed_lessons)
    elif attempt.mode == "legendary":
        progress.legendary = True
    elif attempt.mode == "practice" and user.hearts < user.max_hearts:
        user.hearts = min(user.max_hearts, user.hearts + PRACTICE_HEART_REWARD)
        log_heart_event(db, user, "practice_reward", PRACTICE_HEART_REWARD, attempt.id)
    db.flush()
    new_achievements = evaluate_achievements(db, user, today)
    try:
        db.commit()
    except IntegrityError:  # a concurrent request completed the same attempt first
        db.rollback()
        attempt = get_attempt(db, attempt_id)
        if attempt.status == "completed":
            return completion_payload(db, attempt, get_user(db, attempt.user_id), [])
        raise HTTPException(409, "Attempt could not be completed") from None
    return completion_payload(db, attempt, user, new_achievements)


def completion_payload(db: Session, attempt: LessonAttempt, user: User, achievements: list[dict[str, Any]]) -> dict[str, Any]:
    answered = db.scalar(select(func.count()).select_from(ExerciseAttempt).where(ExerciseAttempt.attempt_id == attempt.id)) or attempt.current_index
    accuracy = attempt.correct_count / max(answered, 1)
    today = today_utc()
    today_xp = today_xp_for(db, user.id, today)
    return {
        "attempt_id": attempt.id,
        "mode": attempt.mode,
        "xp_awarded": attempt.xp_awarded,
        "accuracy": round(accuracy * 100),
        "streak": effective_streak(user, today),
        "total_xp": user.total_xp,
        "hearts": user.hearts,
        "today_xp": today_xp,
        "daily_goal": user.daily_goal,
        "daily_goal_reached": today_xp >= user.daily_goal,
        "perfect": answered > 0 and attempt.correct_count == answered,
        "new_achievements": achievements,
    }


# ---------------------------------------------------------------- leaderboard, quests, activity
def leaderboard_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    now = current_time()
    weekly = weekly_xp_by_user(db, now)
    users = sorted(db.scalars(select(User)).all(), key=lambda user: (-weekly.get(user.id, 0), user.id))
    total = len(users)
    entries = []
    for rank, user in enumerate(users, start=1):
        zone = "promotion" if rank <= LEAGUE_PROMOTION_SPOTS else "demotion" if rank > total - LEAGUE_DEMOTION_SPOTS else "safe"
        entries.append({"rank": rank, "id": user.id, "name": user.display_name, "username": user.username, "xp": weekly.get(user.id, 0), "avatar_color": user.avatar_color, "is_current": user.id == user_id, "zone": zone})
    ends_at = week_start(now) + timedelta(days=7)
    return {"league": "Bronze", "ends_in": format_remaining(ends_at - now), "ends_at": ends_at.isoformat(), "entries": entries}


def quests_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    now = current_time()
    user = get_user(db, user_id, now)
    today = today_utc(now)
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    xp = activity.xp_earned if activity else 0
    lessons = activity.lessons_completed if activity else 0
    day_start = datetime.combine(today, datetime.min.time())
    perfect = db.scalar(
        select(func.count()).select_from(LessonAttempt).where(
            LessonAttempt.user_id == user.id,
            LessonAttempt.status == "completed",
            LessonAttempt.completed_at >= day_start,
            LessonAttempt.current_index > 0,
            LessonAttempt.correct_count == LessonAttempt.current_index,
        )
    ) or 0
    definitions = [
        ("daily-xp", f"Earn {user.daily_goal} XP", xp, user.daily_goal, 10),
        ("daily-lesson", "Complete a lesson", lessons, 1, 10),
        ("daily-perfect", "Finish a lesson with no mistakes", perfect, 1, 20),
    ]
    quests = [{"id": key, "title": title, "progress": min(progress, target), "target": target, "completed": progress >= target, "reward_gems": reward} for key, title, progress, target, reward in definitions]
    return {"ends_in": format_remaining(day_start + timedelta(days=1) - now), "quests": quests}


def activity_payload(db: Session, days: int, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    now = current_time()
    user = get_user(db, user_id, now)
    today = today_utc(now)
    start = today - timedelta(days=days - 1)
    rows = {row.activity_date: row for row in db.scalars(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date >= start)).all()}
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = rows.get(day)
        xp = row.xp_earned if row else 0
        result.append({"date": day.isoformat(), "xp": xp, "lessons": row.lessons_completed if row else 0, "goal_met": xp >= user.daily_goal})
    return {"days": result, "current_streak": effective_streak(user, today), "longest_streak": user.longest_streak}


def profile_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    user = get_user(db, user_id)
    states = skill_states(db, user.id)
    return {
        "user": serialize_user(db, user),
        "achievements": achievements_payload(db, user_id),
        "league": leaderboard_payload(db, user_id)["league"],
        "completed_skills": sum(1 for state in states if state["status"] == "completed"),
        "lessons_completed": learner_metrics(db, user, today_utc())["lessons"],
    }
