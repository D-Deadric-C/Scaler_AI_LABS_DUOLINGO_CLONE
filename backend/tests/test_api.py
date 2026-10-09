from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import ExerciseAttempt, LessonAttempt, User, UserAchievement
from app.seed import seed_database
from app.services.hearts import regenerate_hearts
from app.services.streaks import effective_streak, update_streak
from conftest import APIClient, Clock
from helpers import FIRST_LESSON_ANSWERS, finish_perfect_lesson, start, submit_answer


def test_health_and_seeded_path(client: APIClient) -> None:
    assert client.get("/api/v1/health").json()["status"] == "ok"
    payload = client.get("/api/v1/courses/1/path").json()
    assert len(payload["units"]) == 2
    statuses = [skill["status"] for unit in payload["units"] for skill in unit["skills"]]
    assert statuses[:3] == ["completed", "available", "locked"]


def test_seeded_progress_has_consistent_achievements(client: APIClient) -> None:
    profile = client.get("/api/v1/me/profile").json()
    achievements = {item["title"]: item for item in profile["achievements"]}
    assert all(achievements[title]["earned"] for title in ("First Steps", "XP Explorer", "Wildfire"))
    assert achievements["First Steps"]["progress"] == 1
    assert achievements["Scholar"]["progress"] == 1
    assert not achievements["Scholar"]["earned"]


def test_existing_sample_data_is_reconciled_without_resetting_stats(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'existing.db'}")
    Base.metadata.create_all(bind=engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with sessions() as db:
        seed_database(db)
        db.execute(delete(ExerciseAttempt))
        db.execute(delete(LessonAttempt))
        db.execute(delete(UserAchievement))
        db.commit()
        original_xp = db.scalar(select(User.total_xp).where(User.username == "learner"))
        seed_database(db)
        seed_database(db)
        assert db.scalar(select(func.count()).select_from(LessonAttempt)) == 1
        assert db.scalar(select(func.count()).select_from(UserAchievement)) == 4
        assert db.scalar(select(User.total_xp).where(User.username == "learner")) == original_xp
    engine.dispose()


def test_complete_lesson_is_idempotent(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    answers = ["My name is Ana", ["Vivo", "en", "Delhi"], [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]], "llamo", "mucho gusto"]
    for exercise, answer in zip(attempt["exercises"], answers, strict=True):
        response = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": answer})
        assert response.status_code == 200
        assert response.json()["correct"] is True
    first = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    second = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    assert first["xp_awarded"] == second["xp_awarded"]
    assert first["total_xp"] == second["total_xp"]


def test_lesson_rewards_update_profile_quest_leaderboard_and_path(client: APIClient) -> None:
    before = client.get("/api/v1/courses/1/path").json()
    lesson_id = before["units"][0]["skills"][1]["lesson_id"]
    weekly_before = next(entry["xp"] for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if entry["is_current"])
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    answers = ["wrong", ["Vivo", "en", "Delhi"], [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]], "llamo", "mucho gusto"]
    for exercise, answer in zip(attempt["exercises"], answers, strict=True):
        response = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": answer})
        assert response.status_code == 200
    assert client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").status_code == 409  # the wrong answer is still queued
    retry = submit_answer(client, attempt, 0, "My name is Ana")
    assert retry.json()["correct"] is True and retry.json()["ready_to_complete"] is True

    completion = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    after = client.get("/api/v1/courses/1/path").json()
    profile = client.get("/api/v1/me/profile").json()
    weekly_after = next(entry["xp"] for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if entry["is_current"])
    assert completion["xp_awarded"] == 18
    assert completion["accuracy"] == 83  # 5 correct out of 6 submitted answers
    assert after["user"]["total_xp"] == before["user"]["total_xp"] + 18
    assert after["user"]["today_xp"] == before["user"]["today_xp"] + 18
    assert after["user"]["current_streak"] == before["user"]["current_streak"] + 1
    assert after["user"]["hearts"] == before["user"]["hearts"] - 1
    assert after["units"][0]["skills"][1]["status"] == "completed"
    assert after["units"][0]["skills"][2]["status"] == "available"
    assert weekly_after == weekly_before + 18
    assert any(item["title"] == "First Steps" and item["earned"] for item in profile["achievements"])


