"""
Rule-Based Baselines for HotWAY GĐ2:
1. ImmediateDispatch (Myopic Greedy)
2. PeriodicDispatch (Fixed Interval T minutes)
3. BatchSizeDispatch (Fixed Batch Size k orders)
4. AgeThresholdDispatch (Max Order Age Threshold theta_age minutes)
5. OfflinePrescientReference (OR-Tools Prescient Scheduler)
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
import numpy as np


class BaseDispatchPolicy:
    def __init__(self, name: str):
        self.name = name

    def select_action(self, env: Any, obs: np.ndarray) -> int:
        raise NotImplementedError


class ImmediateDispatchPolicy(BaseDispatchPolicy):
    """Dispatches available idle driver as soon as any order is READY (up to capacity Q)."""
    def __init__(self, capacity: int = 4):
        super().__init__("Immediate")
        self.capacity = capacity

    def select_action(self, env: Any, obs: np.ndarray) -> int:
        ready_count = sum(1 for o in env.orders if o["state"] == "READY")
        if ready_count > 0:
            return min(self.capacity, ready_count)
        return 0


class PeriodicDispatchPolicy(BaseDispatchPolicy):
    """Dispatches every T minutes if ready orders exist."""
    def __init__(self, interval_min: float = 12.0, capacity: int = 4):
        super().__init__(f"Periodic_T{interval_min}")
        self.interval_min = interval_min
        self.capacity = capacity
        self.last_dispatch_time = 0.0

    def select_action(self, env: Any, obs: np.ndarray) -> int:
        ready_count = sum(1 for o in env.orders if o["state"] == "READY")
        if ready_count == 0:
            return 0

        # In Drain phase (t >= day_length_min), dispatch immediately
        if env.current_time >= env.day_length_min:
            return min(self.capacity, ready_count)

        if (env.current_time - self.last_dispatch_time) >= self.interval_min or ready_count >= self.capacity:
            self.last_dispatch_time = env.current_time
            return min(self.capacity, ready_count)
        return 0


class BatchSizeDispatchPolicy(BaseDispatchPolicy):
    """Dispatches only when at least k orders are READY (or in drain phase)."""
    def __init__(self, batch_k: int = 3, capacity: int = 4):
        super().__init__(f"Batch_k{batch_k}")
        self.batch_k = batch_k
        self.capacity = capacity

    def select_action(self, env: Any, obs: np.ndarray) -> int:
        ready_count = sum(1 for o in env.orders if o["state"] == "READY")
        if ready_count == 0:
            return 0

        # In Drain phase or if queue satisfies k or capacity
        if env.current_time >= env.day_length_min or ready_count >= self.batch_k:
            return min(self.capacity, ready_count)
        return 0


class AgeThresholdDispatchPolicy(BaseDispatchPolicy):
    """Dispatches when oldest ready order exceeds age threshold theta or queue reaches Q."""
    def __init__(self, theta_age_min: float = 20.0, capacity: int = 4):
        super().__init__(f"AgeThreshold_theta{theta_age_min}")
        self.theta_age_min = theta_age_min
        self.capacity = capacity

    def select_action(self, env: Any, obs: np.ndarray) -> int:
        ready_orders = [o for o in env.orders if o["state"] == "READY"]
        if not ready_orders:
            return 0

        # In Drain phase
        if env.current_time >= env.day_length_min or len(ready_orders) >= self.capacity:
            return min(self.capacity, len(ready_orders))

        max_age = max(env.current_time - o["placed_time"] for o in ready_orders)
        if max_age >= self.theta_age_min:
            return min(self.capacity, len(ready_orders))
        return 0
