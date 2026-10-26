"""
Traffic Provider Module for HotWAY.
Supports Synthetic Markov model, Replay simulation, and Live API provider.
"""

from src.traffic.provider import (
    TrafficState,
    TrafficProvider,
    SyntheticProvider,
    ReplayProvider,
    LiveProvider,
)

__all__ = [
    "TrafficState",
    "TrafficProvider",
    "SyntheticProvider",
    "ReplayProvider",
    "LiveProvider",
]
