# Changelog

All notable backend changes, newest first. API details live in [API_DOCS.md](API_DOCS.md).

## [Unreleased]

### Added — LLM Integration (Gemini) (#5)
- `POST /api/meals/analyze` now sends the image to Gemini (`gemini-3.1-flash-lite`, `google-genai` SDK) with a strict system prompt and a JSON response schema, and returns the identified FoodItems and quantities instead of the mock.
- The prompt lists the known FoodItems and their units from the DB, so Gemini reuses those names and counts in those units.
- Errors: Gemini API failure or unreadable output → `502`; no API key configured → `503`.
- Gemini client is a FastAPI dependency (`get_gemini_client`); tests replace it with a fake.
- Config: `GEMINI_API_KEY`, `GEMINI_MODEL`; settings now also read a local `.env` (see `.env.example`). Lambda template takes the key as a `NoEcho` parameter.
- Added [OPEN_ITEMS.md](OPEN_ITEMS.md) to track pending work, review points and unaddressed problems.

### Changed (#5)
- Uploaded images are deleted after analysis (previously kept forever).
- `pydantic` 2.9.2 → 2.13.5 and `httpx` 0.27.2 → 0.28.1 (required by `google-genai`); `httpx` moved from dev to runtime requirements.

### Added — Image Upload & Interface Contract (#4)
- `POST /api/meals/analyze` accepts a `multipart/form-data` `image` and returns the Meal contract `{"items": [{"food_item", "quantity"}]}`, currently a fixed mock (one Banana).
- Uploads are streamed to `UPLOAD_DIR` (default `./uploads`, `/tmp/uploads` on Lambda) under random names; non-image types get `415`, files over `MAX_UPLOAD_BYTES` (default 5 MB) get `413` and are not kept.
- Lambda template declares binary media types so image uploads survive API Gateway.
- Pinned `python-multipart`.

### Added — Database Setup & Seed Data (#3)
- SQLite database via SQLAlchemy 2.0, with a `get_db` FastAPI dependency that tests override with an in-memory DB.
- `food_items` table (FoodItem: name, calories per unit, unit description), seeded on startup with Banana, Apple, Orange, Egg, Bread, Chicken Breast, White Rice and Pizza. Seeding is idempotent.
- `GET /api/food-items` lists the seeded FoodItems.
- `DATABASE_URL` setting (default `sqlite:///./wmd.db`); the Lambda template points it at `/tmp/wmd.db`.

### Added — Foundation & Mock Authentication (#2)
- `POST /api/auth/mock-login` returns a static dummy bearer token (MockAuth).
- `/api` router, pytest suite using `TestClient`, and `requirements-dev.txt` for test dependencies.
- Changed: `pydantic` 2.7.1 → 2.9.2 (2.7.1 has no Python 3.13 wheels).
