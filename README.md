# HotWAY — Nền Tảng Lập Lịch & Tối Ưu Tuyến Giao Hàng CVRP

> **Tài liệu:** Tổng quan dự án và hướng dẫn vận hành  
> **Phiên bản:** v5.0.0 (Production Multi-Region & Live Benchmark Edition)  
> **Ngày cập nhật:** 21/10/2026  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ARCHITECTURE.md) | [ALGORITHM.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ALGORITHM.md) | [DECISIONS.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/docs/DECISIONS.md)

---

## 1. Giới Thiệu Dự Án

HotWAY là hệ thống điều phối và tối ưu hóa tuyến đường giao hàng chuẩn **Production** cho chuỗi quán ăn nóng (bếp trung tâm tại 490 Điện Biên Phủ, Bình Thạnh, TP.HCM) dựa trên mô hình toán **Capacitated Vehicle Routing Problem (CVRP)** kết hợp ràng buộc nhiệt động học Newton.

Hệ thống tích hợp mạng lưới đường bộ có hướng thực tế từ **OpenStreetMap** qua OSMnx (**46,055 nút, 107,224 cạnh, 8,551 km đường đô thị**), dịch vụ ma trận bất đối xứng gia tốc bằng **cKDTree** ($< 0.1\text{ms}$) và thuật toán tìm kiếm đường đi ngắn nhất Dijkstra đơn nguồn.

Toàn bộ kết quả đối soát học thuật trong thư mục `rel_result/` được **tự tay sinh ra từ pipeline benchmark độc lập** (30 instances chuẩn, 5 giao thức đánh giá, 750 lượt chạy thực nghiệm), tự huấn luyện mô hình **DQN và Double DQN** với vector đặc trưng $F28$ trên PyTorch, và kiểm định bằng phép thử phi tham số **Wilcoxon Signed-Rank** kèm hiệu chỉnh **Holm-Bonferroni**.

**Câu chủ đạo:** *Tuyến giao hàng ngắn nhất để món còn nóng.*

---

## 2. Giao Diện Người Dùng (OptimoRoute WebGIS Layout)

1. **Bàn Điều Phối & Lập Kế Hoạch (Planning):** Người điều phối chọn số xe, sức chứa thùng hàng ($Q=40$), ngưỡng nhiệt độ tối thiểu ($60^\circ\text{C}$), chọn phương pháp giải và nhận tuyến đường bám sát hình học đường thật trên bản đồ MapLibre.
2. **Strategy Lab (Nghiệm Thu Khoa Học):** Đối chiếu khoa học giữa tác tử DQN/Double DQN và các baseline theo các giao thức $A, A2, A3, B, B2$; giải thích 3 nguyên nhân cốt lõi vì sao DQN không vượt qua được baseline trên dữ liệu nghiệm thu thực tế.
3. **Search Replay & Điều Phối Live:** Phát lại từng bước chọn toán tử của Local Search với thanh tua tốc độ $1\times, 4\times, 16\times$ và theo dõi xe mô phỏng di chuyển trên đồ thị có hướng thật.
4. **Interactive Notebook (`notebooks/cvrp_benchmark.ipynb`):** Sổ tay Jupyter phân tích trực quan toàn diện từ cấu trúc đồ thị, phân bố khách hàng, đường cong học RL đến biểu đồ hộp so sánh chi phí và kiểm định thống kê.

---

## 3. Hướng Dẫn Khởi Chạy (3 Lệnh Duy Nhất)

### Lệnh 1: Khởi động cơ sở hạ tầng Backend (Docker hoặc Local)
```bash
# Khởi chạy backend qua docker:
docker compose up -d

# Hoặc khởi chạy local development trực tiếp:
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend FastAPI hoạt động tại `http://localhost:8000`, cung cấp tài liệu OpenAPI tại `http://localhost:8000/docs`.

### Lệnh 2: Khởi chạy Giao diện Frontend (Cổng 3001)
```bash
cd frontend && npm run dev
# Hoặc chạy bản build production: npm run start -- -p 3001
```
Giao diện mở tại `http://localhost:3001` (Cổng 3000 được bảo vệ nguyên vẹn).

