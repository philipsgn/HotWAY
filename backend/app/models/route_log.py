"""SQLAlchemy model for Route Logs."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.order import Order
        from backend.app.models.shipper import Shipper
    except ImportError:
        from .order import Order
        from .shipper import Shipper


class RouteLog(Base):
    """Spatial waypoint breadcrumb recorded during delivery."""

    __tablename__ = "route_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    shipper_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("shippers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    waypoint: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    temperature_at_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="route_logs")
    shipper: Mapped[Optional[Shipper]] = relationship("Shipper", back_populates="route_logs")

    def __repr__(self) -> str:
        return f"<RouteLog(id={self.id}, order_id={self.order_id}, speed={self.speed_kmh})>"
