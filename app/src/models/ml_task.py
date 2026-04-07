import uuid

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, Relationship, Text
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import declared_attr

if TYPE_CHECKING:
    from models.user import User
    from models.transaction import Transaction
    from models.prediction import Prediction
    from models.ml_model import MLModel


class MLTaskStatus(str, Enum):
    NEW = "NEW"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MLTask(SQLModel, table=True):
    @declared_attr
    def __tablename__(cls) -> str:
        return "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    user: Optional["User"] = Relationship(back_populates="tasks", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    model_id: int = Field(foreign_key="models.id")
    model: Optional["MLModel"] = Relationship(back_populates="tasks", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    prediction_id: int = Field(default=None, foreign_key="predictions.id", nullable=True, unique=True)
    prediction: Optional["Prediction"] = Relationship(back_populates="task", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    transaction_id: Optional[uuid.UUID] = Field(default=None, foreign_key="transactions.id", nullable=True, unique=True)
    transaction: Optional["Transaction"] = Relationship(back_populates="task", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    request: Optional[str] = Field(sa_column=Column(Text, nullable=True))

    status: MLTaskStatus = Field(default=MLTaskStatus.NEW, sa_column=Column(SQLEnum(MLTaskStatus), nullable=False))
    duration_ms: int = Field(default=0)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
