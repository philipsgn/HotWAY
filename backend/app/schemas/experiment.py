"""Pydantic schemas for Experiment Runs and Metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

try:
    from backend.app.schemas.enums import AlgorithmType
except ImportError:
    from .enums import AlgorithmType


class ExperimentRunBase(BaseModel):
    run_code: str = Field(..., max_length=100)
    algorithm_type: AlgorithmType
    scenario_name: str = Field(..., max_length=100)


class ExperimentRunCreate(ExperimentRunBase):
    pass


class ExperimentMetricCreate(BaseModel):
    order_id: Optional[int] = None
    delivered_temp: Optional[float] = None
    delay_seconds: float = Field(default=0.0, ge=0.0)
    total_distance_m: float = Field(default=0.0, ge=0.0)


class ExperimentMetricResponse(BaseModel):
    id: int
    run_id: int
    order_id: Optional[int] = None
    delivered_temp: Optional[float] = None
    delay_seconds: float
    total_distance_m: float

    model_config = ConfigDict(from_attributes=True)


class ExperimentRunResponse(ExperimentRunBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentRunDetailResponse(ExperimentRunResponse):
    metrics: List[ExperimentMetricResponse] = Field(default_factory=list)