### Lệnh 3: Chạy toàn bộ kiểm thử tự động
```bash
pytest tests/ -v
```
*(Toàn bộ 15/15 tests thuộc 4 tầng Gate 1-5 đều PASS tuyệt đối: Geometry, Solver Feasibility, Data Consistency, Audit Trail)*.

---

## 4. Pipeline Dành Cho AI Data Engineer

Dự án cung cấp bộ công cụ dòng lệnh hoàn chỉnh để tái tạo toàn bộ dữ liệu từ đầu:

```bash
# 1. Tải và xây dựng đồ thị OSMnx TP.HCM (46k nút, 107k cạnh, SCC 100%):
python -m src.data.build_graph --region hcmc_compact

# 2. Sinh bộ dữ liệu 30 instances chuẩn trên đường thật TP.HCM:
python -m src.benchmark.instance_generator --region hcmc_compact

# 3. Huấn luyện tác tử DQN & Double DQN trên F28 features:
python -m src.rl.train_cvrp_rl --instances-dir data/benchmark_instances --episodes 25

# 4. Chạy Benchmark 750 lượt trên 5 giao thức (A2, A, A3, B, B2):
python -m src.benchmark.runner

# 5. Thực hiện kiểm định thống kê Wilcoxon & Holm-Bonferroni:
python -m src.benchmark.analysis

# 6. Khởi động Jupyter Notebook tương tác:
jupyter notebook notebooks/cvrp_benchmark.ipynb
```

---

## 5. Cấu Trúc Thư Mục Dự Án

```
HotWAY/
├── config/
│   └── site.yaml             # Nguồn sự thật duy nhất (depot, multi-region, fleet, thermal)
├── data/
│   ├── hcmc_compact_graph.pickle # Đồ thị TP.HCM OSMnx (46,055 nút, 107,224 cạnh)
│   ├── hcmc_compact_graph.graphml# Định dạng GraphML tiêu chuẩn
│   ├── hcmc_compact_roads.geojson# Dữ liệu hình học cạnh cho MapLibre (107k features)
│   ├── binhthanh_graph.pickle    # Đồ thị thu nhỏ Bình Thạnh (legacy demo)
│   └── benchmark_instances/      # 30 instances chuẩn hóa (HCMC_VN_01 -> HCMC_VN_30)
├── notebooks/
│   └── cvrp_benchmark.ipynb      # Jupyter Notebook phân tích học thuật trực quan
├── rel_result/                   # Bộ kết quả thực nghiệm khoa học tự sinh 100%
│   ├── raw_runs.csv              # 750 bản ghi chạy chi tiết từng bước
│   ├── summary_by_algorithm.csv  # Bảng tổng hợp theo phương pháp (A, A2, A3, B, B2)
│   ├── paired_comparisons.csv    # Kiểm định thống kê Wilcoxon & Holm-Bonferroni
│   ├── per_decision_cost.csv     # Chi phí tính toán và số candidate đánh giá
│   ├── training_curves.csv       # Đường cong học của DQN và Double DQN
│   └── legacy_pdf_reference/     # Bản lưu trữ dữ liệu đối chứng lịch sử
├── src/
│   ├── data/                 # build_graph.py xây dựng mạng lưới đường có hướng OSMnx
│   ├── services/             # road_matrix.py (cKDTree snap, Dijkstra on-demand)
│   ├── cvrp_solver/          # problem, validator, constructive, operators, search, F28
│   │   └── weights/          # Checkpoint trọng số PyTorch (dqn_model.pt, double_dqn_model.pt)
│   ├── benchmark/            # instance_generator, runner, analysis
│   └── rl/                   # train_cvrp_rl.py pipeline huấn luyện Q-Network F28
├── backend/                  # FastAPI Monolith (/api/v1)
├── frontend/                 # Next.js 14 WebGIS (OptimoRoute Layout, 6 màn hình)
└── tests/                    # Bộ kiểm thử 4 tầng (Geometry D4, Solver T2, Data T3, Honesty T4)
```
