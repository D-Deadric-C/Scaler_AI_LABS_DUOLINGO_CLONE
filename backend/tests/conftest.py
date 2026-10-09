import asyncio
from datetime import datetime

import httpx
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import utc_now
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

    def patch(self, path: str, **kwargs) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)


@pytest.fixture()
def client(tmp_path):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    test_sessions = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=test_engine)
    with test_sessions() as db:
        seed_database(db)

    def test_db():
        with test_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    api = APIClient()
    api.sessions = test_sessions  # lets tests inspect or arrange database rows directly
    try:
        yield api
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


class Clock:
    """Controllable replacement for services.clock.current_time."""

    def __init__(self, value: datetime) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


@pytest.fixture()
def clock(monkeypatch) -> Clock:
    import app.services.clock as clock_module

    fake = Clock(utc_now())
    monkeypatch.setattr(clock_module, "current_time", fake)
    return fake


@pytest.fixture()
def seeded_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'schema.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)() as db:
        seed_database(db)
        yield db
    engine.dispose()
