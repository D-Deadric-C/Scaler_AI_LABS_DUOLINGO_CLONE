from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
from random import shuffle
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    Achievement,
    DailyActivity,
    Exercise,
    ExerciseAttempt,
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


def get_user(db: Session, user_id: int = DEFAULT_USER_ID) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Learner not found")
    regenerate_hearts(user)
    return user


def regenerate_hearts(user: User, now: datetime | None = None) -> None:
    if user.hearts >= user.max_hearts:
        return
    current = now or utc_now()
    elapsed = current - user.hearts_updated_at
    regenerated = int(elapsed.total_seconds() // (HEART_REGEN_MINUTES * 60))
    if regenerated > 0:
        user.hearts = min(user.max_hearts, user.hearts + regenerated)
        user.hearts_updated_at += timedelta(minutes=regenerated * HEART_REGEN_MINUTES)


def effective_streak(user: User, today: date) -> int:
    if user.last_active_date not in {today, today - timedelta(days=1)}:
        return 0
    return user.current_streak


def serialize_user(db: Session, user: User) -> dict[str, Any]:
    today_xp = db.scalar(select(DailyActivity.xp_earned).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == date.today())) or 0
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_color": user.avatar_color,
        "total_xp": user.total_xp,
        "weekly_xp": user.weekly_xp,
        "gems": user.gems,
        "hearts": user.hearts,
        "max_hearts": user.max_hearts,
        "current_streak": effective_streak(user, date.today()),
        "longest_streak": user.longest_streak,
        "daily_goal": user.daily_goal,
        "today_xp": today_xp,
        "dark_mode": user.dark_mode,
        "next_heart_at": None if user.hearts >= user.max_hearts else (user.hearts_updated_at + timedelta(minutes=HEART_REGEN_MINUTES)).isoformat(),
    }


def ordered_skills(db: Session) -> list[Skill]:
    return list(db.scalars(select(Skill).join(Unit).order_by(Unit.position, Skill.position)).all())


def path_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    user = get_user(db, user_id)
    units = db.scalars(select(Unit).order_by(Unit.position)).all()
    skills = ordered_skills(db)
    skills_by_unit: dict[int, list[Skill]] = {unit.id: [] for unit in units}
    for skill in skills:
        skills_by_unit[skill.unit_id].append(skill)
    first_lessons: dict[int, Lesson] = {}
    for lesson in db.scalars(select(Lesson).order_by(Lesson.skill_id, Lesson.position)).all():
        first_lessons.setdefault(lesson.skill_id, lesson)
    progress = {p.skill_id: p for p in db.scalars(select(SkillProgress).where(SkillProgress.user_id == user.id)).all()}
    completed_ids = {skill_id for skill_id, row in progress.items() if row.completed_lessons > 0}
    result_units = []
    previous_complete = True
    for unit in units:
        unit_skills = []
        for skill in skills_by_unit[unit.id]:
            row = progress.get(skill.id)
            status = "completed" if skill.id in completed_ids else "available" if previous_complete else "locked"
            lesson = first_lessons.get(skill.id)
            unit_skills.append({
                "id": skill.id,
                "title": skill.title,
                "description": skill.description,
                "icon": skill.icon,
                "status": status,
                "progress": 1 if row and row.completed_lessons else 0,
                "total_lessons": 1,
                "lesson_id": lesson.id if lesson else None,
                "xp_reward": lesson.xp_reward if lesson else 0,
            })
            previous_complete = skill.id in completed_ids
        result_units.append({"id": unit.id, "position": unit.position, "title": unit.title, "objective": unit.objective, "color": unit.color, "skills": unit_skills})
    return {"course": {"id": 1, "title": "Spanish", "flag": "ES"}, "user": serialize_user(db, user), "units": result_units}


