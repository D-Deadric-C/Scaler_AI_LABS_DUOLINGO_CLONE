import asyncio
import httpx
import pytest

from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_database


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
def client():
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield APIClient()
    engine.dispose()


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
