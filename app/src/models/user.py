from enum import Enum
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, String, Text, Relationship
from sqlalchemy.types import Enum as SQLEnum
from models.ml_task import MLTask
from models.transaction import Transaction
from sqlalchemy.orm import declared_attr

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserAuth(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "user_auth"

    user_id: Optional[int] = Field(default=None, foreign_key="users.id", primary_key=True)
    user: Optional["User"] = Relationship(back_populates="auth", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    login: str = Field(sa_column=Column(String(50), index=True, nullable=False, unique=True))
    pwd_hash: str = Field(sa_column=Column(Text, nullable=False))

    changed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class User(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "users"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)

    name: Optional[str] = Field(max_length=255)
    email: str = Field(sa_column=Column(String(255), index=True, nullable=False, unique=True))

    role: UserRole = Field(sa_column=Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False))

    auth: Optional["UserAuth"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    balance: Optional[Decimal] = Field(max_digits=15, decimal_places=4, nullable=True)

    ml_tasks: List["MLTask"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    transactions: List["Transaction"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    def __str__(self):
        return f"{self.role}(id={self.id} name:'{self.name}' email:{self.email} login:{self.auth.login if self.auth else None})"
