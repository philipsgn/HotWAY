"""Spatial Pydantic schemas and geometry conversion helpers."""

from __future__ import annotations

import re
from typing import Any, Optional, Tuple
from pydantic import BaseModel, Field
from geoalchemy2.elements import WKBElement, WKTElement


class PointCoordinates(BaseModel):
    """Geographic point coordinates in WGS84 (lat/lon)."""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    def to_wkt(self) -> str:
        """Returns WKT formatted string: POINT(lon lat)."""
        return f"POINT({self.lon} {self.lat})"

    def to_wkt_element(self, srid: int = 4326) -> WKTElement:
        """Returns GeoAlchemy2 WKTElement."""
        return WKTElement(self.to_wkt(), srid=srid)


class GeoJSONPoint(BaseModel):
    """Standard GeoJSON Point geometry representation."""
    type: str = Field(default="Point")
    coordinates: Tuple[float, float] = Field(..., description="[longitude, latitude]")

    @property
    def lon(self) -> float:
        return self.coordinates[0]

    @property
    def lat(self) -> float:
        return self.coordinates[1]


def parse_geometry_to_coords(v: Any) -> Optional[PointCoordinates]:
    """Helper validator converting WKBElement, WKTElement, WKT str, GeoJSON, or dict to PointCoordinates."""
    if v is None:
        return None
    if isinstance(v, PointCoordinates):
        return v
    if isinstance(v, dict):
        if "lat" in v and "lon" in v:
            return PointCoordinates(lat=float(v["lat"]), lon=float(v["lon"]))
        if v.get("type") == "Point" and "coordinates" in v:
            coords = v["coordinates"]
            return PointCoordinates(lat=float(coords[1]), lon=float(coords[0]))
    if isinstance(v, WKBElement):
        try:
            from geoalchemy2.shape import to_shape
            shape = to_shape(v)
            return PointCoordinates(lat=shape.y, lon=shape.x)
        except Exception:
            pass
    if isinstance(v, WKTElement):
        v = str(v.data)
    if isinstance(v, str):
        # Support WKT like 'POINT(107.2401 10.9212)' or 'SRID=4326;POINT(107.2401 10.9212)'
        match = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", v, re.IGNORECASE)
        if match:
            lon, lat = float(match.group(1)), float(match.group(2))
            return PointCoordinates(lat=lat, lon=lon)
        # Fallback split
        cleaned = v.split(";")[-1].replace("POINT", "").replace("(", "").replace(")", "").strip()
        parts = cleaned.split()
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            return PointCoordinates(lat=lat, lon=lon)
    # Check if object has x and y (e.g. Shapely Point)
    if hasattr(v, "x") and hasattr(v, "y"):
        return PointCoordinates(lat=float(v.y), lon=float(v.x))
    return None
