"""
HotWAY v7.0.0 Route Optimization & Real-Time Simulation API (Gate G6).
Exposes T1 Multi-Criteria Routes, T2 VRPTW Benchmark, T3 Adaptive Rerouting,
and Server-Sent Events (SSE) telemetry stream on Port 8000.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from src.routing.multicriteria_router import MultiCriteriaRouter
from src.envs.adaptive_routing_env import AdaptiveRoutingEnv
from src.traffic.provider import SyntheticProvider, TrafficState
from src.agents.baseline_policies import StaticDijkstraPolicy, DynamicDijkstraPolicy
from src.agents.candidate_edge_dqn import EdgeScoringDQNAgent, extract_candidate_edge_features
from src.services.neural_tsp_service import NeuralTSPService
from src.services.live_traffic_adapter import LiveTrafficAdapter


router = APIRouter(tags=["Route Optimization & Adaptive Dispatch"])

# Singleton router & environment cache
_ROUTER_INSTANCE: Optional[MultiCriteriaRouter] = None
_ENV_INSTANCE: Optional[AdaptiveRoutingEnv] = None
_DQN_AGENT: Optional[EdgeScoringDQNAgent] = None


def get_router() -> MultiCriteriaRouter:
    global _ROUTER_INSTANCE
    if _ROUTER_INSTANCE is None:
        _ROUTER_INSTANCE = MultiCriteriaRouter.from_hcmc_subgraph(radius_km=1.2)
    return _ROUTER_INSTANCE


def get_adaptive_env() -> AdaptiveRoutingEnv:
    global _ENV_INSTANCE
    if _ENV_INSTANCE is None:
        r = get_router()
        traffic = SyntheticProvider(seed=2026)
        _ENV_INSTANCE = AdaptiveRoutingEnv(graph=r.graph, traffic_provider=traffic, max_steps=60)
    return _ENV_INSTANCE


def get_dqn_agent() -> Optional[EdgeScoringDQNAgent]:
    global _DQN_AGENT
    if _DQN_AGENT is None:
        model_path = "results/t3_edge_dqn_model.pt"
        if os.path.exists(model_path):
            agent = EdgeScoringDQNAgent(in_features=10, hidden_dim=64)
            agent.load(model_path)
            _DQN_AGENT = agent
    return _DQN_AGENT


def snap_nearest_node(router_obj: MultiCriteriaRouter, lat: float, lon: float) -> int:
    """Finds nearest node in the strongly connected subgraph."""
    G = router_obj.graph
    best_node = None
    min_dist_sq = 1e18
    for n in G.nodes():
        n_lat = G.nodes[n]["y"]
        n_lon = G.nodes[n]["x"]
        d = ((lat - n_lat) * 111.0) ** 2 + ((lon - n_lon) * 111.0 * math.cos(math.radians(lat))) ** 2
        if d < min_dist_sq:
            min_dist_sq = d
            best_node = n
    return best_node


class ODRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    rain: bool = False


# =========================================================================
# 1. T1: Multi-Criteria Routes Endpoint
# =========================================================================
@router.get("/routes/t1", summary="Get T1 4 Pareto-optimal routes (Sample or Custom)")
async def get_t1_routes(
    origin: Optional[int] = Query(None, description="Origin node ID in subgraph"),
    destination: Optional[int] = Query(None, description="Destination node ID in subgraph"),
    rain: bool = Query(False, description="Whether rainy weather speed degradation is active"),
):
    """
    Returns 4 labeled routes: Fastest Expected, Shortest Distance, Most Stable p90, Easiest Ride.
    If no origin/destination provided, loads certified benchmark result from results/t1_routes_sample.json.
    """
    sample_path = "results/t1_routes_sample.json"

    # If neither origin nor destination is specified, return certified sample
    if origin is None and destination is None and not rain:
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["attribution"] = "MÔ PHỎNG"
            data["source"] = "results/t1_routes_sample.json"
            return data

    r = get_router()
    nodes = list(r.graph.nodes())

    orig_node = origin if origin is not None and origin in r.graph else 1497276525
    dest_node = destination if destination is not None and destination in r.graph else 5337055581

    labeled = r.select_four_labeled_routes(orig_node, dest_node, k_candidates=15)
    if not labeled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between the specified origin and destination nodes."
        )

    response = {
        "metadata": {
            "origin": {"node_id": orig_node, "lat": r.graph.nodes[orig_node]["y"], "lon": r.graph.nodes[orig_node]["x"]},
            "destination": {"node_id": dest_node, "lat": r.graph.nodes[dest_node]["y"], "lon": r.graph.nodes[dest_node]["x"]},
            "subgraph_nodes": r.graph.number_of_nodes(),
            "subgraph_edges": r.graph.number_of_edges(),
            "rain": rain,
            "attribution": "MÔ PHỎNG",
        },
        "routes": labeled,
    }
    return response


@router.post("/routes/t1/calculate", summary="Calculate T1 routes from GPS coordinates")
async def calculate_t1_custom(req: ODRequest):
    r = get_router()
    orig_node = snap_nearest_node(r, req.origin_lat, req.origin_lon)
    dest_node = snap_nearest_node(r, req.dest_lat, req.dest_lon)

    if orig_node == dest_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin and destination snap to the same graph node. Please choose points farther apart."
        )

    labeled = r.select_four_labeled_routes(orig_node, dest_node, k_candidates=15)
    return {
        "metadata": {
            "origin": {"node_id": orig_node, "lat": r.graph.nodes[orig_node]["y"], "lon": r.graph.nodes[orig_node]["x"]},
            "destination": {"node_id": dest_node, "lat": r.graph.nodes[dest_node]["y"], "lon": r.graph.nodes[dest_node]["x"]},
            "rain": req.rain,
            "attribution": "MÔ PHỎNG",
        },
        "routes": labeled,
    }


# =========================================================================
# 2. T2: Multi-Stop VRPTW Benchmark Endpoint
# =========================================================================
@router.get("/vrptw/benchmark", summary="Get T2 VRPTW Solvers Benchmark Results")
async def get_t2_benchmark():
    """
    Returns comparative performance metrics for Greedy, Clarke-Wright+LS, and Google OR-Tools
    across 10 delivery instances under dry vs rain simulation.
    """
    benchmark_path = "results/baselines/t2_vrptw_benchmark.json"
    if not os.path.exists(benchmark_path):
        raise HTTPException(status_code=404, detail="T2 benchmark data not found.")

    with open(benchmark_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["attribution"] = "MÔ PHỎNG"
    return data


# =========================================================================
# 3. T3: Adaptive Routing Benchmark Endpoint
# =========================================================================
@router.get("/routing/t3/benchmark", summary="Get T3 Adaptive Routing Policy Benchmark Results")
async def get_t3_benchmark():
    """
    Returns comparative evaluation of Static Dijkstra, Dynamic Dijkstra, and Edge-Scoring DQN
    with Wilcoxon signed-rank statistics across 3 operational scenarios.
    """
    t3_path = "results/t3_policy_comparison.json"
    if not os.path.exists(t3_path):
        raise HTTPException(status_code=404, detail="T3 policy comparison data not found.")

    with open(t3_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["attribution"] = "MÔ PHỎNG"
    return data


# =========================================================================
# 4. SSE Simulation Stream Endpoint
# =========================================================================
@router.get("/sim/stream", summary="Server-Sent Events (SSE) stream for real-time routing simulation")
async def stream_simulation(
    policy: str = Query("dynamic_dijkstra", description="'dynamic_dijkstra', 'static_dijkstra', or 'edge_dqn'"),
    rain: bool = Query(False, description="Enable rain inflation factor (1.40x)"),
    incident: bool = Query(False, description="Inject random road incident bottleneck"),
    speed_mult: float = Query(5.0, description="Playback speed multiplier (1.0 to 50.0)"),
    seed: int = Query(2026, description="Random seed for traffic determinism"),
):
    """
    Streams step-by-step vehicle progress, instantaneous traffic congestion states,
    turn maneuvers, and dynamic rerouting triggers.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        r = get_router()
        traffic = SyntheticProvider(
            seed=seed,
            noise_sigma=0.15,
            rain_factor=1.40 if rain else 1.0,
            incident_prob=0.08 if incident else 0.0,
        )
        env = AdaptiveRoutingEnv(graph=r.graph, traffic_provider=traffic, max_steps=50, rain=rain)

        # Use canonical representative OD pair
        origin_node = 1497276525
        target_node = 5337055581

        obs, info = env.reset(
            seed=seed,
            options={"source_node": origin_node, "target_node": target_node, "rain": rain}
        )

        # Policy init
        static_pol = StaticDijkstraPolicy(env)
        static_pol.reset(origin_node, target_node)
        dynamic_pol = DynamicDijkstraPolicy(env)
        dqn_agent = get_dqn_agent()

        # Send Init Event
        init_payload = {
            "event_type": "INIT",
            "policy": policy,
            "rain": rain,
            "incident": incident,
            "origin": {"node_id": origin_node, "lat": env.coords[origin_node][0], "lon": env.coords[origin_node][1]},
            "destination": {"node_id": target_node, "lat": env.coords[target_node][0], "lon": env.coords[target_node][1]},
            "subgraph_nodes": env.n_nodes,
            "planned_path": static_pol.cached_path,
            "attribution": "MÔ PHỎNG",
        }
        yield f"event: init\ndata: {json.dumps(init_payload, ensure_ascii=False)}\n\n"

        step_delay = max(0.05, 1.0 / max(1.0, speed_mult))
        total_time_min = 0.0

        for step in range(env.max_steps):
            if env.current_node == env.target_node:
                break

            curr_u = env.current_node
            succs = env.adj[curr_u]

            # Select action based on policy
            if policy == "static_dijkstra":
                action = static_pol.select_action(curr_u)
            elif policy == "edge_dqn" and dqn_agent is not None:
                feats, _ = extract_candidate_edge_features(
                    env, curr_u, env.target_node, env.prev_node, env.current_time_min, rain
                )
                action = dqn_agent.select_action(feats, deterministic=True)
            else:  # default: dynamic_dijkstra
                action = dynamic_pol.select_action(curr_u, env.target_node)

            chosen_v = succs[action]
            c_state = traffic.get_edge_state(curr_u, chosen_v)

            # Detect reroute: if dynamic policy deviates from static plan
            is_reroute = (
                policy == "dynamic_dijkstra"
                and curr_u in static_pol.cached_path
                and action != static_pol.select_action(curr_u)
            )

            # Step environment
            obs, reward, term, trunc, step_info = env.step(action)
            total_time_min += float(-reward)

            step_payload = {
                "event_type": "PROGRESS",
                "step": step + 1,
                "current_node": env.current_node,
                "coordinates": [env.coords[env.current_node][0], env.coords[env.current_node][1]],
                "edge_traversed": [curr_u, chosen_v],
                "congestion_state": int(c_state),  # 0: Clear, 1: Slow, 2: Congested
                "step_duration_sec": float(round(step_info.get("step_duration_sec", 0.0), 1)),
                "cumulative_time_min": float(round(total_time_min, 2)),
                "is_reroute": is_reroute,
            }

            if is_reroute:
                yield f"event: reroute\ndata: {json.dumps(step_payload, ensure_ascii=False)}\n\n"
            else:
                yield f"event: step\ndata: {json.dumps(step_payload, ensure_ascii=False)}\n\n"

            await asyncio.sleep(step_delay)

            if term or trunc:
                break

        # Send Completion Event
        complete_payload = {
            "event_type": "COMPLETE",
            "success": (env.current_node == env.target_node),
            "total_travel_time_min": float(round(total_time_min, 2)),
            "total_travel_time_sec": float(round(env.total_travel_time_sec, 1)),
            "steps_taken": env.step_count,
            "path_traversed": env.path_history,
            "attribution": "MÔ PHỎNG",
        }
        yield f"event: complete\ndata: {json.dumps(complete_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =========================================================================
