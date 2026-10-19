"""Enumerations for system entities and status fields."""

from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PREPARING = "PREPARING"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ShipperStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class VehicleType(str, Enum):
    MOTORBIKE = "MOTORBIKE"
    BICYCLE = "BICYCLE"
    ELECTRIC_SCOOTER = "ELECTRIC_SCOOTER"


class ContainerType(str, Enum):
    INSULATED_BAG = "INSULATED_BAG"  # alpha = 0.5
    FOAM_BOX = "FOAM_BOX"            # alpha = 0.7
    OPEN_BASKET = "OPEN_BASKET"      # alpha = 1.0


class AlgorithmType(str, Enum):
    MASKABLE_PPO = "MASKABLE_PPO"
    DQN = "DQN"
    Q_LEARNING = "Q_LEARNING"
    DIJKSTRA = "DIJKSTRA"
    OR_TOOLS = "OR_TOOLS"
    GREEDY = "GREEDY"
