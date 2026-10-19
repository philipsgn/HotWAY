"""Database models package initialization and discovery."""

try:
    from backend.app.models.base import Base
    from backend.app.models.restaurant import Restaurant
    from backend.app.models.menu_item import MenuItem
    from backend.app.models.order import Order
    from backend.app.models.order_item import OrderItem
    from backend.app.models.shipper import Shipper
    from backend.app.models.route_log import RouteLog
    from backend.app.models.experiment import ExperimentRun, ExperimentMetric
except ImportError:
    from .base import Base
    from .restaurant import Restaurant
    from .menu_item import MenuItem
    from .order import Order
    from .order_item import OrderItem
    from .shipper import Shipper
    from .route_log import RouteLog
    from .experiment import ExperimentRun, ExperimentMetric

__all__ = [
    "Base",
    "Restaurant",
    "MenuItem",
    "Order",
    "OrderItem",
    "Shipper",
    "RouteLog",
    "ExperimentRun",
    "ExperimentMetric",
]
