# Đặc Tả Kỹ Thuật: Trình Diễn Họa Thuật Toán Tìm Đường Không Gian Thời Gian Thực

> **Tài liệu:** Kiến trúc hệ thống, API đặc tả & Diễn họa sóng đồ thị thời gian thực cho báo cáo Hội đồng  
> **Tuyến truy cập WebGIS:** `http://localhost:3001/visualizer`  
> **Tệp mã nguồn:** `backend/app/services/graph_stepper.py`, `backend/app/api/endpoints/visualizer.py`, `frontend/src/app/visualizer/page.tsx`, `frontend/src/components/WavefrontCanvas.tsx`, `frontend/src/components/VisualizerHUD.tsx`

---

## 1. Mục Tiêu & Bối Cảnh

Để phục vụ trình diễn học thuật và minh chứng khả năng tìm đường thực tế của hệ thống HotWAY, ứng dụng **Pathfinding Wavefront Visualizer** trực quan hóa từng bước lan truyền của sóng thuật toán trên mạng lưới đường phố thực tế với đồ họa độ tương phản cao phong cách Cyber-Sci-Fi.

Người dùng chọn Điểm Xuất Phát (Start) và Điểm Đích (Destination) trên bản đồ đêm, hệ thống backend tính toán và ghi lại toàn bộ chuỗi mở rộng đỉnh/cạnh theo trình tự thời gian (**chronological animation frames**), sau đó frontend diễn họa mượt mà ở tốc độ 60 FPS qua HTML5 Canvas overlay.

---

## 2. Kiến Trúc Backend: Graph Step Engine

### 2.1 Cấu Trúc Đồ Thị Thực Tế
- Đồ thị được trích xuất từ dữ liệu OpenStreetMap (OSM) khu vực trung tâm TP.HCM, lọc thành thành phần liên thông mạnh (Strongly Connected Component - SCC) gồm:
  - **2,957 đỉnh (nodes)**
  - **6,735 cạnh có hướng (directed edges)**
- Định dạng lưu trữ: `data/visualizer_graph_scc.pickle`

### 2.2 Các Thuật Toán Được Hiện Thực Hóa
1. **A\* Search:**
   - Sử dụng hàm Heuristic khoảng cách Haversine $h(n)$ làm dưới (admissible).
   - Sóng mở rộng hình elip tập trung hướng về đích, giảm thiểu số đỉnh cần khám phá.
   - Thống kê: **261 bước duyệt**, độ trễ **11.54 ms**, cự ly **2.588 km**.
2. **Dijkstra (Uniform Cost Search):**
   - Khám phá đồng mức chi phí khoảng cách theo hình tròn 360 độ từ điểm xuất phát.
   - Thống kê: **675 bước duyệt**, độ trễ **104.2 ms**, cự ly **2.588 km**.
3. **Bidirectional Search:**
   - Kích hoạt 2 đầu tìm kiếm song song từ Start tiến tới và từ End lùi lại, gặp nhau ở giữa.
   - Thống kê: **566 bước duyệt**, độ trễ **10.89 ms**, cự ly **2.588 km**.
4. **HotWAY Dynamic Dijkstra với Phạt Tắc Đường $C(t)$:**
   - Giả lập điểm nghẽn giao thông cực lớn trên trục đường chính Điện Biên Phủ / Hàng Xanh.
   - Sóng tự động uốn lượn né tránh trục kẹt xe, chọn đường vòng nhanh hơn dù cự ly tăng lên **2.777 km**.

### 2.3 Đặc Tả REST API
- `GET /map/bounds`:
  ```json
  {
    "status": "success",
    "bounds": {
      "min_lat": 10.770, "max_lat": 10.815,
      "min_lon": 106.685, "max_lon": 106.735
    },
    "sample_landmarks": [
      {"name": "Landmark 81", "lat": 10.7951, "lon": 106.7218},
      {"name": "Ngã tư Hàng Xanh", "lat": 10.8014, "lon": 106.7112}
    ]
  }
  ```
- `POST /api/solve-path`:
  - Request:
    ```json
    {
      "start_coords": [10.8014, 106.7112],
      "end_coords": [10.7951, 106.7218],
      "algorithm": "a_star",
      "max_steps": 1200
    }
    ```
  - Response:
    ```json
    {
      "status": "success",
      "algorithm": "a_star",
      "metrics": {
        "compute_time_ms": 11.54,
        "nodes_visited_count": 261,
        "path_distance_km": 2.588,
        "path_duration_min": 5.18
      },
      "frames": [
        {"step": 0, "type": "visit", "node_id": 1497276525, "coords": [10.8014, 106.7112]},
        {"step": 1, "type": "frontier", "node_id": 533701234, "coords": [10.8018, 106.7119]}
      ],
      "path": [[10.8014, 106.7112], [10.8015, 106.7118], ...]
    }
    ```

---

## 3. Kiến Trúc Frontend: Canvas Overlay 60 FPS

- **Thư viện bản đồ:** MapLibre GL JS với CartoDB Dark Matter tiles (`https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`).
- **Canvas Renderer (`WavefrontCanvas.tsx`):**
  - Đồng bộ góc nhìn bản đồ với ma trận chiếu của MapLibre GL JS thông qua `map.project([lon, lat])`.
  - Hiệu ứng phát sáng neon bằng `ctx.shadowBlur` và `ctx.shadowColor`:
    - Visited Nodes: Xanh lơ (`#00f0ff` / `#38bdf8`) với hiệu ứng sóng ripple lan tỏa.
    - Frontier Nodes: Hồng magenta (`#ec4899`) biểu thị đỉnh đang chờ trong hàng đợi ưu tiên.
    - Congested Nodes: Đỏ rực (`#ef4444`).
    - Final Path: Vàng neon hổ phách (`#f59e0b`).
- **Bảng điều khiển HUD (`VisualizerHUD.tsx`):**
  - Tuân thủ nghiêm ngặt Hallmark Anti-Slop (0 shadow-2xl, đường hairline border-neutral-800).
  - Tùy chỉnh tốc độ diễn họa: 1x, 5x, 15x, 30x, 50x.
  - Hỗ trợ thanh tua tiến độ sóng lan truyền (Scrub Bar).
