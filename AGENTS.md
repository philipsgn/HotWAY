# Multi-Agent Architecture & Collaboration Protocol — HotWAY

**Tài liệu:** Bản thiết kế Kiến trúc Đa Tác tử (Subagents Architecture) dự án HotWAY  
**Phiên bản:** v1.0.0  
**Thư mục làm việc:** `c:\Users\TanPhat\Documents\AI_E\HotWAY/agents`  
**Tài liệu liên kết:** [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/PRD.md) | [TECH_ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/TECH_ARCHITECTURE.md) | [PLAN.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/PLAN.md)  

---

## 1. Cơ cấu 5 Vai trò Chuyên biệt (Specialized Subagent Roles)

Để phát triển dự án HotWAY một cách chuyên nghiệp, chuẩn mực và bảo đảm tính phân quyền rõ ràng, hệ thống phân bổ thành 5 chuyên gia AI tác tử độc lập:

```mermaid
flowchart TD
    Lead["Subagent 5: evaluator_architect_lead\n(Kiến trúc sư & Đánh giá Khoa học)"]
    
    RL["Subagent 1: rl_researcher_engineer\n(Nghiên cứu & Huấn luyện RL)"]
    BE["Subagent 2: backend_webgis_engineer\n(Backend FastAPI & WebGIS Services)"]
    FE["Subagent 3: frontend_webgis_engineer\n(Frontend Next.js & Shipper PWA)"]
    Game["Subagent 4: game_simulation_engineer\n(Mini-game 3D HotWAY Rider)"]

    Lead -->|Phân rã đặc tả & Yêu cầu chuẩn| RL
    Lead -->|Phân rã đặc tả & API Schema| BE
    Lead -->|Yêu cầu giao diện & UX| FE
    Lead -->|Kịch bản 3D & Dữ liệu OSM| Game

    RL -->|Mô hình (.zip/.pt) & Replay Log (.json)| BE
    RL -.->|Lộ trình AI Ghost| Game
    BE -->|REST API & WebSocket Protocol| FE
    BE -->|OSM Road Mesh & Ghost API| Game

    RL -->|Chỉ số thực nghiệm & TensorBoard| Lead
    BE -->|Báo cáo kiểm thử tích hợp| Lead
    FE -->|UX Verification| Lead
    Game -->|FPS & Physics Test| Lead
```

### Bảng Mô tả Trách nhiệm & Phạm vi Mã nguồn

| Tên Subagent | Mã định danh | Trách nhiệm cốt lõi | Phạm vi thư mục độc quyền |
|---|---|---|---|
| **RL Research & Model Engineer** | `rl_researcher_engineer` | Xây dựng Gymnasium Env, OSMnx graph, mô hình nhiệt Newton, huấn luyện Q-learning/DQN/PPO, xây dựng baselines và ablation study. | `src/rl/`, `src/baselines/`, `models/`, `experiments/` |
| **Backend & WebGIS Engineer** | `backend_webgis_engineer` | Xây dựng FastAPI monolith, PostGIS models, WebSocket Manager, Redis cache, OSRM router và đóng gói Docker Compose. | `backend/`, `docker/`, `migrations/`, `docker-compose.yml` |
| **Frontend & Shipper PWA Engineer** | `frontend_webgis_engineer` | Xây dựng giao diện Next.js, MapLibre GL JS, deck.gl, màn hình đặt món, Shipper PWA GPS và Academic Dashboard. | `frontend/src/app/`, `frontend/src/components/`, `frontend/public/` |
| **3D Game & Simulation Engineer** | `game_simulation_engineer` | Xây dựng mini-game HotWAY Rider (Three.js / R3F + Rapier), mesh đường 3D từ OSM, xe máy người chơi và AI Ghost. | `frontend/src/game/`, `frontend/public/models_3d/`, `src/game_assets/` |
| **System Architect & Evaluator Lead** | `evaluator_architect_lead` | Giám sát tiến độ toàn hệ thống, đánh giá tính chuẩn xác khoa học, kiểm thử tích hợp E2E và biên soạn Báo cáo Đồ án LaTeX. | `docs/`, `tests/e2e/`, `reports/`, các file gốc (`*.md`) |

