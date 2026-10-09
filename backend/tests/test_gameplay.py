"""Gameplay rules exercised end to end through the HTTP API (plus pure rule unit tests)."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.models import Course, Exercise, HeartEvent, Lesson, LessonAttempt, Skill, Unit, SkillProgress, User, XPEvent
from app.services.exercises import check_answer, normalize_text
from conftest import APIClient, Clock
from helpers import SET_A, SET_B, all_skills, finish_perfect_lesson, start, submit_answer


def me(client: APIClient) -> dict:
    return client.get("/api/v1/me").json()


# ------------------------------------------------------------ progression
def test_playing_the_whole_course_completes_the_path_and_awards_scholar(client: APIClient) -> None:
    results = [finish_perfect_lesson(client, index) for index in range(1, 12)]
    assert any(item["title"] == "Scholar" for result in results for item in result["new_achievements"])
    skills = all_skills(client)
    assert [skill["status"] for skill in skills] == ["completed"] * 12
    payload = client.get("/api/v1/bootstrap").json()
    assert payload["practice_lesson_id"] == skills[-1]["lesson_id"]
    assert client.get("/api/v1/me/profile").json()["completed_skills"] == 12


def test_replaying_a_finished_lesson_keeps_progress_and_adds_xp(client: APIClient) -> None:
    first = finish_perfect_lesson(client, 1)
    again = finish_perfect_lesson(client, 1)
    assert again["xp_awarded"] == first["xp_awarded"]
    assert me(client)["total_xp"] == 185 + first["xp_awarded"] * 2
    assert [skill["status"] for skill in all_skills(client)[:3]] == ["completed", "completed", "available"]


def test_skills_with_several_lessons_unlock_in_order(client: APIClient) -> None:
    skill = all_skills(client)[1]
    with client.sessions() as db:
        first = db.get(Lesson, skill["lesson_id"])
        second = Lesson(skill_id=first.skill_id, position=2, title="Second lesson", xp_reward=12)
        db.add(second)
        db.flush()
        for exercise in db.scalars(select(Exercise).where(Exercise.lesson_id == first.id)).all():
            db.add(Exercise(lesson_id=second.id, position=exercise.position, type=exercise.type, prompt=exercise.prompt, payload=exercise.payload, answer=exercise.answer))
        db.commit()
        second_id = second.id
    skill = all_skills(client)[1]
    assert (skill["status"], skill["progress"], skill["total_lessons"]) == ("available", 0, 2)
    assert client.post(f"/api/v1/lessons/{second_id}/attempts", json={"mode": "lesson"}).status_code == 403
    finish_perfect_lesson(client, 1)
    skills = all_skills(client)
    assert (skills[1]["status"], skills[1]["progress"], skills[1]["lesson_id"]) == ("available", 1, second_id)
    assert skills[2]["status"] == "locked"
    attempt = client.post(f"/api/v1/lessons/{second_id}/attempts", json={"mode": "lesson"}).json()
    for index, value in enumerate(SET_B):
        submit_answer(client, attempt, index, value)
    client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete")
    skills = all_skills(client)
    assert (skills[1]["status"], skills[2]["status"]) == ("completed", "available")


def test_courses_are_independent_paths(client: APIClient) -> None:
    with client.sessions() as db:
        course = Course(slug="french", title="French", target_language="French", flag="FR")
        db.add(course)
        db.flush()
        unit = Unit(course_id=course.id, position=1, title="Unit 1", objective="Bonjour")
        db.add(unit)
        db.flush()
        skill = Skill(unit_id=unit.id, position=1, title="Greetings", description="Say hello")
        db.add(skill)
        db.flush()
        lesson = Lesson(skill_id=skill.id, position=1, title="Greetings 1")
        db.add(lesson)
        db.commit()
        course_id, lesson_id = course.id, lesson.id
    french = client.get(f"/api/v1/courses/{course_id}/path").json()
    assert french["course"]["title"] == "French" and len(french["units"]) == 1
    assert [skill["status"] for skill in french["units"][0]["skills"]] == ["available"]  # unaffected by Spanish progress
    assert client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).status_code == 200
    assert [skill["status"] for skill in all_skills(client)[:3]] == ["completed", "available", "locked"]
    assert client.get("/api/v1/courses/999/path").status_code == 404


def test_leaderboard_rank_improves_as_xp_is_earned(client: APIClient) -> None:
    def rank() -> int:
        return next(entry["rank"] for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if entry["is_current"])

    assert rank() == 5
    finish_perfect_lesson(client, 1)
    finish_perfect_lesson(client, 2)  # 95 + 20 + 20 = 135 passes Nora (125)
    assert rank() == 4


def test_xp_ledger_matches_total_xp_and_daily_activity(client: APIClient) -> None:
    for index in (1, 2):
        finish_perfect_lesson(client, index)
    with client.sessions() as db:
        earned = db.scalar(select(func.sum(XPEvent.amount)).where(XPEvent.user_id == 1, XPEvent.source != "seed"))
        total = db.scalar(select(User.total_xp).where(User.id == 1))
    assert total == 185 + earned == 225
    assert client.get("/api/v1/me/activity?days=1").json()["days"][0]["xp"] == 15 + earned


# ------------------------------------------------------------------ attempts
def test_resuming_mid_lesson_returns_the_same_attempt_and_position(client: APIClient) -> None:
    attempt = start(client)
    submit_answer(client, attempt, 0, SET_B[0])
    submit_answer(client, attempt, 1, SET_B[1])
    resumed = start(client)
    assert resumed["attempt_id"] == attempt["attempt_id"] and len(resumed["queue"]) == 3 and resumed["correct_count"] == 2
    assert client.get(f"/api/v1/attempts/{attempt['attempt_id']}").json()["queue"] == resumed["queue"]


def test_modes_are_independent_and_abandoned_attempts_restart(client: APIClient) -> None:
    lesson, practice = start(client), start(client, mode="practice")
    assert lesson["attempt_id"] != practice["attempt_id"]
    client.post(f"/api/v1/attempts/{lesson['attempt_id']}/abandon")
    fresh = start(client)
    assert fresh["attempt_id"] not in {lesson["attempt_id"], practice["attempt_id"]} and len(fresh["queue"]) == 5 and fresh["correct_count"] == 0


def test_posting_without_a_body_defaults_to_a_lesson_attempt(client: APIClient) -> None:
    lesson_id = all_skills(client)[1]["lesson_id"]
    response = client.post(f"/api/v1/lessons/{lesson_id}/attempts")
    assert response.status_code == 200 and response.json()["mode"] == "lesson"


def test_skipping_counts_as_a_mistake(client: APIClient) -> None:
    attempt = start(client)
    result = submit_answer(client, attempt, 0, "").json()
    assert result["correct"] is False and result["hearts"] == 3


def test_attempts_of_other_learners_are_invisible(client: APIClient) -> None:
    with client.sessions() as db:
        lesson_id = db.scalar(select(Lesson.id))
        foreign = LessonAttempt(user_id=2, lesson_id=lesson_id)
        db.add(foreign)
        db.commit()
        foreign_id = foreign.id
    assert client.get(f"/api/v1/attempts/{foreign_id}").status_code == 404
    assert client.post(f"/api/v1/attempts/{foreign_id}/answers", json={"exercise_id": 1, "answer": "x"}).status_code == 404
    assert client.post(f"/api/v1/attempts/{foreign_id}/complete").status_code == 404
    assert client.post(f"/api/v1/attempts/{foreign_id}/abandon").status_code == 404


def test_legendary_doubles_xp_costs_no_hearts_and_marks_the_skill(client: APIClient) -> None:
    attempt = start(client, skill_index=0, mode="legendary")
    answers = SET_A
    assert submit_answer(client, attempt, 0, "wrong").json()["hearts"] == 4
    for index in range(1, 5):
        submit_answer(client, attempt, index, answers[index])
    submit_answer(client, attempt, 0, answers[0])  # retry of the wrong answer
    result = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    assert (result["mode"], result["xp_awarded"], result["hearts"]) == ("legendary", (10 + 4 * 2) * 2, 4)
    with client.sessions() as db:
        assert db.scalar(select(SkillProgress.legendary).where(SkillProgress.user_id == 1, SkillProgress.skill_id == 1)) is True


def test_concurrent_completion_requests_award_xp_once(client: APIClient) -> None:
    attempt = start(client)
    for index, value in enumerate(SET_B):
        submit_answer(client, attempt, index, value)
    url = f"/api/v1/attempts/{attempt['attempt_id']}/complete"
    with ThreadPoolExecutor(6) as pool:
        responses = list(pool.map(lambda _: client.post(url), range(6)))
    assert all(response.status_code == 200 for response in responses)
    assert {response.json()["xp_awarded"] for response in responses} == {20}
    assert me(client)["total_xp"] == 205
    assert client.get("/api/v1/me/activity?days=1").json()["days"][0]["lessons"] == 1


# ------------------------------------------------------------ hearts & ledger
def test_hearts_regenerate_over_time(client: APIClient, clock: Clock) -> None:
    attempt = start(client)
    submit_answer(client, attempt, 0, "wrong")
    submit_answer(client, attempt, 1, "wrong")
    assert client.get("/api/v1/hearts").json()["hearts"] == 2
    clock.value += timedelta(minutes=65)
    after = client.get("/api/v1/hearts").json()
    assert after["hearts"] == 4 and after["next_heart_at"] is not None
    clock.value += timedelta(hours=5)
    assert client.get("/api/v1/hearts").json() == {"hearts": 5, "max_hearts": 5, "next_heart_at": None}


def test_heart_events_form_a_ledger(client: APIClient) -> None:
    attempt = start(client)
    submit_answer(client, attempt, 0, "wrong")
    client.post("/api/v1/hearts/gem-refill")
    with client.sessions() as db:
        events = db.execute(select(HeartEvent.kind, HeartEvent.delta, HeartEvent.hearts_after, HeartEvent.gems_spent).order_by(HeartEvent.id)).all()
    assert [tuple(event) for event in events] == [("mistake", -1, 3, 0), ("gem_refill", 2, 5, 350)]


# ---------------------------------------------------------- streaks & days
def test_streak_grows_daily_and_resets_after_a_gap(client: APIClient, clock: Clock) -> None:
    assert finish_perfect_lesson(client, 1)["streak"] == 8
    clock.value += timedelta(days=1)
    assert me(client)["today_xp"] == 0
    assert finish_perfect_lesson(client, 2)["streak"] == 9
    clock.value += timedelta(days=3)
    assert me(client)["current_streak"] == 0
    assert finish_perfect_lesson(client, 3)["streak"] == 1
    assert me(client)["longest_streak"] == 12


def test_two_lessons_on_one_day_count_once_for_the_streak(client: APIClient) -> None:
    finish_perfect_lesson(client, 1)
    assert finish_perfect_lesson(client, 2)["streak"] == 8


def test_simulating_days_repeatedly_keeps_history_consistent(client: APIClient) -> None:
    finish_perfect_lesson(client, 1)
    for _ in range(3):
        assert client.post("/api/v1/dev/simulate-day").status_code == 200
    days = client.get("/api/v1/me/activity?days=5").json()["days"]
    assert sum(day["xp"] for day in days) == 15 + 20 and days[-1]["xp"] == 0


def test_reset_leaves_rivals_untouched(client: APIClient) -> None:
    before = [(entry["name"], entry["xp"]) for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if not entry["is_current"]]
    finish_perfect_lesson(client, 1)
    client.post("/api/v1/dev/reset")
    after = [(entry["name"], entry["xp"]) for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if not entry["is_current"]]
    assert before == after


# ----------------------------------------------------------------- settings
def test_settings_persist_and_drive_the_daily_goal(client: APIClient) -> None:
    assert client.patch("/api/v1/me/settings", json={"dark_mode": True}).json()["dark_mode"] is True
    assert me(client)["dark_mode"] is True
    changed = client.patch("/api/v1/me/settings", json={"daily_goal": 30}).json()
    assert changed["daily_goal"] == 30 and changed["dark_mode"] is True
    quest = next(item for item in client.get("/api/v1/quests").json()["quests"] if item["id"] == "daily-xp")
    assert (quest["target"], quest["title"]) == (30, "Earn 30 XP")
    assert client.patch("/api/v1/me/settings", json={}).status_code == 200


@pytest.mark.parametrize("body", [{"daily_goal": 4}, {"daily_goal": 101}, {"daily_goal": "lots"}, {"dark_mode": "maybe"}])
def test_invalid_settings_are_rejected(client: APIClient, body: dict) -> None:
    assert client.patch("/api/v1/me/settings", json=body).status_code == 422
    assert me(client)["daily_goal"] == 20


# ------------------------------------------------------------ API surface
def test_health_checks_the_database(client: APIClient) -> None:
    assert client.get("/api/v1/health").json() == {"status": "ok", "service": "duolingo-api"}


def test_openapi_documents_every_route_with_typed_responses(client: APIClient) -> None:
    spec = client.get("/api/openapi.json").json()
    for path in ("/api/v1/bootstrap", "/api/v1/courses/{course_id}/path", "/api/v1/lessons/{lesson_id}/attempts", "/api/v1/attempts/{attempt_id}/answers", "/api/v1/attempts/{attempt_id}/complete", "/api/v1/leaderboards/weekly", "/api/v1/quests", "/api/v1/hearts/gem-refill"):
        assert path in spec["paths"]
    assert {"PathOut", "AttemptOut", "AnswerOut", "CompletionOut", "LeaderboardOut"} <= set(spec["components"]["schemas"])


def test_unknown_routes_and_methods_use_standard_errors(client: APIClient) -> None:
    assert client.get("/api/v1/nope").status_code == 404
    assert client.post("/api/v1/me").status_code == 405
    assert client.post("/api/v1/attempts/1/answers", content="not json", headers={"content-type": "application/json"}).status_code == 422


def test_a_busy_database_is_reported_as_retryable(client: APIClient, monkeypatch) -> None:
    def locked(*_args, **_kwargs):
        raise OperationalError("UPDATE", {}, Exception("database is locked"))

    monkeypatch.setattr("app.api.routes.learner.me_payload", locked)
    response = client.get("/api/v1/me")
    assert response.status_code == 503 and response.headers["retry-after"] == "1"


# --------------------------------------------------------- rule unit tests
def exercise(kind: str, answer: dict) -> Exercise:
    return Exercise(type=kind, answer=answer, payload={}, prompt="p", position=1, lesson_id=1)


@pytest.mark.parametrize(
    ("kind", "answer", "submitted", "expected"),
    [
        ("multiple_choice", {"value": "hello"}, "Hello", True),
        ("multiple_choice", {"value": "hello"}, " hello. ", True),
        ("multiple_choice", {"value": "hello"}, "goodbye", False),
        ("multiple_choice", {"value": "hello"}, ["hello"], False),
        ("fill_blank", {"value": "quiero"}, "quiero", True),
        ("fill_blank", {"value": "está"}, "esta", False),  # accents matter outside typed answers
        ("type_answer", {"accepted": ["mucho gusto", "encantado"]}, "Encantado!", True),
        ("type_answer", {"accepted": ["está"]}, "esta", True),
        ("type_answer", {"accepted": ["gracias"]}, "gracias por todo", False),
        ("type_answer", {"accepted": ["gracias"]}, None, False),
        ("word_bank", {"tokens": ["Vivo", "en", "Delhi"]}, ["Vivo", "en", "Delhi"], True),
        ("word_bank", {"tokens": ["Vivo", "en", "Delhi"]}, ["en", "Vivo", "Delhi"], False),
        ("word_bank", {"tokens": ["Vivo", "en", "Delhi"]}, ["Vivo", "en"], False),
        ("word_bank", {"tokens": ["Vivo", "en", "Delhi"]}, "Vivo en Delhi", False),
        ("word_bank", {"tokens": ["Vivo", "en", "Delhi"]}, [1, 2, 3], False),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, [["a", "1"], ["b", "2"]], True),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, [["b", "2"], ["a", "1"]], True),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, [["a", "2"], ["b", "1"]], False),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, [["a", "1"]], False),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, [], False),
        ("match_pairs", {"pairs": [["a", "1"], ["b", "2"]]}, "a1b2", False),
    ],
)
def test_answer_checking(kind, answer, submitted, expected) -> None:
    assert check_answer(exercise(kind, answer), submitted) is expected


def test_text_normalisation() -> None:
    assert normalize_text("  ¿Qué   TAL?! ") == "qué tal"
    assert normalize_text("Qué", fold_accents=True) == "que"
    assert normalize_text("ÑANDÚ", fold_accents=True) == "nandu"


# ------------------------------------------------- wrong answers come back
def test_a_wrong_answer_is_requeued_at_the_end(client: APIClient) -> None:
    attempt = start(client)
    ids = [exercise["id"] for exercise in attempt["exercises"]]
    assert attempt["queue"] == ids
    wrong = submit_answer(client, attempt, 0, "wrong").json()
    assert wrong["correct"] is False and wrong["queue"] == ids[1:] + [ids[0]] and wrong["remaining"] == 5
    assert wrong["correct_count"] == 0 and wrong["ready_to_complete"] is False
    right = submit_answer(client, attempt, 1, SET_B[1]).json()
    assert right["queue"] == ids[2:] + [ids[0]] and right["correct_count"] == 1


def test_the_lesson_only_finishes_when_every_exercise_is_correct(client: APIClient) -> None:
    attempt = start(client)
    base = f"/api/v1/attempts/{attempt['attempt_id']}"
    submit_answer(client, attempt, 0, "wrong")
    for index in range(1, 5):
        done = submit_answer(client, attempt, index, SET_B[index]).json()
    assert done["ready_to_complete"] is False and done["queue"] == [attempt["exercises"][0]["id"]]
    assert client.post(f"{base}/complete").status_code == 409
    assert submit_answer(client, attempt, 0, "still wrong").json()["queue"] == [attempt["exercises"][0]["id"]]  # asked again
    final = submit_answer(client, attempt, 0, SET_B[0]).json()
    assert final["ready_to_complete"] is True and final["queue"] == []
    result = client.post(f"{base}/complete").json()
    assert result["perfect"] is False and result["accuracy"] == 71  # 5 correct out of 7 answers
    assert result["xp_awarded"] == 10 + 2 * 4  # bonus XP only for exercises right on the first try


def test_only_the_head_of_the_queue_can_be_answered(client: APIClient) -> None:
    attempt = start(client)
    submit_answer(client, attempt, 0, "wrong")
    assert submit_answer(client, attempt, 0, SET_B[0]).status_code == 409  # exercise 0 is now last in the queue
    assert submit_answer(client, attempt, 1, SET_B[1]).status_code == 200


def test_the_queue_survives_a_refresh(client: APIClient) -> None:
    attempt = start(client)
    submit_answer(client, attempt, 0, "wrong")
    submit_answer(client, attempt, 1, SET_B[1])
    resumed = start(client)
    ids = [exercise["id"] for exercise in attempt["exercises"]]
    assert resumed["attempt_id"] == attempt["attempt_id"]
    assert resumed["queue"] == ids[2:] + [ids[0]] and resumed["correct_count"] == 1


def test_retrying_costs_a_heart_each_time_and_can_fail_the_lesson(client: APIClient) -> None:
    attempt = start(client)
    results = [submit_answer(client, attempt, 0, "wrong").json()]
    assert results[0]["hearts"] == 3
    for expected_hearts in (2, 1, 0):  # the same exercise keeps coming back (after the others) while answered wrong
        for index in range(1, 5):
            if index > 1 or expected_hearts != 2:
                break
        # answer the head of the queue wrongly each time
        head_id = results[-1]["queue"][0]
        index = next(i for i, exercise in enumerate(attempt["exercises"]) if exercise["id"] == head_id)
        results.append(submit_answer(client, attempt, index, "wrong").json())
        assert results[-1]["hearts"] == expected_hearts
    assert results[-1]["failed"] is True and results[-1]["ready_to_complete"] is False
    assert client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").status_code == 409


def test_practice_and_legendary_also_retry_but_never_cost_hearts(client: APIClient) -> None:
    for mode, skill in (("practice", 1), ("legendary", 0)):
        hearts_before = me(client)["hearts"]
        attempt = start(client, skill_index=skill, mode=mode)
        first = submit_answer(client, attempt, 0, "wrong").json()
        assert first["hearts"] == hearts_before and first["queue"][-1] == attempt["exercises"][0]["id"]
        answers = SET_A if skill == 0 else SET_B
        for index in range(1, 5):
            submit_answer(client, attempt, index, answers[index])
        assert submit_answer(client, attempt, 0, answers[0]).json()["ready_to_complete"] is True
        assert client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").status_code == 200


def test_skipping_requeues_the_exercise_too(client: APIClient) -> None:
    attempt = start(client)
    skipped = submit_answer(client, attempt, 0, "").json()
    assert skipped["queue"][-1] == attempt["exercises"][0]["id"] and skipped["hearts"] == 3


def test_perfect_lessons_have_no_retries(client: APIClient) -> None:
    result = finish_perfect_lesson(client)
    assert result["perfect"] is True and result["accuracy"] == 100 and result["xp_awarded"] == 20


# ---------------------------------------------------------------- unit chest
def chest(client: APIClient, unit_index: int = 0) -> dict:
    return client.get("/api/v1/courses/1/path").json()["units"][unit_index]["chest"]


def unit_id(client: APIClient, unit_index: int = 0) -> int:
    return client.get("/api/v1/courses/1/path").json()["units"][unit_index]["id"]


def test_chest_unlocks_after_the_first_three_levels(client: APIClient) -> None:
    assert chest(client)["status"] == "locked"
    assert client.post(f"/api/v1/lessons/{all_skills(client)[4]['lesson_id']}/attempts", json={"mode": "lesson"}).status_code == 403
    assert client.post(f"/api/v1/units/{unit_id(client)}/chest").status_code == 403
    finish_perfect_lesson(client, 1)
    assert chest(client)["status"] == "locked"  # one skill is still open
    finish_perfect_lesson(client, 2)
    assert chest(client) == {"status": "ready", "gems": 30}
    assert [skill["status"] for skill in all_skills(client)[:6]] == ["completed"] * 3 + ["available"] + ["locked"] * 2
    assert client.post(f"/api/v1/lessons/{all_skills(client)[4]['lesson_id']}/attempts", json={"mode": "lesson"}).status_code == 403
    assert chest(client, 1)["status"] == "locked"  # the next unit's chest is independent


def test_opening_the_chest_pays_gems_once(client: APIClient) -> None:
    finish_perfect_lesson(client, 1)
    finish_perfect_lesson(client, 2)
    before = me(client)["gems"]
    result = client.post(f"/api/v1/units/{unit_id(client)}/chest").json()
    assert result == {"gems_awarded": 30, "gems": before + 30}
    assert chest(client)["status"] == "opened" and me(client)["gems"] == before + 30
    assert client.post(f"/api/v1/units/{unit_id(client)}/chest").status_code == 403  # already opened
    assert me(client)["gems"] == before + 30
    assert client.post("/api/v1/units/999/chest").status_code == 404


def test_reset_closes_the_chest_again(client: APIClient) -> None:
    finish_perfect_lesson(client, 1)
    finish_perfect_lesson(client, 2)
    client.post(f"/api/v1/units/{unit_id(client)}/chest")
    client.post("/api/v1/dev/reset")
    assert chest(client)["status"] == "locked" and me(client)["gems"] == 480


# ------------------------------------------------------- learner timezone
def test_me_reports_the_learners_calendar_day_and_last_active_day(client: APIClient, clock: Clock) -> None:
    clock.value = clock.value.replace(hour=12, minute=0)
    user = me(client)
    assert user["today"] == clock.value.date().isoformat() and user["tz_offset_minutes"] == 0
    assert user["last_active_date"] == (clock.value.date() - timedelta(days=1)).isoformat()  # seeded: active yesterday
    finish_perfect_lesson(client, 1)
    assert me(client)["last_active_date"] == clock.value.date().isoformat()


def test_streak_days_follow_the_learners_timezone(client: APIClient, clock: Clock) -> None:
    from datetime import datetime as dt

    base = clock.value.date()
    clock.value = dt.combine(base, dt.min.time()).replace(hour=20)  # 20:00 UTC
    assert client.patch("/api/v1/me/settings", json={"tz_offset_minutes": 330}).json()["today"] == (base + timedelta(days=1)).isoformat()  # already tomorrow in India
    result = finish_perfect_lesson(client, 1)
    assert result["streak"] == 1  # the seeded streak ended two local days ago
    assert me(client)["last_active_date"] == (base + timedelta(days=1)).isoformat()
    assert client.patch("/api/v1/me/settings", json={"tz_offset_minutes": 0}).json()["today"] == base.isoformat()
    client.post("/api/v1/dev/reset")
    assert finish_perfect_lesson(client, 1)["streak"] == 8  # same instant, a UTC learner keeps the streak


@pytest.mark.parametrize("offset", [841, -841, "later"])
def test_invalid_timezone_offsets_are_rejected(client: APIClient, offset) -> None:
    assert client.patch("/api/v1/me/settings", json={"tz_offset_minutes": offset}).status_code == 422
