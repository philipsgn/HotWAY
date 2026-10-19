"""Pydantic schemas package initialization."""

try:
    from backend.app.schemas.spatial import PointCoordinates, GeoJSONPoint, parse_geometry_to_coords
    from backend.app.schemas.enums import (
        OrderStatus,
        ShipperStatus,
        VehicleType,
        ContainerType,
        AlgorithmType,
    )
    from backend.app.schemas.restaurant import (
        RestaurantBase,
        RestaurantCreate,
        RestaurantUpdate,
        RestaurantResponse,
    )
    from backend.app.schemas.menu import (
        MenuItemBase,
        MenuItemCreate,
        MenuItemUpdate,
        MenuItemResponse,
    )
    from backend.app.schemas.order import (
        OrderItemCreate,
        OrderItemResponse,
        OrderCreate,
        OrderStatusUpdate,
        OrderResponse,
        OrderDetailResponse,
    )
    from backend.app.schemas.shipper import (
        ShipperBase,
        ShipperCreate,
        ShipperLocationUpdate,
        ShipperResponse,
    )
    from backend.app.schemas.route_log import (
        RouteLogCreate,
        RouteLogResponse,
    )
    from backend.app.schemas.experiment import (
        ExperimentRunBase,
        ExperimentRunCreate,
        ExperimentRunResponse,
        ExperimentRunDetailResponse,
        ExperimentMetricCreate,
        ExperimentMetricResponse,
    )
except ImportError:
    from .spatial import PointCoordinates, GeoJSONPoint, parse_geometry_to_coords
    from .enums import (
        OrderStatus,
        ShipperStatus,
        VehicleType,
        ContainerType,
        AlgorithmType,
    )
    from .restaurant import (
        RestaurantBase,
        RestaurantCreate,
        RestaurantUpdate,
        RestaurantResponse,
    )
    from .menu import (
        MenuItemBase,
        MenuItemCreate,
        MenuItemUpdate,
        MenuItemResponse,
    )
    from .order import (
        OrderItemCreate,
        OrderItemResponse,
        OrderCreate,
        OrderStatusUpdate,
        OrderResponse,
        OrderDetailResponse,
    )
    from .shipper import (
        ShipperBase,
        ShipperCreate,
        ShipperLocationUpdate,
        ShipperResponse,
    )
    from .route_log import (
        RouteLogCreate,
        RouteLogResponse,
    )
    from .experiment import (
        ExperimentRunBase,
        ExperimentRunCreate,
        ExperimentRunResponse,
        ExperimentRunDetailResponse,
        ExperimentMetricCreate,
        ExperimentMetricResponse,
    )

__all__ = [
    "PointCoordinates",
    "GeoJSONPoint",
    "parse_geometry_to_coords",
    "OrderStatus",
    "ShipperStatus",
    "VehicleType",
    "ContainerType",
    "AlgorithmType",
    "RestaurantBase",
    "RestaurantCreate",
    "RestaurantUpdate",
    "RestaurantResponse",
    "MenuItemBase",
    "MenuItemCreate",
    "MenuItemUpdate",
    "MenuItemResponse",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderCreate",
    "OrderStatusUpdate",
    "OrderResponse",
    "OrderDetailResponse",
    "ShipperBase",
    "ShipperCreate",
    "ShipperLocationUpdate",
    "ShipperResponse",
    "RouteLogCreate",
    "RouteLogResponse",
    "ExperimentRunBase",
    "ExperimentRunCreate",
    "ExperimentRunResponse",
    "ExperimentRunDetailResponse",
    "ExperimentMetricCreate",
    "ExperimentMetricResponse",
]
