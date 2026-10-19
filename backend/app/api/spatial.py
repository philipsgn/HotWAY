"""
Spatial & GIS Endpoints for Hàng Gòn Map & 3D Assets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from backend.app.services.routing_service import DEPOT_LAT, DEPOT_LON

router = APIRouter()


@router.get("/depot", summary="Get Quán Bánh Canh Gà Hàng Gòn depot location")
async def get_depot():
    return {
        "name": "Quán Bánh Canh Gà Hàng Gòn",
        "address": "Quốc Lộ 56, Xã Hàng Gòn, TP. Long Khánh, Tỉnh Đồng Nai",
        "latitude": DEPOT_LAT,
        "longitude": DEPOT_LON,
        "bounds": {
            "min_lat": 10.90,
            "max_lat": 10.95,
            "min_lon": 107.21,
            "max_lon": 107.27,
        },
    }


@router.get("/roads", summary="Get Hàng Gòn Road Network GeoJSON")
async def get_roads():
    road_path = Path("data/hanggon_roads.geojson")
    if road_path.is_file():
        try:
            with open(road_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read roads geojson: {exc}")

    # Fallback minimal GeoJSON
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [DEPOT_LON, DEPOT_LAT],
                        [107.2435, 10.9260],
                        [107.2480, 10.9320],
                    ],
                },
                "properties": {"name": "Quốc Lộ 56 Hàng Gòn", "maxspeed": "60"},
            }
        ],
    }


@router.get("/buildings", summary="Get Hàng Gòn 3D Building Polygons GeoJSON")
async def get_buildings():
    bldg_path = Path("data/hanggon_buildings.geojson")
    if bldg_path.is_file():
        try:
            with open(bldg_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read buildings geojson: {exc}")

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [107.2398, 10.9209],
                        [107.2404, 10.9209],
                        [107.2404, 10.9215],
                        [107.2398, 10.9215],
                        [107.2398, 10.9209],
                    ]],
                },
                "properties": {"name": "Quán Bánh Canh Gà", "height": 6.0},
            }
        ],
    }
