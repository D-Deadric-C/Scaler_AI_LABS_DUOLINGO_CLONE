"""Lesson attempt state machine: start/resume, answer, complete, abandon."""
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    AttemptMode,
    AttemptStatus,
    DailyActivity,
    Exercise,
    ExerciseAttempt,
    HeartEventKind,
    Lesson,
    LessonAttempt,
    SkillProgress,
    SkillStatus,
    User,
    XPEvent,
)
from . import clock
from .achievements import evaluate_achievements
from .exercises import check_answer, display_answer, lesson_exercises, public_exercise
from .hearts import PRACTICE_HEART_REWARD, log_heart_event, lose_heart
from .path import course_id_for_skill, skill_states
from .streaks import effective_streak, update_streak
from .users import get_user, today_xp_for

LEGENDARY_SECONDS = 75
LEGENDARY_GRACE_SECONDS = 3
XP_PER_CORRECT_ANSWER = 2


def attempt_expired(attempt: LessonAttempt, now: datetime) -> bool:
    return attempt.expires_at is not None and now > attempt.expires_at + timedelta(seconds=LEGENDARY_GRACE_SECONDS)


def seconds_left(attempt: LessonAttempt, now: datetime) -> int | None:
    if attempt.expires_at is None or attempt.status != AttemptStatus.ACTIVE:
        return None
    return max(0, int((attempt.expires_at - now).total_seconds()))


def get_attempt(db: Session, attempt_id: int, user_id: int) -> LessonAttempt:
    attempt = db.get(LessonAttempt, attempt_id)
    if not attempt or attempt.user_id != user_id:
        raise HTTPException(404, "Attempt not found")
    return attempt


def start_attempt(db: Session, user_id: int, lesson_id: int, mode: str) -> dict[str, Any]:
    now = clock.current_time()
    user = get_user(db, user_id, now)
    lesson = db.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    state = next((item for item in skill_states(db, user.id, course_id_for_skill(db, lesson.skill_id)) if item["skill"].id == lesson.skill_id), None)
    if state is None or state["status"] == SkillStatus.LOCKED:
        raise HTTPException(403, "Complete the previous skill to unlock this lesson")
    if mode == AttemptMode.LESSON and lesson.position > state["completed_lessons"] + 1:
        raise HTTPException(403, "Finish the earlier lessons in this skill first")
    if mode == AttemptMode.LEGENDARY and state["status"] != SkillStatus.COMPLETED:
        raise HTTPException(403, "Complete this skill to unlock the legendary challenge")
    if mode == AttemptMode.LESSON and user.hearts <= 0:
        raise HTTPException(409, "You need a heart to start this lesson")
    active = db.scalar(
        select(LessonAttempt).where(
            LessonAttempt.user_id == user.id,
            LessonAttempt.lesson_id == lesson.id,
            LessonAttempt.mode == mode,
            LessonAttempt.status == AttemptStatus.ACTIVE,
        )
    )
    if active and attempt_expired(active, now):
        active.status = AttemptStatus.ABANDONED
        active.completed_at = now
        active = None
    attempt = active
    if attempt is None:
        attempt = LessonAttempt(
            user_id=user.id,
            lesson_id=lesson.id,
            mode=mode,
            started_at=now,
            expires_at=now + timedelta(seconds=LEGENDARY_SECONDS) if mode == AttemptMode.LEGENDARY else None,
        )
        db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt_payload(db, attempt, now)


def attempt_payload(db: Session, attempt: LessonAttempt, now: datetime | None = None) -> dict[str, Any]:
    now = now or clock.current_time()
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


def read_attempt(db: Session, user_id: int, attempt_id: int) -> dict[str, Any]:
    return attempt_payload(db, get_attempt(db, attempt_id, user_id))


def abandon_attempt(db: Session, user_id: int, attempt_id: int) -> dict[str, str]:
    attempt = get_attempt(db, attempt_id, user_id)
    if attempt.status == AttemptStatus.ACTIVE:
        attempt.status = AttemptStatus.ABANDONED
        attempt.completed_at = clock.current_time()
        db.commit()
    return {"status": attempt.status}


def answer_attempt(db: Session, user_id: int, attempt_id: int, exercise_id: int, submitted: Any) -> dict[str, Any]:
    now = clock.current_time()
    attempt = get_attempt(db, attempt_id, user_id)
    if attempt.status != AttemptStatus.ACTIVE:
        raise HTTPException(409, "Attempt is not active")
    if attempt_expired(attempt, now):
        attempt.status = AttemptStatus.ABANDONED
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
    elif attempt.mode == AttemptMode.LESSON and lose_heart(user, now):
        attempt.hearts_lost += 1
        log_heart_event(db, user, HeartEventKind.MISTAKE, -1, attempt.id)
    attempt.current_index += 1
    failed = attempt.mode == AttemptMode.LESSON and user.hearts == 0 and not correct
    if failed:
        attempt.status = AttemptStatus.FAILED
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


