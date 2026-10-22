# Kế Hoạch Triển Khai & Bàn Giao Kỹ Thuật (PLAN.MD) — HotWAY

> **Tài liệu:** Kế hoạch thực hiện hợp nhất từ PLAN, PHASES và ROADMAP  
> **Phiên bản:** v5.0.0 (Production Multi-Region & Live Benchmark Edition)  
> **Ngày cập nhật:** 21/10/2026  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ARCHITECTURE.md) | [TESTING.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/TESTING.md)

---

## 5 Giai Đoạn Triển Khai v5.0 (AI Data Engineer Edition)

```mermaid
flowchart LR
    G1["Phase 1\nĐồ thị TP.HCM OSMnx\n(46k nút, 107k cạnh)"] --> G2["Phase 2\nInstance Generator\n(30 instances chuẩn)"]
    G2 --> G3["Phase 3\nHuấn luyện RL PyTorch\n(DQN & Double DQN F28)"]
    G3 --> G4["Phase 4\nBenchmark & Thống Kê\n(750 runs, Wilcoxon/Holm)"]
    G4 --> G5["Phase 5\nTích hợp UI & Notebook\n(6 màn hình, Jupyter)"]
```

---

### Giai Đoạn 1: Đồ Thị Đường Bộ TP.HCM Thực Tế & Spatial Indexing
- **Mục tiêu:** Thay thế đồ thị 38 nút bằng đồ thị đường bộ thực tế toàn TP.HCM từ OpenStreetMap (OSMnx) và dịch vụ ma trận gia tốc.
- **Đầu ra kiểm chứng được:**
  - `data/hcmc_compact_graph.pickle` (**46,055 nút**, **107,224 cạnh**, **8,551.9 km đường**).
  - `data/hcmc_compact_graph.graphml`, `data/hcmc_compact_roads.geojson`.
  - Mạng lưới liên thông mạnh 100% (SCC Verified).
  - `src/services/road_matrix.py` tích hợp **cKDTree** snapping thời gian thực ($< 0.1\text{ms}$) và Dijkstra đơn nguồn.
- **Checklist nghiệm thu:**
  - [x] Tạo `config/site.yaml` đa vùng (`binhthanh` demo, `hcmc_compact` production).
  - [x] Nâng cấp `src/data/build_graph.py` tải OSMnx và chuẩn hóa toạ độ.
  - [x] Vượt qua 5/5 test case hình học tại `tests/test_geometry.py`.

---

### Giai Đoạn 2: Bộ Sinh Dữ Liệu Thực Nghiệm (Instance Generator)
- **Mục tiêu:** Xây dựng pipeline tự động sinh dữ liệu CVRP ngẫu nhiên bám theo tim đường thật TP.HCM, thay thế dữ liệu tĩnh cũ.
- **Đầu ra kiểm chứng được:**
  - `src/benchmark/instance_generator.py`.
  - Thư mục `data/benchmark_instances/` chứa **30 instances chuẩn hóa** (`HCMC_VN_01.pickle` $\dots$ `HCMC_VN_30.pickle`) cùng index tóm tắt `instances_index.json`.
  - Mỗi instance gồm 15-25 khách hàng, tọa độ snap chính xác vào nút đường, tải ngẫu nhiên [1, 8] tô, sức chứa $Q=40$.
- **Checklist nghiệm thu:**
  - [x] Bộ sinh dữ liệu kiểm soát hoàn toàn bằng seed (`base_seed + instance_idx`) bảo đảm tính khả lặp 100%.
  - [x] Tự động tính toán ma trận chi phí bất đối xứng cho từng instance từ đồ thị OSMnx thật.

---

### Giai Đoạn 3: Huấn Luyện Tác Tử RL Tuyến Đường (PyTorch DQN / Double DQN)
- **Mục tiêu:** Huấn luyện mạng nơ-ron Q-Network ($28 \to 128 \to 128 \to 4$) thực sự chọn toán tử Local Search, lưu trữ trọng số có thể kiểm tra.
- **Đầu ra kiểm chứng được:**
  - `src/rl/train_cvrp_rl.py`: Pipeline huấn luyện Q-learning với Replay Buffer và $\epsilon$-greedy.
  - `src/cvrp_solver/weights/dqn_model.pt` & `src/cvrp_solver/weights/double_dqn_model.pt`.
  - `rel_result/training_curves.csv`: Ghi nhận loss, reward và quãng đường tiết kiệm qua từng episode.
- **Checklist nghiệm thu:**
  - [x] Tích hợp bộ trích xuất đặc trưng trạng thái $F28$ chuẩn mực.
  - [x] `src/cvrp_solver/search.py` tự động nạp trọng số đã train khi chạy chiến lược DQN/Double DQN.

---

### Giai Đoạn 4: Benchmark Tự Động & Kiểm Định Thống Kê Chuyên Sâu
- **Mục tiêu:** Thực thi 750 lượt chạy qua 5 giao thức ($A2, A, A3, B, B2$) và kiểm định khoa học.
- **Đầu ra kiểm chứng được:**
  - `src/benchmark/runner.py` & `src/benchmark/analysis.py`.
  - `rel_result/raw_runs.csv`: 750 dòng dữ liệu chi tiết từng lượt chạy.
  - `rel_result/summary_by_algorithm.csv`: 25 dòng tóm tắt hiệu năng, độ khả thi 100%, 95% Bootstrap CI.
  - `rel_result/paired_comparisons.csv`: 35 cặp so sánh với phép thử Wilcoxon Signed-Rank và hiệu chỉnh Holm-Bonferroni.
  - `rel_result/per_decision_cost.csv`: Thời gian suy luận mạng nơ-ron và số ứng viên khảo sát.
- **Checklist nghiệm thu:**
  - [x] Vượt qua 4/4 test case dữ liệu tại `tests/test_benchmark_data.py`.
  - [x] Lưu trữ bản đối chứng lịch sử tại `rel_result/legacy_pdf_reference/`.

---

### Giai Đoạn 5: Giao Diện OptimoRoute & Jupyter Notebook Tương Tác
- **Mục tiêu:** Hoàn thiện trải nghiệm người dùng và cung cấp công cụ phân tích tương tác.
- **Đầu ra kiểm chứng được:**
  - `notebooks/cvrp_benchmark.ipynb`: Notebook trực quan hóa toàn diện đồ thị, phân bố khách hàng, đường cong học RL, biểu đồ hộp so sánh chi phí và kiểm định thống kê.
  - Giao diện 6 màn hình WebGIS (Đơn hàng, Lập kế hoạch, Chi tiết tuyến, Strategy Lab, Search Replay, Điều phối Live).
  - Vượt qua 15/15 test cases toàn diện trong kho mã nguồn.
- **Checklist nghiệm thu:**
  - [x] Backend FastAPI phản hồi đầy đủ dữ liệu mới từ `rel_result/`.
  - [x] Cổng 3000 được bảo vệ an toàn, Frontend chạy cổng 3001, Backend chạy cổng 8000.
