import httpx
from google.genai import errors

from app.core.config import settings
from app.main import app
from app.services.food_recognition import get_gemini_client

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def analyze(client, content=PNG_BYTES, filename="lunch.png", content_type="image/png"):
    """Upload an image to the analyze endpoint."""
    return client.post(
        "/api/meals/analyze",
        files={"image": (filename, content, content_type)},
    )


def test_analyze_returns_food_items_identified_by_gemini(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "Apple", "quantity": 2},
            {"food_item": "Egg", "quantity": 1.5},
        ]
    }

    response = analyze(client)

    assert response.status_code == 200
    assert [item["food_item"] for item in response.json()["items"]] == ["Apple", "Egg"]
    assert [item["quantity"] for item in response.json()["items"]] == [2, 1.5]


def test_analyze_sends_uploaded_image_to_gemini(client, gemini):
    analyze(client)

    [call] = gemini.calls
    [image_part] = call["contents"]
    assert image_part.inline_data.data == PNG_BYTES
    assert image_part.inline_data.mime_type == "image/png"
    assert call["config"].response_mime_type == "application/json"


def test_analyze_does_not_keep_uploaded_image(client, upload_dir):
    response = analyze(client)

    assert response.status_code == 200
    assert not any(upload_dir.iterdir())


def test_analyze_rejects_non_image_upload(client, upload_dir):
    response = analyze(
        client, content=b"not an image", filename="notes.txt", content_type="text/plain"
    )

    assert response.status_code == 415
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_analyze_rejects_image_over_size_limit(client, upload_dir, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 1024)

    response = analyze(client, content=PNG_BYTES + b"\x00" * 1024, filename="huge.png")

    assert response.status_code == 413
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_analyze_returns_502_when_gemini_reply_is_not_valid_json(
    client, gemini, upload_dir
):
    gemini.raw_reply = "Sorry, I can't help with that."

    response = analyze(client)

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())


def test_analyze_returns_502_when_gemini_call_fails(client, gemini, upload_dir):
    gemini.error = errors.ServerError(
        503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}
    )

    response = analyze(client)

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())


def test_analyze_returns_502_when_gemini_is_unreachable(client, gemini, upload_dir):
    gemini.error = httpx.ConnectTimeout("timed out")

    response = analyze(client)

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())


def test_analyze_returns_503_when_gemini_api_key_is_missing(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    app.dependency_overrides.pop(get_gemini_client)

    response = analyze(client)

    assert response.status_code == 503


def test_analyze_prices_known_foods_and_totals_the_meal(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "Banana", "quantity": 1},
            {"food_item": "Apple", "quantity": 2},
        ]
    }

    response = analyze(client)

    assert response.status_code == 200
    # Seeded baselines: Banana 105/medium banana, Apple 95/medium apple.
    assert response.json() == {
        "items": [
            {"food_item": "Banana", "quantity": 1, "calories": 105},
            {"food_item": "Apple", "quantity": 2, "calories": 190},
        ],
        "total_calories": 295,
    }


def test_analyze_lists_unknown_foods_without_calories(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "Banana", "quantity": 1},
            {"food_item": "Pasta", "quantity": 1},
        ]
    }

    response = analyze(client)

    assert response.json() == {
        "items": [
            {"food_item": "Banana", "quantity": 1, "calories": 105},
            {"food_item": "Pasta", "quantity": 1, "calories": None},
        ],
        "total_calories": 105,
    }


def test_analyze_merges_repeated_foods_and_ignores_name_case(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "egg", "quantity": 1},
            {"food_item": " EGG ", "quantity": 2},
        ]
    }

    response = analyze(client)

    # Seeded baseline: Egg 78/large boiled egg, so 3 eggs is 234.
    assert response.json() == {
        "items": [{"food_item": "Egg", "quantity": 3, "calories": 234}],
        "total_calories": 234,
    }


def test_analyze_drops_foods_with_no_quantity(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "Banana", "quantity": 1},
            {"food_item": "Apple", "quantity": 0},
            {"food_item": "Pizza", "quantity": -2},
        ]
    }

    response = analyze(client)

    assert response.json() == {
        "items": [{"food_item": "Banana", "quantity": 1, "calories": 105}],
        "total_calories": 105,
    }


def test_analyze_rounds_half_portions_up(client, gemini):
    gemini.reply = {"items": [{"food_item": "Banana", "quantity": 0.5}]}

    response = analyze(client)

    # Half a 105 kcal banana is 52.5, reported as 53 rather than 52.
    assert response.json() == {
        "items": [{"food_item": "Banana", "quantity": 0.5, "calories": 53}],
        "total_calories": 53,
    }


def test_analyze_returns_empty_meal_when_no_food_is_recognised(client, gemini):
    gemini.reply = {"items": []}

    response = analyze(client)

    assert response.json() == {"items": [], "total_calories": 0}
