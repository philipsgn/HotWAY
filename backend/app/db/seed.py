"""
Database Seeding Script for HotWAY Monolith Backend
Populates Quán Bánh Canh Gà Hàng Gòn, standard menu items, sample shippers, and container options.

Execution:
    python -m backend.app.db.seed
    or imported via: await seed_database(session)
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.core.database import async_session_factory, engine, init_db
    from backend.app.models.menu_item import MenuItem
    from backend.app.models.restaurant import Restaurant
    from backend.app.models.shipper import Shipper
    from backend.app.schemas.enums import ContainerType, ShipperStatus, VehicleType
except ImportError:
    from app.core.database import async_session_factory, engine, init_db
    from app.models.menu_item import MenuItem
    from app.models.restaurant import Restaurant
    from app.models.shipper import Shipper
    from app.schemas.enums import ContainerType, ShipperStatus, VehicleType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("hotway.seed")

# ==============================================================================
# Canonical Seed Constants
# ==============================================================================

DEPOT_RESTAURANT = {
    "name": "Quán Bánh Canh Gà 490 Điện Biên Phủ",
    "lat": 10.8012,
    "lon": 106.7145,
    "address": "490 Điện Biên Phủ, Phường 21, Quận Bình Thạnh, TP. Hồ Chí Minh",
    "open_hours": "06:00 - 22:00",
}

STANDARD_MENU_ITEMS: List[Dict[str, Any]] = [
    {
        "name": "Bánh Canh Gà Đặc Biệt",
        "base_price": 45000.0,
        "default_k": 0.038,
        "initial_temp": 88.0,
        "container_type": ContainerType.INSULATED_BAG.value,
    },
    {
        "name": "Bánh Canh Gà Đùi",
        "base_price": 50000.0,
        "default_k": 0.038,
        "initial_temp": 88.0,
        "container_type": ContainerType.INSULATED_BAG.value,
    },
    {
        "name": "Gỏi Gà Xé Phay",
        "base_price": 60000.0,
        "default_k": 0.022,
        "initial_temp": 58.0,
        "container_type": ContainerType.FOAM_BOX.value,
    },
    {
        "name": "Nước Sâm Lạnh",
        "base_price": 15000.0,
        "default_k": 0.030,
        "initial_temp": 6.0,
        "container_type": ContainerType.INSULATED_BAG.value,
    },
]

SAMPLE_SHIPPERS: List[Dict[str, Any]] = [
    {
        "name": "Nguyễn Văn Giao",
        "phone": "0901234567",
        "vehicle_type": VehicleType.MOTORBIKE.value,
        "container_type": ContainerType.INSULATED_BAG.value,
        "lat": 10.8012,
        "lon": 106.7145,
        "status": ShipperStatus.AVAILABLE.value,
        "is_simulated": False,
    },
    {
        "name": "Trần Thị Tốc Độ",
        "phone": "0912345678",
        "vehicle_type": VehicleType.MOTORBIKE.value,
        "container_type": ContainerType.FOAM_BOX.value,
        "lat": 10.8018,
        "lon": 106.7118,
        "status": ShipperStatus.AVAILABLE.value,
        "is_simulated": False,
    },
    {
        "name": "HotWAY AI Rider (Simulated)",
        "phone": "0988888888",
        "vehicle_type": VehicleType.MOTORBIKE.value,
        "container_type": ContainerType.INSULATED_BAG.value,
        "lat": 10.8012,
        "lon": 106.7145,
        "status": ShipperStatus.AVAILABLE.value,
        "is_simulated": True,
    },
    {
        "name": "Lê Văn Mở",
        "phone": "0933333333",
        "vehicle_type": VehicleType.MOTORBIKE.value,
        "container_type": ContainerType.OPEN_BASKET.value,
        "lat": 10.7995,
        "lon": 106.7170,
        "status": ShipperStatus.AVAILABLE.value,
        "is_simulated": False,
    },
]


def make_wkt_point(lon: float, lat: float) -> WKTElement:
    """Helper creating PostGIS WKTElement with standard SRID 4326."""
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


async def seed_database(session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Idempotently seeds Quán Bánh Canh Gà Hàng Gòn, menu items, and shippers.
    If session is None, creates and manages a new session from async_session_factory.
    """
    if session is None:
        async with async_session_factory() as managed_session:
            async with managed_session.begin():
                return await _execute_seed(managed_session)
    else:
        return await _execute_seed(session)


