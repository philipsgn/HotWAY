"""Pydantic schemas for Orders and Order Items."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from backend.app.schemas.spatial import PointCoordinates, parse_geometry_to_coords
    from backend.app.schemas.enums import OrderStatus
except ImportError:
    from .spatial import PointCoordinates, parse_geometry_to_coords
    from .enums import OrderStatus


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, gt=0)
    unit_price: float = Field(..., ge=0.0)


class OrderItemResponse(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    order_code: Optional[str] = Field(default=None, max_length=50)
    customer_name: str = Field(..., max_length=255)
    customer_phone: str = Field(..., max_length=20)
    delivery_location: PointCoordinates
    items: List[OrderItemCreate] = Field(..., min_length=1)
    container_factor: float = Field(default=1.0, gt=0.0)
    target_temp: float = Field(default=60.0, gt=0.0)
    deadline_minutes: int = Field(default=30, gt=0)
    restaurant_id: Optional[int] = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    assigned_shipper_id: Optional[int] = None


class OrderResponse(BaseModel):
    id: int
    order_code: str
    customer_name: str
    customer_phone: str
    delivery_location: PointCoordinates
    status: OrderStatus
    container_factor: float
    target_temp: float
    deadline_minutes: int
    created_at: datetime
    restaurant_id: Optional[int] = None
    assigned_shipper_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("delivery_location", mode="before")
    @classmethod
    def serialize_delivery_location(cls, v: Any) -> Optional[PointCoordinates]:
        return parse_geometry_to_coords(v)


class OrderDetailResponse(OrderResponse):
    order_items: List[OrderItemResponse] = Field(default_factory=list)
