"""
Menu REST API Endpoints.
"""

from typing import List
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List menu items")
async def list_menu():
    """Returns list of Bánh Canh Gà items with pricing and thermal parameters."""
    return [
        {
            "id": 1,
            "name": "Bánh Canh Gà Đặc Biệt",
            "base_price": 45000.0,
            "default_k": 0.038,
            "initial_temp": 88.0,
            "container_type": "INSULATED_BAG",
        },
        {
            "id": 2,
            "name": "Bánh Canh Gà Đùi",
            "base_price": 50000.0,
            "default_k": 0.038,
            "initial_temp": 88.0,
            "container_type": "INSULATED_BAG",
        },
        {
            "id": 3,
            "name": "Gỏi Gà Xé Phay",
            "base_price": 60000.0,
            "default_k": 0.022,
            "initial_temp": 58.0,
            "container_type": "FOAM_BOX",
        },
        {
            "id": 4,
            "name": "Nước Sâm Lạnh",
            "base_price": 15000.0,
            "default_k": 0.030,
            "initial_temp": 6.0,
            "container_type": "INSULATED_BAG",
        },
    ]
