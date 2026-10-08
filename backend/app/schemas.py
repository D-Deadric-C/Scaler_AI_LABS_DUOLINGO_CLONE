from typing import Any

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    exercise_id: int
    answer: Any


class SettingsRequest(BaseModel):
    dark_mode: bool | None = None
    daily_goal: int | None = Field(default=None, ge=5, le=100)


class AttemptCreateRequest(BaseModel):
    mode: str = Field(default="lesson", pattern="^(lesson|practice|legendary)$")

