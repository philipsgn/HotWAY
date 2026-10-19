# HotWAY — Dynamic Thermal-Aware Food Delivery Optimization System

> **Hệ sinh thái Điều phối Giao hàng Thông minh Tối ưu Hóa Nhiệt độ Món ăn bằng Học Tăng Cường (Reinforcement Learning)**  
> **Địa bàn thực nghiệm:** Quán Bánh Canh Gà Hàng Gòn — Xã Hàng Gòn, TP. Long Khánh, Tỉnh Đồng Nai  
> **Đồ án môn học:** Học Tăng Cường (Reinforcement Learning) & WebGIS  

---

## 🌟 Điểm Nhấn Sáng Tạo Cốt Lõi (Core Innovations)

1. **Lõi Học Tăng Cường Bảo Toàn Nhiệt Độ (60% Trọng số Đề tài):**
   - Giải quyết biến thể bài toán **Dynamic VRP with Time Windows and Temperature Decay (DVRP-TW-TD)**.
   - Ứng dụng **Định luật làm nguội Newton** $T(t) = T_{\text{env}} + (T_0 - T_{\text{env}}) \cdot e^{-kt}$ đa tham số cho bánh canh gà nóng sốt, đồ khô và nước giải khát kèm 3 loại túi giữ nhiệt.
   - Không gian hành động phân cấp (Hierarchical MDP): High-level RL Agent gom và sắp xếp thứ tự đơn, Low-level routing đường phố thực tế Hàng Gòn qua OSRM/A*.
2. **Bộ Thuật toán Đối chứng Toàn diện (Baselines & Ablation Study):**
   - So sánh trực tiếp RL (MaskablePPO, DQN) với Dijkstra, Greedy Nearest Neighbor và Google OR-Tools VRP.
   - Thử nghiệm bóc tách (Ablation study) chứng minh tác động vượt trội của hàm thưởng nhiệt độ đối với chất lượng món ăn khi đến tay khách.
3. **Nền tảng WebGIS & Real-time Platform:**
   - Bản đồ MapLibre GL JS + deck.gl hiển thị chuyển động của shipper mượt 60 FPS.
   - Đồng hồ đo nhiệt độ món ăn cập nhật thời gian thực qua WebSocket.
   - Ứng dụng Shipper PWA thu thập GPS thực tế trên điện thoại hoặc giả lập kẹt xe giờ cao điểm.
4. **Mini-game 3D Đua xe với AI ("HotWAY Rider"):**
   - Dựng trực tiếp mesh 3D đường phố và khối nhà Hàng Gòn từ dữ liệu OpenStreetMap (Three.js / React Three Fiber + Rapier physics).
   - Đua xe máy với "bóng ma" (Ghost AI) chạy theo đúng lộ trình RL tối ưu; tính điểm theo nhiệt độ món ăn khi về đích và tặng voucher giảm giá thật của quán.

---

## 📚 Bộ Tài liệu Đặc tả Hệ thống (Documentation Suite)

| Tài liệu | Mô tả chi tiết |
|---|---|
| [**PRD.md**](PRD.md) | Tài liệu Yêu cầu Sản phẩm: Bối cảnh, Chân dung người dùng, Mô hình toán học MDP, Định luật Newton, Ma trận tính năng MVP & Out-of-scope. |
| [**TECH_ARCHITECTURE.md**](TECH_ARCHITECTURE.md) | Kiến trúc Kỹ thuật Toàn diện: Sơ đồ khối, Tech Stack (FastAPI, PostGIS, Redis, Next.js, MapLibre, SB3, Three.js), Database Schemas và WebSocket Protocol. |
| [**PLAN.md**](PLAN.md) | Kế hoạch Thực hiện Dự án: Phân rã công việc WBS (60% RL - 25% Web - 15% Game), Quản trị rủi ro và Tiêu chí thành công (Definition of Done). |
| [**PHASES.md**](PHASES.md) | Chi tiết 5 Giai đoạn Triển khai: Từ thu thập GIS, huấn luyện RL, xây dựng WebGIS, tích hợp hệ thống đến bảo vệ đồ án. |
| [**ROADMAP.md**](ROADMAP.md) | Lộ trình 12 Tuần: Tiến độ chi tiết từng tuần, các mốc bàn giao sản phẩm và phân bổ công việc. |
| [**AGENTS.md**](AGENTS.md) | Kiến trúc Đa tác tử (Multi-Agent System): Phân chia 5 Subagents chuyên biệt, hợp đồng dữ liệu và cấu trúc thư mục làm việc. |

---

## 🤖 Hệ thống Subagents Chuyên biệt (`agents/`)

