from fastapi import APIRouter

from app.api.endpoints import auth

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
