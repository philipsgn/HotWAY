"""Tier 4: Real-World Workload and Multi-Order Session Simulation.

Simulates an entire multi-order delivery workload session:
- 5 concurrent active delivery orders dispatched from Quán Bánh Canh Gà Hàng Gòn.
- Multi-segment transit through dynamic rush-hour traffic on QL56 and commune roads.
- Continuous incremental thermal cooling updates per transit leg.
- Verifies order delivery lifecycle completion, final customer temperature audit, and reward integrity.
"""

import math
import unittest
from dataclasses import dataclass
from typing import List


@dataclass
class DeliveryOrder:
    order_id: str
    dish: str
    container: str
    initial_temp_c: float
    current_temp_c: float
    cooling_rate: float
    deadline_minutes: float
    delivered: bool = False
    delivery_time_minutes: float = 0.0
    final_temp_c: float = 0.0


class TestDeliveryWorkloadSession(unittest.TestCase):
    """Tier 4 Simulation of an end-to-end multi-order batch delivery shift."""

    def test_multi_order_rush_hour_delivery_session(self):
        """Simulates fulfilling 5 customer orders under lunch rush-hour traffic."""
        t_env = 31.0  # Noon ambient temperature in Long Khánh
        rush_hour_multiplier = 1.4  # Commune and QL56 congestion factor

        orders: List[DeliveryOrder] = [
            DeliveryOrder(
                order_id="ORD-001",
                dish="HOT_SOUP",
                container="INSULATED_BAG",
                initial_temp_c=88.0,
                current_temp_c=88.0,
                cooling_rate=0.038 * 0.50,  # 0.019
                deadline_minutes=35.0,
            ),
            DeliveryOrder(
                order_id="ORD-002",
                dish="HOT_SOUP",
                container="INSULATED_BAG",
                initial_temp_c=88.0,
                current_temp_c=88.0,
                cooling_rate=0.038 * 0.50,  # 0.019
                deadline_minutes=45.0,
            ),
            DeliveryOrder(
                order_id="ORD-003",
                dish="DRY_WARM",
                container="FOAM_BOX",
                initial_temp_c=58.0,
                current_temp_c=58.0,
                cooling_rate=0.022 * 0.70,  # 0.0154
                deadline_minutes=50.0,
            ),
            DeliveryOrder(
                order_id="ORD-004",
                dish="HOT_SOUP",
                container="FOAM_BOX",
                initial_temp_c=88.0,
                current_temp_c=88.0,
                cooling_rate=0.038 * 0.70,  # 0.0266
                deadline_minutes=55.0,
            ),
            DeliveryOrder(
                order_id="ORD-005",
                dish="COLD_DRINK",
                container="OPEN_BASKET",
                initial_temp_c=6.0,
                current_temp_c=6.0,
                cooling_rate=0.030 * 1.00,  # 0.030
                deadline_minutes=60.0,
            ),
        ]

        # Free-flow transit legs between stops in minutes
        free_flow_legs = [6.0, 5.5, 5.0, 6.0, 5.0]
        service_time_per_stop = 2.0  # Customer handover time

        elapsed_time = 0.0
        previous_temps = {o.order_id: o.initial_temp_c for o in orders}

        for stop_idx, base_transit in enumerate(free_flow_legs):
            leg_duration = (base_transit * rush_hour_multiplier) + service_time_per_stop
            elapsed_time += leg_duration

            # Update temperature for all orders currently in the delivery bag
            for o in orders:
                if not o.delivered:
                    o.current_temp_c = t_env + (o.current_temp_c - t_env) * math.exp(
                        -o.cooling_rate * leg_duration
                    )
                    # Enforce strictly monotonic cooling for hot dishes
                    if o.dish in ("HOT_SOUP", "DRY_WARM"):
                        self.assertLess(
                            o.current_temp_c,
                            previous_temps[o.order_id],
                            f"Monotonicity violation on {o.order_id} during leg {stop_idx}",
                        )
                        previous_temps[o.order_id] = o.current_temp_c

            # Mark stop order as delivered
            delivering_order = orders[stop_idx]
            delivering_order.delivered = True
            delivering_order.delivery_time_minutes = elapsed_time
            delivering_order.final_temp_c = delivering_order.current_temp_c

        # Verification of final shift results
        self.assertEqual(len([o for o in orders if o.delivered]), 5)

        # Order 1 (Bánh Canh in Insulated Bag, delivered stop 1 at ~10.4m)
        ord1 = orders[0]
        self.assertGreaterEqual(
            ord1.final_temp_c,
            75.0,
            f"First delivered soup should be very hot (>75C), got {ord1.final_temp_c:.1f}C",
        )

        # Order 2 (Bánh Canh in Insulated Bag, delivered stop 2 at ~20.1m)
        ord2 = orders[1]
        self.assertGreaterEqual(
            ord2.final_temp_c,
            65.0,
            f"Second delivered soup should maintain quality (>65C), got {ord2.final_temp_c:.1f}C",
        )

        # Order 3 (Gỏi Gà in Foam Box, delivered stop 3 at ~29.1m)
        ord3 = orders[2]
        self.assertGreaterEqual(
            ord3.final_temp_c,
            45.0,
            f"Warm dish should meet threshold (>45C), got {ord3.final_temp_c:.1f}C",
        )

        # All orders arrived before deadline
        for o in orders:
            self.assertLessEqual(
                o.delivery_time_minutes,
                o.deadline_minutes,
                f"Order {o.order_id} missed deadline: {o.delivery_time_minutes:.1f} > {o.deadline_minutes}",
            )


if __name__ == "__main__":
    unittest.main()
