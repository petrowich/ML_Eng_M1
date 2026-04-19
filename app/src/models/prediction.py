from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field, Column, Text, Relationship
from models.ml_task import MLTask
from sqlalchemy.orm import declared_attr


class Prediction(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "predictions"

    id: Optional[int] = Field(default=None, primary_key=True)

    result: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    cost: Decimal = Field(default=Decimal("0.0"), max_digits=8, decimal_places=4)

    ml_task_id: int = Field(foreign_key="ml_tasks.id", nullable=False, index=True)
    ml_task: Optional["MLTask"] = Relationship(back_populates="prediction", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

