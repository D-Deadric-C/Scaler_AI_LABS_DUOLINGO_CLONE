from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .core.config import cors_origins
from .database import SessionLocal, ensure_schema
from .seed import seed_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema()
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title="Duolingo API",
    version="1.2.0",
    description="Server-authoritative API for the Duolingo clone: path, lesson attempts, hearts, XP, streaks and leagues.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
