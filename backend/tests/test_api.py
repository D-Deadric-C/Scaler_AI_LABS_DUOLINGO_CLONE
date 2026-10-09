import asyncio
from datetime import date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import create_engine, delete, event, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import ExerciseAttempt, LessonAttempt, User, UserAchievement
from app.seed import seed_database
from app.service import effective_streak, regenerate_hearts, update_streak


class APIClient:
    def request(self, method: str, path: str, **kwargs) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str) -> httpx.Response:
        return self.request("GET", path)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self.request("POST", path, **kwargs)


@pytest.fixture()
def client(tmp_path):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    test_sessions = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)
    with test_sessions() as db:
        seed_database(db)

    async def test_db():
        with test_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        yield APIClient()
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


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
        assert db.scalar(select(func.count()).select_from(UserAchievement)) == 3
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

    completion = client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
    after = client.get("/api/v1/courses/1/path").json()
    profile = client.get("/api/v1/me/profile").json()
    weekly_after = next(entry["xp"] for entry in client.get("/api/v1/leaderboards/weekly").json()["entries"] if entry["is_current"])
    assert completion["xp_awarded"] == 18
    assert completion["accuracy"] == 80
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
    assert resumed["current_index"] == len(resumed["exercises"])
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
