# Open Items

Pending work, things needing review, and known problems not yet addressed. Updated with every ticket; tick an item and note where it was resolved rather than deleting it. What *was* built is in [CHANGELOG.md](CHANGELOG.md).

Last updated: 2026-09-20 (after #5).

## Needs a decision

- [x] ~~**Merge `feature/backend-mvp` into `main`.**~~ Done 2026-09-20 after #5, at the user's request. #6 will follow the same path (branch off and merge into `feature/backend-mvp`, then `main`).
- [ ] **Should endpoints require the MockAuth token?** `POST /api/auth/mock-login` issues `mock-token-wmd-mvp`, but no endpoint checks it. The spec allows either; decide before the frontend hard-codes behaviour. (#2)
- [ ] **What to do with foods Gemini names that aren't in the DB.** #5 lets Gemini return generic names for unknown foods; #6 must decide whether to skip them, return them with `calories: null`, or fail. (#5 → #6)

## Needs review

- [ ] **Live Gemini call never exercised.** No API key was available, so tests only use a fake client. Run one real request with a `GEMINI_API_KEY` and a few meal photos to check that the JSON schema is accepted by the model, and how accurate names and quantities are. (#5)
- [ ] **Seed calorie values** in `app/db/seed.py` are approximate USDA-style figures written by hand; have someone sanity-check them. (#3)
- [ ] **Lambda deployment is untested.** `template.yaml` changes (`/tmp` DB and uploads, `BinaryMediaTypes`, `GeminiApiKey` parameter) have never been deployed. (#3, #4, #5)

## Known gaps and problems

### Uploads (#4)
- [ ] **Size limit applies after the body is received.** Starlette buffers the whole multipart body (to a spooled temp file) before the endpoint's 5 MB check runs, so huge uploads still cost bandwidth and temp disk. Fix: middleware that rejects on `Content-Length` first.
- [ ] **Lambda payload limit is lower than 5 MB in practice.** Lambda's synchronous payload cap is 6 MB and API Gateway base64-encodes binary bodies (+33%), so images over ~4.4 MB will fail on Lambda before reaching the app. Lower `MAX_UPLOAD_BYTES` on Lambda or have the frontend downscale images.
- [ ] **Content type is trusted from the client header.** No magic-byte sniffing; a mislabelled file reaches Gemini and fails there (→ 502).
- [x] ~~Uploaded images were never deleted.~~ Resolved in #5: deleted after analysis.

### Database (#3)
- [ ] **For #6: match FoodItem names case-insensitively.** `food_items.name` is a case-sensitive unique column and no lookup exists yet. #5's prompt asks Gemini to reuse the exact known names, which helps, but the #6 lookup should still normalise case/whitespace.
- [ ] **SQLite on Lambda lives in `/tmp` per container.** Fine for read-only seed data; anything written at runtime (e.g. future Meal history) would be lost. The README tech stack still mentions PostgreSQL for later.
- [ ] **Startup seeding isn't covered by automated tests.** Idempotency was checked manually (two startups, no duplicates).

### Gemini (#5)
- [ ] **No request timeout on the Gemini call.** A slow call could run into the Lambda 30 s timeout; consider setting `HttpOptions(timeout=...)` on the client.
- [ ] **For #6: Gemini's quantities are not sanitised.** Nothing rejects zero/negative quantities or merges a food listed twice (e.g. two "Egg" entries); both would flow straight into the calorie total. (Kept out of the response schema on purpose: Gemini's schema support for numeric bounds is unverified.)
- [ ] **Missing API key returns 503 before the upload is validated**, so a bad file gets 503 rather than 415 on a server without a key. Harmless, but surprising.
- [ ] **The image makes a disk round trip for no reason now.** It is saved (per spec #1), read straight back and deleted; sending the bytes directly would be simpler. The sync file read and DB query also run inside an `async def` endpoint — fine at MVP scale.
- [ ] **The real `genai.Client` construction is never exercised by tests** (`get_gemini_client` is always overridden, and the 503 test stops before the client is built).
- [x] ~~Network failures (timeouts, connection errors) returned 500 instead of 502.~~ Resolved in #5 review: `httpx` errors now map to 502.
- [ ] **The missing-API-key test never failed first.** The 503 check was written before its test, so the test documents the behaviour rather than having driven it.

### Tooling (#2)
- [ ] **No typechecker or linter configured** (e.g. mypy/pyright, ruff). Checks so far are compile-only plus tests.
- [ ] **Deprecation warnings in the test run** come from FastAPI 0.111 / Starlette 0.37 (`python_multipart` import, `anyio` `BlockingPortal`). Upgrading FastAPI would clear them.

### Minor (judgement calls from code reviews)
- [ ] `FoodItem.unit` holds a serving description (e.g. "medium banana"); a name like `serving` might read better. (#3)
- [ ] `tests/test_meals.py` repeats the upload call in every test (now 9 times); a small helper would tidy it. (#4, #5)
- [ ] `food_item` fields (`MealItem`, `IdentifiedFood`) hold a food *name*, not a FoodItem; `food_name` would be more precise, but it is part of the published API contract now. The service's `IdentifiedFood`/`FoodIdentification` mirror `MealItem`/`MealAnalysis` and are copied field by field; kept separate so #6 can add calories to the response only. (#5)
- [ ] Response models `MealAnalysis` / `MealItem` don't follow the `...Response` suffix used by `TokenResponse` / `FoodItemResponse`. (#4)
