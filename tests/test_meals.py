import httpx
from google.genai import errors

from app.core.config import settings
from app.main import app
from app.services.food_recognition import get_gemini_client

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_analyze_returns_food_items_identified_by_gemini(client, gemini):
    gemini.reply = {
        "items": [
            {"food_item": "Apple", "quantity": 2},
            {"food_item": "Egg", "quantity": 1.5},
        ]
    }

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {"food_item": "Apple", "quantity": 2},
            {"food_item": "Egg", "quantity": 1.5},
        ]
    }


def test_analyze_sends_uploaded_image_to_gemini(client, gemini):
    client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    [call] = gemini.calls
    [image_part] = call["contents"]
    assert image_part.inline_data.data == PNG_BYTES
    assert image_part.inline_data.mime_type == "image/png"
    assert call["config"].response_mime_type == "application/json"


def test_analyze_does_not_keep_uploaded_image(client, upload_dir):
    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert not any(upload_dir.iterdir())


def test_analyze_rejects_non_image_upload(client, upload_dir):
    response = client.post(
        "/api/meals/analyze",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_analyze_rejects_image_over_size_limit(client, upload_dir, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 1024)
    too_big = PNG_BYTES + b"\x00" * 1024

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("huge.png", too_big, "image/png")},
    )

    assert response.status_code == 413
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_analyze_returns_502_when_gemini_reply_is_not_valid_json(client, gemini, upload_dir):
    gemini.raw_reply = "Sorry, I can't help with that."

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())


def test_analyze_returns_502_when_gemini_call_fails(client, gemini, upload_dir):
    gemini.error = errors.ServerError(
        503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}
    )

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())


def test_analyze_returns_503_when_gemini_api_key_is_missing(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", None)
    app.dependency_overrides.pop(get_gemini_client)

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 503


def test_analyze_returns_502_when_gemini_is_unreachable(client, gemini, upload_dir):
    gemini.error = httpx.ConnectTimeout("timed out")

    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 502
    assert not any(upload_dir.iterdir())
