# Personal Fitness Coach — Backend

**Snap a photo of your plate, get an auditable calorie count.**

A FastAPI backend that turns a meal photo into a list of foods, quantities and calories — using a multimodal LLM only to *see* what is on the plate, and never to do the arithmetic.

![Status](https://img.shields.io/badge/status-MVP%20complete-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen)
![Deploy](https://img.shields.io/badge/deploy-AWS%20SAM%20%7C%20Lambda-orange)

---

## The problem

Calorie tracking works. Almost nobody sticks with it.

The reason is friction: logging one meal means searching a food database, scrolling past forty near-identical entries, guessing a portion, and repeating that for every item on the plate — three times a day, forever. People quit in the first fortnight.

The obvious fix is a photo. The obvious *implementation* of that fix — send the photo to an LLM and ask "how many calories is this?" — is a trap:

1. **The numbers are invented.** A language model asked for "calories in 2 eggs" is generating plausible text, not doing arithmetic. The answer moves between calls and cannot be audited.
2. **It is slow.** Reasoning about nutrition and portions costs tokens, and tokens cost seconds.
3. **It is expensive.** A large multimodal call on every meal, three meals a day, per user.

## The design decision

> **Identification is a perception problem. Calorie counting is a database lookup and a multiplication.**
> Only one of those needs an LLM.

Gemini answers exactly one question — *"what food is on this plate, and how much of it?"* — and returns structured JSON. It never sees a calorie number and is never asked for one. Calories come from our own `food_items` table: `calories_per_unit × quantity`, computed in Python.

| | LLM does everything | **This backend** |
|---|---|---|
| Calorie numbers | Hallucinated, vary per call | **Deterministic** — same photo, same answer |
| Latency | Model reasons about nutrition + maths | **One cheap vision call**, then an indexed lookup |
| Cost per meal | Large prompt + long output | **A short JSON reply** from a Flash-Lite class model |
| Fixing a wrong figure | Re-prompt and hope | **Fix one database row** — every future meal is right |
| Trust | "Where did 640 come from?" | Every number traces to a row a dietitian can review |

The prompt is also built *at request time* from the foods already in the database, with their serving units — so the model is not asked to invent a vocabulary, it is asked to match what we already know and to count in our units. Recognition quality and data quality improve together.

---

## How it works

```
  Phone / web client
         │  multipart image
         ▼
  ┌──────────────────────┐
  │  POST /api/meals/    │   validate type + size, stream to scratch disk
  │        analyze       │
  └──────────┬───────────┘
             │ image bytes + prompt built from known foods
             ▼
      ┌─────────────┐          "what is on the plate?"  (identification only)
      │   Gemini    │  ──────► {"items":[{"food_item":"Banana","quantity":1}]}
      │ 3.1 Flash-  │
      │    Lite     │
      └──────┬──────┘
             │ structured JSON, schema-enforced
             ▼
  ┌──────────────────────┐    calories_per_unit × quantity   (no LLM involved)
  │  food_items table    │  ──────►  per-item calories + meal total
  └──────────┬───────────┘
             ▼
     { items: [...], total_calories: 261 }      image deleted
```

---

## Quick start

**Prerequisites:** Python 3.11+ (developed on 3.13). A Gemini API key is only needed for live meal analysis — the tests do not need one.

```bash
git clone https://github.com/ath34-tech/wmd.git
cd wmd
python -m venv .venv
# Windows: .\.venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then set GEMINI_API_KEY
uvicorn app.main:app --reload
```

The API is then at `http://localhost:8000`, with interactive Swagger docs at **`http://localhost:8000/docs`**. The SQLite database is created and seeded with its food items on startup — no migration step.

**Analyze a meal:**

```bash
curl -X POST http://localhost:8000/api/meals/analyze -F "image=@lunch.jpg;type=image/jpeg"
```

```json
{
  "items": [
    { "food_item": "Banana", "quantity": 1.0, "calories": 105 },
    { "food_item": "Egg",    "quantity": 2.0, "calories": 156 },
    { "food_item": "Pasta",  "quantity": 1.0, "calories": null }
  ],
  "total_calories": 261
}
```

**Run the tests** (no network, no API key, about one second):

```bash
pip install -r requirements-dev.txt && pytest
```

---

## API

Full reference with cURL examples for every endpoint: **[API_DOCS.md](API_DOCS.md)**. Live Swagger UI at `/docs`, ReDoc at `/redoc`, OpenAPI JSON at `/openapi.json`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/meals/analyze` | **The product.** Upload a photo → foods, quantities, per-item calories, meal total. |
| `GET` | `/api/food-items` | The nutrition table the app can price, so the UI can show what it knows. |
| `POST` | `/api/auth/mock-login` | MockAuth — a static bearer token, so the frontend could integrate on day one. |
| `GET` | `/health`, `/` | Liveness. |

**`POST /api/meals/analyze` contract**

- Request: `multipart/form-data`, one file field named `image`. Accepts `image/jpeg`, `png`, `webp`, `heic`, `heif`; max 5 MB (`MAX_UPLOAD_BYTES`).
- `quantity` is in the food's `unit` from `GET /api/food-items` (fractions allowed); `calories` is `calories_per_unit × quantity`, rounded half up.
- Foods not in the database are still listed, with `calories: null`, and are excluded from `total_calories` — so the total stays honest and the UI can prompt the user.
- Errors: `413` too large · `415` not an image type · `422` no `image` field · `502` Gemini failed or returned unreadable JSON (safe to retry) · `503` no API key configured.

---

## What makes it demo-safe

A photo pipeline fails in messy ways. Each failure mode was made boring and explicit, and each is pinned by a test:

- **Uploads are bounded.** Non-image types are rejected (`415`); oversized files are rejected *mid-stream* and the partial file deleted (`413`). No unbounded memory growth.
- **Photos are transient.** The image is written to scratch space, sent to Gemini, then **deleted in a `finally` block** — so it goes even when the call fails. Meal photos are among the most personal data a fitness app touches; we keep them for seconds.
- **The model is an unreliable network dependency, not an oracle.** Outage, timeout, or a reply that is not valid JSON → a clean `502` the client can retry. Missing key → `503`. Nothing 500s.
- **Nonsense input cannot corrupt the total.** Quantities of zero or less are dropped; a food recognised twice is merged rather than double-counted; names match regardless of case or stray spaces.
- **Calories round half up**, consistently — Python's default rounds half to *even*, which quietly makes half a banana 52 and half an apple 48.

---

## Tech stack

| Layer | Choice | Notes |
|---|---|---|
| API | **FastAPI** + Pydantic v2 | Typed request/response models, auto-generated OpenAPI |
| Vision | **Google Gemini** (`gemini-3.1-flash-lite`, `google-genai` SDK) | Identification only, with an enforced JSON response schema |
| Data | **SQLAlchemy 2.0** over SQLite | `DATABASE_URL` swaps it for PostgreSQL; Postgres already in `docker-compose.yml` |
| Deploy | **AWS SAM** → Lambda + API Gateway | `template.yaml`, ASGI-to-Lambda via **Mangum** |
| Local cloud | **LocalStack** via `docker-compose` | AWS-shaped local development, no AWS bill |
| Tests | **pytest** + FastAPI `TestClient` | 17 tests, fake Gemini client, in-memory DB |

---

## Project layout

```
app/
  main.py                      FastAPI app, CORS, lifespan DB init, Mangum handler
  core/config.py               Pydantic settings (.env + environment variables)
  api/
    router.py                  /api router
    endpoints/auth.py          MockAuth token
    endpoints/food_items.py    GET /api/food-items
    endpoints/meals.py         POST /api/meals/analyze — orchestrates the three services
  db/
    models.py                  FoodItem
    database.py                Engine, session, get_db dependency
    seed.py                    Baseline food items, seeded idempotently on startup
  services/
    image_storage.py           Type + size validation, streamed save, delete
    food_recognition.py        Gemini client dependency, prompt, schema, error mapping
    nutrition.py               Name matching, merging, quantity × calories, rounding
tests/                         17 tests at the HTTP boundary
template.yaml                  AWS SAM: Lambda + API Gateway (binary uploads, /tmp paths)
docker-compose.yml             LocalStack + PostgreSQL
```

About 435 lines of application code and 295 lines of tests.

---

## Deployment (AWS)

Written as a **serverless-first** app from the first commit, not a server app someone might containerise later.

- **AWS Lambda** runs the FastAPI app directly; [Mangum](https://mangum.io) adapts ASGI to the Lambda event model, so the same code serves `uvicorn` locally and Lambda in the cloud.
- **API Gateway** fronts it with a catch-all proxy route, configured with **binary media types** for `multipart/form-data` and `image/*` — without which API Gateway base64-mangles every uploaded photo.
- **Lambda `/tmp`** holds the SQLite file and the in-flight image (the rest of the filesystem is read-only). Both are environment variables, so the same code runs unchanged on a laptop.
- **The Gemini key is a `NoEcho` CloudFormation parameter**, injected as an environment variable — never committed, never printed in stack output.

```bash
sam build
sam deploy --guided --parameter-overrides GeminiApiKey=<your-key>
```

**Why serverless fits this product:** meal logging is spiky by nature — three daily bursts at breakfast, lunch and dinner, near zero in between. The request is short and stateless: one photo in, one JSON answer out. Lambda's per-request billing and automatic scale-out match that shape, and the 30-second timeout bounds a hung model call.

---

## Configuration

Copy `.env.example` to `.env`. All values are optional except `GEMINI_API_KEY`.

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | Required by `POST /api/meals/analyze` (`503` without it) |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Recognition model |
| `DATABASE_URL` | `sqlite:///./wmd.db` | `/tmp/wmd.db` on Lambda |
| `UPLOAD_DIR` | `./uploads` | Scratch space for the in-flight image |
| `MAX_UPLOAD_BYTES` | `5242880` (5 MB) | Upload size limit |

---

## Status and honest limitations

All five MVP tickets are complete and merged to `main`, with 17 passing tests, full API documentation, and a SAM template for Lambda and API Gateway.

Two things worth knowing up front rather than discovering:

1. **The live Gemini call has not been exercised yet.** Development ran against a faked client because no API key was available in the build environment. The integration is written and unit-covered end to end; the first real call is a key away.
2. **The stack has not been deployed to a live AWS account yet.** The template is complete, and the Lambda-specific pitfalls (read-only filesystem, binary uploads, secret handling) are already solved in it.

Other known gaps — exact-only name matching (no plurals or synonyms), no request timeout on the Gemini call, the Lambda payload cap being lower than 5 MB in practice — are all written down, with context, in **[OPEN_ITEMS.md](OPEN_ITEMS.md)**.

## Roadmap

Each next step is a dependency swap, not a rewrite — the seams that make the code testable are the same seams that make it cloud-portable.

| Next step | AWS service | Why it drops in cleanly |
|---|---|---|
| Nutrition data shared across users | DynamoDB / Aurora Serverless | The database sits behind one injected dependency |
| Meal history and progress over time | DynamoDB | A Meal is already a clean domain object with a total |
| Optional photo retention | S3 + lifecycle rules | Storage is one module with a single save/delete responsibility |
| Swappable/multi-model recognition | Amazon Bedrock | Recognition is one function behind an injected client — the seam the tests already fake |
| Per-user auth replacing MockAuth | Amazon Cognito | Auth is already isolated behind its own router |

Beyond meal analysis, the product PRD covers profiles and deterministic daily targets, workout and step logging, a daily dashboard, and a grounded AI coach. Planned endpoint shapes are previewed at the end of [API_DOCS.md](API_DOCS.md).

---

## Documentation

| Document | What is in it |
|---|---|
| [API_DOCS.md](API_DOCS.md) | Every endpoint, with cURL examples and error codes |
| [CHANGELOG.md](CHANGELOG.md) | What shipped, per ticket |
| [OPEN_ITEMS.md](OPEN_ITEMS.md) | Known gaps, pending decisions, things needing review |
| [CONTEXT.md](CONTEXT.md) | Domain glossary — FoodItem, Meal, MealFood, MockAuth |
| [Hackathon_Writeup.md](Hackathon_Writeup.md) | The submission writeup: problem, insight, build, AWS story |

## How it was built

Test-first, at the HTTP boundary: every test drives the real endpoint through FastAPI's `TestClient`, with Gemini replaced by a fake client and the database swapped for in-memory SQLite. The suite needs no network and no API key. Work was tracked as GitHub issues (#1–#6), each one branched, reviewed against both repo standards and its spec, and merged with its documentation updated.

---

## The takeaway

Anyone can wire a photo to an LLM and print whatever number comes back. The interesting decision was drawing a hard line through the middle of the problem: **let the model do perception, and never let it near the arithmetic.** That single choice is what makes the calorie figures reproducible, the cost per meal small, the latency short, and the nutrition data an asset we own rather than a black box we hope is right.