def test_fully_answered_attempt_can_resume_and_complete_once(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    initial_xp = path["user"]["total_xp"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    answers = ["My name is Ana", ["Vivo", "en", "Delhi"], [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]], "llamo", "mucho gusto"]
    for exercise, answer in zip(attempt["exercises"], answers, strict=True):
        response = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": answer})
        assert response.status_code == 200
    resumed = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    assert resumed["attempt_id"] == attempt["attempt_id"]
    assert resumed["status"] == "active"
    assert resumed["queue"] == []
    first = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    second = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    assert first["total_xp"] == second["total_xp"] == initial_xp + first["xp_awarded"]
    assert first["new_achievements"] == []
    assert client.get("/api/v1/courses/1/path").json()["units"][0]["skills"][2]["status"] == "available"


def test_completing_unit_one_unlocks_unit_two(client: APIClient) -> None:
    answer_sets = [
        ["My name is Ana", ["Vivo", "en", "Delhi"], [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]], "llamo", "mucho gusto"],
        ["hello", ["Quiero", "café"], [["hola", "hello"], ["café", "coffee"], ["gracias", "thanks"]], "quiero", "gracias"],
    ]
    for skill_index, answers in zip((1, 2), answer_sets, strict=True):
        path = client.get("/api/v1/courses/1/path").json()
        lesson_id = path["units"][0]["skills"][skill_index]["lesson_id"]
        attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
        for exercise, answer in zip(attempt["exercises"], answers, strict=True):
            response = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": answer})
            assert response.json()["correct"] is True
        client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete")

    path = client.get("/api/v1/courses/1/path").json()
    assert all(skill["status"] == "completed" for skill in path["units"][0]["skills"])
    assert path["units"][1]["skills"][0]["status"] == "available"
    assert all(skill["status"] == "locked" for skill in path["units"][1]["skills"][1:])


