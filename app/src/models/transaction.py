import uuid

from enum import Enum
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Column, Field, Relationship
from sqlalchemy.types import Enum as SQLEnum
from models.ml_task import MLTask
from sqlalchemy.orm import declared_attr

if TYPE_CHECKING:
    from models.user import User


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    PROCESSING = "PROCESSING"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"


class Transaction(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    user_id: int = Field(foreign_key="users.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="transactions", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    type: TransactionType = Field(default=TransactionType.DEPOSIT, sa_column=Column(SQLEnum(TransactionType), nullable=False))
    status: TransactionStatus = Field(default=TransactionStatus.PENDING, sa_column=Column(SQLEnum(TransactionStatus), nullable=False))
    amount: Decimal = Field(max_digits=15, decimal_places=4, nullable=False)
    balance: Decimal = Field(max_digits=15, decimal_places=4, nullable=False)

    ml_task: Optional["MLTask"] = Relationship(back_populates="transaction", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self):
        return f"{self.type}(id:{self.id} status:'{self.status}' amount: {self.amount}; balance: {self.balance}; {self.timestamp})"