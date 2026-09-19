import logging
from functools import lru_cache

import httpx
from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.db.models import FoodItem

logger = logging.getLogger(__name__)


class IdentifiedFood(BaseModel):
    food_item: str = Field(description="Name of the food, from the known list when it matches.")
    quantity: float = Field(description="How many units of the food, in the listed unit.")


class FoodIdentification(BaseModel):
    items: list[IdentifiedFood]


SYSTEM_PROMPT_TEMPLATE = """\
You identify the foods in a photo of a meal for a calorie tracker.
Return every distinct food you can see with its quantity.
Rules:
- When a food matches one in the known list, use that exact name and give the
  quantity in that food's unit (fractions allowed, e.g. 0.5).
- Otherwise use a short, singular, generic name (e.g. "Pasta") and a best-guess
  quantity in typical servings.
- If the photo contains no food, return an empty items list.
- Respond only with JSON matching the schema.

Known foods (name: unit):
{known_foods}
"""


@lru_cache
def _client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def get_gemini_client() -> genai.Client:
    """FastAPI dependency for the Gemini client; override it in tests."""
    if not settings.gemini_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Gemini API key is not configured"
        )
    return _client(settings.gemini_api_key)


async def identify_foods(
    client: genai.Client,
    image: bytes,
    mime_type: str,
    known_foods: list[FoodItem],
) -> list[IdentifiedFood]:
    """Ask Gemini which foods, and how many of each, are in the image."""
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        known_foods="\n".join(f"- {food.name}: {food.unit}" for food in known_foods)
    )
    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[types.Part.from_bytes(data=image, mime_type=mime_type)],
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                response_mime_type="application/json",
                response_schema=FoodIdentification,
            ),
        )
    except (errors.APIError, httpx.HTTPError) as exc:
        logger.warning("Gemini call failed: %s", exc)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Food recognition is unavailable right now"
        ) from exc
    try:
        return FoodIdentification.model_validate_json(response.text or "").items
    except ValidationError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Gemini returned an unreadable food list"
        ) from exc
