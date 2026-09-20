# Personal Fitness Coach — Snap a photo, get your calories

**One sentence:** point your camera at a plate, and the backend tells you what you ate and how many calories it was — using the LLM only to *see*, never to do the maths.

---

## The problem

Calorie tracking works, and almost nobody sticks with it.

The reason is friction. Logging a single meal in a conventional tracker means searching a database for "chicken breast", scrolling past forty near-identical entries, guessing a portion size, and repeating that for every item on the plate. It takes a minute or two per meal, three or more times a day, forever. People quit in the first fortnight — not because they stopped caring about their health, but because the app asked them to do data entry after every meal.

The obvious fix is a photo. The obvious implementation of that fix is: send the photo to a multimodal LLM and ask, "how many calories is this?"

**That implementation is the trap, and it is the thing our design exists to avoid.**

Ask an LLM for a calorie number and you get three problems at once:

1. **It makes numbers up.** A language model asked for "calories in 2 eggs" is generating plausible text, not doing arithmetic. The number moves between calls. It cannot be audited, and a fitness app whose numbers wobble is worse than no app at all — users make real decisions on these figures.
2. **It is slow.** Reasoning over nutrition, portions and multiplication takes tokens, and tokens take seconds. A user standing over a cooling plate notices.
3. **It costs money on every single meal.** Multiply an expensive multimodal call by three meals a day by every user, and the unit economics collapse before you have a business.

## The insight

**Identification is a perception problem. Calorie counting is a database lookup and a multiplication.** These are two different jobs, and only one of them needs an LLM.

So we split them:

> Gemini answers exactly one question — *"what food is on this plate, and how much of it?"* — and returns structured JSON. It never sees a calorie number and is never asked for one. The calories come from our own `food_items` table: `calories_per_unit × quantity`, computed in Python.

The payoff is direct:

| | LLM does everything | **Our split** |
|---|---|---|
| Calorie numbers | Hallucinated, vary per call | **Deterministic and auditable** — same photo, same answer |
| Latency | Model reasons about nutrition and maths | **One cheap vision call**, then an indexed lookup |
| Cost per meal | Large multimodal prompt + long output | **A short JSON reply** from a Flash-Lite class model |
| Correcting a wrong figure | Re-prompt and hope | **Fix one database row** — every future meal is right |
| Trust | "Where did 640 come from?" | Every number traces to a row a dietitian can review |

That last row is the one that matters commercially. Nutrition data is a **regulated, reviewable asset**. When the calorie table is ours, a nutritionist can audit it, a regional team can localise it, and a partner can license it. When it lives inside a model's weights, nobody can do any of that.

We also made the model's job *easier* rather than harder: the prompt is built at request time from the foods already in our database, with their serving units. Gemini isn't asked to invent a vocabulary; it's asked to match what we already know, and to count in our units. Recognition quality and data quality improve together.

---

## The build

A small, complete FastAPI backend — about 435 lines of application code, covered by 17 tests — that takes a meal photo and returns a priced meal.

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

### What it does

| Endpoint | Purpose |
|---|---|
| `POST /api/meals/analyze` | The product. Upload a photo → foods, quantities, per-item calories, meal total. |
| `GET /api/food-items` | The nutrition table the app can price, so the UI can show what it knows. |
| `POST /api/auth/mock-login` | Stub auth, so the frontend could integrate on day one instead of waiting on us. |
| `GET /health`, `GET /` | Liveness. |

Every endpoint is documented with copy-paste cURL examples in [API_DOCS.md](API_DOCS.md), plus auto-generated Swagger at `/docs`.

### The engineering that makes it demo-safe

A photo pipeline fails in messy ways, so each failure was made boring and explicit:

- **Uploads are bounded.** Only real image types are accepted (`415` otherwise); anything over the size limit is rejected mid-stream and the partial file deleted (`413`). No unbounded memory growth.
- **Photos are transient.** The image is written to scratch space, sent to Gemini, then **deleted** — in a `finally` block, so it goes even when the call fails. Meal photos are among the most personal data a fitness app touches; we keep them for seconds, not forever.
- **The model is treated as an unreliable network dependency, not an oracle.** A Gemini outage, a timeout, or a reply that isn't valid JSON all return a clean `502` the client can retry. A missing API key returns `503`. Nothing 500s.
- **Nonsense input can't corrupt the total.** Quantities of zero or less are dropped, a food recognised twice is merged into one entry rather than double-counted, and names match regardless of case or stray spaces.
- **A food we don't know is shown, not silently swallowed.** It comes back with `calories: null` and is excluded from the total, so the number stays honest and the UI can prompt the user.
- **Calories round half up**, consistently — because Python's default rounds half to even, which quietly makes half a banana 52 and half an apple 48.