def test_match_pair_answers_are_not_sent_to_the_browser(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    match = next(exercise for exercise in attempt["exercises"] if exercise["type"] == "match_pairs")
    assert set(match["payload"]) == {"left", "right"}
    assert len(match["payload"]["left"]) == len(match["payload"]["right"]) == 3


def test_malformed_match_pairs_do_not_crash_the_api(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    for exercise in attempt["exercises"][:2]:
        response = client.post(
            f"/api/v1/attempts/{attempt['attempt_id']}/answers",
            json={"exercise_id": exercise["id"], "answer": "wrong"},
        )
        assert response.status_code == 200
    match = attempt["exercises"][2]
    response = client.post(
        f"/api/v1/attempts/{attempt['attempt_id']}/answers",
        json={"exercise_id": match["id"], "answer": [["hola"], 42]},
    )
    assert response.status_code == 200
    assert response.json()["correct"] is False


def test_duplicate_match_pair_does_not_count_as_correct(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    for exercise, answer in zip(attempt["exercises"][:2], ["My name is Ana", ["Vivo", "en", "Delhi"]], strict=True):
        response = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": answer})
        assert response.json()["correct"] is True
    pairs = [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]]
    response = client.post(
        f"/api/v1/attempts/{attempt['attempt_id']}/answers",
        json={"exercise_id": attempt["exercises"][2]["id"], "answer": pairs + [pairs[0]]},
    )
    assert response.json()["correct"] is False


def test_wrong_answer_loses_one_heart(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    exercise = attempt["exercises"][0]
    result = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": exercise["id"], "answer": "wrong"}).json()
    assert result["correct"] is False
    assert result["hearts"] == attempt["hearts"] - 1


def test_locked_lesson_cannot_be_started(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    locked_lesson_id = path["units"][0]["skills"][2]["lesson_id"]
    response = client.post(f"/api/v1/lessons/{locked_lesson_id}/attempts", json={"mode": "lesson"})
    assert response.status_code == 403


def test_zero_hearts_blocks_lessons_until_practice_refill(client: APIClient) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    lesson_id = path["units"][0]["skills"][1]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).json()
    for exercise in attempt["exercises"][:4]:
        response = client.post(
            f"/api/v1/attempts/{attempt['attempt_id']}/answers",
            json={"exercise_id": exercise["id"], "answer": "wrong"},
        )
        assert response.status_code == 200
    assert response.json()["failed"] is True
    assert response.json()["hearts"] == 0
    failed_path = client.get("/api/v1/courses/1/path").json()
    assert failed_path["user"]["total_xp"] == path["user"]["total_xp"]
    assert failed_path["units"][0]["skills"][1]["status"] == "available"
    assert client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").status_code == 409
    assert client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).status_code == 409
    refill = client.post("/api/v1/hearts/practice-refill").json()
    assert refill["hearts"] == path["user"]["max_hearts"]
    assert client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": "lesson"}).status_code == 200


def test_streak_and_hearts_rules_accept_an_explicit_clock() -> None:
    today = date(2026, 10, 9)
    now = datetime(2026, 10, 9, 12, 0)
    user = User(
        username="clock-test", display_name="Clock Test", hearts=2, max_hearts=5,
        hearts_updated_at=now - timedelta(minutes=65), current_streak=3,
        longest_streak=3, last_active_date=today - timedelta(days=1),
    )
    regenerate_hearts(user, now)
    assert user.hearts == 4
    update_streak(user, today)
    update_streak(user, today)
    assert user.current_streak == 4
    assert user.longest_streak == 4
    update_streak(user, today + timedelta(days=2))
    assert user.current_streak == 1
    assert user.longest_streak == 4


def test_displayed_streak_expires_after_a_missed_day() -> None:
    today = date(2026, 10, 9)
    user = User(username="streak-test", display_name="Streak Test", current_streak=7, longest_streak=7, last_active_date=today - timedelta(days=2))
    assert effective_streak(user, today) == 0
    assert user.current_streak == 7
    update_streak(user, today)
    assert effective_streak(user, today) == 1


def test_second_mistake_does_not_restart_the_heart_timer() -> None:
    from app.services.hearts import lose_heart

    now = datetime(2026, 10, 9, 12, 0)
    user = User(username="t", display_name="T", hearts=5, max_hearts=5, hearts_updated_at=now - timedelta(days=3))
    assert lose_heart(user, now) and user.hearts == 4
    assert lose_heart(user, now + timedelta(minutes=20)) and user.hearts == 3
    regenerate_hearts(user, now + timedelta(minutes=31))
    assert user.hearts == 4  # first heart returns 30 minutes after the first mistake, not the second
    assert user.hearts_updated_at == now + timedelta(minutes=30)


def test_lose_heart_never_goes_below_zero() -> None:
    from app.services.hearts import lose_heart

    now = datetime(2026, 10, 9, 12, 0)
    user = User(username="t", display_name="T", hearts=0, max_hearts=5, hearts_updated_at=now)
    assert lose_heart(user, now) is False
    assert user.hearts == 0


def test_refill_rules_and_gem_ledger(client: APIClient) -> None:
    assert client.post("/api/v1/hearts/practice-refill").json()["hearts"] == 5
    assert client.post("/api/v1/hearts/practice-refill").status_code == 409
    assert client.post("/api/v1/hearts/gem-refill").status_code == 409
    attempt = start(client)
    submit_answer(client, attempt, 0, "wrong")
    refill = client.post("/api/v1/hearts/gem-refill").json()
    assert refill["hearts"] == 5
    assert refill["gems"] == 480 - 350
    submit_answer(client, attempt, 1, "wrong")
    assert client.post("/api/v1/hearts/gem-refill").status_code == 409  # only 130 gems left


def test_practice_never_costs_hearts_and_rewards_one(client: APIClient) -> None:
    attempt = start(client, mode="practice")
    assert submit_answer(client, attempt, 0, "wrong").json()["hearts"] == 4
    for index, value in list(enumerate(FIRST_LESSON_ANSWERS))[1:]:
        submit_answer(client, attempt, index, value)
    submit_answer(client, attempt, 0, FIRST_LESSON_ANSWERS[0])  # the missed exercise comes back
    result = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    assert result["hearts"] == 5
    path = client.get("/api/v1/courses/1/path").json()
    assert path["units"][0]["skills"][1]["status"] == "available"  # practice does not complete a skill


def test_practice_is_allowed_with_zero_hearts(client: APIClient) -> None:
    attempt = start(client)
    for index in range(4):
        submit_answer(client, attempt, index, "wrong")
    assert client.post(f"/api/v1/lessons/{attempt['lesson']['id']}/attempts", json={"mode": "lesson"}).status_code == 409
    assert client.post(f"/api/v1/lessons/{attempt['lesson']['id']}/attempts", json={"mode": "practice"}).status_code == 200


def test_legendary_requires_completed_skill_and_is_server_timed(client: APIClient, clock: Clock) -> None:
    path = client.get("/api/v1/courses/1/path").json()
    open_lesson = path["units"][0]["skills"][1]["lesson_id"]
    assert client.post(f"/api/v1/lessons/{open_lesson}/attempts", json={"mode": "legendary"}).status_code == 403
    done_lesson = path["units"][0]["skills"][0]["lesson_id"]
    attempt = client.post(f"/api/v1/lessons/{done_lesson}/attempts", json={"mode": "legendary"}).json()
    assert attempt["seconds_left"] == 75
    clock.value += timedelta(seconds=40)
    resumed = client.post(f"/api/v1/lessons/{done_lesson}/attempts", json={"mode": "legendary"}).json()
    assert resumed["attempt_id"] == attempt["attempt_id"] and resumed["seconds_left"] == 35
    clock.value += timedelta(seconds=60)
    late = submit_answer(client, attempt, 0, "hello")
    assert late.status_code == 409 and late.json()["detail"] == "Time is up"
    assert client.get(f"/api/v1/attempts/{attempt['attempt_id']}").json()["status"] == "abandoned"
    fresh = client.post(f"/api/v1/lessons/{done_lesson}/attempts", json={"mode": "legendary"}).json()
    assert fresh["attempt_id"] != attempt["attempt_id"] and fresh["seconds_left"] == 75


def test_answer_validation_and_ordering(client: APIClient) -> None:
    attempt = start(client)
    base = f"/api/v1/attempts/{attempt['attempt_id']}/answers"
    assert client.post(base, json={"exercise_id": attempt["exercises"][0]["id"], "answer": {"a": 1}}).status_code == 422
    assert client.post(base, json={"exercise_id": attempt["exercises"][0]["id"], "answer": "x" * 400}).status_code == 422
    assert client.post(base, json={"exercise_id": attempt["exercises"][0]["id"], "answer": ["a"] * 100}).status_code == 422
    assert client.post(base, json={"exercise_id": attempt["exercises"][3]["id"], "answer": "llamo"}).status_code == 409
    assert submit_answer(client, attempt, 0, "My name is Ana").status_code == 200
    assert submit_answer(client, attempt, 0, "My name is Ana").status_code == 409
    assert client.post(base, json={"exercise_id": 99999, "answer": "x"}).status_code == 409
    assert client.post("/api/v1/attempts/99999/answers", json={"exercise_id": 1, "answer": "x"}).status_code == 404
    assert client.get("/api/v1/attempts/99999").status_code == 404
    assert client.post("/api/v1/lessons/99999/attempts", json={"mode": "lesson"}).status_code == 404
    assert client.post("/api/v1/lessons/1/attempts", json={"mode": "cheat"}).status_code == 422


def test_typed_answers_ignore_case_punctuation_and_accents(client: APIClient) -> None:
    attempt = start(client)
    for index in range(4):
        submit_answer(client, attempt, index, FIRST_LESSON_ANSWERS[index])
    assert submit_answer(client, attempt, 4, "  Mucho   GUSTO! ").json()["correct"] is True


def test_attempt_state_machine_blocks_invalid_transitions(client: APIClient) -> None:
    attempt = start(client)
    base = f"/api/v1/attempts/{attempt['attempt_id']}"
    assert client.post(f"{base}/complete").status_code == 409  # nothing answered yet
    assert client.post(f"{base}/abandon").json()["status"] == "abandoned"
    assert client.post(f"{base}/abandon").json()["status"] == "abandoned"
    assert submit_answer(client, attempt, 0, "My name is Ana").status_code == 409
    assert client.post(f"{base}/complete").status_code == 409
    done = finish_perfect_lesson(client)
    assert client.post(f"/api/v1/attempts/{done['attempt_id']}/abandon").json()["status"] == "completed"


def test_perfect_lesson_reports_goal_and_perfect_flag(client: APIClient) -> None:
    result = finish_perfect_lesson(client)
    assert result["perfect"] is True and result["accuracy"] == 100
    assert result["xp_awarded"] == 20
    assert result["daily_goal_reached"] is True and result["today_xp"] == 35
    assert result["new_achievements"] == []  # Flawless was already earned by the seeded first lesson
    assert result["hearts"] == 4


def test_failed_attempt_gives_no_rewards_and_cannot_resume(client: APIClient) -> None:
    attempt = start(client)
    for index in range(4):
        last = submit_answer(client, attempt, index, "wrong").json()
    assert last["failed"] is True
    assert submit_answer(client, attempt, 4, "mucho gusto").status_code == 409
    state = client.get(f"/api/v1/attempts/{attempt['attempt_id']}").json()
    assert state["status"] == "failed"
    assert client.get("/api/v1/me").json()["total_xp"] == 185


def test_league_is_weekly_and_resets_with_the_calendar(client: APIClient, clock: Clock) -> None:
    board = client.get("/api/v1/leaderboards/weekly").json()
    assert [entry["name"] for entry in board["entries"]][:2] == ["Maya", "Leo"]
    assert {entry["zone"] for entry in board["entries"]} == {"promotion", "safe", "demotion"}
    assert board["entries"][0]["zone"] == "promotion" and board["entries"][-1]["zone"] == "demotion"
    clock.value = clock.value + timedelta(days=8)
    next_week = client.get("/api/v1/leaderboards/weekly").json()
    learner = next(entry for entry in next_week["entries"] if entry["is_current"])
    assert learner["xp"] == 0  # the learner's starting XP belongs to the first week only
    assert {entry["name"]: entry["xp"] for entry in next_week["entries"] if not entry["is_current"]}["Maya"] == 260  # rivals earn again
    assert next_week["entries"][-1]["is_current"]
    assert next_week["ends_in"].endswith("h")


def test_week_start_is_monday_midnight() -> None:
    from app.services.clock import week_start

    assert week_start(datetime(2026, 10, 9, 15, 30)) == datetime(2026, 10, 5)
    assert week_start(datetime(2026, 10, 5, 0, 0)) == datetime(2026, 10, 5)
    assert week_start(datetime(2026, 10, 11, 23, 59)) == datetime(2026, 10, 5)


def test_streak_lapses_after_simulated_days_and_restarts(client: APIClient) -> None:
    assert client.get("/api/v1/me").json()["current_streak"] == 7
    assert client.post("/api/v1/dev/simulate-day").status_code == 200
    me = client.get("/api/v1/me").json()
    assert me["current_streak"] == 0 and me["today_xp"] == 0
    assert finish_perfect_lesson(client)["streak"] == 1
    assert client.get("/api/v1/me").json()["longest_streak"] == 12


def test_dev_reset_restores_seeded_learner(client: APIClient) -> None:
    finish_perfect_lesson(client)
    client.post("/api/v1/hearts/gem-refill")
    assert client.post("/api/v1/dev/reset").status_code == 200
    me = client.get("/api/v1/me").json()
    assert (me["total_xp"], me["hearts"], me["gems"], me["current_streak"], me["today_xp"]) == (185, 4, 480, 7, 15)
    path = client.get("/api/v1/courses/1/path").json()
    assert [skill["status"] for skill in path["units"][0]["skills"]] == ["completed", "available", "locked"]
    assert sum(1 for item in client.get("/api/v1/achievements").json() if item["earned"]) == 4
    assert client.post("/api/v1/dev/reset").status_code == 200  # repeatable


def test_dev_endpoints_can_be_disabled(client: APIClient, monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_DEV_ENDPOINTS", "0")
    assert client.post("/api/v1/dev/reset").status_code == 404
    assert client.post("/api/v1/dev/simulate-day").status_code == 404


def test_quests_activity_and_profile_reflect_progress(client: APIClient) -> None:
    quests = {quest["id"]: quest for quest in client.get("/api/v1/quests").json()["quests"]}
    assert quests["daily-xp"]["progress"] == 15 and not quests["daily-xp"]["completed"]
    assert not quests["daily-lesson"]["completed"]
    finish_perfect_lesson(client)
    quests = {quest["id"]: quest for quest in client.get("/api/v1/quests").json()["quests"]}
    assert all(quest["completed"] for quest in quests.values())
    days = client.get("/api/v1/me/activity?days=7").json()
    assert len(days["days"]) == 7 and days["days"][-1]["xp"] == 35 and days["days"][-1]["goal_met"]
    assert client.get("/api/v1/me/activity?days=0").status_code == 422
    profile = client.get("/api/v1/me/profile").json()
    assert profile["completed_skills"] == 2 and profile["lessons_completed"] == 2


def test_bootstrap_exposes_practice_lesson_and_hides_answers(client: APIClient) -> None:
    payload = client.get("/api/v1/bootstrap").json()
    assert payload["practice_lesson_id"] == payload["units"][0]["skills"][0]["lesson_id"]
    attempt = start(client)
    leaked = {"answer", "accepted", "pairs", "value", "correct"}  # word-bank "tokens" are the shuffled bank, not the answer
    for exercise in attempt["exercises"]:
        assert not leaked & set(exercise)
        assert not leaked & set(exercise["payload"])
    assert client.get("/api/v1/courses/2/path").status_code == 404


def test_match_pair_order_is_stable_across_refresh(client: APIClient) -> None:
    attempt = start(client)
    again = client.get(f"/api/v1/attempts/{attempt['attempt_id']}").json()
    assert attempt["exercises"][2]["payload"] == again["exercises"][2]["payload"]


def test_ensure_schema_adds_missing_columns_to_an_old_database(tmp_path) -> None:
    from app.database import ensure_schema

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE lesson_attempts (id INTEGER PRIMARY KEY, user_id INTEGER, lesson_id INTEGER, mode VARCHAR(20), status VARCHAR(20), current_index INTEGER, correct_count INTEGER, hearts_lost INTEGER, xp_awarded INTEGER, started_at DATETIME, completed_at DATETIME)")
    ensure_schema(engine)
    ensure_schema(engine)
    with engine.connect() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(lesson_attempts)")}
        tables = {row[0] for row in connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "expires_at" in columns and "heart_events" in tables
    engine.dispose()


def test_option_and_token_order_does_not_reveal_the_answer(client: APIClient) -> None:
    attempt = start(client)
    again = client.get(f"/api/v1/attempts/{attempt['attempt_id']}").json()
    assert attempt["exercises"] == again["exercises"]  # stable on refresh
    positions = set()
    for _ in range(8):  # different attempts reorder differently
        fresh = start(client)
        client.post(f"/api/v1/attempts/{fresh['attempt_id']}/abandon")
        options = fresh["exercises"][0]["payload"]["options"]
        assert sorted(options) == sorted(["My name is Ana", "I know Ana", "Ana is here", "Goodbye Ana"])
        positions.add(options.index("My name is Ana"))
    assert len(positions) > 1
