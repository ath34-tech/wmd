# Changelog

All notable backend changes, newest first. API details live in [API_DOCS.md](API_DOCS.md).

## [Unreleased]

### Added — Database Setup & Seed Data (#3)
- SQLite database via SQLAlchemy 2.0, with a `get_db` FastAPI dependency that tests override with an in-memory DB.
- `food_items` table (FoodItem: name, calories per unit, unit description), seeded on startup with Banana, Apple, Orange, Egg, Bread, Chicken Breast, White Rice and Pizza. Seeding is idempotent.
- `GET /api/food-items` lists the seeded FoodItems.
- `DATABASE_URL` setting (default `sqlite:///./wmd.db`); the Lambda template points it at `/tmp/wmd.db`.

### Added — Foundation & Mock Authentication (#2)
- `POST /api/auth/mock-login` returns a static dummy bearer token (MockAuth).
- `/api` router, pytest suite using `TestClient`, and `requirements-dev.txt` for test dependencies.
- Changed: `pydantic` 2.7.1 → 2.9.2 (2.7.1 has no Python 3.13 wheels).
