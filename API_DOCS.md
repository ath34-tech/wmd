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
