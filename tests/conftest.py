import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import get_db, init_db
from app.main import app
from app.services.food_recognition import get_gemini_client


class FakeGeminiClient:
    """Stands in for google.genai.Client: records calls, returns a canned reply.

    Set `reply` to the JSON-serialisable body Gemini should return, `raw_reply`
    to return text verbatim, or `error` to make the call raise.
    """

    def __init__(self):
        self.reply = {"items": [{"food_item": "Banana", "quantity": 1}]}
        self.raw_reply = None
        self.error = None
        self.calls = []
        self.aio = SimpleNamespace(
            models=SimpleNamespace(generate_content=self._generate_content)
        )

    async def _generate_content(self, *, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.error:
            raise self.error
        text = self.raw_reply if self.raw_reply is not None else json.dumps(self.reply)
        return SimpleNamespace(text=text)


@pytest.fixture
def gemini():
    return FakeGeminiClient()


@pytest.fixture
def client(gemini):
    """TestClient backed by an isolated, seeded in-memory SQLite database and
    a fake Gemini client (no network calls).

    Not used as a context manager, so the app lifespan (which initialises the
    real file DB) does not run.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_gemini_client] = lambda: gemini
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Keep uploaded images out of the repo: save them to a per-test temp dir."""
    path = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(path))
    return path