# 5. T2+: Neural TSP Optimization (Kool et al., 2019 Attention Model)
# =========================================================================
class MultiStopRequest(BaseModel):
    depot: Dict[str, Any]
    stops: List[Dict[str, Any]]
    departure_hour: float = 8.0


@router.post('/optimize-route/attention', summary='Solve dynamic TSP via Neural Attention Model')
async def optimize_route_attention(req: MultiStopRequest):
    """
    Solves multi-stop itinerary permutation using Transformer Attention Model (Kool et al., ICLR 2019).
    Computes time-dependent transit duration on HCMC road network.
    """
    service = NeuralTSPService()
    result = service.solve(
        depot=req.depot,
        stops=req.stops,
        departure_hour=req.departure_hour,
    )
    result['attribution'] = 'MÔ PHỎNG (Kool et al. Attention Model)'
    return result


@router.get('/traffic/travel-time', summary='Query segment travel time with 3-layer live fallback')
async def get_travel_time(
    origin_lat: float = Query(..., description='Origin latitude'),
    origin_lon: float = Query(..., description='Origin longitude'),
    dest_lat: float = Query(..., description='Destination latitude'),
    dest_lon: float = Query(..., description='Destination longitude'),
    departure_hour: float = Query(8.0, description='Hour of day (0-24)'),
):
    """
    3-Layer Live Traffic Pipeline:
    Layer 1: TomTom Traffic API (Live duration matrix)
    Layer 2: HERE Routing API (Secondary fallback)
    Layer 3: Offline Graph Matrix * Empirical C(t) Congestion Multiplier
    """
    adapter = LiveTrafficAdapter()
    res = adapter.get_segment_travel_time(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        departure_hour=departure_hour,
    )
    return res


@router.get('/routing/benchmark-multi-model', summary='Return 4-Model Comparative Benchmark results on 100 POIs')
async def get_multi_model_benchmark():
    bench_file = Path('results/benchmark_multi_model_results.json')
    if not bench_file.exists():
        raise HTTPException(status_code=404, detail='Benchmark results not found on disk.')
    with open(bench_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {
        'summary': data['summary'],
        'dqn_fatal_flaws': data['dqn_fatal_flaws_diagnostic'],
        'metadata': data['metadata']
    }