def complete_attempt(db: Session, user_id: int, attempt_id: int) -> dict[str, Any]:
    now = clock.current_time()
    attempt = get_attempt(db, attempt_id, user_id)
    user = get_user(db, attempt.user_id, now)
    if attempt.status == AttemptStatus.COMPLETED:
        return completion_payload(db, attempt, user, [])
    lesson = db.get(Lesson, attempt.lesson_id)
    exercise_count = db.scalar(select(func.count()).select_from(Exercise).where(Exercise.lesson_id == lesson.id)) or 0
    if attempt.status != AttemptStatus.ACTIVE or attempt.current_index < exercise_count:
        raise HTTPException(409, "Attempt is not ready to complete")
    earned = lesson.xp_reward + attempt.correct_count * XP_PER_CORRECT_ANSWER
    if attempt.mode == AttemptMode.LEGENDARY:
        earned *= 2
    # Atomically claim the completion: exactly one concurrent request wins and applies the rewards.
    claimed = db.execute(
        update(LessonAttempt).where(LessonAttempt.id == attempt.id, LessonAttempt.status == AttemptStatus.ACTIVE).values(status=AttemptStatus.COMPLETED, completed_at=now)
    ).rowcount
    if claimed == 0:
        db.rollback()
        db.refresh(attempt)
        if attempt.status == AttemptStatus.COMPLETED:
            return completion_payload(db, attempt, get_user(db, attempt.user_id), [])
        raise HTTPException(409, "Attempt is not ready to complete")
    db.refresh(attempt)
    today = clock.today_utc(now)
    key = f"attempt:{attempt.id}:completion"
    if not db.scalar(select(XPEvent.id).where(XPEvent.idempotency_key == key)):
        db.add(XPEvent(user_id=user.id, amount=earned, source=attempt.mode, idempotency_key=key, created_at=now))
        user.total_xp += earned
        attempt.xp_awarded = earned
    update_streak(user, today)
    record_daily_activity(db, user, today, attempt.xp_awarded)
    apply_skill_progress(db, user, lesson, attempt)
    db.flush()
    new_achievements = evaluate_achievements(db, user, today)
    try:
        db.commit()
    except IntegrityError:  # a concurrent request completed the same attempt first
        db.rollback()
        attempt = get_attempt(db, attempt_id, user_id)
        if attempt.status == AttemptStatus.COMPLETED:
            return completion_payload(db, attempt, get_user(db, attempt.user_id), [])
        raise HTTPException(409, "Attempt could not be completed") from None
    return completion_payload(db, attempt, user, new_achievements)


def record_daily_activity(db: Session, user: User, today: date, xp: int) -> None:
    activity = db.scalar(select(DailyActivity).where(DailyActivity.user_id == user.id, DailyActivity.activity_date == today))
    if not activity:
        activity = DailyActivity(user_id=user.id, activity_date=today, xp_earned=0, lessons_completed=0)
        db.add(activity)
    activity.xp_earned += xp
    activity.lessons_completed += 1


def apply_skill_progress(db: Session, user: User, lesson: Lesson, attempt: LessonAttempt) -> None:
    progress = db.scalar(select(SkillProgress).where(SkillProgress.user_id == user.id, SkillProgress.skill_id == lesson.skill_id))
    if not progress:
        progress = SkillProgress(user_id=user.id, skill_id=lesson.skill_id, completed_lessons=0, crowns=0, legendary=False)
        db.add(progress)
    if attempt.mode == AttemptMode.LESSON:
        progress.completed_lessons = max(progress.completed_lessons, lesson.position)
        progress.crowns = max(progress.crowns, progress.completed_lessons)
    elif attempt.mode == AttemptMode.LEGENDARY:
        progress.legendary = True
    elif attempt.mode == AttemptMode.PRACTICE and user.hearts < user.max_hearts:
        user.hearts = min(user.max_hearts, user.hearts + PRACTICE_HEART_REWARD)
        log_heart_event(db, user, HeartEventKind.PRACTICE_REWARD, PRACTICE_HEART_REWARD, attempt.id)


def completion_payload(db: Session, attempt: LessonAttempt, user: User, achievements: list[dict[str, Any]]) -> dict[str, Any]:
    answered = db.scalar(select(func.count()).select_from(ExerciseAttempt).where(ExerciseAttempt.attempt_id == attempt.id)) or attempt.current_index
    accuracy = attempt.correct_count / max(answered, 1)
    today = clock.today_utc()
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
