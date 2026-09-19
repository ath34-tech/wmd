# Personal Fitness Coach - Backend

This repository contains the backend for the Personal Fitness Coach, a privacy-conscious, local-first fitness companion that turns a user's profile, goals, food, workouts, steps, and habits into a continuously updated daily plan.

## Tech Stack

This backend follows the "BUILD IT" local-first hackathon track:
- **API Framework**: Python + FastAPI
- **Cloud Infrastructure**: AWS SAM CLI + LocalStack (Serverless)
- **Database**: PostgreSQL (Nutrition DB)
- **Search**: OpenSearch
- **Authorization**: Cedar (Policies)
- **AI/ML Orchestration**: Strands Agents SDK

## Current Development Progress

The MVP backend (spec: issue #1) uses SQLite and Google Gemini for meal photo recognition.

- [CHANGELOG.md](CHANGELOG.md): what has been built, per ticket.
- [OPEN_ITEMS.md](OPEN_ITEMS.md): known gaps, pending decisions and things needing review.
- [API_DOCS.md](API_DOCS.md): every endpoint, with cURL examples.

## Local Development Setup

To run the API locally during development:

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows: .\venv\Scripts\activate
   # Mac/Linux: source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure: copy `.env.example` to `.env` and set `GEMINI_API_KEY` (needed by `POST /api/meals/analyze`; tests don't need it).
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Run the tests:
   ```bash
   pip install -r requirements-dev.txt
   pytest
   ```

To run the local infrastructure (PostgreSQL, OpenSearch, etc.):
```bash
docker-compose up -d
```
