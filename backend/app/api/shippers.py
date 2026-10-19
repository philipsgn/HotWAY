"""
Shippers REST API Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status

router = APIRouter()


@router.get("/", summary="List active shippers")
async def list_shippers(status: Optional[str] = None):
    return [
        {
            "id": 1,
            "name": "Nguyễn Văn Giao",
            "phone": "0901234567",
            "vehicle_type": "MOTORBIKE",
            "status": "AVAILABLE",
        }
    ]


@router.post("/", summary="Register shipper", status_code=status.HTTP_201_CREATED)
async def create_shipper(payload: Dict[str, Any]):
    return {
        "id": 2,
        "name": payload.get("name", "Shipper Mới"),
        "phone": payload.get("phone", "0909999999"),
        "vehicle_type": payload.get("vehicle_type", "MOTORBIKE"),
        "status": "AVAILABLE",
    }