### How it was built

Test-first, at the HTTP boundary: every test drives the real endpoint through FastAPI's `TestClient`, with Gemini replaced by a fake client and the database swapped for an in-memory SQLite instance. The suite runs in about two seconds, needs no network and no API key, and each of the behaviours above is pinned by a test — including the rounding bug, which a review caught and a test now prevents from returning. Work was tracked as GitHub issues (#1–#6), each one branched, reviewed against both repo standards and its spec, and merged with its documentation updated.

Honest engineering log: [CHANGELOG.md](CHANGELOG.md) records what shipped per ticket, and **[OPEN_ITEMS.md](OPEN_ITEMS.md) records what is still open** — including the big one below.

---

## Where AWS fits

The application was written as a **serverless-first** app from the first commit, not a server app that someone might containerise later. `template.yaml` is AWS SAM, in the repo since day one.

**Deployed shape today:**

- **AWS Lambda** runs the FastAPI app directly. [Mangum](https://mangum.io) adapts ASGI to the Lambda event model, so the same code serves `uvicorn` locally and Lambda in the cloud — no second code path to maintain, and no cold-start-heavy container image.
- **Amazon API Gateway** fronts it with a catch-all proxy route. It is configured with **binary media types** for `multipart/form-data` and `image/*`, without which API Gateway base64-mangles every uploaded photo — the kind of detail that only shows up in production, so we handled it in the template.
- **Lambda's `/tmp` scratch space** holds both the SQLite file and the in-flight image, because the rest of the Lambda filesystem is read-only. Paths are environment variables (`DATABASE_URL`, `UPLOAD_DIR`), so the same code runs unchanged on a laptop.
- **The Gemini API key is a `NoEcho` CloudFormation parameter**, injected as an environment variable — never committed, never printed in stack output.
- **LocalStack** (via `docker-compose`) gives the whole team AWS-shaped local development without an AWS bill during a hackathon.

**Why serverless is the right fit for this product, not just a convenient host:** meal logging is spiky by nature — traffic arrives in three daily bursts at breakfast, lunch and dinner and is near zero between them. Paying for idle capacity through the night is exactly what this workload shouldn't do. The request is also naturally short and stateless: one photo in, one JSON answer out, no session to keep. Lambda's per-request billing and automatic scale-out match that shape precisely, and the 30-second timeout bounds a hung model call.

**The path onward, already in the design:**

| Next step | AWS service | Why it drops in cleanly |
|---|---|---|
| Nutrition data shared across all users | **DynamoDB** or **Aurora Serverless** | The database sits behind one injected dependency; the calorie lookup doesn't care what's underneath. |
| Meal history and progress over time | **DynamoDB** | Meals are already a clean domain object with a total. |
| Optional photo retention | **S3** + lifecycle rules | Storage is one small module with a single `save`/`delete` responsibility. |
| Swappable/multi-model recognition | **Amazon Bedrock** | Recognition is one function behind an injected client — the same seam the tests already use to substitute a fake. |
| Per-user auth replacing MockAuth | **Amazon Cognito** | Auth is already isolated behind its own router. |

Each of those is a dependency swap, not a rewrite — which is the real argument for the layering: **the seams we built to make the code testable are the same seams that make it cloud-portable.**

---

## Current status, honestly

Complete and merged to `main`: all five MVP tickets, 17 passing tests, full API documentation, SAM template for Lambda and API Gateway.

Two things a judge should know rather than discover:

1. **The live Gemini call hasn't been exercised yet** — development ran against a faked client because no API key was available in the build environment. The integration is written and unit-covered end to end; the first real call is a key away, and it's item one in `OPEN_ITEMS.md`.
2. **The stack hasn't been deployed to a live AWS account yet.** The template is complete and the Lambda-specific pitfalls (read-only filesystem, binary uploads, secret handling) are already solved in it.

Everything we know is unfinished is written down in the open-items log rather than left to be found. That list is short, specific, and public — which is how we'd want to hand this to the next engineer.

---

## The takeaway

Anyone can wire a photo to an LLM and print whatever number comes back. The interesting decision was drawing a hard line through the middle of the problem: **let the model do perception, and never let it near the arithmetic.** That single choice is what makes the calorie figures reproducible, the cost per meal small, the latency short, and the nutrition data an asset we own rather than a black box we hope is right.
