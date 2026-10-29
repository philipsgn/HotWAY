"""
Spatial & GIS Endpoints for Bình Thạnh Map, 3D Assets & Dual Benchmark Routes.
Authoritative Territory: Quán Bánh Canh Gà 490 Điện Biên Phủ, Phường 21, Bình Thạnh.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query

from backend.app.services.routing_service import (
    DEPOT_LAT,
    DEPOT_LON,
    DEPOT_NAME,
    DEPOT_ADDRESS,
    routing_service,
)

router = APIRouter()


@router.get("/depot", summary="Get Quán Bánh Canh Gà 490 Điện Biên Phủ depot location")
async def get_depot():
    return {
        "name": DEPOT_NAME,
        "address": DEPOT_ADDRESS,
        "latitude": DEPOT_LAT,
        "longitude": DEPOT_LON,
        "bounds": {
            "min_lat": 10.78,
            "max_lat": 10.83,
            "min_lon": 106.68,
            "max_lon": 106.73,
        },
    }


@router.get("/benchmark-routes", summary="Get dual benchmark routes (Dijkstra vs DQN/RL) from 490 ĐBP to Landmark 81")
async def get_benchmark_routes(
    destination: str = Query(default="lm81", description="Destination ID (default: Landmark 81)"),
    rush_hour: bool = Query(default=True, description="Enable rush hour bottleneck multiplier (3.0x at Hàng Xanh)"),
):
    """
    Returns dual GeoJSON benchmark routes with travel times, Newton cooling temperatures,
    and bottleneck analysis for Bình Thạnh:
    - Dijkstra Bottleneck Route (Neon Red): Forces through Hàng Xanh choke point, cooling < 65°C (~58.4°C).
    - DQN / RL Optimal Route (Gold Yellow): Smart detour via D1-D2, cooling > 75°C (~77.2°C).
    """
    return routing_service.get_benchmark_routes(destination=destination, rush_hour=rush_hour)


@router.get("/roads", summary="Get Bình Thạnh Road Network GeoJSON")
async def get_roads():
    road_path = Path("data/hcmc_compact_roads.geojson")
    if not road_path.is_file():
        road_path = Path("data/hcmc_compact_roads.geojson")

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
                        [106.7180, 10.7995],
                        [106.7215, 10.7950],
                    ],
                },
                "properties": {"name": "Đường Điện Biên Phủ", "maxspeed": "60"},
            }
        ],
    }


@router.get("/buildings", summary="Get Bình Thạnh 3D Building Polygons GeoJSON")
async def get_buildings():
    bldg_path = Path("data/buildings.geojson")
    if not bldg_path.is_file():
        bldg_path = Path("data/buildings.geojson")

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
                        [106.7143, 10.8010],
                        [106.7147, 10.8010],
                        [106.7147, 10.8014],
                        [106.7143, 10.8014],
                        [106.7143, 10.8010],
                    ]],
                },
                "properties": {"name": DEPOT_NAME, "height": 12.0},
            }
        ],
    }
