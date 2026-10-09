"""Exercise presentation and answer checking."""
import random
import re
import unicodedata
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Exercise

_PUNCTUATION = re.compile(r"[¿¡!?.,;:\"“”]")


def lesson_exercises(db: Session, lesson_id: int) -> list[Exercise]:
    return list(db.scalars(select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.position)).all())


def public_exercise(exercise: Exercise, attempt_id: int) -> dict[str, Any]:
    """Exercise as shown to the learner: no canonical answer, and no answer hidden in the option order."""
    rng = random.Random(attempt_id * 100_003 + exercise.id)  # stable across refreshes of one attempt
    payload = dict(exercise.payload)
    if exercise.type == "match_pairs":
        pairs = payload["pairs"]
        right = [pair[1] for pair in pairs]
        rng.shuffle(right)
        payload = {"left": [pair[0] for pair in pairs], "right": right}
    else:
        for key in ("options", "tokens"):
            if key in payload:
                payload[key] = rng.sample(payload[key], len(payload[key]))
    return {"id": exercise.id, "type": exercise.type, "prompt": exercise.prompt, "hint": exercise.hint, "payload": payload}


def normalize_text(value: Any, fold_accents: bool = False) -> str:
    text = unicodedata.normalize("NFC", str(value)).casefold()
    text = _PUNCTUATION.sub("", text)
    if fold_accents:
        text = "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))
    return " ".join(text.split())


def _pair_key(pair: Any) -> tuple[str, ...]:
    return tuple(sorted(normalize_text(word) for word in pair))


def check_answer(exercise: Exercise, submitted: Any) -> bool:
    answer = exercise.answer
    if exercise.type == "word_bank":
        if not isinstance(submitted, list) or not all(isinstance(token, str) for token in submitted):
            return False
        return [normalize_text(item) for item in submitted] == [normalize_text(item) for item in answer["tokens"]]
    if exercise.type == "match_pairs":
        if not isinstance(submitted, list):
            return False
        if any(not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(word, str) for word in pair) for pair in submitted):
            return False
        return Counter(_pair_key(pair) for pair in submitted) == Counter(_pair_key(pair) for pair in answer["pairs"])
    if not isinstance(submitted, str):
        return False
    if exercise.type == "type_answer":
        return normalize_text(submitted, True) in {normalize_text(item, True) for item in answer["accepted"]}
    return normalize_text(submitted) == normalize_text(answer["value"])


def display_answer(exercise: Exercise) -> Any:
    answer = exercise.answer
    if exercise.type == "word_bank":
        return answer["tokens"]
    if exercise.type == "match_pairs":
        return answer["pairs"]
    if exercise.type == "type_answer":
        return answer["accepted"][0]
    return answer["value"]
