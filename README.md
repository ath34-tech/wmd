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

1. **Initial Project Setup**: 
   - Created the AWS SAM `template.yaml`.
   - Set up the basic FastAPI application structure in `app/`.
   - Created `docker-compose.yml` for LocalStack and Postgres.

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
3. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload
   ```

To run the local infrastructure (PostgreSQL, OpenSearch, etc.):
```bash
docker-compose up -d
```
