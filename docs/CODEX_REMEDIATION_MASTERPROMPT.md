# MASTERPROMPT CHỈ ĐẠO SỬA LỖI TOÀN DIỆN (REMEDIATION DIRECTIVE)
## KHẮC PHỤC TRIỆT ĐỂ 17 LỖ HỔNG THEO BIÊN BẢN KIỂM TOÁN CODEX v7.3.1

> **Hướng dẫn sử dụng:**  
> Sao chép toàn bộ nội dung từ tiêu đề bên dưới và cung cấp cho **Codex Agent** (hoặc dùng làm kim chỉ nam thực thi trực tiếp trên repository) để tái cấu trúc toàn diện mã nguồn, hàm mục tiêu toán học và số liệu kiểm chuẩn của HotWAY.

---

```markdown
# CHỈ THỊ SỬA LỖI MÃ NGUỒN CẤP CAO: CHUẨN HÓA LOGIC & PRODUCTION HOTWAY v7.3.1

Bạn là **Principal Systems Engineer & Lead AI Architect**. 
Nhiệm vụ của bạn là tiếp nhận **Biên bản kiểm toán kỹ thuật HotWAY v7.3.1 (Điểm tin cậy: 28/100)** và thực thi sửa đổi dứt điểm toàn bộ **8 lỗi [FATAL]**, **6 cảnh báo [WARNING]** và **3 lỗ hổng [LOGIC GAP]** đã được vạch trần.

### Tôn chỉ sửa lỗi:
1. **Một nguồn chân lý duy nhất (Single Source of Truth) cho hàm mục tiêu:** Thời gian di chuyển cơ sở (Base Duration) chỉ lưu tốc độ không tải; hệ số giao thông $C(t)$ chỉ được nhân duy nhất 1 lần trong vòng lặp mô phỏng tích lũy thời gian thực tế `elapsed_min`.
2. **Liêm chính toán học (Mathematical Integrity):** Bỏ hoàn toàn việc cắt cúp `max(0.0, ...)`; đổi tên metric thành `relative_gap_vs_ortools_pct`; tour phải khép kín về depot và được xác thực hoán vị nghiêm ngặt bằng `validate_closed_tour()`.
3. **Không thỏa hiệp (No Cheating):** DQN vượt ngưỡng 20 điểm phải bị đánh dấu `is_overflow=True`, `valid=False`, `total_duration_min=NaN` và tính vào tỷ lệ thất bại (Failure Rate), tuyệt đối không được che giấu để tính điểm.

---

## I. CHI TIẾT CÁC BẢN SỬA LỖI THEO TỪNG TỆP MÃ NGUỒN

---

### PATCH 1: TRIỆT TIÊU NHÂN ĐÔI $C(t)$ TRONG BỘ DỮ LIỆU KIỂM CHUẨN
* **Tệp:** `scripts/build_nationwide_benchmark.py`
* **Vấn đề [FATAL F1, LOGIC GAP L2]:** Dòng 250 đã nhân `traffic_factor` vào `duration_matrix_min`, sau đó khi solver giải và đánh giá lại nhân $C(t)$ lần nữa, dẫn đến thời gian bị nhân $C_{\text{departure}} \times C_{\text{current}}$ sai lệch hoàn toàn.
* **Hành động sửa đổi:**
  1. Trong `generate_instance()`, tính ma trận thời lượng cơ sở thuần túy (không nhân traffic factor):
     ```python
     # SỬA LỖI: Chỉ tính thời gian di chuyển cơ sở (Base travel time).
     # Hệ số giao thông C(t) sẽ được áp dụng động DUY NHẤT 1 LẦN trong quá trình mô phỏng hành trình.
     dur_min = (d_km / base_speed_kmh) * 60.0
     dur_row.append(round(dur_min, 2))
     ```
  2. Cập nhật metadata của bộ dữ liệu minh bạch:
     ```python
     "dataset_type": "Synthetic nationwide benchmark based on calibrated urban tortuosity & empirical C(t)",
     ```

---

### PATCH 2: ĐỒNG NHẤT HÀM MÔ PHỎNG THỜI GIAN ĐỘNG VÀ TÁCH BIỆT LATENCY TRONG ATTENTION MODEL
* **Tệp:** `models/attention_model.py`
* **Vấn đề [FATAL F1, WARNING W3]:** Đoán trước thời gian sai và đo latency gộp cả phần dựng feature và post-processing.
* **Hành động sửa đổi:**
  1. Trong `AttentionModelWrapper.solve()`, tách riêng thời gian suy luận nơ-ron:
     ```python
     # Đo riêng biệt thời gian suy luận thuần túy của Model Forward
     if torch.cuda.is_available():
         torch.cuda.synchronize()
     t_infer_start = time.perf_counter()
     
     with torch.no_grad():
         tour_tensor, _ = self.model(feature_tensor, decode_type="greedy")
     
     if torch.cuda.is_available():
         torch.cuda.synchronize()
     inference_latency_ms = (time.perf_counter() - t_infer_start) * 1000.0
     ```
  2. Tính thời lượng động chuẩn xác qua từng cạnh tích lũy:
     ```python
     elapsed_min = 0.0
     total_dist_km = 0.0
     for i in range(len(route) - 1):
         u, v = route[i], route[i + 1]
         d_km = dist_mat[u][v]
         base_t = dur_mat[u][v]
         current_hour = (departure_hour + elapsed_min / 60.0) % 24.0
         c_t = compute_traffic_multiplier(current_hour)
         leg_min = base_t * c_t
         elapsed_min += leg_min
         total_dist_km += d_km
     ```
  3. Trả về cả `inference_latency_ms` và `solve_time_ms`.

---

### PATCH 3: TRIỆT TIÊU DEPOT LẶP [0, 0, ..., 0] TRONG POINTER NETWORK
* **Tệp:** `models/pointer_net.py`
* **Vấn đề [FATAL F6, WARNING W3]:** Mạng `PointerNetwork.forward()` đã tự chọn node 0 làm điểm bắt đầu; wrapper lại làm `route = [0] + action_seq`, khiến depot xuất hiện hai lần ở đầu tour: `[0, 0, ...]`.
* **Hành động sửa đổi:**
  Trong `PointerNetWrapper.solve()`:
  ```python
  # SỬA LỖI DEPOT LẶP:
  # self.model.forward() đã sinh ra chuỗi bắt đầu từ node 0.
  action_seq, _, _ = self.model(node_tensor, deterministic=True)
  raw_route = action_seq.squeeze(0).cpu().tolist()
  
  if raw_route[0] == 0:
      route = list(raw_route)
  else:
      route = [0] + list(raw_route)
  
  # Khép kín tour quay về depot
  if route[-1] != 0:
      route.append(0)
  ```

---

### PATCH 4: XỬ LÝ OVERFLOW & CHUẨN HÓA MIN-MAX CHO DQN AGENT
* **Tệp:** `models/dqn_agent.py` & `env/traffic_tsp_env.py`
* **Vấn đề [FATAL F5, FATAL F7]:** DQN cắt cúp điểm khi $N > 20$ nhưng vẫn trả kết quả như hợp lệ; tọa độ đầu vào chưa qua Min-Max scaling; thời lượng dùng $C(t)$ tĩnh cho toàn tuyến.
* **Hành động sửa đổi:**
  1. Trong `DQNAgentWrapper.solve()`:
     ```python
     if num_stops > 20:
         return {
             "route": [],
             "total_distance_km": float("nan"),
             "total_duration_min": float("nan"),
             "solve_time_ms": 0.0,
             "is_overflow": True,
             "valid": False,
             "error": f"DQN action space dimension fixed to max 20 stops (got {num_stops})"
         }
     ```
  2. Áp dụng Dynamic Min-Max Scaling per-instance cho tọa độ đưa vào quan sát DQN trong `env/traffic_tsp_env.py`.
  3. Tính `total_duration_min` tích lũy từng chặng theo `compute_traffic_multiplier((departure_hour + elapsed_min / 60.0) % 24.0)` giống như Attention Model.

---

### PATCH 5: ĐỒNG BỘ MỤC TIÊU VÀ MÔ PHỎNG CHO GOOGLE OR-TOOLS
* **Tệp:** `models/ortools_solver.py`
* **Vấn đề [FATAL F1, FATAL F2]:** OR-Tools dùng callback chi phí tĩnh, nhưng benchmark lại so sánh thời lượng động; cần dùng cùng một trình mô phỏng để tính kết quả cuối cùng.
* **Hành động sửa đổi:**
  1. OR-Tools giải dựa trên ma trận cự ly và thời gian cơ sở.
  2. Sau khi trích xuất được `route`, nạp `route` qua đúng hàm mô phỏng thời gian động $C(t)$ tích lũy:
     ```python
     elapsed_min = 0.0
     total_dist_km = 0.0
     for i in range(len(route) - 1):
         u, v = route[i], route[i + 1]
         d_km = dist_matrix[u][v]
         base_t = dur_matrix[u][v]
         c_t = compute_traffic_multiplier((departure_hour + elapsed_min / 60.0) % 24.0)
         elapsed_min += base_t * c_t
         total_dist_km += d_km
     ```

---

### PATCH 6: KHÉP KÍN CUNG QUAY VỀ DEPOT TRONG `train.py` & ĐỒNG BỘ VALIDATION
* **Tệp:** `train.py`
* **Vấn đề [FATAL F4, WARNING W5]:** Hàm `calc_tour_cost` tính tour mở, thiếu cạnh từ `tour[-1]` về `tour[0]`. Cập nhật baseline không qua tập validation.
* **Hành động sửa đổi:**
  1. Thay thế `calc_tour_cost` bằng phép tính vector hóa khép kín:
     ```python
     def calc_tour_cost(t_seq):
         ordered_coords = torch.gather(coords, 1, t_seq.unsqueeze(-1).expand(batch_size, n_nodes, 2))
         ordered_traffic = torch.gather(traffic, 1, t_seq.unsqueeze(-1).expand(batch_size, n_nodes, 1))
         
         # Sử dụng torch.roll để tạo cung kế tiếp (bao gồm cả cung từ node cuối về node đầu)
         next_coords = torch.roll(ordered_coords, shifts=-1, dims=1)
         next_traffic = torch.roll(ordered_traffic, shifts=-1, dims=1)
         
         seg_dists = torch.linalg.vector_norm(ordered_coords - next_coords, dim=-1)
         avg_traffic = 0.5 * (ordered_traffic[..., 0] + next_traffic[..., 0])
         return (seg_dists * avg_traffic).sum(dim=-1)
     ```
  2. Bổ sung vòng lặp validation độc lập đánh giá trước khi cập nhật baseline model.

---

### PATCH 7: XÁC THỰC HOÁN VỊ HỢP LỆ & BỎ KẸP `max(0.0, ...)` TRONG EVALUATOR
* **Tệp:** `evaluate_benchmark.py`
* **Vấn đề [FATAL F2, FATAL F3, WARNING W1]:** Bị kẹp `max(0.0, ...)`; không xác thực route; coi tour lỗi của DQN là nghiệm hợp lệ.
* **Hành động sửa đổi:**
  1. Thêm hàm kiểm tra chặt chẽ hoán vị tour đóng:
     ```python
     def validate_closed_tour(route: list[int], num_stops: int) -> bool:
         if not route or len(route) != num_stops + 2:
             return False
         if route[0] != 0 or route[-1] != 0:
             return False
         expected_nodes = set(range(num_stops + 1))
         # Nút bên trong (từ 0 đến num_stops) phải xuất hiện đúng 1 lần
         if set(route[:-1]) != expected_nodes or len(route[:-1]) != len(expected_nodes):
             return False
         return True
     ```
  2. Xử lý mô hình thất bại hoặc overflow:
     ```python
     is_valid = validate_closed_tour(route, num_stops) and not res.get("is_overflow", False)
     if not is_valid:
         failure_count += 1
         duration_list.append(float("nan"))
     else:
         duration_list.append(res["total_duration_min"])
     ```
  3. Tính toán chênh lệch tương đối trung thực (Relative Gap vs OR-Tools):
     ```python
     def compute_relative_gap(m_cost: float, ref_cost: float) -> float:
         if not np.isfinite(m_cost) or not np.isfinite(ref_cost) or ref_cost <= 0:
             return float("nan")
         # BỎ HOÀN TOÀN max(0.0, ...)
         return ((m_cost - ref_cost) / ref_cost) * 100.0
     ```
  4. Đổi tên cột trong CSV/JSON thành `mean_relative_gap_vs_ortools_pct`.

---

### PATCH 8: ĐỒNG BỘ ĐO LATENCY GPU TRONG KAGGLE NOTEBOOK
* **Tệp:** `notebooks/kaggle_train_attention_tsp.ipynb`
* **Vấn đề [WARNING W2, LOGIC GAP L1]:** Đo thời gian thiếu `synchronize()`; hàm tính thời gian chưa khớp với evaluator.
* **Hành động sửa đổi:**
  Bổ sung `torch.cuda.synchronize()` trước và sau khối đo thời gian suy luận:
  ```python
  if device.type == 'cuda':
      torch.cuda.synchronize()
  t0 = time.perf_counter()
  
  with torch.no_grad():
      tour, _ = model(t_feat, decode_type='greedy')
      
  if device.type == 'cuda':
      torch.cuda.synchronize()
  lat_ms = (time.perf_counter() - t0) * 1000.0
  ```

---

### PATCH 9: HIỂN THỊ ROUTE THỰC TẾ TRÊN WEBGIS FRONTEND
* **Tệp:** `frontend/src/app/demo/page.tsx` & `frontend/src/components/ScreenT2VRPTW.tsx`
* **Vấn đề [LOGIC GAP L3]:** MapLibre vẽ tuyến theo thứ tự ngẫu nhiên của JSON và gán cự ly bằng `num_stops * 1.8km`.
* **Hành động sửa đổi:**
  Khi người dùng chọn một hành trình trong danh sách, trích xuất thứ tự `route` thực tế từ kết quả solver đã lưu trong benchmark để nối các tọa độ:
  ```typescript
  // Lấy danh sách điểm theo đúng thứ tự tour của mô hình được chọn
  const orderedStops = instanceRoute.map((nodeIdx: number) => allNodes[nodeIdx]);
  ```

---

## II. QUY TRÌNH KIỂM CHỨNG SAU KHI SỬA LỖI (VERIFICATION PROTOCOL)

1. **Tái tạo lại bộ dữ liệu chuẩn:**
   ```bash
   python scripts/build_nationwide_benchmark.py
   ```
2. **Chạy kiểm tra tính đúng đắn của tour:**
   ```bash
   py -3.13 -m pytest tests/test_multi_model_benchmark.py tests/test_neural_tsp.py
   ```
3. **Chạy lại toàn bộ 56 tests hệ thống:**
   ```bash
   py -3.13 -m pytest tests/
   ```
4. **Chạy lại benchmark 100 POI Toàn Quốc và xuất bảng số liệu trung thực:**
   ```bash
   python evaluate_benchmark.py
   ```
5. **Kiểm tra Next.js 14 Build:**
   ```bash
   npm --prefix frontend run build
   ```

---
Hãy bắt tay thực hiện ngay từng bản vá trên theo đúng nguyên tắc khoa học và kỷ luật kỹ thuật cao nhất!
```

