from enum import Enum
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, String, Text, Relationship, DateTime
from sqlalchemy.types import Enum as SQLEnum, DECIMAL
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

    login: str = Field(sa_column=Column(String(50), index=True, nullable=False, unique=True), max_length=50)
    pwd_hash: str = Field(sa_column=Column(Text, nullable=False), max_length=255)

    changed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class User(SQLModel, table=True):
    @declared_attr
    def __tablename__(self) -> str:
        return "users"

    id: Optional[int] = Field(default=None, primary_key=True, nullable=False)

    name: Optional[str] = Field(sa_column=Column(String(255)), min_length=1, max_length=255)

    email: Optional[str] = Field(sa_column=Column(String(255), nullable=False, unique=True), min_length=3, max_length=255)

    role: UserRole = Field(default=UserRole.USER, sa_column=Column(SQLEnum(UserRole), nullable=False))

    auth: Optional["UserAuth"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})

    balance: Optional[Decimal] = Field(sa_column=Column(DECIMAL(precision=15, scale=4), nullable=True))

    ml_tasks: List["MLTask"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    transactions: List["Transaction"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    created: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))

    def __str__(self):
        return f"{self.role}(id={self.id} name:'{self.name}' email:{self.email} login:{self.auth.login if self.auth else None})"
