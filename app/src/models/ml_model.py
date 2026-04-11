from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, String, Relationship
from sqlalchemy.orm import declared_attr

if TYPE_CHECKING:
    from models import MLTask


class MLModel(SQLModel, table=True):
    @declared_attr
    def __tablename__(cls) -> str:
        return "models"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: Optional[str] = Field(max_length=255)
    reference: Optional[str] = Field(min_length=1, max_length=50, nullable=False)
    description: Optional[str] = Field(sa_column=Column(String(2000), nullable=False))
    prediction_cost: Decimal = Field(default=Decimal("0.0"), max_digits=12, decimal_places=4)

    tasks: List["MLTask"] = Relationship(back_populates="model", sa_relationship_kwargs={"lazy": "selectin"})
