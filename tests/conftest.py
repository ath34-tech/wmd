import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import get_db, init_db
from app.main import app


@pytest.fixture
def client():
    """TestClient backed by an isolated, seeded in-memory SQLite database.

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
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    """Keep uploaded images out of the repo: save them to a per-test temp dir."""
    path = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(path))
    return path
