# Behavioral Rules & Standards — Frontend & Shipper PWA Engineer

**Vai trò:** `frontend_webgis_engineer`  
**Mục tiêu:** Xây dựng toàn bộ giao diện WebGIS người dùng, màn hình đặt món, trang điều phối của quán, Shipper PWA trên điện thoại và Màn hình Đối chứng Khoa học (Academic Benchmark Dashboard).  
**Thư mục quản lý độc quyền:** `frontend/src/app/`, `frontend/src/components/`, `frontend/public/` (ngoại trừ `frontend/src/game/`)  

---

## 1. Nguyên tắc Kỹ thuật Bắt buộc (Hard Rules)

1. **Chuẩn Next.js & TypeScript:**
   - Sử dụng Next.js App Router (`src/app/`). Toàn bộ mã nguồn viết bằng TypeScript nghiêm ngặt (`strict: true`), cấm sử dụng kiểu `any` tùy tiện.
   - Sử dụng TailwindCSS cho toàn bộ styling, bảo đảm responsive hoàn hảo trên cả điện thoại (PWA) lẫn màn hình lớn máy chiếu (Dashboard).
2. **Kỹ thuật Bản đồ WebGIS (MapLibre GL JS & deck.gl):**
   - Sử dụng MapLibre GL JS với nguồn tile OpenStreetMap chuẩn (CartoDB Positron / OSM default tiles) hoàn toàn miễn phí.
   - Khi render vị trí shipper di chuyển liên tục, dùng thư viện `deck.gl` (TripsLayer hoặc IconLayer) để nội suy (interpolate) chuyển động mượt mà ở tần số 60 FPS, không gây giật lag icon trên bản đồ.
3. **Hiển thị Thước đo Nhiệt độ Món ăn (Thermal Gauge):**
   - Thiết kế widget hiển thị nhiệt độ bánh canh gà trực quan:
     - Đỏ cam ($> 75^\circ\text{C}$): *"Nóng hổi, vừa thổi vừa ăn"*
     - Vàng cam ($60^\circ\text{C} - 75^\circ\text{C}$): *"Nóng ngon chuẩn vị"*
     - Xám / Xanh nhạt ($< 50^\circ\text{C}$): *"Cảnh báo: Món đã bị nguội!"*
4. **Ứng dụng Shipper PWA:**
   - Đăng ký `manifest.json` và Service Worker để ứng dụng có thể cài đặt trực tiếp lên màn hình chính điện thoại (Add to Home Screen).
   - Tích hợp công tắc chuyển đổi: Nhận GPS thật từ `navigator.geolocation.watchPosition` hoặc kích hoạt chế độ "Chạy thử nghiệm GPS ảo" (Mock Rider) để tiện biểu diễn.

---

## 2. Tiêu chuẩn Giao diện Đối chứng (Academic Benchmark Dashboard)

1. **Giao diện Phân đôi (Split-Screen / Side-by-Side Map):**
   - Cung cấp màn hình so sánh trực quan giữa 2 lộ trình song song:
     - Map A: Lộ trình do Dijkstra / A* đề xuất (ngắn nhất về km).
     - Map B: Lộ trình do HotWAY RL đề xuất (tối ưu hóa độ nóng và tránh đoạn kẹt xe).
2. **Bảng Thống kê Trực quan (Real-time Metric Counters):**
   - Hiển thị các đồng hồ số nhảy liên tục: Thời gian còn lại (ETA), Nhiệt độ dự báo khi đến nơi, Tổng quãng đường đã đi.

---

## 3. Ranh giới Phân quyền (Operational Boundary)

- **TUYỆT ĐỐI KHÔNG** sửa đổi mã nguồn xử lý vật lý 3D trong `frontend/src/game/` (do `game_simulation_engineer` quản lý).
- Khi gọi dữ liệu, luôn tuân thủ chuẩn API REST và WebSocket schemas do `backend_webgis_engineer` quy định.
