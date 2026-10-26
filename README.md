# HotWAY — Nền Tảng Học Tăng Cường Điều Phối Thời Gian Thực Cho Giao Vận Đô Thị

> **Tài liệu:** Báo cáo Tổng Quan Hệ Thống & Hướng Dẫn Vận Hành Production  
> **Phiên bản:** v6.2.0 (Real-Time RL Restaurant Dispatch Edition - Production & Final Publication)  
> **Ngày cập nhật:** 24/10/2026  
> **Báo cáo nghiên cứu chính thức:** [docs/HotWAY_Final_Research_Report.pdf](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/HotWAY_Final_Research_Report.pdf) | [docs/FINAL_RESEARCH_REPORT.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/FINAL_RESEARCH_REPORT.md)  
> **Tài liệu kỹ thuật liên quan:** [PRD.md](file:///c:/Users/Asus/Documents/AI/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ARCHITECTURE.md) | [ALGORITHM.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ALGORITHM.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md) | [TESTING.md](file:///c:/Users/Asus/Documents/AI/HotWAY/TESTING.md)

---

## 1. Giới Thiệu Dự Án & Tóm Tắt Đổi Hướng Nghiên Cứu

HotWAY là hệ thống điều phối giao hàng thời gian thực chuẩn **Production & Research** cho nhà hàng đô thị tại TP.HCM. Dự án tập trung giải quyết bài toán cốt lõi: **Tối thiểu hóa thời gian chờ đợi của khách hàng** ($W_i = t_{\text{giao}, i} - t_{\text{đặt}, i}$) bằng phương pháp Học tăng cường (Reinforcement Learning) kết hợp quy hoạch động tổ hợp dưới dạng **Semi-Markov Decision Process (Semi-MDP)**.

### 1.1. Thí Nghiệm Khởi Đầu E0 (Động cơ chuyển hướng)
* **Hướng cũ (v5.0.0):** Mô hình hóa CVRP tĩnh kết hợp phương trình làm nguội Newton, dùng DQN chọn 1 trong 4 toán tử Local Search trên đồ thị TP.HCM.
* **Kết quả đối soát học thuật:** Toàn bộ kết quả thực nghiệm và mã nguồn cũ được lưu trữ nguyên vẹn tại `archive_e0/` và `rel_result/`. Thuật toán ngẫu nhiên (Random) đạt chi phí $656.359\text{ km}$, tốt hơn tác tử DQN $657.897\text{ km}$ ($p_{\text{Holm}} = 0.0072$).
* **Bài học khoa học:** Lời giải Clarke-Wright khởi tạo đã quá gần biên tối ưu khiến dư địa cải thiện của Local Search chỉ còn khoảng $0.1\%$. Do đó, việc dùng RL để chọn toán tử cục bộ không mang lại giá trị khác biệt. Đồng thời, nhiệt độ thức ăn phụ thuộc vào quy trình bếp chứ không quan sát được trên đường. Dự án đã **bỏ hoàn toàn ràng buộc nhiệt độ Newton và câu slogan "để món còn nóng"**, chuyển toàn bộ trọng tâm sang **Thời Gian Chờ Của Khách Hàng**.

### 1.2. Hai Bài Toán Cốt Lõi
1. **Giai đoạn 1 (GĐ1 - Nền tảng kiểm chứng):** Định tuyến thích nghi $A \to B$ trên đồ thị con 12 nút strongly connected (SCC) tại Bình Thạnh; đối chiếu chân lý với **Quy hoạch động chính xác (Exact Value Iteration)**.
2. **Giai đoạn 2 (GĐ2 - Lõi nghiên cứu HotWAY):** Điều phối đơn tại quán ăn dưới dạng **Semi-MDP**. Quá trình đơn đến Poisson không đồng nhất với đợt bùng nổ đột biến (Surge $3.5\times$); máy trạng thái đơn 5 pha (`Placed` $\to$ `Cooking` $\to$ `Ready` $\to$ `In-Transit` $\to$ `Delivered`); bảo đảm đẳng thức bảo toàn phần thưởng Bellman $\sum R = -\sum W_i$ với sai số tuyệt đối $< 10^{-11}$.

---

## 2. Bảng Tổng Hợp Kết Quả Thực Nghiệm & Đối Soát Khoa Học

Toàn bộ số liệu trong bảng được sinh tự động từ tệp kết quả gốc tại `results/all_metrics_registry.json` và vượt qua kiểm thử độ trung thực T3 (`tests/test_report_fidelity.py`):

| Phương pháp / Mô hình | Thời gian chờ TB $W$ (phút) | 95% Bootstrap CI | p90 (phút) | Tỷ lệ trễ ETA (%) | Gini khách | Tải tài xế (%) | Tổng km | p_Holm vs Imm |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Immediate (Xuất phát ngay)** | **89.70** | [78.27, 98.62] | 173.57 | 81.6% | 0.324 | 91.4% | 794.7 | Reference |
| **BatchSize ($k=1$)** | 89.70 | [78.27, 98.62] | 173.57 | 81.6% | 0.324 | 91.4% | 794.7 | 1.000 |
| **AgeThreshold ($\theta=10.0\text{m}$)** | 90.39 | [78.42, 99.36] | 171.77 | 82.9% | 0.319 | 91.3% | 794.7 | 0.375 |
| **Periodic ($T=8.0\text{m}$)** | 93.06 | [80.66, 103.41] | 173.50 | 88.2% | 0.305 | 87.6% | 761.4 | 0.375 |
| **DQN (5 seeds)** | 114.06 | [103.82, 125.37] | 214.93 | 85.0% | 0.331 | 91.3% | 862.0 | 0.375 |
| **Double DQN (5 seeds)** | 118.29 | [102.82, 136.50] | 238.83 | 84.7% | 0.333 | 89.3% | 840.1 | 0.375 |
| **PPO (5 seeds)** | 118.94 | [112.16, 126.19] | 227.45 | 87.6% | 0.332 | 90.5% | 863.8 | 0.375 |

> **Công bố kết quả âm tính (Open Science):** Dưới lưu lượng đô thị dày đặc và thời gian nấu bếp ngẫu nhiên log-normal, quy tắc phản xạ **Immediate Dispatch** đạt hiệu quả cao nhất ($89.70\text{ min}$), vượt trội hơn DQN ($114.06\text{ min}$), Double DQN ($118.29\text{ min}$) và PPO ($118.94\text{ min}$). Các mô hình RL bị thiên lệch phóng đại giá trị hành động Chờ (overestimation bias $+45.2\%$ ở DQN) dẫn đến tích tụ hàng đợi dây chuyền.

---

## 3. Kiến Trúc 4 Chiều Phân Tích Mô Hình (Deep Model Analytics)

Các biểu đồ phân tích chuyên sâu được sinh tự động tại `results/figures/`:
1. **Queue Waterfall & Saturation Dynamics (`queue_waterfall_dynamics.png`):** Phân tích sự tích tụ hàng đợi dưới đợt đột biến $3.5\times$; heuristic gom đơn gây nghẽn đỉnh điểm 73 đơn, trong khi điều phối động giải phóng hàng đợi nhanh hơn 44%.
2. **Q-Value Landscape & Failure Modes (`q_value_landscape_failures.png`):** Vết phân rã hàm giá trị $Q(s, a)$, chứng minh Double DQN khắc phục thiên lệch phóng đại của DQN nhưng vẫn chịu tỷ lệ chọn nhầm hành động chờ $14.1\%$.
3. **Pareto Efficiency Frontier (`pareto_frontier_tradeoff.png`):** Biên hiệu quả Pareto giữa Thời gian chờ khách hàng và Tổng quãng đường km; Periodic Dispatch tiết kiệm cự ly ($761.4\text{ km}$) nhưng tăng thời gian chờ ($93.06\text{ min}$); các tác tử RL nằm hoàn toàn trong vùng bị lấn át.
4. **Multi-parametric Sensitivity Matrix (`sensitivity_heatmap_matrix.png`):** Ma trận độ nhạy $2 \times 3$ giữa Mưa bão đô thị ($1.0\times$ vs $1.4\times$) và Tốc độ bếp ($8\text{m}, 12\text{m}, 16\text{m}$). Mưa bão làm thời gian chờ tăng $+56.2\%$.

---

## 4. Hướng Dẫn Vận Hành & Tái Lập (Reproducibility)

### 4.1. Chạy Bộ Kiểm Thử Tự Động
```bash
pytest tests/ -v
```

### 4.2. Khởi Động Backend API Server (:8000)
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* API Documentation: `http://localhost:8000/docs`
* Event Stream SSE: `http://localhost:8000/api/v1/sim/stream`
* Benchmark Summary: `http://localhost:8000/api/v1/sim/benchmark_summary`

### 4.3. Khởi Động Frontend WebGIS Console (:3001)
```bash
cd frontend
npm run build
npm run start -- -p 3001
```
* Giao diện người dùng: `http://localhost:3001`
* **Quy tắc an toàn mạng:** Cổng **3000** tuyệt đối bị cấm sử dụng.

### 4.4. Tái Lập Biểu Đồ & Xuất Báo Cáo Học Thuật PDF
```bash
# 1. Sinh 4 biểu đồ phân tích chuyên sâu & tệp kết quả
python -m scripts.generate_model_analytics

# 2. Biên dịch báo cáo chuẩn IEEE/ACM dạng PDF đơn sắc
python scripts/export_pdf_report.py
```

---

## 5. Cấu Trúc Thư Mục Chuẩn Tinh Gọn

```
HotWAY/
├── backend/app/                 # FastAPI Monolith (:8000)
│   ├── api/realtime_dispatch.py # Streaming SSE, Parallel, Benchmark Endpoints
│   └── main.py                  # ASGI Application Factory
├── frontend/                    # Next.js 14 OptimoRoute Console (:3001)
│   ├── src/app/page.tsx         # 3 Phân hệ chính: Live, Orders, Strategy Lab
│   └── src/components/          # ScreenLiveDispatch, ScreenStrategyLab, MapLibre
├── src/                         # Core Semi-MDP RL & Dispatch Engine
│   ├── envs/dispatch_env.py     # Native Gymnasium Semi-MDP Environment
│   ├── agents/                  # DQN, Double DQN, PPO Checkpoints & PyTorch Modules
│   └── routing/                 # Permutation Exhaustive Router & Nearest Neighbor
├── docs/                        # Chuỗi tài liệu nghiên cứu
│   ├── HotWAY_Final_Research_Report.pdf # Báo cáo nghiên cứu học thuật PDF đơn sắc
│   ├── FINAL_RESEARCH_REPORT.md         # Báo cáo học thuật Markdown
│   └── research/                # Chuỗi bài báo chuyên đề 00-06
├── results/                     # Số liệu thực nghiệm bất biến
│   ├── all_metrics_registry.json# Registry 97 chỉ số niêm phong
│   ├── model_analytics_data.json# Dữ liệu phân tích 4 chiều
│   └── figures/                 # 4 Biểu đồ học thuật phân giải cao 300 DPI
├── archive_e0/                  # Kho lưu trữ mã nguồn CVRP tĩnh cũ (E0)
└── tests/                       # Bộ kiểm thử 4 tầng T1-T7
```
