"""
Orders REST API Endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/", summary="List delivery orders")
async def list_orders(status: Optional[str] = None):
    return []


@router.post("/", summary="Create delivery order", status_code=status.HTTP_201_CREATED)
async def create_order(payload: Dict[str, Any]):
    return {
        "id": 1,
        "order_code": payload.get("order_code", "ORD-HOTWAY-001"),
        "customer_name": payload.get("customer_name", "Khách Hàng"),
        "customer_phone": payload.get("customer_phone", "0901234567"),
        "status": "PENDING",
        "container_factor": payload.get("container_factor", 1.0),
        "target_temp": payload.get("target_temp", 60.0),
        "deadline_minutes": payload.get("deadline_minutes", 30),
    }


@router.get("/{order_id}", summary="Get order details")
async def get_order(order_id: int):
    return {
        "id": order_id,
        "order_code": f"ORD-HOTWAY-{order_id:03d}",
        "status": "PREPARING",
        "current_temp": 82.0,
    }


@router.patch("/{order_id}/status", summary="Update order lifecycle status")
async def update_order_status(order_id: int, payload: Dict[str, Any]):
    return {
        "id": order_id,
        "new_status": payload.get("status", "DISPATCHED"),
    }
