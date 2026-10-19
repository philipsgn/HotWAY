"""Pydantic schemas for Restaurants."""

from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from backend.app.schemas.spatial import PointCoordinates, parse_geometry_to_coords
except ImportError:
    from .spatial import PointCoordinates, parse_geometry_to_coords


class RestaurantBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: Optional[str] = None
    open_hours: Optional[str] = Field(default="06:00 - 21:00", max_length=100)


class RestaurantCreate(RestaurantBase):
    location: PointCoordinates


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    open_hours: Optional[str] = Field(None, max_length=100)
    location: Optional[PointCoordinates] = None


class RestaurantResponse(RestaurantBase):
    id: int
    location: PointCoordinates

    model_config = ConfigDict(from_attributes=True)

    @field_validator("location", mode="before")
    @classmethod
    def serialize_location(cls, v: Any) -> Optional[PointCoordinates]:
        return parse_geometry_to_coords(v)
