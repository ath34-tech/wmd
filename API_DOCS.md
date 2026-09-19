# Personal Fitness Coach - API Documentation

The backend is built with **FastAPI**. FastAPI automatically generates interactive API documentation.

## Interactive API Docs

Once you have the backend running locally (e.g. `uvicorn app.main:app --reload`), you can view the live interactive documentation and test endpoints directly from your browser:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON)**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Currently Implemented Endpoints

### 1. Root
- **Path**: `GET /`
- **Description**: Verifies the API is reachable.
- **Response**:
  ```json
  {
    "message": "Welcome to the Personal Fitness Coach API"
  }
  ```

### 2. Health Check
- **Path**: `GET /health`
- **Description**: Checks the health status of the API.
- **Response**:
  ```json
  {
    "status": "healthy"
  }
  ```

### 3. Mock Login
- **Path**: `POST /api/auth/mock-login`
- **Description**: MockAuth for the MVP. Returns a static dummy token so the frontend can connect without a registration/login flow. No request body is required.
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/auth/mock-login
  ```
- **Response**:
  ```json
  {
    "access_token": "mock-token-wmd-mvp",
    "token_type": "bearer"
  }
  ```

### 4. List Food Items
- **Path**: `GET /api/food-items`
- **Description**: Lists every known FoodItem with its baseline calories for one unit (serving), sorted by name. These are the foods whose calories the meal analyzer can calculate. The database is seeded on startup.
- **Example**:
  ```bash
  curl http://localhost:8000/api/food-items
  ```
- **Response**:
  ```json
  [
    { "id": 2, "name": "Apple", "calories_per_unit": 95, "unit": "medium apple" },
    { "id": 1, "name": "Banana", "calories_per_unit": 105, "unit": "medium banana" }
  ]
  ```
  (truncated; the seed set also includes Bread, Chicken Breast, Egg, Orange, Pizza, White Rice)

### 5. Analyze Meal
- **Path**: `POST /api/meals/analyze`
- **Description**: Upload a photo of a Meal; returns the FoodItems identified in it with their quantities. **Currently returns a fixed mock result** (one Banana) while the Gemini integration is built; the response shape is the contract and will gain calorie fields later.
- **Request**: `multipart/form-data` with one file field named `image`.
  - Allowed types: `image/jpeg`, `image/png`, `image/webp`, `image/heic`, `image/heif`.
  - Max size: 5 MB (configurable via the `MAX_UPLOAD_BYTES` env var).
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/meals/analyze \
    -F "image=@lunch.jpg;type=image/jpeg"
  ```
- **Response** (`200 OK`):
  ```json
  {
    "items": [
      { "food_item": "Banana", "quantity": 1.0 }
    ]
  }
  ```
- **Errors**:
  - `413` — image larger than the size limit.
  - `415` — file is not one of the allowed image types.
  - `422` — no `image` field in the form.

---

## Planned Endpoints (Architecture based on PRD)

The following endpoints will be developed as per the Product Requirements Document. This serves as a preview for the frontend team.

### Profiles & Goals
- `POST /api/profile` - Create or update user onboarding profile (measurements, activity level, etc.)
- `GET /api/profile/targets` - Retrieve deterministically calculated daily targets (calories, macros, steps).

### Logging
- `POST /api/logs/food` - Submit a food log. Will support barcode, text, or image payload.
- `POST /api/logs/workout` - Submit a workout log (sets, reps, load).

### Dashboard & Progress
- `GET /api/dashboard/daily` - Retrieve aggregated stats for the current day (calories consumed/remaining, workout status).

### AI Coach
- `POST /api/coach/ask` - Submit a natural language query to the local LLM and receive grounded advice based on current state.
