from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from app.services.image_storage import save_upload

router = APIRouter(prefix="/meals", tags=["meals"])


class MealItem(BaseModel):
    food_item: str
    quantity: float


class MealAnalysis(BaseModel):
    items: list[MealItem]


@router.post("/analyze", response_model=MealAnalysis)
async def analyze_meal(image: UploadFile):
    await save_upload(image)
    # Mocked identification until the Gemini integration (#5) lands.
    return MealAnalysis(items=[MealItem(food_item="Banana", quantity=1)])
