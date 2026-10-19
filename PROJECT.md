# Project: HotWAY

## Architecture
HotWAY is an intelligent food delivery dispatch & routing system powered by Reinforcement Learning (optimizing dynamic VRP with Newton's cooling law constraints) on real-world OpenStreetMap data of Hàng Gòn (Long Khánh, Đồng Nai).

The architecture consists of four tightly-coupled subsystems:
1. **RL Research & Baselines Engine (`src/rl/`, `src/baselines/`)**:
   - OSMnx road network graph with rush-hour congestion factors.
   - Gymnasium environment with Newton cooling physics: $T(t) = T_{\text{env}} + (T_0 - T_{\text{env}})e^{-kt}$.
   - Baselines: Dijkstra shortest path, Greedy Nearest-Neighbor, Google OR-Tools VRP.
   - RL models: Tabular Q-learning, DQN, and MaskablePPO (`sb3-contrib`).
   - Inference wrapper (`HotWAYPolicyRunner`) and Ghost trajectory export (`best_route_ghost.json`).
2. **Backend WebGIS Monolith (`backend/`)**:
   - FastAPI application with async SQLAlchemy + GeoAlchemy2 on PostgreSQL/PostGIS.
   - Redis geospatial cache (`GEOADD`, driver hashes, Pub/Sub).
   - High-throughput WebSocket hub (<200ms broadcast latency) handling `SHIPPER_TELEMETRY_UPDATE`, `DRIVER_GPS_EMIT`, and `ORDER_STATUS_CHANGED`.
   - Routing service with Dijkstra fallback to guarantee zero delivery dispatch downtime.
3. **Frontend WebGIS Platform & Shipper PWA (`frontend/`)**:
   - Next.js 14 App Router with MapLibre GL JS and deck.gl for 60 FPS live tracking overlay.
   - Customer ordering page with interactive pin-dropping on OSM map.
   - Mobile-first Shipper PWA with HTML5 Geolocation API and developer Mock GPS toggle.
   - Academic Comparison Studio (`/admin/comparison-studio`) for side-by-side RL vs. Baseline visual inspection.
4. **3D Mini-Game "HotWAY Rider" (`frontend/src/game/`)**:
   - Three.js / React Three Fiber + Rapier 3D physics.
   - Procedural extrusion of OSM road ribbons and building footprints from GeoJSON.
   - Player motorbike keyboard controller racing against the RL agent's AI Ghost replay.
   - Dynamic thermal HUD tracking soup cooling and voucher reward logic (`BANHCANH_AI_WINNER_15`).
   - Cleanly packaged as `<HotWAYRiderCanvas />` for Next.js route `/game/rider`.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | OSMnx Road Network Extraction | Extract and parse Hàng Gòn road network into GraphML with speed limits and rush-hour factors | M2 | survey_rl.md |
| 2 | Synthetic Fallback Road Network | Deterministic fallback graph for offline development and testing environments | M2 | survey_rl.md |
| 3 | Newton Cooling Physics Model | Implementation of $T(t) = T_{\text{env}} + (T_0 - T_{\text{env}})e^{-kt}$ with dish/container coefficients | M2 | survey_rl.md |
| 4 | Container & Dish Thermal Matrix | Thermal degradation coefficients for Bánh Canh Gà and insulated vs standard containers | M2 | survey_rl.md |
| 5 | Rush-Hour Traffic Simulator | Dynamic congestion factor modulation ($\times 1.5$ to $\times 3.0$ on QL56) during peak hours | M2 | survey_rl.md |
| 6 | Multi-Order Delivery MDP State | Formal state representation $\langle p_{\text{shipper}}, \mathcal{O}_{\text{active}}, \tau_{\text{current}}, \mathcal{W}_{\text{env}}, \mathcal{C}_{\text{traffic}} \rangle$ | M2 | survey_rl.md |
| 7 | Action Space with Action Masking | Discrete delivery decision space with masking to prohibit invalid destinations or closed orders | M2 | survey_rl.md |
| 8 | Delivery Step State Machine | Environment step dynamics updating order statuses, transit times, and vehicle positions | M2 | survey_rl.md |
| 9 | Piecewise Quadratic Thermal Reward | Positive bonus for $T \ge 60^\circ\text{C}$ and quadratic penalty for ruined cold food | M2 | survey_rl.md |
| 10 | On-Time Bonus & Delay Penalty | Reward terms balancing arrival timeliness against maximum delivery deadline | M2 | survey_rl.md |
| 11 | Invalid Action & Distance Penalties | Penalties discouraging illegal route decisions and excessive fuel/distance expenditure | M2 | survey_rl.md |
| 12 | Dijkstra Shortest Path Baseline | Exact classical shortest path router on metric graph | M2 | survey_rl.md |
| 13 | Greedy Nearest-Neighbor Baseline | Heuristic baseline serving geographically closest order first | M2 | survey_rl.md |
| 14 | Google OR-Tools VRP Baseline | Combinatorial solver solving vehicle routing problem constraints | M2 | survey_rl.md |
| 15 | Tabular Q-Learning Algorithm | Exact value-iteration on 10-node subgraph proving MDP optimality | M2 | survey_rl.md |
| 16 | Deep Q-Network (DQN) Algorithm | Neural Q-learning for single-order delivery routing | M2 | survey_rl.md |
| 17 | MaskablePPO Algorithm | Policy gradient RL supporting multi-order batching with action masks | M2 | survey_rl.md |
| 18 | Model Evaluation Engine | Comparative evaluation calculating average temperature, delay, and travel time | M2 | survey_rl.md |
| 19 | Thermal Ablation Study Runner | Comparative benchmark of policy trained with vs. without thermal reward | M2 | survey_rl.md |
| 20 | Model & Config Exporter | Export trained SB3 model (`models/rl_best_model.zip`) and hyperparams (`models/config.json`) | M2 | survey_rl.md |
| 21 | HotWAYPolicyRunner Inference Class | High-performance Python inference wrapper (<20ms) for FastAPI integration | M2 | survey_rl.md |
| 22 | Ghost Trajectory Exporter | Generate `best_route_ghost.json` with GPS waypoints, speeds, and timestamps | M2 | survey_rl.md |
| 23 | 1000-Step Environment Liveness Check | Acceptance test verifying 1000 steps without error and monotone temperature decay | M2 | survey_rl.md |
| 24 | Congestion Superiority Verification | Automated test proving RL beats Dijkstra in arrival temp and delay under congestion | M2 | survey_rl.md |
| 25 | Ablation 15% Gain Verification | Automated verification proving $\ge 15\%$ higher temperature when thermal reward enabled | M2 | survey_rl.md |
| 26 | FastAPI Monolith Application Factory | Modular FastAPI application setup with CORS, lifespan management, and routers | M1 | survey_web.md |
| 27 | Configuration & Settings Management | Pydantic v2 settings loading environment variables and database URLs | M1 | survey_web.md |
| 28 | PostgreSQL & PostGIS Session Management | Async SQLAlchemy session maker and database engine with spatial extension checks | M1 | survey_web.md |
| 29 | PostGIS Spatial DDL & Tables | 8 spatial entities (RESTAURANTS, MENU_ITEMS, ORDERS, ORDER_ITEMS, SHIPPERS, ROUTE_LOGS, EXPERIMENT_RUNS, EXPERIMENT_METRICS) | M1 | survey_web.md |
| 30 | GeoJSON Spatial Query Services | Endpoints returning road networks, restaurant locations, and delivery boundaries | M3 | survey_web.md |
| 31 | Menu & Catalog APIs | REST endpoints for querying Bánh Canh Gà menu, prices, and container options | M3 | survey_web.md |
| 32 | Order Creation API | REST endpoint creating delivery orders with GPS coordinates and preparation times | M3 | survey_web.md |
| 33 | Order Lifecycle Query APIs | Endpoints tracking order status (PREPARING, DISPATCHED, DELIVERED) and thermal stats | M3 | survey_web.md |
| 34 | Redis Telemetry Cache & GeoStore | In-memory storage for high-frequency driver coordinates (`GEOADD`) and active state | M3 | survey_web.md |
| 35 | WebSocket Real-Time Broadcast Hub | Connection manager broadcasting telemetry to customer and admin channels (<200ms) | M3 | survey_web.md |
| 36 | Order Status Event Pipeline | Real-time push of `ORDER_STATUS_CHANGED` events to connected clients | M3 | survey_web.md |
| 37 | Shipper GPS Ingestion Pipeline | Ingestion of `DRIVER_GPS_EMIT` WebSocket messages from Shipper PWA | M3 | survey_web.md |
| 38 | Graph Routing Service | Internal NetworkX/OSRM shortest path calculation service | M3 | survey_web.md |
| 39 | RL Inference Service with Fallback | Backend integration of `HotWAYPolicyRunner` with safe Dijkstra fallback | M3 | survey_web.md |
| 40 | Traffic Congestion Provider | In-memory rush-hour traffic multiplier applied to routing graph edges | M3 | survey_web.md |
| 41 | Docker Compose Fullstack Setup | Multi-service compose file (`docker compose up`) for PostGIS, Redis, Backend, Frontend | M3 | survey_web.md |
| 42 | Alembic Database Migrations | Version-controlled database migration scripts for spatial tables | M1 | survey_web.md |
| 43 | Database Seeding Script | Initial data seed for Quán Bánh Canh Gà Hàng Gòn, default menu, and sample nodes | M1 | survey_web.md |
| 44 | Next.js App Router Structure | Next.js 14 frontend setup with Tailwind CSS, TypeScript, and layout shell | M3 | survey_web.md |
| 45 | MapLibre GL JS Base Map | Vector/raster map component centered on Hàng Gòn using free CartoDB/OSM tiles | M3 | survey_web.md |
| 46 | deck.gl Real-Time Overlay | High-performance 60 FPS animated shipper and route overlay layer | M3 | survey_web.md |
| 47 | Interactive Customer Order Page | Map pin dropping, menu selection, and order placement UI | M3 | survey_web.md |
| 48 | Customer Order Tracking Page | Real-time delivery view with live route, dynamic Thermal Gauge, and ETA countdown | M3 | survey_web.md |
| 49 | Shipper PWA Interface | Mobile-optimized interface showing active batch orders, route steps, and delivery controls | M3 | survey_web.md |
| 50 | HTML5 Geolocation Tracking | Shipper device GPS tracking emitting coordinates via WebSocket | M3 | survey_web.md |
| 51 | Mock GPS Simulation Toggle | Interactive development tool allowing simulated driver movement along road network | M3 | survey_web.md |
| 52 | Academic Comparison Studio | Split-screen map comparing RL vs Baseline routes with Newton cooling charts | M3 | survey_web.md |
| 53 | Three.js / R3F Canvas & Scene | React Three Fiber canvas wrapper configured with WebGL 2.0 and performance limits | M4 | survey_game.md |
| 54 | Rapier 3D Physics Engine | Physics world with gravity, collision detection, and rigid bodies | M4 | survey_game.md |
| 55 | Procedural Road Ribbon Generator | Procedural 3D road ribbons extruded from OSM road LineStrings (QL56, branch, alleys) | M4 | survey_game.md |
| 56 | Procedural Building Extrusion | Low-poly 3D building footprint extrusion with randomized heights (4m-12m) | M4 | survey_game.md |
| 57 | Local Metric Projection | Equirectangular metric projection converting (Lat, Lon) to 3D Cartesian (X, Y, Z) | M4 | survey_game.md |
| 58 | Player Motorbike Rig & Physics | Responsive vehicle physics body with collision hull, friction, and restitution | M4 | survey_game.md |
| 59 | Keyboard Vehicle Controller | WASD / Arrow keys input handler for acceleration, braking, and steering | M4 | survey_game.md |
| 60 | Third-Person Chase Camera | Smooth damping camera controller following player motorbike orientation and velocity | M4 | survey_game.md |
| 61 | AI Ghost Ingestion Engine | JSON loader for `best_route_ghost.json` with timestamp and waypoint extraction | M4 | survey_game.md |
| 62 | AI Ghost Waypoint Interpolator | Hermite/linear interpolation animating AI Ghost along RL trajectory | M4 | survey_game.md |
| 63 | AI Ghost Shader Material | Semitransparent blue glowing material distinguishing AI Ghost from player vehicle | M4 | survey_game.md |
| 64 | Real-Time Thermal HUD Overlay | UI displaying soup temperature decay $T(t)$, cooling graph, and elapsed time | M4 | survey_game.md |
| 65 | Delivery Target Trigger Zone | Cylindrical drop-zone trigger detecting delivery completion | M4 | survey_game.md |
| 66 | Race Scoring & Victory Logic | Evaluation comparing player final temperature vs AI Ghost final temperature | M4 | survey_game.md |
| 67 | Voucher Reward Generator | Award voucher code `BANHCANH_AI_WINNER_15` when player beats RL temperature | M4 | survey_game.md |
| 68 | `<HotWAYRiderCanvas />` Component | Standalone React component accepting `orderId`, `ghostTrajectoryUrl`, `onGameComplete` | M4 | survey_game.md |
| 69 | WebGL Resource Disposal Cleanup | Complete disposal of geometries, materials, and physics bodies on unmount | M4 | survey_game.md |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Specs & Shared Schemas | Project skeleton, database DDL, shared Pydantic models, seed scripts (Features 26-29, 42-43) | None | DONE |
| M2 | RL Core & Baselines Implementation | OSMnx graph, Newton cooling, Gymnasium env, Baselines, Q-learning, DQN, MaskablePPO, Ablation study, Inference class, Ghost exporter (Features 1-25) | M1 | DONE |
| M3 | Fullstack Web & Real-Time GIS Backend | FastAPI services, PostGIS spatial queries, Redis telemetry, WebSocket hub, Next.js WebGIS, Shipper PWA, Comparison Studio, Docker Compose (Features 30-41, 44-52) | M1, M2 | PLANNED |
| M4 | 3D Mini-game HotWAY Rider | Three.js/R3F, Rapier physics, procedural OSM mesh, player bike, AI Ghost replay, Thermal HUD, voucher logic (Features 53-69) | M1, M2, M3 | PLANNED |
| M5 | Final Milestone: 100% E2E Pass & Hardening | Pass 100% of E2E tests (Tiers 1-4) published by E2E Testing Track; Tier 5 Adversarial Coverage Hardening | M1, M2, M3, M4 | PLANNED |

---

## Interface Contracts

### 1. `src/rl/` ↔ `backend/` (Inference & Routing Contract)
- Class: `src.rl.policy_runner.HotWAYPolicyRunner`
- Interface:
  ```python
  class HotWAYPolicyRunner:
      def __init__(self, model_path: str, graph_path: str):
          """Loads SB3 MaskablePPO model and NetworkX graph."""
          ...

      def predict_next_order(self, observation: dict, action_mask: list[int]) -> int:
          """Returns chosen action index within <20ms latency."""
          ...
  ```
- Fallback: If `HotWAYPolicyRunner` fails or raises an exception, `backend/app/services/routing_service.py` executes Dijkstra shortest path routing without error.

### 2. `src/rl/` ↔ `frontend/src/game/` (AI Ghost Replay Contract)
- File path: `experiments/trajectories/best_route_ghost.json`
- Schema:
  ```json
  {
    "order_id": "ord_sample_01",
    "total_time_seconds": 412.5,
    "final_temperature_c": 74.8,
    "waypoints": [
      {"timestamp_offset": 0.0, "lat": 10.9212, "lon": 107.2401, "speed_kmh": 0.0},
      {"timestamp_offset": 5.0, "lat": 10.9216, "lon": 107.2405, "speed_kmh": 28.5}
    ]
  }
  ```

### 3. `backend/` ↔ `frontend/` (WebSocket Telemetry Contract)
- Endpoints:
  - `/ws/tracking/{order_id}`: Client tracking stream
  - `/ws/driver/{driver_id}`: Shipper PWA bidirectional stream
  - `/ws/dispatcher`: Admin overview stream
- Latency budget: `< 200 ms`
- Event types:
  - `SHIPPER_TELEMETRY_UPDATE` (Server $\to$ Client): `{order_id, lat, lon, current_temp_c, speed_kmh, status}`
  - `DRIVER_GPS_EMIT` (Shipper $\to$ Server): `{driver_id, order_id, lat, lon, heading, timestamp}`
  - `ORDER_STATUS_CHANGED` (Server $\to$ Client): `{order_id, old_status, new_status, timestamp}`

### 4. `frontend/src/game/` ↔ `frontend/src/app/` (Mini-Game React Contract)
- Component: `<HotWAYRiderCanvas />`
- Interface:
  ```typescript
  export interface GameProps {
    orderId: string;
    ghostTrajectoryUrl: string;
    onGameComplete: (result: {
      playerTempC: number;
      timeSeconds: number;
      wonAI: boolean;
      voucherCode?: string;
    }) => void;
  }
  ```

---

## Code Layout
```
HotWAY/
├── PROJECT.md
├── docker-compose.yml
├── data/
│   ├── hanggon_graph.graphml
│   ├── hanggon_center_roads.geojson
│   └── hanggon_buildings.geojson
├── models/
│   ├── rl_best_model.zip
│   └── config.json
├── experiments/
│   └── trajectories/
│       └── best_route_ghost.json
├── src/
│   ├── rl/
│   │   ├── __init__.py
│   │   ├── osm_graph_loader.py
│   │   ├── newton_cooling.py
│   │   ├── traffic_model.py
│   │   ├── delivery_env.py
│   │   ├── train_qlearning.py
│   │   ├── train_dqn.py
│   │   ├── train_ppo.py
│   │   ├── policy_runner.py
│   │   └── ablation_study.py
│   └── baselines/
│       ├── __init__.py
│       ├── dijkstra_router.py
│       ├── greedy_solver.py
│       └── ortools_vrp.py
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── orders.py
│   │   │   ├── menu.py
│   │   │   ├── spatial.py
│   │   │   └── websockets.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── order.py
│   │   │   ├── menu.py
│   │   │   └── spatial.py
│   │   ├── services/
│   │   │   ├── routing_service.py
│   │   │   ├── telemetry_service.py
│   │   │   └── inference_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── track/[id]/page.tsx
│   │   │   ├── shipper/page.tsx
│   │   │   ├── game/rider/page.tsx
│   │   │   └── admin/comparison-studio/page.tsx
│   │   ├── components/
│   │   │   ├── MapView.tsx
│   │   │   ├── ThermalGauge.tsx
│   │   │   └── OrderCard.tsx
│   │   └── game/
│   │       ├── HotWAYRiderCanvas.tsx
│   │       ├── ProceduralMap.tsx
│   │       ├── MotorbikeRig.tsx
│   │       ├── AIGhostRider.tsx
│   │       └── ThermalHUD.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
└── tests/
    └── e2e/
        ├── runner.py
        ├── tier1_features/
        ├── tier2_boundaries/
        ├── tier3_pairwise/
        └── tier4_workloads/
```
