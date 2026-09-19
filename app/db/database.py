from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import Base
from app.db.seed import seed_food_items

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)


def init_db(bind: Engine = engine) -> None:
    """Create tables and insert seed data. Safe to run repeatedly."""
    Base.metadata.create_all(bind)
    with Session(bind) as db:
        seed_food_items(db)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a DB session; override it in tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
