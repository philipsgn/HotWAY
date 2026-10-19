"""Pydantic schemas for Route Logs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from backend.app.schemas.spatial import PointCoordinates, parse_geometry_to_coords
except ImportError:
    from .spatial import PointCoordinates, parse_geometry_to_coords


class RouteLogCreate(BaseModel):
    order_id: int
    shipper_id: Optional[int] = None
    waypoint: PointCoordinates
    temperature_at_point: Optional[float] = None
    speed_kmh: float = Field(default=0.0, ge=0.0)


class RouteLogResponse(BaseModel):
    id: int
    order_id: int
    shipper_id: Optional[int] = None
    waypoint: PointCoordinates
    recorded_at: datetime
    temperature_at_point: Optional[float] = None
    speed_kmh: float

    model_config = ConfigDict(from_attributes=True)

    @field_validator("waypoint", mode="before")
    @classmethod
    def serialize_waypoint(cls, v: Any) -> Optional[PointCoordinates]:
        return parse_geometry_to_coords(v)
