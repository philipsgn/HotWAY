"""SQLAlchemy model for Restaurants."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.menu_item import MenuItem
        from backend.app.models.order import Order
    except ImportError:
        from .menu_item import MenuItem
        from .order import Order


class Restaurant(Base):
    """Restaurant entity representing a depot/kitchen location."""

    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    open_hours: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    menu_items: Mapped[List[MenuItem]] = relationship(
        "MenuItem", back_populates="restaurant", cascade="all, delete-orphan"
    )
    orders: Mapped[List[Order]] = relationship("Order", back_populates="restaurant")

    def __repr__(self) -> str:
        return f"<Restaurant(id={self.id}, name='{self.name}')>"
