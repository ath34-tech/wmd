# Changelog

All notable backend changes, newest first. API details live in [API_DOCS.md](API_DOCS.md).

## [Unreleased]

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
