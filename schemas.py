from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    price: Decimal = Field(gt=0, decimal_places=2)
    delivery_days: int = Field(gt=0, le=30)


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1)
    price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    delivery_days: Optional[int] = Field(default=None, gt=0, le=30)


class ListingRead(ListingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