def start_attempt(db: Session, lesson_id: int, mode: str, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    user = get_user(db, user_id)
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    ordered_skill_ids = [skill.id for skill in ordered_skills(db)]
    skill_index = ordered_skill_ids.index(lesson.skill_id)
    if skill_index > 0:
        previous_skill_id = ordered_skill_ids[skill_index - 1]
        previous_progress = db.scalar(
            select(SkillProgress).where(
                SkillProgress.user_id == user.id,
                SkillProgress.skill_id == previous_skill_id,
            )
        )
        if not previous_progress or previous_progress.completed_lessons < 1:
            raise HTTPException(403, "Complete the previous skill to unlock this lesson")
    if user.hearts <= 0 and mode == "lesson":
        raise HTTPException(409, "You need a heart to start this lesson")
    active = db.scalar(
        select(LessonAttempt).where(
            LessonAttempt.user_id == user.id,
            LessonAttempt.lesson_id == lesson.id,
            LessonAttempt.mode == mode,
            LessonAttempt.status == "active",
        )
    )
    attempt = active or LessonAttempt(user_id=user.id, lesson_id=lesson.id, mode=mode)
    if not active:
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
    return attempt_payload(db, attempt)


def attempt_payload(db: Session, attempt: LessonAttempt) -> dict[str, Any]:
    lesson = db.get(Lesson, attempt.lesson_id)
    exercises = db.scalars(select(Exercise).where(Exercise.lesson_id == attempt.lesson_id).order_by(Exercise.position)).all()
    user = get_user(db, attempt.user_id)
    def public_exercise(exercise: Exercise) -> dict[str, Any]:
        payload = exercise.payload
        if exercise.type == "match_pairs":
            pairs = payload["pairs"]
            right = [pair[1] for pair in pairs]
            shuffle(right)
            payload = {"left": [pair[0] for pair in pairs], "right": right}
        return {"id": exercise.id, "type": exercise.type, "prompt": exercise.prompt, "hint": exercise.hint, "payload": payload}

    return {
        "attempt_id": attempt.id,
        "lesson": {"id": lesson.id, "title": lesson.title, "xp_reward": lesson.xp_reward},
        "status": attempt.status,
        "current_index": attempt.current_index,
        "hearts": user.hearts,
        "exercises": [public_exercise(exercise) for exercise in exercises],
    }


def normalize_text(value: Any) -> str:
    return " ".join(str(value).strip().lower().split())


def check_answer(exercise: Exercise, submitted: Any) -> bool:
    answer = exercise.answer
    if exercise.type == "word_bank":
        if not isinstance(submitted, list) or not all(isinstance(token, str) for token in submitted):
            return False
        tokens = submitted
        return [normalize_text(item) for item in tokens] == [normalize_text(item) for item in answer["tokens"]]
    if exercise.type == "match_pairs":
        pairs = submitted if isinstance(submitted, list) else []
        if any(
            not isinstance(pair, list)
            or len(pair) != 2
            or not all(isinstance(word, str) for word in pair)
            for pair in pairs
        ):
            return False
        normalized = Counter(tuple(sorted((normalize_text(a), normalize_text(b)))) for a, b in pairs)
        expected = Counter(tuple(sorted((normalize_text(a), normalize_text(b)))) for a, b in answer["pairs"])
        return normalized == expected
    if exercise.type == "type_answer":
        if not isinstance(submitted, str):
            return False
        return normalize_text(submitted) in {normalize_text(item) for item in answer["accepted"]}
    if not isinstance(submitted, str):
        return False
    return normalize_text(submitted) == normalize_text(answer["value"])


def answer_attempt(db: Session, attempt_id: int, exercise_id: int, submitted: Any) -> dict[str, Any]:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt or attempt.status != "active":
        raise HTTPException(409, "Attempt is not active")
    exercises = db.scalars(select(Exercise).where(Exercise.lesson_id == attempt.lesson_id).order_by(Exercise.position)).all()
    if attempt.current_index >= len(exercises):
        raise HTTPException(409, "All exercises are already answered")
    exercise = exercises[attempt.current_index]
    if exercise.id != exercise_id:
        raise HTTPException(409, "Exercises must be answered in order")
    prior = db.scalar(select(ExerciseAttempt).where(ExerciseAttempt.attempt_id == attempt.id, ExerciseAttempt.exercise_id == exercise.id))
    if prior:
        raise HTTPException(409, "Exercise already answered")
    correct = check_answer(exercise, submitted)
    db.add(ExerciseAttempt(attempt_id=attempt.id, exercise_id=exercise.id, submitted_answer={"value": submitted}, correct=correct))
    user = get_user(db, attempt.user_id)
    if correct:
        attempt.correct_count += 1
    elif attempt.mode == "lesson":
        user.hearts = max(0, user.hearts - 1)
        user.hearts_updated_at = utc_now()
        attempt.hearts_lost += 1
    attempt.current_index += 1
    failed = user.hearts == 0 and attempt.mode == "lesson"
    if failed:
        attempt.status = "failed"
        attempt.completed_at = utc_now()
    db.commit()
    correct_answer = exercise.answer.get("value") or exercise.answer.get("accepted", [None])[0] or exercise.answer.get("tokens") or exercise.answer.get("pairs")
    return {
        "correct": correct,
        "explanation": exercise.explanation,
        "correct_answer": correct_answer,
        "hearts": user.hearts,
        "next_index": attempt.current_index,
        "ready_to_complete": attempt.current_index == len(exercises) and not failed,
        "failed": failed,
    }


def update_streak(user: User, today: date) -> None:
    if user.last_active_date == today:
        return
    if user.last_active_date == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1
    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_active_date = today


def evaluate_achievements(db: Session, user: User) -> list[dict[str, Any]]:
    lesson_count = db.scalar(select(func.count()).select_from(LessonAttempt).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "completed")) or 0
    metrics = {"lessons": lesson_count, "xp": user.total_xp, "streak": effective_streak(user, date.today())}
    awarded_ids = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    newly_awarded = []
    for achievement in db.scalars(select(Achievement)).all():
        if achievement.id not in awarded_ids and metrics.get(achievement.metric, 0) >= achievement.threshold:
            db.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
            newly_awarded.append({"title": achievement.title, "icon": achievement.icon})
    return newly_awarded


