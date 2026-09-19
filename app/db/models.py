from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FoodItem(Base):
    """A generic type of food with baseline calories for one unit (serving)."""

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    calories_per_unit: Mapped[int]
    unit: Mapped[str] = mapped_column(String(50))
