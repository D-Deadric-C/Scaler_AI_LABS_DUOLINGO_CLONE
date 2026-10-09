from fastapi import APIRouter

from .routes import attempts, dev, gamification, learner, path, system

api_router = APIRouter(prefix="/api/v1")
for module in (system, path, learner, attempts, gamification, dev):
    api_router.include_router(module.router)
