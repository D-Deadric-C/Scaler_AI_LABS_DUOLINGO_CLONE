"""Learning path: ordered skills with unlock state derived from progress."""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Lesson, Skill, SkillProgress, Unit
from . import clock
from .users import get_user, serialize_user


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


def path_payload(db: Session, user_id: int) -> dict[str, Any]:
    now = clock.current_time()
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
