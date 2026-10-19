"""
Self-Contained Verification Test Suite for Milestone M1
Tests SQLAlchemy 2.0 ORM models, Pydantic v2 schemas, spatial point geometry creation,
and database seed data validation without external network calls.

Run via:
    pytest backend/tests/test_m1_schemas.py -v
or:
    python backend/tests/test_m1_schemas.py
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from geoalchemy2.elements import WKTElement
from pydantic import ValidationError

# Import ORM Models
from backend.app.models.base import Base
from backend.app.models.restaurant import Restaurant
from backend.app.models.menu_item import MenuItem
from backend.app.models.order import Order
from backend.app.models.order_item import OrderItem
from backend.app.models.shipper import Shipper
from backend.app.models.route_log import RouteLog
from backend.app.models.experiment import ExperimentRun, ExperimentMetric

# Import Pydantic Schemas & Enums
from backend.app.schemas.enums import (
    AlgorithmType,
    ContainerType,
    OrderStatus,
    ShipperStatus,
    VehicleType,
)
from backend.app.schemas.spatial import PointCoordinates, GeoJSONPoint, parse_geometry_to_coords
from backend.app.schemas.restaurant import RestaurantBase, RestaurantCreate, RestaurantResponse
from backend.app.schemas.menu import MenuItemBase, MenuItemCreate, MenuItemResponse
from backend.app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from backend.app.schemas.shipper import ShipperCreate, ShipperResponse
from backend.app.schemas.route_log import RouteLogCreate, RouteLogResponse
from backend.app.schemas.experiment import (
    ExperimentRunCreate,
    ExperimentRunResponse,
    ExperimentMetricCreate,
    ExperimentMetricResponse,
)

# Import Seed Data for Integrity Verification
from backend.app.db.seed import (
    DEPOT_RESTAURANT,
    STANDARD_MENU_ITEMS,
    SAMPLE_SHIPPERS,
    make_wkt_point,
)
from backend.app.core.config import settings
from backend.app.main import create_app


class TestSQLAlchemyModels(unittest.TestCase):
    """Test suite verifying all 8 SQLAlchemy ORM models."""

    def test_restaurant_model_instantiation(self):
        wkt = make_wkt_point(107.2401, 10.9212)
        r = Restaurant(
            id=1,
            name="Quán Bánh Canh Gà Hàng Gòn",
            location=wkt,
            address="QL56, Xã Hàng Gòn",
            open_hours="06:00 - 21:00",
        )
        self.assertEqual(r.name, "Quán Bánh Canh Gà Hàng Gòn")
        self.assertEqual(r.id, 1)
        self.assertIn("Quán Bánh Canh Gà Hàng Gòn", repr(r))
        self.assertEqual(Restaurant.__tablename__, "restaurants")

    def test_menu_item_model_instantiation(self):
        m = MenuItem(
            id=10,
            restaurant_id=1,
            name="Bánh Canh Gà Đặc Biệt",
            base_price=45000.0,
            default_k=0.038,
            initial_temp=88.0,
            container_type="INSULATED_BAG",
        )
        self.assertEqual(m.name, "Bánh Canh Gà Đặc Biệt")
        self.assertEqual(m.base_price, 45000.0)
        self.assertEqual(m.default_k, 0.038)
        self.assertEqual(m.initial_temp, 88.0)
        self.assertIn("Bánh Canh Gà Đặc Biệt", repr(m))
        self.assertEqual(MenuItem.__tablename__, "menu_items")

    def test_order_model_instantiation(self):
        wkt = make_wkt_point(107.2450, 10.9230)
        o = Order(
            id=100,
            order_code="ORD-HG-001",
            customer_name="Lê Văn Khách",
            customer_phone="0909888777",
            delivery_location=wkt,
            status="PENDING",
            container_factor=0.5,
            target_temp=60.0,
            deadline_minutes=35,
            restaurant_id=1,
        )
        self.assertEqual(o.order_code, "ORD-HG-001")
        self.assertEqual(o.status, "PENDING")
        self.assertEqual(o.deadline_minutes, 35)
        self.assertIn("ORD-HG-001", repr(o))
        self.assertEqual(Order.__tablename__, "orders")

    def test_order_item_model_instantiation(self):
        item = OrderItem(
            id=500,
            order_id=100,
            menu_item_id=10,
            quantity=2,
            unit_price=45000.0,
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, 45000.0)
        self.assertIn("qty=2", repr(item))
        self.assertEqual(OrderItem.__tablename__, "order_items")

    def test_shipper_model_instantiation(self):
        wkt = make_wkt_point(107.2401, 10.9212)
        s = Shipper(
            id=5,
            name="Nguyễn Văn Giao",
            phone="0901234567",
            vehicle_type="MOTORBIKE",
            current_location=wkt,
            status="AVAILABLE",
        )
        self.assertEqual(s.name, "Nguyễn Văn Giao")
        self.assertEqual(s.status, "AVAILABLE")
        self.assertIn("Nguyễn Văn Giao", repr(s))
        self.assertEqual(Shipper.__tablename__, "shippers")

    def test_route_log_model_instantiation(self):
        wkt = make_wkt_point(107.2420, 10.9225)
        now = datetime.now(timezone.utc)
        log = RouteLog(
            id=1000,
            order_id=100,
            shipper_id=5,
            waypoint=wkt,
            recorded_at=now,
            temperature_at_point=82.5,
            speed_kmh=32.0,
        )
        self.assertEqual(log.order_id, 100)
        self.assertEqual(log.temperature_at_point, 82.5)
        self.assertEqual(log.speed_kmh, 32.0)
        self.assertIn("speed=32.0", repr(log))
        self.assertEqual(RouteLog.__tablename__, "route_logs")

    def test_experiment_models_instantiation(self):
        run = ExperimentRun(
            id=1,
            run_code="EXP-PPO-001",
            algorithm_type="MASKABLE_PPO",
            scenario_name="RUSH_HOUR_QL56",
        )
        metric = ExperimentMetric(
            id=1,
            run_id=1,
            order_id=100,
            delivered_temp=68.5,
            delay_seconds=0.0,
            total_distance_m=2450.0,
        )
        self.assertEqual(run.run_code, "EXP-PPO-001")
        self.assertEqual(metric.delivered_temp, 68.5)
        self.assertEqual(ExperimentRun.__tablename__, "experiment_runs")
        self.assertEqual(ExperimentMetric.__tablename__, "experiment_metrics")


class TestPydanticSchemas(unittest.TestCase):
    """Test suite verifying Pydantic v2 schemas and validation rules."""

    def test_point_coordinates_valid(self):
        pt = PointCoordinates(lat=10.9212, lon=107.2401)
        self.assertEqual(pt.lat, 10.9212)
        self.assertEqual(pt.lon, 107.2401)
        self.assertEqual(pt.to_wkt(), "POINT(107.2401 10.9212)")
        
        wkt_elem = pt.to_wkt_element()
        self.assertIsInstance(wkt_elem, WKTElement)
        self.assertEqual(wkt_elem.srid, 4326)

    def test_point_coordinates_invalid_bounds(self):
        # Invalid Latitude (> 90 or < -90)
        with self.assertRaises(ValidationError):
            PointCoordinates(lat=95.0, lon=107.2401)
        with self.assertRaises(ValidationError):
            PointCoordinates(lat=-95.0, lon=107.2401)

        # Invalid Longitude (> 180 or < -180)
        with self.assertRaises(ValidationError):
            PointCoordinates(lat=10.9212, lon=185.0)
        with self.assertRaises(ValidationError):
            PointCoordinates(lat=10.9212, lon=-185.0)

    def test_geojson_point(self):
        geojson = GeoJSONPoint(type="Point", coordinates=(107.2401, 10.9212))
        self.assertEqual(geojson.lon, 107.2401)
        self.assertEqual(geojson.lat, 10.9212)

    def test_parse_geometry_to_coords(self):
        # From dict
        coords = parse_geometry_to_coords({"lat": 10.9212, "lon": 107.2401})
        self.assertIsNotNone(coords)
        self.assertEqual(coords.lat, 10.9212)
        self.assertEqual(coords.lon, 107.2401)

        # From GeoJSON dict
        coords_geo = parse_geometry_to_coords({"type": "Point", "coordinates": [107.2401, 10.9212]})
        self.assertIsNotNone(coords_geo)
        self.assertEqual(coords_geo.lat, 10.9212)
        self.assertEqual(coords_geo.lon, 107.2401)

        # From WKT String
        coords_wkt = parse_geometry_to_coords("SRID=4326;POINT(107.2401 10.9212)")
        self.assertIsNotNone(coords_wkt)
        self.assertAlmostEqual(coords_wkt.lat, 10.9212)
        self.assertAlmostEqual(coords_wkt.lon, 107.2401)

    def test_restaurant_schemas(self):
        req = RestaurantCreate(
            name="Quán Bánh Canh Gà Hàng Gòn",
            location=PointCoordinates(lat=10.9212, lon=107.2401),
            address="QL56, Xã Hàng Gòn",
            open_hours="06:00 - 21:00",
        )
        self.assertEqual(req.name, "Quán Bánh Canh Gà Hàng Gòn")

    def test_menu_item_schemas(self):
        item = MenuItemCreate(
            restaurant_id=1,
            name="Bánh Canh Gà Đặc Biệt",
            base_price=45000.0,
            default_k=0.038,
            initial_temp=88.0,
            container_type=ContainerType.INSULATED_BAG,
        )
        self.assertEqual(item.base_price, 45000.0)
        self.assertEqual(item.default_k, 0.038)

        # Negative price must raise ValidationError
        with self.assertRaises(ValidationError):
            MenuItemCreate(
                restaurant_id=1,
                name="Invalid Item",
                base_price=-1000.0,
                default_k=0.038,
                initial_temp=88.0,
                container_type=ContainerType.INSULATED_BAG,
            )

        # Non-positive k must raise ValidationError
        with self.assertRaises(ValidationError):
            MenuItemCreate(
                restaurant_id=1,
                name="Invalid Item",
                base_price=30000.0,
                default_k=-0.01,
                initial_temp=88.0,
                container_type=ContainerType.INSULATED_BAG,
            )

    def test_order_schemas_and_status_update(self):
        order_in = OrderCreate(
            order_code="ORD-HG-001",
            customer_name="Nguyễn Văn A",
            customer_phone="0911222333",
            delivery_location=PointCoordinates(lat=10.9250, lon=107.2450),
            items=[{"menu_item_id": 1, "quantity": 2, "unit_price": 45000.0}],
            deadline_minutes=30,
        )
        self.assertEqual(order_in.order_code, "ORD-HG-001")
        self.assertEqual(len(order_in.items), 1)

        # Status update schema
        status_update = OrderStatusUpdate(status=OrderStatus.DISPATCHED)
        self.assertEqual(status_update.status, OrderStatus.DISPATCHED)

        # Invalid status enum
        with self.assertRaises(ValidationError):
            OrderStatusUpdate(status="FLYING_TO_CUSTOMER")


class TestSeedDataIntegrity(unittest.TestCase):
    """Test suite verifying seed constants against schemas and physical bounds."""

    def test_depot_restaurant_seed_validity(self):
        self.assertEqual(DEPOT_RESTAURANT["name"], "Quán Bánh Canh Gà Hàng Gòn")
        # Ensure within Hàng Gòn coordinate bounds [10.90 - 10.96 N, 107.21 - 107.27 E]
        self.assertTrue(10.90 <= DEPOT_RESTAURANT["lat"] <= 10.96)
        self.assertTrue(107.21 <= DEPOT_RESTAURANT["lon"] <= 107.27)

        # WKT generator test
        wkt = make_wkt_point(DEPOT_RESTAURANT["lon"], DEPOT_RESTAURANT["lat"])
        self.assertIn("POINT(107.2401 10.9212)", str(wkt.data))

    def test_standard_menu_items_physical_properties(self):
        self.assertGreaterEqual(len(STANDARD_MENU_ITEMS), 4)

        dish_names = [d["name"] for d in STANDARD_MENU_ITEMS]
        self.assertIn("Bánh Canh Gà Đặc Biệt", dish_names)
        self.assertIn("Bánh Canh Gà Đùi", dish_names)
        self.assertIn("Gỏi Gà Xé Phay", dish_names)
        self.assertIn("Nước Sâm Lạnh", dish_names)

        for item in STANDARD_MENU_ITEMS:
            # Price must be positive
            self.assertGreater(item["base_price"], 0.0)
            # Cooling rate k must be physically plausible (0.01 <= k <= 0.10)
            self.assertGreater(item["default_k"], 0.0)
            self.assertLessEqual(item["default_k"], 0.10)
            # Temperature must be realistic
            self.assertGreater(item["initial_temp"], 0.0)
            self.assertLess(item["initial_temp"], 100.0)

        # Special check for Bánh Canh Gà Đặc Biệt
        dac_biet = next(d for d in STANDARD_MENU_ITEMS if d["name"] == "Bánh Canh Gà Đặc Biệt")
        self.assertEqual(dac_biet["initial_temp"], 88.0)
        self.assertEqual(dac_biet["default_k"], 0.038)

    def test_sample_shippers_and_containers(self):
        self.assertGreaterEqual(len(SAMPLE_SHIPPERS), 4)
        has_simulated = False
        valid_containers = {c.value for c in ContainerType}

        for shipper in SAMPLE_SHIPPERS:
            self.assertTrue(shipper["phone"].startswith("09"))
            self.assertIn(shipper["container_type"], valid_containers)
            self.assertTrue(10.90 <= shipper["lat"] <= 10.96)
            self.assertTrue(107.21 <= shipper["lon"] <= 107.27)
            if shipper["is_simulated"]:
                has_simulated = True

        self.assertTrue(has_simulated, "Seed shippers must include at least one simulated AI driver")

    def test_fastapi_app_factory_and_settings(self):
        """Verifies that FastAPI application factory initializes cleanly."""
        test_app = create_app()
        self.assertIsNotNone(test_app)
        self.assertEqual(test_app.title, settings.PROJECT_NAME)
        self.assertEqual(settings.DEPOT_NAME, "Quán Bánh Canh Gà Hàng Gòn")
        self.assertTrue(settings.USE_DIJKSTRA_FALLBACK)


def run_tests():
    """Runs all test cases using unittest runner."""
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestSQLAlchemyModels))
    suite.addTests(loader.loadTestsFromTestCase(TestPydanticSchemas))
    suite.addTests(loader.loadTestsFromTestCase(TestSeedDataIntegrity))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
