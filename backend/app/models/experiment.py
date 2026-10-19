"""SQLAlchemy models for Experiment Runs and Metrics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.models.base import Base
except ImportError:
    from .base import Base

if TYPE_CHECKING:
    try:
        from backend.app.models.order import Order
    except ImportError:
        from .order import Order


class ExperimentRun(Base):
    """Academic benchmark experiment run record."""

    __tablename__ = "experiment_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    run_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    algorithm_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    metrics: Mapped[List[ExperimentMetric]] = relationship(
        "ExperimentMetric", back_populates="run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ExperimentRun(id={self.id}, code='{self.run_code}', algo='{self.algorithm_type}')>"


class ExperimentMetric(Base):
    """Quantitative evaluation metrics for an order in an experiment run."""

    __tablename__ = "experiment_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    delivered_temp: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delay_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_distance_m: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Relationships
    run: Mapped[ExperimentRun] = relationship("ExperimentRun", back_populates="metrics")
    order: Mapped[Optional[Order]] = relationship("Order", back_populates="experiment_metrics")

    def __repr__(self) -> str:
        return f"<ExperimentMetric(id={self.id}, run_id={self.run_id}, temp={self.delivered_temp})>"
