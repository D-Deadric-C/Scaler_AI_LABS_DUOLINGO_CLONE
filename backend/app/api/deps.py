"""Shared FastAPI dependencies."""
from fastapi import HTTPException

from ..core.config import DEFAULT_USER_ID, dev_endpoints_enabled
from ..database import get_db  # noqa: F401  (re-exported so routes import dependencies from one place)


def current_user_id() -> int:
    """The acting learner. Single seeded demo learner today; swap for a session lookup to add auth."""
    return DEFAULT_USER_ID


def require_dev_endpoints() -> None:
    if not dev_endpoints_enabled():
        raise HTTPException(404, "Not found")
