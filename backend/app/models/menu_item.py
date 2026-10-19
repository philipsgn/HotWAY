"""SQLAlchemy model for Menu Items."""

from __future__ import annotations

from typing import TYPE_CHECKING, List
from sqlalchemy import Integer, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.restaurant import Restaurant
        from backend.app.models.order_item import OrderItem
    except ImportError:
        from .restaurant import Restaurant
        from .order_item import OrderItem


class MenuItem(Base):
    """Menu item with thermodynamic parameters for Newton cooling."""

    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("base_price >= 0", name="chk_menu_item_price_positive"),
        CheckConstraint("default_k > 0", name="chk_menu_item_k_positive"),
        CheckConstraint("initial_temp > 0", name="chk_menu_item_temp_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    default_k: Mapped[float] = mapped_column(Float, nullable=False, default=0.038)
    initial_temp: Mapped[float] = mapped_column(Float, nullable=False, default=88.0)
    container_type: Mapped[str] = mapped_column(String(50), nullable=False, default="INSULATED_BAG")

    # Relationships
    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="menu_items")
    order_items: Mapped[List[OrderItem]] = relationship("OrderItem", back_populates="menu_item")

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name='{self.name}', price={self.base_price})>"
