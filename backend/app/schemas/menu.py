"""Pydantic schemas for Menu Items."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

try:
    from backend.app.schemas.enums import ContainerType
except ImportError:
    from .enums import ContainerType


class MenuItemBase(BaseModel):
    name: str = Field(..., max_length=255)
    base_price: float = Field(..., ge=0.0, description="Price in VND")
    default_k: float = Field(default=0.038, gt=0.0, description="Newton cooling coefficient k")
    initial_temp: float = Field(default=88.0, gt=0.0, description="Initial serving temperature in °C")
    container_type: ContainerType = Field(default=ContainerType.INSULATED_BAG)


class MenuItemCreate(MenuItemBase):
    restaurant_id: int


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    base_price: Optional[float] = Field(None, ge=0.0)
    default_k: Optional[float] = Field(None, gt=0.0)
    initial_temp: Optional[float] = Field(None, gt=0.0)
    container_type: Optional[ContainerType] = None


class MenuItemResponse(MenuItemBase):
    id: int
    restaurant_id: int

    model_config = ConfigDict(from_attributes=True)
