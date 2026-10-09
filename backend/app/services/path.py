"""Learning path: ordered skills with unlock state derived from progress."""
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Course, Lesson, Skill, SkillProgress, SkillStatus, Unit
from . import clock
from .users import get_user, serialize_user


def default_course(db: Session) -> Course:
    course = db.scalar(select(Course).order_by(Course.id).limit(1))
    if course is None:
        raise HTTPException(503, "No course has been seeded")
    return course


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "Course not found")
    return course


def course_id_for_skill(db: Session, skill_id: int) -> int:
    return db.scalar(select(Unit.course_id).join(Skill, Skill.unit_id == Unit.id).where(Skill.id == skill_id))


def ordered_skills(db: Session, course_id: int) -> list[Skill]:
    return list(db.scalars(select(Skill).join(Unit).where(Unit.course_id == course_id).order_by(Unit.position, Skill.position)).all())


def skill_states(db: Session, user_id: int, course_id: int) -> list[dict[str, Any]]:
    """Ordered skills with derived lock state; unlocking is computed, never stored."""
    skills = ordered_skills(db, course_id)
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
        status = SkillStatus.COMPLETED if complete else SkillStatus.AVAILABLE if previous_complete and lessons else SkillStatus.LOCKED
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
    for status in (SkillStatus.COMPLETED, SkillStatus.AVAILABLE):
        candidates = [state for state in states if state["status"] == status]
        if candidates:
            lesson = next_lesson(candidates[-1] if status == SkillStatus.COMPLETED else candidates[0])
            return lesson.id if lesson else None
    return None


def path_payload(db: Session, user_id: int, course_id: int | None = None) -> dict[str, Any]:
    now = clock.current_time()
    user = get_user(db, user_id, now)
    course = get_course(db, course_id) if course_id is not None else default_course(db)
    states = skill_states(db, user.id, course.id)
    states_by_unit: dict[int, list[dict[str, Any]]] = {}
    for state in states:
        states_by_unit.setdefault(state["skill"].unit_id, []).append(state)
    from .chests import CHEST_GEMS, chest_status, claimed_unit_ids  # local import: chests builds on this module

    claimed = claimed_unit_ids(db, user.id)
    units = []
    for unit in db.scalars(select(Unit).where(Unit.course_id == course.id).order_by(Unit.position)).all():
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
        chest = {"status": chest_status([skill["status"] for skill in skills], unit.id in claimed), "gems": CHEST_GEMS}
        units.append({"id": unit.id, "position": unit.position, "title": unit.title, "objective": unit.objective, "color": unit.color, "skills": skills, "chest": chest})
    return {
        "course": {"id": course.id, "title": course.title, "flag": course.flag},
        "user": serialize_user(db, user, now),
        "units": units,
        "practice_lesson_id": practice_lesson_id(states),
    }
