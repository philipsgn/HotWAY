"""
Master APIRouter uniting all domain-specific routers
"""

from fastapi import APIRouter
from backend.app.api import (
    orders,
    menu,
    shippers,
    dispatch,
    simulation,
    spatial,
    websockets,
)

api_router = APIRouter()

api_router.include_router(menu.router, prefix="/menu", tags=["Menu"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(shippers.router, prefix="/shippers", tags=["Shippers"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["Dispatch & Routing"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["Spatial & GIS"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(websockets.router, tags=["WebSockets"])
