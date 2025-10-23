from fastapi import APIRouter
from .auth import router as auth_router
from .games import router as games_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(games_router)

__all__ = ["api_router"]