def complete_attempt(db: Session, attempt_id: int) -> dict[str, Any]:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    user = get_user(db, attempt.user_id)
    lesson = db.get(Lesson, attempt.lesson_id)
    exercise_count = db.scalar(select(func.count()).select_from(Exercise).where(Exercise.lesson_id == lesson.id)) or 0
    if attempt.status == "completed":
        return completion_payload(db, attempt, user, [])
    if attempt.status != "active" or attempt.current_index < exercise_count:
        raise HTTPException(409, "Attempt is not ready to complete")
    accuracy = attempt.correct_count / max(exercise_count, 1)
    earned = lesson.xp_reward + round(attempt.correct_count * 2)
    if attempt.mode == "legendary":
        earned *= 2
    key = f"attempt:{attempt.id}:completion"
    if not db.scalar(select(XPEvent.id).where(XPEvent.idempotency_key == key)):
        db.add(XPEvent(user_id=user.id, amount=earned, source=attempt.mode, idempotency_key=key))
        user.total_xp += earned
        user.weekly_xp += earned
        attempt.xp_awarded = earned
    attempt.status = "completed"
    attempt.completed_at = utc_now()
    today = date.today()
    update_streak(user, today)
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    if not activity:
        activity = DailyActivity(user_id=user.id, activity_date=today)
        db.add(activity)
    activity.xp_earned += attempt.xp_awarded
    activity.lessons_completed += 1
    progress = db.scalar(select(SkillProgress).where(SkillProgress.user_id == user.id, SkillProgress.skill_id == lesson.skill_id))
    if not progress:
        progress = SkillProgress(
            user_id=user.id,
            skill_id=lesson.skill_id,
            completed_lessons=0,
            crowns=0,
            legendary=False,
        )
        db.add(progress)
    if attempt.mode == "lesson":
        progress.completed_lessons = max(progress.completed_lessons, 1)
        progress.crowns = max(progress.crowns, 1)
    db.flush()
    new_achievements = evaluate_achievements(db, user)
    db.commit()
    return completion_payload(db, attempt, user, new_achievements, accuracy)


def completion_payload(db: Session, attempt: LessonAttempt, user: User, achievements: list[dict[str, Any]], accuracy: float | None = None) -> dict[str, Any]:
    count = db.scalar(select(func.count()).select_from(ExerciseAttempt).where(ExerciseAttempt.attempt_id == attempt.id)) or 0
    computed_accuracy = accuracy if accuracy is not None else attempt.correct_count / max(count, 1)
    return {
        "attempt_id": attempt.id,
        "xp_awarded": attempt.xp_awarded,
        "accuracy": round(computed_accuracy * 100),
        "streak": effective_streak(user, date.today()),
        "total_xp": user.total_xp,
        "new_achievements": achievements,
    }


def leaderboard_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> dict[str, Any]:
    users = db.scalars(select(User).order_by(User.weekly_xp.desc(), User.id)).all()
    return {"league": "Bronze", "ends_in": "3d 8h", "entries": [
        {"rank": index, "id": user.id, "name": user.display_name, "username": user.username, "xp": user.weekly_xp, "avatar_color": user.avatar_color, "is_current": user.id == user_id}
        for index, user in enumerate(users, start=1)
    ]}


def achievements_payload(db: Session, user_id: int = DEFAULT_USER_ID) -> list[dict[str, Any]]:
    user = get_user(db, user_id)
    lesson_count = db.scalar(select(func.count()).select_from(LessonAttempt).where(LessonAttempt.user_id == user.id, LessonAttempt.status == "completed")) or 0
    metrics = {"lessons": lesson_count, "xp": user.total_xp, "streak": effective_streak(user, date.today())}
    earned = set(db.scalars(select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)).all())
    return [
        {"id": item.id, "title": item.title, "description": item.description, "icon": item.icon, "earned": item.id in earned, "progress": min(metrics.get(item.metric, 0), item.threshold), "threshold": item.threshold}
        for item in db.scalars(select(Achievement).order_by(Achievement.id)).all()
    ]