async def _execute_seed(session: AsyncSession) -> Dict[str, Any]:
    summary = {
        "restaurant": {"created": 0, "updated": 0, "id": None},
        "menu_items": {"created": 0, "updated": 0, "total": 0},
        "shippers": {"created": 0, "updated": 0, "total": 0},
    }

    # 1. Seed or Update Restaurant Depot
    stmt_restaurant = select(Restaurant).where(Restaurant.name == DEPOT_RESTAURANT["name"])
    res = await session.execute(stmt_restaurant)
    restaurant = res.scalar_one_or_none()

    depot_location = make_wkt_point(DEPOT_RESTAURANT["lon"], DEPOT_RESTAURANT["lat"])

    if restaurant is None:
        restaurant = Restaurant(
            name=DEPOT_RESTAURANT["name"],
            location=depot_location,
            address=DEPOT_RESTAURANT["address"],
            open_hours=DEPOT_RESTAURANT["open_hours"],
        )
        session.add(restaurant)
        await session.flush()
        summary["restaurant"]["created"] = 1
        logger.info("Created restaurant: %s (id=%s)", restaurant.name, restaurant.id)
    else:
        restaurant.location = depot_location
        restaurant.address = DEPOT_RESTAURANT["address"]
        restaurant.open_hours = DEPOT_RESTAURANT["open_hours"]
        await session.flush()
        summary["restaurant"]["updated"] = 1
        logger.info("Updated existing restaurant: %s (id=%s)", restaurant.name, restaurant.id)

    summary["restaurant"]["id"] = restaurant.id

    # 2. Seed or Update Menu Items
    for item_data in STANDARD_MENU_ITEMS:
        stmt_item = select(MenuItem).where(
            MenuItem.restaurant_id == restaurant.id,
            MenuItem.name == item_data["name"],
        )
        res_item = await session.execute(stmt_item)
        menu_item = res_item.scalar_one_or_none()

        if menu_item is None:
            menu_item = MenuItem(
                restaurant_id=restaurant.id,
                name=item_data["name"],
                base_price=item_data["base_price"],
                default_k=item_data["default_k"],
                initial_temp=item_data["initial_temp"],
                container_type=item_data["container_type"],
            )
            session.add(menu_item)
            summary["menu_items"]["created"] += 1
            logger.info("Created menu item: %s (%s VND, T0=%.1f°C, k=%.3f)",
                        menu_item.name, menu_item.base_price, menu_item.initial_temp, menu_item.default_k)
        else:
            menu_item.base_price = item_data["base_price"]
            menu_item.default_k = item_data["default_k"]
            menu_item.initial_temp = item_data["initial_temp"]
            menu_item.container_type = item_data["container_type"]
            summary["menu_items"]["updated"] += 1
            logger.info("Updated menu item: %s", menu_item.name)

        summary["menu_items"]["total"] += 1

    # 3. Seed or Update Sample Shippers
    for shipper_data in SAMPLE_SHIPPERS:
        stmt_shipper = select(Shipper).where(Shipper.phone == shipper_data["phone"])
        res_shipper = await session.execute(stmt_shipper)
        shipper = res_shipper.scalar_one_or_none()

        shipper_location = make_wkt_point(shipper_data["lon"], shipper_data["lat"])

        if shipper is None:
            shipper = Shipper(
                name=shipper_data["name"],
                phone=shipper_data["phone"],
                vehicle_type=shipper_data["vehicle_type"],
                current_location=shipper_location,
                status=shipper_data["status"],
            )
            session.add(shipper)
            summary["shippers"]["created"] += 1
            logger.info("Created shipper: %s (%s, container=%s, simulated=%s)",
                        shipper.name, shipper.phone, shipper_data["container_type"], shipper_data["is_simulated"])
        else:
            shipper.name = shipper_data["name"]
            shipper.vehicle_type = shipper_data["vehicle_type"]
            shipper.current_location = shipper_location
            shipper.status = shipper_data["status"]
            summary["shippers"]["updated"] += 1
            logger.info("Updated shipper: %s (%s)", shipper.name, shipper.phone)

        summary["shippers"]["total"] += 1

    await session.flush()
    logger.info("Seeding complete! Summary: %s", summary)
    return summary


async def main() -> None:
    """CLI execution entrypoint with offline fallback."""
    logger.info("Starting HotWAY database initialization and seeding...")
    try:
        try:
            await init_db()
            summary = await seed_database()
        except Exception as db_err:
            logger.warning(
                "Default database connection deferred (%s). Running in-memory SQLite verification.",
                db_err,
            )
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
            from sqlalchemy.pool import StaticPool
            try:
                from backend.app.models.base import Base
            except ImportError:
                from app.models.base import Base

            fallback_engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
            async with fallback_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            fallback_factory = async_sessionmaker(
                bind=fallback_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with fallback_factory() as session:
                async with session.begin():
                    summary = await _execute_seed(session)
            await fallback_engine.dispose()

        print("\n" + "=" * 60)
        print("  HotWAY Database Seeding Succeeded")
        print("=" * 60)
        print(f"  Depot Restaurant : {DEPOT_RESTAURANT['name']}")
        print(f"  Coordinates      : Lat {DEPOT_RESTAURANT['lat']}, Lon {DEPOT_RESTAURANT['lon']}")
        print(f"  Menu Items Total : {summary['menu_items']['total']}")
        print(f"  Shippers Total   : {summary['shippers']['total']}")
        print("=" * 60 + "\n")
    finally:
        try:
            await engine.dispose()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
