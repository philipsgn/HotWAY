"""
Real-Time RL Restaurant Dispatch API (Gate G6).
Streams discrete-event simulation from DispatchEnv via Server-Sent Events (SSE).
Supports policy selection (Immediate, Periodic, AgeThreshold, DQN, Double DQN, PPO),
surge injection, rain toggle (1.4x), parallel execution, and explainability reasoning.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncGenerator

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

import numpy as np
import torch

from src.envs.dispatch_env import DispatchEnv
from src.agents.dqn_dispatch import DQNAgent
from src.agents.ppo_dispatch import PPOAgent
from src.baselines.rule_baselines import (
    ImmediateDispatchPolicy,
    PeriodicDispatchPolicy,
    BatchSizeDispatchPolicy,
    AgeThresholdDispatchPolicy,
)

router = APIRouter(prefix="/sim", tags=["Real-Time Simulation & Dispatch"])

# Cache loaded agents
_AGENT_CACHE: Dict[str, Any] = {}


def get_agent_policy(policy_name: str, seed: int = 2026):
    """Loads and caches policy or neural agent."""
    p_lower = policy_name.lower().replace("-", "_").replace(" ", "_")
    
    if "immediate" in p_lower:
        return ImmediateDispatchPolicy()
    elif "periodic" in p_lower:
        return PeriodicDispatchPolicy(interval_min=8.0)
    elif "batch" in p_lower:
        return BatchSizeDispatchPolicy(batch_k=1)
    elif "age" in p_lower or "threshold" in p_lower:
        return AgeThresholdDispatchPolicy(theta_age_min=10.0)
    
    # RL Agents
    cache_key = f"{p_lower}_{seed}"
    if cache_key in _AGENT_CACHE:
        return _AGENT_CACHE[cache_key]
    
    weights_dir = Path("results/training")
    if "double" in p_lower:
        agent = DQNAgent(state_dim=12, action_dim=5, is_double=True, name="Double_DQN")
        pt_file = weights_dir / f"double_dqn_seed_{seed}.pt"
        if not pt_file.exists():
            pt_file = weights_dir / "double_dqn_seed_2026.pt"
        if pt_file.exists():
            agent.load(pt_file)
        _AGENT_CACHE[cache_key] = agent
        return agent
    elif "dqn" in p_lower:
        agent = DQNAgent(state_dim=12, action_dim=5, is_double=False, name="DQN")
        pt_file = weights_dir / f"dqn_seed_{seed}.pt"
        if not pt_file.exists():
            pt_file = weights_dir / "dqn_seed_2026.pt"
        if pt_file.exists():
            agent.load(pt_file)
        _AGENT_CACHE[cache_key] = agent
        return agent
    elif "ppo" in p_lower:
        agent = PPOAgent(state_dim=12, action_dim=5, name="PPO")
        pt_file = weights_dir / f"ppo_seed_{seed}.pt"
        if not pt_file.exists():
            pt_file = weights_dir / "ppo_seed_2026.pt"
        if pt_file.exists():
            agent.load(pt_file)
        _AGENT_CACHE[cache_key] = agent
        return agent
    
    return ImmediateDispatchPolicy()


def compute_action_and_reason(policy: Any, obs: np.ndarray, env: DispatchEnv) -> tuple[int, str]:
    """Computes action and human-readable explainability reasoning."""
    n_ready = int(round(obs[0] * 10.0))
    n_cooking = int(round(obs[1] * 10.0))
    wait_ready_max = obs[4] * 60.0
    sigma_spatial = obs[6] * 5.0
    lambda_recent = obs[11] * 2.0

    if hasattr(policy, "select_action"):
        if isinstance(policy, DQNAgent):
            action = policy.select_action(obs, epsilon=0.0)
        elif isinstance(policy, PPOAgent):
            action, _, _ = policy.select_action(obs)
        else:
            action = policy.select_action(env, obs)
    else:
        action = 1 if n_ready > 0 else 0

    # Reason generation
    if action == 0:
        if n_ready == 0:
            reason = f"Chờ thêm: Hiện chưa có đơn nấu xong (Ready=0, Đang nấu={n_cooking})."
        elif n_cooking > 0 and wait_ready_max < 10.0:
            reason = f"Chờ thêm để gom cụm: Có {n_cooking} đơn sắp xong, tuổi đơn lớn nhất mới {wait_ready_max:.1f}m (độ phân tán {sigma_spatial:.1f}km)."
        else:
            reason = f"Chờ nhịp chuyển tiếp kế tiếp: Tốc độ đến hiện tại {lambda_recent:.2f} đơn/phút."
    else:
        m = min(action, n_ready, env.capacity)
        if m == 0:
            reason = "Chờ thêm do không có đơn sẵn sàng thực tế."
            action = 0
        elif wait_ready_max > 12.0:
            reason = f"Xuất phát khẩn cấp {m} đơn: Đơn sẵn sàng cũ nhất đã chờ {wait_ready_max:.1f}m, giải tỏa ách tắc hàng đợi."
        else:
            reason = f"Xuất phát {m} đơn tối ưu: Gom cụm đường vòng <= 1.5km, hoán vị {m}! chặng giao tối thiểu thời gian bàn giao."

    return action, reason


@router.get("/stream")
async def stream_simulation(
    policy: str = Query("Double_DQN", description="Policy: Immediate, Periodic, AgeThreshold, DQN, Double_DQN, PPO"),
    seed: int = Query(2026, description="Random seed for simulation reproducibility"),
    rain_factor: float = Query(1.0, description="Rain penalty factor (1.0 = normal, 1.4 = heavy rain)"),
    surge: bool = Query(False, description="Whether to trigger an intense surge burst"),
    speed: float = Query(20.0, description="Simulation playback speed multiplier"),
):
    """
    Server-Sent Events (SSE) streaming discrete simulation step-by-step.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        env = DispatchEnv(
            matrix_path="data/matrix_standard.npz",
            address_pool_path="data/address_pool_standard.json",
            enable_event_logging=True,
            rain_factor=rain_factor,
        )
        if surge:
            env.surge_factor = 3.5  # High surge injection

        obs, _ = env.reset(seed=seed)
        pol = get_agent_policy(policy, seed=seed)

        terminated = False
        truncated = False
        step_idx = 0

        # Send initial state
        initial_payload = {
            "type": "INIT",
            "policy": policy,
            "seed": seed,
            "rain_factor": rain_factor,
            "surge": surge,
            "depot": {"lat": env.depot_lat, "lon": env.depot_lon, "name": "Bếp 490 Điện Biên Phủ"},
            "timestamp": env.current_time,
            "active_orders": [
                {
                    "id": o["id"],
                    "status": o["state"],
                    "lat": float(env.address_pool[o["address_idx"]]["lat"]),
                    "lon": float(env.address_pool[o["address_idx"]]["lon"]),
                    "placed_time": round(o["placed_time"], 1),
                }
                for o in env.orders[:10]
            ],
            "metrics": env.get_metrics(),
        }
        yield f"data: {json.dumps(initial_payload, default=float)}\n\n"

        while not (terminated or truncated):
            action, reason = compute_action_and_reason(pol, obs, env)
            next_obs, r, terminated, truncated, _ = env.step(action)
            obs = next_obs
            step_idx += 1

            metrics = env.get_metrics()

            # Active orders payload (with coordinates for MapLibre)
            orders_payload = []
            for o in env.orders:
                lat = float(env.address_pool[o["address_idx"]]["lat"])
                lon = float(env.address_pool[o["address_idx"]]["lon"])
                if o["state"] in ["PLACED", "COOKING", "READY", "DELIVERING"]:
                    orders_payload.append({
                        "id": o["id"],
                        "status": o["state"],
                        "lat": lat,
                        "lon": lon,
                        "placed_time": round(o["placed_time"], 1),
                        "wait_time": round(env.current_time - o["placed_time"], 1),
                        "promised_eta": round(o["promised_eta"], 1),
                    })
                elif o["state"] == "DELIVERED" and o.get("delivered_time") and (env.current_time - o["delivered_time"] <= 5.0):
                    # Show recently delivered for 5 mins
                    orders_payload.append({
                        "id": o["id"],
                        "status": "DELIVERED",
                        "lat": lat,
                        "lon": lon,
                        "delivered_time": round(o["delivered_time"], 1),
                        "wait_time": round(o["delivered_time"] - o["placed_time"], 1),
                        "promised_eta": round(o["promised_eta"], 1),
                    })

            # Drivers payload
            drivers_payload = []
            for d in env.drivers:
                drivers_payload.append({
                    "id": d["id"],
                    "is_idle": d["idle"],
                    "return_time": round(d["return_time"], 1),
                    "capacity": env.capacity,
                    "current_pos": [env.depot_lat, env.depot_lon],
                })

            step_data = {
                "type": "STEP",
                "step": step_idx,
                "timestamp": round(env.current_time, 2),
                "action": action,
                "action_reason": reason,
                "active_orders": orders_payload,
                "drivers": drivers_payload,
                "metrics": {
                    "mean_wait_min": round(metrics["mean_wait_min"], 2),
                    "p90_wait_min": round(metrics["p90_wait_min"], 2),
                    "late_rate_pct": round(metrics["late_rate_pct"], 1),
                    "fleet_utilization_pct": round(metrics["fleet_utilization"] * 100.0, 1),
                    "total_km": round(metrics["total_km"], 1),
                    "total_orders": metrics["num_orders"],
                    "delivered_orders": metrics["delivered_orders"],
                    "bellman_abs_error": metrics["bellman_abs_error"],
                },
            }
            yield f"data: {json.dumps(step_data, default=float)}\n\n"

            # Sleep inversely proportional to speed
            delay = max(0.01, 1.0 / speed)
            await asyncio.sleep(delay)

        # Finished event
        final_metrics = env.get_metrics()
        done_data = {
            "type": "DONE",
            "step": step_idx,
            "final_metrics": final_metrics,
        }
        yield f"data: {json.dumps(done_data, default=float)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


