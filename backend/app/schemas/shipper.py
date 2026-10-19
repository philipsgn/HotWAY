"""Pydantic schemas for Shippers."""

from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    from backend.app.schemas.spatial import PointCoordinates, parse_geometry_to_coords
    from backend.app.schemas.enums import ShipperStatus, VehicleType
except ImportError:
    from .spatial import PointCoordinates, parse_geometry_to_coords
    from .enums import ShipperStatus, VehicleType


class ShipperBase(BaseModel):
    name: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    vehicle_type: VehicleType = Field(default=VehicleType.MOTORBIKE)
    status: ShipperStatus = Field(default=ShipperStatus.AVAILABLE)


class ShipperCreate(ShipperBase):
    current_location: Optional[PointCoordinates] = None


class ShipperLocationUpdate(BaseModel):
    current_location: PointCoordinates
    speed_kmh: Optional[float] = Field(default=0.0, ge=0.0)


class ShipperResponse(ShipperBase):
    id: int
    current_location: Optional[PointCoordinates] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("current_location", mode="before")
    @classmethod
    def serialize_location(cls, v: Any) -> Optional[PointCoordinates]:
        return parse_geometry_to_coords(v)
