"""
Simulation & Mock GPS Endpoints.
"""

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter()


@router.post("/spawn", summary="Spawn simulated orders and shippers")
async def spawn_simulation(payload: Dict[str, Any]):
    return {
        "status": "success",
        "spawned_orders": 3,
        "spawned_shippers": 1,
    }


@router.post("/reset", summary="Reset simulation environment")
async def reset_simulation():
    return {
        "status": "reset_completed",
    }
