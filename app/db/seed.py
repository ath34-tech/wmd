from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FoodItem

# Baseline calories per typical serving (approximate USDA values).
SEED_FOOD_ITEMS = [
    {"name": "Banana", "calories_per_unit": 105, "unit": "medium banana"},
    {"name": "Apple", "calories_per_unit": 95, "unit": "medium apple"},
    {"name": "Orange", "calories_per_unit": 62, "unit": "medium orange"},
    {"name": "Egg", "calories_per_unit": 78, "unit": "large boiled egg"},
    {"name": "Bread", "calories_per_unit": 80, "unit": "slice"},
    {"name": "Chicken Breast", "calories_per_unit": 284, "unit": "cooked breast (172 g)"},
    {"name": "White Rice", "calories_per_unit": 205, "unit": "cup cooked"},
    {"name": "Pizza", "calories_per_unit": 285, "unit": "slice"},
]


def seed_food_items(db: Session) -> None:
    """Insert seed FoodItems that are not already present."""
    existing = set(db.scalars(select(FoodItem.name)))
    db.add_all(
        FoodItem(**item) for item in SEED_FOOD_ITEMS if item["name"] not in existing
    )
    db.commit()