---

## 2. Quy ước Giao tiếp & Hợp đồng Dữ liệu (Inter-Agent Communication Contracts)

Để tránh xung đột mã nguồn và bảo đảm khả năng tích hợp trơn tru, các Subagents bắt buộc phải tuân thủ các bản hợp đồng dữ liệu chuẩn:

### 2.1. Hợp đồng giữa `rl_researcher_engineer` và `backend_webgis_engineer`
- **Tệp xuất xưởng mô hình:** Mô hình tốt nhất được lưu tại `models/rl_best_model.zip` (định dạng Stable-Baselines3) kèm tệp cấu hình siêu tham số `models/config.json`.
- **Giao diện suy luận Python:**
```python
class HotWAYPolicyRunner:
    def __init__(self, model_path: str, graph_path: str): ...
    def predict_next_order(self, observation: dict, action_mask: list[int]) -> int: ...
```
- **Tệp Replay Log cho Ghost AI:** Xuất ra định dạng `experiments/trajectories/best_route_ghost.json`:
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

### 2.2. Hợp đồng giữa `backend_webgis_engineer` và `frontend_webgis_engineer`
- **Tài liệu OpenAPI/Swagger:** Tự động phát sinh tại `http://localhost:8000/docs`.
- **WebSocket Event Naming Convention:**
  - `SHIPPER_TELEMETRY_UPDATE` (Client $\leftarrow$ Server): Cập nhật vị trí GPS và nhiệt độ món.
  - `ORDER_STATUS_CHANGED` (Client $\leftarrow$ Server): Chuyển trạng thái đơn (PREPARING $\to$ DISPATCHED $\to$ DELIVERED).
  - `DRIVER_GPS_EMIT` (Shipper PWA $\to$ Server): Đẩy tọa độ thiết bị về máy chủ.

### 2.3. Hợp đồng giữa `game_simulation_engineer` và `frontend_webgis_engineer`
- Mini-game được đóng gói thành một React Component độc lập: `<HotWAYRiderCanvas />`.
- Nhận props điều khiển:
```typescript
interface GameProps {
  orderId: string;
  ghostTrajectoryUrl: string;
  onGameComplete: (result: { playerTempC: number; timeSeconds: number; wonAI: boolean }) => void;
}
```

---

## 3. Cấu trúc Cây Thư mục Dự án Chuẩn

```
HotWAY/
├── PRD.md
├── TECH_ARCHITECTURE.md
├── PLAN.md
├── PHASES.md
├── ROADMAP.md
├── AGENTS.md
├── docker-compose.yml
│
├── agents/
│   ├── rules/
│   │   ├── rl_engineer_rules.md
│   │   ├── backend_engineer_rules.md
│   │   ├── frontend_engineer_rules.md
│   │   ├── game_engineer_rules.md
│   │   └── evaluator_lead_rules.md
│   └── workflows/
│       ├── rl_experimentation_workflow.md
│       ├── fullstack_integration_workflow.md
│       ├── mini_game_pipeline_workflow.md
│       └── multi_agent_collaboration_workflow.md
│
├── src/
│   ├── rl/                  # Do rl_researcher_engineer quản lý
│   │   ├── environment.py
│   │   ├── newton_cooling.py
│   │   ├── osm_graph_loader.py
│   │   └── train_ppo.py
│   └── baselines/            # Các thuật toán đối chứng
│       ├── dijkstra_router.py
│       ├── greedy_solver.py
│       └── ortools_vrp.py
│
├── backend/                  # Do backend_webgis_engineer quản lý
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   └── requirements.txt
│
├── frontend/                 # Do frontend_webgis_engineer quản lý
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── game/            # Do game_simulation_engineer quản lý
│   ├── package.json
│   └── tsconfig.json
│
├── data/                     # Dữ liệu OSMnx & GeoJSON Hàng Gòn
├── models/                   # Trọng số mô hình RL đã huấn luyện
└── reports/                  # Báo cáo học thuật LaTeX & Biểu đồ
```
