from fastapi import APIRouter, Depends, UploadFile
from google import genai
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FoodItem
from app.services.food_recognition import get_gemini_client, identify_foods
from app.services.image_storage import save_upload

router = APIRouter(prefix="/meals", tags=["meals"])


class MealItem(BaseModel):
    food_item: str
    quantity: float


class MealAnalysis(BaseModel):
    items: list[MealItem]


@router.post("/analyze", response_model=MealAnalysis)
async def analyze_meal(
    image: UploadFile,
    db: Session = Depends(get_db),
    gemini: genai.Client = Depends(get_gemini_client),
):
    path = await save_upload(image)
    try:
        known_foods = list(db.scalars(select(FoodItem)))
        foods = await identify_foods(
            gemini, path.read_bytes(), image.content_type, known_foods
        )
    finally:
        path.unlink()  # the upload dir is scratch space, not an archive
    return MealAnalysis(
        items=[MealItem(food_item=f.food_item, quantity=f.quantity) for f in foods]
    )