Hệ thống được chia nhánh thành 5 vai trò tác tử độc lập, mỗi vai trò có bộ quy tắc (Rules) và quy trình chuẩn (SOP Workflows) riêng:

### 1. Bộ Quy tắc Hành vi (`agents/rules/`)
- [**rl_engineer_rules.md**](agents/rules/rl_engineer_rules.md): Quy chuẩn cho `rl_researcher_engineer` (Gymnasium, SB3, Reproducibility seed, Baselines, Ablation study).
- [**backend_engineer_rules.md**](agents/rules/backend_engineer_rules.md): Quy chuẩn cho `backend_webgis_engineer` (FastAPI async, PostGIS spatial queries, WebSocket Hub, Docker Compose).
- [**frontend_engineer_rules.md**](agents/rules/frontend_engineer_rules.md): Quy chuẩn cho `frontend_webgis_engineer` (Next.js TypeScript, MapLibre, deck.gl, Shipper PWA, Split Dashboard).
- [**game_engineer_rules.md**](agents/rules/game_engineer_rules.md): Quy chuẩn cho `game_simulation_engineer` (Three.js/R3F low-poly, Rapier physics, Ghost AI replay, Thermal HUD).
- [**evaluator_lead_rules.md**](agents/rules/evaluator_lead_rules.md): Quy chuẩn cho `evaluator_architect_lead` (Gatekeeper, kiểm thử E2E, báo cáo học thuật LaTeX, slide thuyết trình).

### 2. Quy trình Vận hành Chuẩn (`agents/workflows/`)
- [**rl_experimentation_workflow.md**](agents/workflows/rl_experimentation_workflow.md): Quy trình 8 bước huấn luyện mô hình RL, TensorBoard logging và xuất file trọng số/trajectory.
- [**fullstack_integration_workflow.md**](agents/workflows/fullstack_integration_workflow.md): Quy trình kết nối API, PostGIS, WebSocket Hub và WebGIS.
- [**mini_game_pipeline_workflow.md**](agents/workflows/mini_game_pipeline_workflow.md): Quy trình sinh địa hình 3D từ OSM GeoJSON và tích hợp xe máy người chơi/AI Ghost.
- [**multi_agent_collaboration_workflow.md**](agents/workflows/multi_agent_collaboration_workflow.md): Quy trình bàn giao sản phẩm qua 4 Cổng Kiểm định (Verification Gates) và giải quyết xung đột.

---

## 🚀 Cấu trúc Thư mục Dự án

```
HotWAY/
├── PRD.md                         # Đặc tả bài toán & MDP
├── TECH_ARCHITECTURE.md           # Kiến trúc kỹ thuật & Sơ đồ
├── PLAN.md                        # Kế hoạch & Quản trị rủi ro
├── PHASES.md                      # Chi tiết 5 giai đoạn triển khai
├── ROADMAP.md                     # Lộ trình 12 tuần
├── AGENTS.md                      # Kiến trúc Đa tác tử
├── README.md                      # Tổng quan & Điều hướng
│
├── agents/                        # Cấu hình Subagents
│   ├── rules/                     # 5 Bộ quy tắc kỹ thuật
│   └── workflows/                 # 4 Quy trình chuẩn (SOP)
│
├── src/                           # Mã nguồn RL Core & Baselines
│   ├── rl/
│   └── baselines/
│
├── backend/                       # FastAPI Monolith, PostGIS & WebSocket
├── frontend/                      # Next.js 14, MapLibre & Three.js Game
├── data/                          # Bản đồ OSMnx & GeoJSON Hàng Gòn
├── models/                        # Trọng số mô hình RL đã huấn luyện
└── reports/                       # Báo cáo học thuật LaTeX & Biểu đồ
```

---

## 🌐 Đường Dẫn Truy Cập Cục Bộ (Local Services Port 3001 & 8000)

> [!NOTE]
> Để tránh xung đột với các dịch vụ đang chạy trên cổng 3000, giao diện Frontend HotWAY được cấu hình mặc định trên **Cổng 3001**.

- 🍲 **Trang Đặt Món Khách Hàng:** `http://localhost:3001`
- 📱 **Ứng Dụng Tài Xế Shipper PWA:** `http://localhost:3001/shipper`
- 📊 **Studio Đối Chứng Khoa Học RL vs Baseline:** `http://localhost:3001/admin/comparison-studio`
- 🎮 **Mini-Game 3D Đua Xe Với AI Ghost:** `http://localhost:3001/game/rider`
- 📖 **Tài Liệu Swagger API Backend:** `http://localhost:8000/docs`
