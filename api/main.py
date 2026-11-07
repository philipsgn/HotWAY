"""
FastAPI Microservice serving the winning Attention Model (Graph Transformer),
4-Model Comparative Benchmark Suite, T1-T3 Multi-Criteria Routing, and Pathfinding Visualizer.
Port: 8000 (Local serving, CPU inference < 25ms).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.endpoints import visualizer, nco_benchmark
from backend.app.api import route_optimization

app = FastAPI(
    title="HotWAY Dynamic Traffic-Aware Neural Routing API",
    version="7.3.2",
    description="Unified API serving Attention Model, OR-Tools, PointerNet, DQN, T1-T3 Pareto routing and Pathfinding Visualizer."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount 100% endpoints for unified dual-mount architecture
app.include_router(visualizer.router)
app.include_router(nco_benchmark.router)
app.include_router(route_optimization.router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "HotWAY Dynamic Traffic-Aware Neural Routing API",
        "version": "7.3.2",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "champion_model": "Attention Model (Graph Transformer Kool et al., 2019)",
        "traffic_fallback": "3-Tier (TomTom -> HERE -> Offline C(t))",
        "inference_engine": "PyTorch CPU Native / Sub-25ms",
        "supported_models": ["am", "ortools", "ptr", "dqn"],
        "version": "7.3.2",
    }


if __name__ == "__main__":
    import uvicorn
    # Enforce port discipline: Backend 8000, never 3000
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
