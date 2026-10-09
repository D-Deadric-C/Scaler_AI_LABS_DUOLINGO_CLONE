"""Shared helpers for driving lessons through the HTTP API in tests."""
import httpx
from sqlalchemy import select

from app.models import Exercise
from conftest import APIClient

SET_A = ["hello", ["Quiero", "café"], [["hola", "hello"], ["café", "coffee"], ["gracias", "thanks"]], "quiero", "gracias"]
SET_B = ["My name is Ana", ["Vivo", "en", "Delhi"], [["nombre", "name"], ["vivo", "I live"], ["mucho gusto", "nice to meet you"]], "llamo", "mucho gusto"]
FIRST_LESSON_ANSWERS = SET_B  # the first open skill (skill 2) uses set B


def all_skills(client: APIClient) -> list[dict]:
    path = client.get("/api/v1/courses/1/path").json()
    return [skill for unit in path["units"] for skill in unit["skills"]]


def start(client: APIClient, skill_index: int = 1, mode: str = "lesson") -> dict:
    lesson_id = all_skills(client)[skill_index]["lesson_id"]
    return client.post(f"/api/v1/lessons/{lesson_id}/attempts", json={"mode": mode}).json()


def submit_answer(client: APIClient, attempt: dict, index: int, value) -> httpx.Response:
    return client.post(f"/api/v1/attempts/{attempt['attempt_id']}/answers", json={"exercise_id": attempt["exercises"][index]["id"], "answer": value})


def finish_perfect_lesson(client: APIClient, skill_index: int = 1, mode: str = "lesson") -> dict:
    attempt = start(client, skill_index, mode)
    with client.sessions() as db:
        rows = db.scalars(select(Exercise).where(Exercise.id.in_([item["id"] for item in attempt["exercises"]]))).all()
        answers = {row.id: row.answer.get("value") or row.answer.get("tokens") or row.answer.get("pairs") or row.answer["accepted"][0] for row in rows}
    for index, exercise in enumerate(attempt["exercises"]):
        value = answers[exercise["id"]]
        assert submit_answer(client, attempt, index, value).json()["correct"] is True
    return client.post(f"/api/v1/attempts/{attempt['attempt_id']}/complete").json()
