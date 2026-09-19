from dataclasses import dataclass

from app.db.models import FoodItem
from app.services.food_recognition import IdentifiedFood


@dataclass
class PricedFood:
    """An identified food with its calories, or None when it isn't a known FoodItem."""

    food_item: str
    quantity: float
    calories: int | None


def _key(name: str) -> str:
    return name.strip().casefold()


def _merge_quantities(foods: list[IdentifiedFood]) -> list[tuple[str, float]]:
    """Total the quantity per food, so one food appears once in the Meal.

    Names that differ only in case or spacing are the same food; the first
    spelling seen is the one reported.
    """
    merged: dict[str, tuple[str, float]] = {}
    for food in foods:
        name = food.food_item.strip()
        reported, quantity = merged.get(_key(name), (name, 0.0))
        merged[_key(name)] = (reported, quantity + food.quantity)
    return list(merged.values())


def price_foods(
    foods: list[IdentifiedFood], known_foods: list[FoodItem]
) -> list[PricedFood]:
    """Look up each identified food's baseline calories and scale by quantity.

    Foods that aren't in the database are kept with `calories` None so the
    caller can show them without counting them.
    """
    baselines = {_key(food.name): food for food in known_foods}
    priced: list[PricedFood] = []
    for name, quantity in _merge_quantities(foods):
        if quantity <= 0:  # nothing on the plate, and never a negative total
            continue
        match = baselines.get(_key(name))
        priced.append(
            PricedFood(
                food_item=match.name if match else name,
                quantity=quantity,
                calories=round(match.calories_per_unit * quantity) if match else None,
            )
        )
    return priced


def total_calories(priced: list[PricedFood]) -> int:
    """Total calories of the Meal, ignoring foods with no baseline."""
    return sum(food.calories for food in priced if food.calories is not None)
