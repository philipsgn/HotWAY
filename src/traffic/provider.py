"""
Traffic Providers for Urban Motorbike Delivery Routing (HotWAY G2).
Implements Synthetic (3-state Markov + rain + noise), Replay, and Live traffic interfaces.
"""

from __future__ import annotations

import json
import math
import os
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class TrafficState(IntEnum):
    CLEAR = 0       # Thông thoáng (~32 km/h đường chính)
    SLOW = 1        # Chậm (~18 km/h đường chính)
    CONGESTED = 2   # Kẹt xe (~8 km/h đường chính)


BASE_SPEEDS_KMH: Dict[str, float] = {
    "primary": 32.0,
    "primary_link": 28.0,
    "secondary": 28.0,
    "secondary_link": 24.0,
    "tertiary": 24.0,
    "tertiary_link": 20.0,
    "residential": 20.0,
    "living_street": 14.0,
    "service": 14.0,
    "unclassified": 20.0,
    "default": 22.0,
}

STATE_SPEED_FACTORS = {
    TrafficState.CLEAR: 1.0,
    TrafficState.SLOW: 0.5625,   # 32.0 * 0.5625 = 18.0 km/h
    TrafficState.CONGESTED: 0.25, # 32.0 * 0.25 = 8.0 km/h
}


