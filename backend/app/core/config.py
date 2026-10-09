"""Environment-driven settings, read lazily so tests and deployments can change them."""
import os
from pathlib import Path

DEFAULT_USER_ID = 1  # the seeded demo learner; replaced by a real session user if auth is added
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "duolingo.db"


def database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE_PATH}")


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def dev_endpoints_enabled() -> bool:
    return os.getenv("ENABLE_DEV_ENDPOINTS", "1").lower() not in {"0", "false", "no", "off"}
