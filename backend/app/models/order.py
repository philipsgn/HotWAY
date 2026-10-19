"""SQLAlchemy model for Orders."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.restaurant import Restaurant
        from backend.app.models.shipper import Shipper
        from backend.app.models.order_item import OrderItem
        from backend.app.models.route_log import RouteLog
        from backend.app.models.experiment import ExperimentMetric
    except ImportError:
        from .restaurant import Restaurant
        from .shipper import Shipper
        from .order_item import OrderItem
        from .route_log import RouteLog
        from .experiment import ExperimentMetric


class Order(Base):
    """Delivery order entity with spatial destination and thermal constraints."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("deadline_minutes > 0", name="chk_order_deadline_positive"),
        CheckConstraint("container_factor > 0", name="chk_order_container_factor_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    order_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    delivery_location: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )
    container_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    target_temp: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)
    deadline_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Optional foreign keys supporting full platform workflow
    restaurant_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("restaurants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_shipper_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("shippers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    restaurant: Mapped[Optional[Restaurant]] = relationship("Restaurant", back_populates="orders")
    shipper: Mapped[Optional[Shipper]] = relationship("Shipper", back_populates="orders")
    order_items: Mapped[List[OrderItem]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    route_logs: Mapped[List[RouteLog]] = relationship(
        "RouteLog", back_populates="order", cascade="all, delete-orphan"
    )
    experiment_metrics: Mapped[List[ExperimentMetric]] = relationship(
        "ExperimentMetric", back_populates="order"
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, code='{self.order_code}', status='{self.status}')>"
