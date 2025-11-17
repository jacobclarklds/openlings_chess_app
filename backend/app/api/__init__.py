from fastapi import APIRouter
from .auth import router as auth_router
from .games import router as games_router
from .routes.lessons import router as lessons_router
from .routes.demo import router as demo_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(games_router)
api_router.include_router(lessons_router, prefix="/lessons", tags=["lessons"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])

__all__ = ["api_router"]