class ParallelRequest(BaseModel):
    policy_a: str = "Immediate"
    policy_b: str = "Double_DQN"
    seed: int = 2026
    rain_factor: float = 1.0
    surge: bool = False


@router.post("/parallel")
async def run_parallel_simulation(payload: ParallelRequest):
    """
    Runs two policies side-by-side on the exact same seed and returns compared metrics.
    """
    results = {}
    for pol_name in [payload.policy_a, payload.policy_b]:
        env = DispatchEnv(
            matrix_path="data/matrix_standard.npz",
            address_pool_path="data/address_pool_standard.json",
            enable_event_logging=False,
            rain_factor=payload.rain_factor,
        )
        if payload.surge:
            env.surge_factor = 3.5

        obs, _ = env.reset(seed=payload.seed)
        pol = get_agent_policy(pol_name, seed=payload.seed)

        terminated = False
        truncated = False
        latencies = []

        while not (terminated or truncated):
            t0 = time.perf_counter()
            act, _ = compute_action_and_reason(pol, obs, env)
            latencies.append((time.perf_counter() - t0) * 1000.0)
            obs, _, terminated, truncated, _ = env.step(act)

        m = env.get_metrics()
        m["policy"] = pol_name
        m["mean_decision_latency_ms"] = float(np.mean(latencies))
        results[pol_name] = m

    return {
        "status": "success",
        "seed": payload.seed,
        "rain_factor": payload.rain_factor,
        "surge": payload.surge,
        "comparison": results,
    }


@router.get("/benchmark_summary")
async def get_benchmark_summary():
    """
    Returns official audited scientific metrics from results/all_metrics_registry.json.
    """
    registry_file = Path("results/all_metrics_registry.json")
    if not registry_file.exists():
        raise HTTPException(status_code=404, detail="Metrics registry not found")
    
    with open(registry_file, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    summary_file = Path("results/training/summary_rl_test.csv")
    base_file = Path("results/baselines/summary_baseline_test.csv")
    
    summary_rows = []
    if base_file.exists():
        import pandas as pd
        df_base = pd.read_csv(base_file)
        summary_rows.extend(df_base.to_dict(orient="records"))
    if summary_file.exists():
        import pandas as pd
        df_rl = pd.read_csv(summary_file)
        summary_rows.extend(df_rl.to_dict(orient="records"))

    return {
        "registry": registry,
        "summary": summary_rows,
    }
