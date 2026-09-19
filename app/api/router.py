from fastapi import APIRouter

from app.api.endpoints import auth, food_items

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(food_items.router)
