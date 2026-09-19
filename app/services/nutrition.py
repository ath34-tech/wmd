from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel

from app.db.models import FoodItem
from app.services.food_recognition import IdentifiedFood


class MealFood(BaseModel):
    """A food in a Meal, with its calories, or None when it is not a known FoodItem."""

    food_item: str
    quantity: float
    calories: int | None


def _normalised_name(name: str) -> str:
    return name.strip().casefold()


def _round_half_up(value: float) -> int:
    """Round 0.5 up, unlike Python's round(), which rounds to even."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _merge_quantities(foods: list[IdentifiedFood]) -> list[IdentifiedFood]:
    """Total the quantity per food, so one food appears once in the Meal.

    Names that differ only in case or surrounding spaces are the same food;
    the first spelling seen is the one reported.
    """
    merged: dict[str, IdentifiedFood] = {}
    for food in foods:
        name = food.food_item.strip()
        seen = merged.get(_normalised_name(name))
        merged[_normalised_name(name)] = IdentifiedFood(
            food_item=seen.food_item if seen else name,
            quantity=(seen.quantity if seen else 0) + food.quantity,
        )
    return list(merged.values())


def calculate_calories(
    foods: list[IdentifiedFood], known_foods: list[FoodItem]
) -> list[MealFood]:
    """Scale each identified food's baseline calories by its quantity.

    Foods with no FoodItem baseline keep `calories` None so the caller can show
    them without counting them; foods with nothing on the plate are dropped.
    """
    baselines = {_normalised_name(food.name): food for food in known_foods}
    meal: list[MealFood] = []
    for food in _merge_quantities(foods):
        if food.quantity <= 0:  # nothing on the plate, and never a negative total
            continue
        match = baselines.get(_normalised_name(food.food_item))
        meal.append(
            MealFood(
                food_item=match.name if match else food.food_item.strip(),
                quantity=food.quantity,
                calories=(
                    _round_half_up(match.calories_per_unit * food.quantity)
                    if match
                    else None
                ),
            )
        )
    return meal


def sum_calories(meal: list[MealFood]) -> int:
    """Total calories of the Meal, ignoring foods with no baseline."""
    return sum(food.calories for food in meal if food.calories is not None)
