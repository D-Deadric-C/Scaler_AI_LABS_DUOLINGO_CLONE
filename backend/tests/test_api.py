import asyncio
from datetime import date, datetime, timedelta

import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.seed import seed_database
from app.service import regenerate_hearts, update_streak


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
    assert any(award["title"] == "First Steps" for award in first["new_achievements"])
    assert client.get("/api/v1/courses/1/path").json()["units"][0]["skills"][2]["status"] == "available"


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
