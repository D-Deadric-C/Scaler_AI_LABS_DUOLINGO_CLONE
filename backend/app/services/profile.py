"""Profile page aggregate."""
from typing import Any

from sqlalchemy.orm import Session

from . import clock
from .achievements import achievements_payload, learner_metrics
from .leaderboard import leaderboard_payload
from .path import skill_states
from .users import get_user, serialize_user


def profile_payload(db: Session, user_id: int) -> dict[str, Any]:
    user = get_user(db, user_id)
    states = skill_states(db, user.id)
    payload = {
        "user": serialize_user(db, user),
        "achievements": achievements_payload(db, user_id),
        "league": leaderboard_payload(db, user_id)["league"],
        "completed_skills": sum(1 for state in states if state["status"] == "completed"),
        "lessons_completed": learner_metrics(db, user, clock.today_utc())["lessons"],
    }
    db.commit()
    return payload
