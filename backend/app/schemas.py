from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from .models import AttemptMode, SkillStatus

MAX_ANSWER_ITEMS = 60
MAX_ANSWER_TEXT = 300


def _within_limits(value: Any, budget: list[int]) -> None:
    budget[0] -= 1
    if budget[0] < 0:
        raise ValueError("Answer is too large")
    if isinstance(value, str) and len(value) > MAX_ANSWER_TEXT:
        raise ValueError("Answer text is too long")
    if isinstance(value, dict):
        raise ValueError("Answer must be text or a list")
    if isinstance(value, list):
        for item in value:
            _within_limits(item, budget)


# ---------------------------------------------------------------- requests
class AnswerRequest(BaseModel):
    exercise_id: int
    answer: Any = None

    @field_validator("answer")
    @classmethod
    def bounded_answer(cls, value: Any) -> Any:
        _within_limits(value, [MAX_ANSWER_ITEMS])
        return value


class SettingsRequest(BaseModel):
    dark_mode: bool | None = None
    daily_goal: int | None = Field(default=None, ge=5, le=100)


class AttemptCreateRequest(BaseModel):
    mode: AttemptMode = AttemptMode.LESSON


# --------------------------------------------------------------- responses
class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    avatar_color: str
    total_xp: int
    weekly_xp: int
    gems: int
    hearts: int
    max_hearts: int
    current_streak: int
    longest_streak: int
    daily_goal: int
    today_xp: int
    dark_mode: bool
    next_heart_at: str | None


class SkillOut(BaseModel):
    id: int
    title: str
    description: str
    icon: str
    status: SkillStatus
    progress: int
    total_lessons: int
    crowns: int
    lesson_id: int | None
    xp_reward: int


class UnitOut(BaseModel):
    id: int
    position: int
    title: str
    objective: str
    color: str
    skills: list[SkillOut]


class CourseOut(BaseModel):
    id: int
    title: str
    flag: str


class LeaderboardEntryOut(BaseModel):
    rank: int
    id: int
    name: str
    username: str
    xp: int
    avatar_color: str
    is_current: bool
    zone: Literal["promotion", "safe", "demotion"]


class LeaderboardOut(BaseModel):
    league: str
    ends_in: str
    ends_at: str
    entries: list[LeaderboardEntryOut]


class AchievementOut(BaseModel):
    id: int
    title: str
    description: str
    icon: str
    earned: bool
    progress: int
    threshold: int


class PathOut(BaseModel):
    course: CourseOut
    user: UserOut
    units: list[UnitOut]


class BootstrapOut(PathOut):
    practice_lesson_id: int | None
    leaderboard: list[LeaderboardEntryOut]
    achievements: list[AchievementOut]


class ProfileOut(BaseModel):
    user: UserOut
    achievements: list[AchievementOut]
    league: str
    completed_skills: int
    lessons_completed: int


class ExerciseOut(BaseModel):
    id: int
    type: str
    prompt: str
    hint: str | None
    payload: dict[str, Any]


class LessonSummaryOut(BaseModel):
    id: int
    title: str
    xp_reward: int


class AttemptOut(BaseModel):
    attempt_id: int
    mode: str
    lesson: LessonSummaryOut
    status: str
    queue: list[int]
    total_exercises: int
    correct_count: int
    hearts: int
    seconds_left: int | None
    exercises: list[ExerciseOut]


class AnswerOut(BaseModel):
    correct: bool
    explanation: str
    correct_answer: Any
    hearts: int
    queue: list[int]
    remaining: int
    correct_count: int
    ready_to_complete: bool
    failed: bool


class AchievementUnlockedOut(BaseModel):
    title: str
    icon: str


class CompletionOut(BaseModel):
    attempt_id: int
    mode: str
    xp_awarded: int
    accuracy: int
    streak: int
    total_xp: int
    hearts: int
    today_xp: int
    daily_goal: int
    daily_goal_reached: bool
    perfect: bool
    new_achievements: list[AchievementUnlockedOut]


class StatusOut(BaseModel):
    status: str


class HeartsOut(BaseModel):
    hearts: int
    max_hearts: int
    next_heart_at: str | None


class RefillOut(BaseModel):
    hearts: int
    gems: int
    message: str


class QuestOut(BaseModel):
    id: str
    title: str
    progress: int
    target: int
    completed: bool
    reward_gems: int


class QuestsOut(BaseModel):
    ends_in: str
    quests: list[QuestOut]


class ActivityDayOut(BaseModel):
    date: str
    xp: int
    lessons: int
    goal_met: bool


class ActivityOut(BaseModel):
    days: list[ActivityDayOut]
    current_streak: int
    longest_streak: int


class DevActionOut(BaseModel):
    status: str
    message: str
