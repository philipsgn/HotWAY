"""SQLAlchemy model for Shippers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.order import Order
        from backend.app.models.route_log import RouteLog
    except ImportError:
        from .order import Order
        from .route_log import RouteLog


class Shipper(Base):
    """Shipper driver entity with location and availability status."""

    __tablename__ = "shippers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False, default="MOTORBIKE")
    current_location: Mapped[Optional[object]] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AVAILABLE", index=True
    )

    # Relationships
    orders: Mapped[List[Order]] = relationship("Order", back_populates="shipper")
    route_logs: Mapped[List[RouteLog]] = relationship("RouteLog", back_populates="shipper")

    def __repr__(self) -> str:
        return f"<Shipper(id={self.id}, name='{self.name}', status='{self.status}')>"
