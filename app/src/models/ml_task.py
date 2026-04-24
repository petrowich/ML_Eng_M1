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
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MLTask(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "ml_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id")
    user: Optional["User"] = Relationship(back_populates="ml_tasks", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    ml_model_id: int = Field(foreign_key="ml_models.id")
    ml_model: Optional["MLModel"] = Relationship(back_populates="ml_tasks", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    prediction: Optional["Prediction"] = Relationship(back_populates="ml_task", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    transaction_id: Optional[uuid.UUID] = Field(default=None, foreign_key="transactions.id", nullable=True, unique=True)
    transaction: Optional["Transaction"] = Relationship(back_populates="ml_task", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    request: Optional[str] = Field(sa_column=Column(Text, nullable=True))

    status: MLTaskStatus = Field(default=MLTaskStatus.NEW, sa_column=Column(SQLEnum(MLTaskStatus), nullable=False))
    duration_ms: int = Field(default=0)

    failure: Optional[str] = Field(sa_column=Column(Text, nullable=True))

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