class TrafficProvider(ABC):
    """Abstract base class for all traffic speed providers."""

    @abstractmethod
    def reset(self, seed: Optional[int] = None) -> None:
        """Resets stochastic states with an optional reproducible seed."""
        pass

    @abstractmethod
    def get_edge_speed_kph(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        """Returns the instantaneous speed (km/h) for directed edge (u, v)."""
        pass

    @abstractmethod
    def get_edge_travel_time_sec(
        self,
        u: int,
        v: int,
        length_m: float,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        """Returns the instantaneous travel time in seconds for directed edge (u, v)."""
        pass

    @abstractmethod
    def get_edge_state(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
    ) -> TrafficState:
        """Returns the discrete 3-state congestion level for edge (u, v)."""
        pass

    @abstractmethod
    def get_provider_label(self) -> str:
        """Returns the UI audit label: 'MÔ PHỎNG', 'REPLAY', or 'LIVE'."""
        pass


class SyntheticProvider(TrafficProvider):
    """
    Synthetic Traffic Model for HCMC:
    - 3-State Markov process (Clear, Slow, Congested)
    - Time-of-day dynamics (Morning/Evening peak hours)
    - Random road incidents
    - Rain degradation factor (eta_rain = 1.40)
    - Multiplicative Log-Normal travel time noise
    """

    def __init__(
        self,
        seed: Optional[int] = 2026,
        noise_sigma: float = 0.20,
        rain_factor: float = 1.40,
        incident_prob: float = 0.03,
        min_speed_kph: float = 3.0,
        max_speed_kph: float = 50.0,
    ):
        self.noise_sigma = noise_sigma
        self.rain_factor = rain_factor
        self.incident_prob = incident_prob
        self.min_speed_kph = min_speed_kph
        self.max_speed_kph = max_speed_kph
        self.current_seed = seed
        self.rng = np.random.default_rng(seed)

        # Edge state tracking: key=(u, v) -> (TrafficState, expiration_min)
        self._edge_states: Dict[Tuple[int, int], TrafficState] = {}
        self._active_incidents: Dict[Tuple[int, int], float] = {}

        # Markov transition matrices P(s' | s)
        # Normal hours
        self.trans_normal = np.array([
            [0.85, 0.12, 0.03],  # CLEAR -> CLEAR, SLOW, CONGESTED
            [0.25, 0.65, 0.10],  # SLOW  -> CLEAR, SLOW, CONGESTED
            [0.10, 0.35, 0.55],  # CONGESTED -> CLEAR, SLOW, CONGESTED
        ], dtype=float)

        # Peak hours (7:00-9:00 = 420-540 min; 17:00-19:00 = 1020-1140 min)
        self.trans_peak = np.array([
            [0.60, 0.30, 0.10],  # CLEAR -> CLEAR, SLOW, CONGESTED
            [0.10, 0.60, 0.30],  # SLOW  -> CLEAR, SLOW, CONGESTED
            [0.05, 0.25, 0.70],  # CONGESTED -> CLEAR, SLOW, CONGESTED
        ], dtype=float)

    def reset(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            self.current_seed = seed
        self.rng = np.random.default_rng(self.current_seed)
        self._edge_states.clear()
        self._active_incidents.clear()

    def is_peak_hour(self, time_of_day_min: float) -> bool:
        """Determines if the current time falls within HCMC peak traffic hours."""
        t = time_of_day_min % 1440.0
        # Morning peak: 7:00 - 9:00 (420 to 540 min)
        # Evening peak: 17:00 - 19:00 (1020 to 1140 min)
        return (420.0 <= t <= 540.0) or (1020.0 <= t <= 1140.0)

    def _sample_next_state(
        self,
        current_state: TrafficState,
        is_peak: bool,
        is_arterial: bool,
    ) -> TrafficState:
        """Samples next Markov state based on time and road arterial status."""
        P = self.trans_peak if is_peak else self.trans_normal
        row = P[int(current_state)].copy()

        # If arterial road during peak, increase congestion transition
        if is_peak and is_arterial:
            row[TrafficState.CONGESTED] += 0.08
            row[TrafficState.CLEAR] = max(0.01, row[TrafficState.CLEAR] - 0.08)
            row /= np.sum(row)

        next_val = self.rng.choice([0, 1, 2], p=row)
        return TrafficState(next_val)

    def get_edge_state(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
    ) -> TrafficState:
        edge_key = (u, v)

        # Check active incident
        if edge_key in self._active_incidents:
            if time_of_day_min <= self._active_incidents[edge_key]:
                return TrafficState.CONGESTED
            else:
                del self._active_incidents[edge_key]

        # Check random incident trigger
        if self.rng.random() < self.incident_prob:
            duration = float(self.rng.uniform(5.0, 20.0))
            self._active_incidents[edge_key] = time_of_day_min + duration
            self._edge_states[edge_key] = TrafficState.CONGESTED
            return TrafficState.CONGESTED

        current_state = self._edge_states.get(edge_key, TrafficState.CLEAR)
        is_peak = self.is_peak_hour(time_of_day_min)
        is_arterial = ("primary" in highway) or ("secondary" in highway)

        next_state = self._sample_next_state(current_state, is_peak, is_arterial)
        self._edge_states[edge_key] = next_state
        return next_state

    def get_edge_speed_kph(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        base_speed = BASE_SPEEDS_KMH.get(highway, BASE_SPEEDS_KMH["default"])
        state = self.get_edge_state(u, v, highway, time_of_day_min)
        factor = STATE_SPEED_FACTORS[state]

        speed = base_speed * factor

        if rain:
            speed /= self.rain_factor

        # Add log-normal stochastic perturbation if noise_sigma > 0
        if self.noise_sigma > 0.0:
            noise = float(self.rng.normal(0.0, self.noise_sigma))
            speed *= math.exp(-noise)  # Noise inflates time -> deflates speed

        return float(np.clip(speed, self.min_speed_kph, self.max_speed_kph))

    def get_edge_travel_time_sec(
        self,
        u: int,
        v: int,
        length_m: float,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        speed_kph = self.get_edge_speed_kph(u, v, highway, time_of_day_min, rain)
        speed_mps = speed_kph / 3.6
        return float(length_m / speed_mps)

    def get_provider_label(self) -> str:
        return "MÔ PHỎNG"


class ReplayProvider(TrafficProvider):
    """
    Replay Traffic Provider:
    Loads pre-recorded traffic snapshots from JSON or NPZ files to guarantee 100% determinism.
    """

    def __init__(self, snapshot_path: Optional[str] = None):
        self.snapshot_path = snapshot_path
        self.snapshots: Dict[int, Dict[str, Any]] = {}
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "r", encoding="utf-8") as f:
                self.snapshots = json.load(f)

    def reset(self, seed: Optional[int] = None) -> None:
        pass

    def get_edge_state(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
    ) -> TrafficState:
        t_key = str(int(time_of_day_min))
        edge_key = f"{u}->{v}"
        if t_key in self.snapshots and edge_key in self.snapshots[t_key]:
            val = self.snapshots[t_key][edge_key].get("state", 0)
            return TrafficState(val)
        return TrafficState.CLEAR

    def get_edge_speed_kph(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        t_key = str(int(time_of_day_min))
        edge_key = f"{u}->{v}"
        if t_key in self.snapshots and edge_key in self.snapshots[t_key]:
            return float(self.snapshots[t_key][edge_key].get("speed_kph", 22.0))

        base_speed = BASE_SPEEDS_KMH.get(highway, BASE_SPEEDS_KMH["default"])
        return base_speed if not rain else base_speed / 1.40

    def get_edge_travel_time_sec(
        self,
        u: int,
        v: int,
        length_m: float,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        speed_kph = self.get_edge_speed_kph(u, v, highway, time_of_day_min, rain)
        speed_mps = speed_kph / 3.6
        return float(length_m / speed_mps)

    def get_provider_label(self) -> str:
        return "REPLAY"


class LiveProvider(TrafficProvider):
    """
    Live API Traffic Provider (TomTom / VietMap / HERE stub).
    Falls back gracefully to SyntheticProvider when no valid API key is available.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HOTWAY_TRAFFIC_API_KEY")
        self._fallback = SyntheticProvider(seed=2026)

    def reset(self, seed: Optional[int] = None) -> None:
        self._fallback.reset(seed)

    def get_compliance_disclaimer(self) -> str:
        return (
            "CẢNH BÁO TUÂN THỦ DỮ LIỆU: API giao thông trực tiếp chỉ được dùng hiển thị "
            "thời gian thực; không được lưu trữ vĩnh viễn dữ liệu bản quyền thương mại."
        )

    def get_edge_state(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
    ) -> TrafficState:
        # Fallback to synthetic if no valid live key
        return self._fallback.get_edge_state(u, v, highway, time_of_day_min)

    def get_edge_speed_kph(
        self,
        u: int,
        v: int,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        return self._fallback.get_edge_speed_kph(u, v, highway, time_of_day_min, rain)

    def get_edge_travel_time_sec(
        self,
        u: int,
        v: int,
        length_m: float,
        highway: str = "residential",
        time_of_day_min: float = 480.0,
        rain: bool = False,
    ) -> float:
        return self._fallback.get_edge_travel_time_sec(u, v, length_m, highway, time_of_day_min, rain)

    def get_provider_label(self) -> str:
        return "LIVE" if self.api_key else "MÔ PHỎNG (FALLBACK)"
