from app.core.config import settings

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_analyze_returns_mock_meal_for_uploaded_image(client):
    response = client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"items": [{"food_item": "Banana", "quantity": 1}]}


def test_analyze_saves_uploaded_image_to_upload_dir(client, upload_dir):
    client.post(
        "/api/meals/analyze",
        files={"image": ("lunch.png", PNG_BYTES, "image/png")},
    )

    saved = list(upload_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].suffix == ".png"
    assert saved[0].read_bytes() == PNG_BYTES


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
