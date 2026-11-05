"""
API Router for Graph & Pathfinding Algorithm Visualizer.
Endpoints:
- GET /map/bounds: Returns bounding box, center, and sample landmark nodes.
- POST /api/solve-path: Accepts start/end coordinates and algorithm, returns chronological step-by-step wavefront.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.graph_stepper import GraphStepEngine

logger = logging.getLogger("visualizer_api")
router = APIRouter(tags=["Algorithm Visualizer"])


class SolvePathRequest(BaseModel):
    start_coords: List[float] = Field(..., description="[lat, lon] of start point", min_length=2, max_length=2)
    end_coords: List[float] = Field(..., description="[lat, lon] of destination point", min_length=2, max_length=2)
    algorithm: str = Field(default="a_star", description="a_star | dijkstra | bidirectional | dynamic_c_t")
    max_steps: Optional[int] = Field(default=1200, description="Maximum number of animation steps to return")


@router.get("/map/bounds", summary="Lấy thông số bounding box và trung tâm bản đồ đồ thị")
def get_map_bounds() -> Dict[str, Any]:
    try:
        engine = GraphStepEngine.get_instance()
        return {
            "status": "success",
            "bounds": engine.bounds,
            "sample_landmarks": [
                {"name": "Landmark 81 / Vinhomes Central Park", "lat": 10.7951, "lon": 106.7218},
                {"name": "Ngã tư Hàng Xanh / Điện Biên Phủ", "lat": 10.8014, "lon": 106.7112},
                {"name": "Nhà Thờ Đức Bà / Quận 1", "lat": 10.7798, "lon": 106.6990},
                {"name": "Chợ Bà Chiểu / Bình Thạnh", "lat": 10.8016, "lon": 106.6961},
                {"name": "Cầu Thị Nghè / Thảo Cầm Viên", "lat": 10.7905, "lon": 106.7052},
            ],
            "supported_algorithms": [
                {"id": "a_star", "name": "A* Search", "description": "Sóng định hướng elip với Heuristic Haversine h(n)"},
                {"id": "dijkstra", "name": "Dijkstra (Uniform Cost)", "description": "Sóng lan truyền tròn 360 độ quét mọi hướng"},
                {"id": "bidirectional", "name": "Bidirectional Search", "description": "2 đầu sóng xuất phát từ A và B gặp nhau ở giữa"},
                {"id": "dynamic_c_t", "name": "HotWAY Dynamic Dijkstra", "description": "Sóng uốn lượn thích nghi né tránh điểm nghẽn C(t)"},
            ],
        }
    except Exception as e:
        logger.error(f"Error loading map bounds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/solve-path", summary="Chạy thuật toán và ghi nhận timeline từng bước lan truyền sóng")
def solve_path(req: SolvePathRequest) -> Dict[str, Any]:
    try:
        engine = GraphStepEngine.get_instance()
        result = engine.solve(
            start_lat=req.start_coords[0],
            start_lon=req.start_coords[1],
            end_lat=req.end_coords[0],
            end_lon=req.end_coords[1],
            algorithm=req.algorithm,
            max_steps=req.max_steps or 1200,
        )
        return {
            "status": "success",
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error solving path: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to solve path: {e}")
