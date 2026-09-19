from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import FoodItem

router = APIRouter(prefix="/food-items", tags=["food-items"])


class FoodItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    calories_per_unit: int
    unit: str


@router.get("", response_model=list[FoodItemResponse])
def list_food_items(db: Session = Depends(get_db)):
    return db.scalars(select(FoodItem).order_by(FoodItem.name)).all()
