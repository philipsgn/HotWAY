# Bản Đặc Tả Yêu Cầu Sản Phẩm (PRD) — HotWAY

> **Tài liệu:** Yêu cầu sản phẩm hệ thống học tăng cường điều phối & tối ưu hóa tuyến đường giao vận toàn quốc  
> **Phiên bản:** v7.3.1 (Eliminate Hardcoded Regional Biases & Dynamic Min-Max Scaling Edition)  
> **Ngày cập nhật:** 29/10/2026  
> **Tài liệu liên quan:** [README.md](file:///c:/Users/Asus/Documents/AI/HotWAY/README.md) | [ARCHITECTURE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ARCHITECTURE.md) | [ALGORITHM.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ALGORITHM.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md)

---

## 1. Bài Toán & Mục Tiêu Sản Phẩm

### 1.1. Bối cảnh bài toán & Định vị hệ thống
Hệ thống logistics giao chặng cuối bằng xe máy và xe tải nhẹ tại các đại đô thị Việt Nam (Hà Nội, Đà Nẵng, TP.HCM) đối mặt với hàng chục ngàn bưu kiện mỗi ngày trong điều kiện giao thông đông đúc, ngập úng cục bộ và ùn tắc đỉnh nhọn vào giờ cao điểm sáng (07:00 - 08:30) và chiều (17:00 - 18:30).
- **Hạn chế của mô hình CVRP cũ (Thí nghiệm E0):** Giả định bài toán tĩnh với ma trận chi phí cố định và mô hình nhiệt độ Newton đóng kín ở một khu vực nhỏ. Kết quả thực nghiệm E0 chứng minh thuật toán ngẫu nhiên tốt hơn DQN trên lựa chọn toán tử Local Search, và các ràng buộc cục bộ không thể mở rộng quy mô.
- **Mục tiêu sản phẩm mới:** Chuyển trọng tâm hoàn toàn sang **Tối Ưu Tuyến Đường Động Đa Điểm Thích Nghi Giao Thông (Dynamic Traffic-Aware TSP/VRP)** trên quy mô toàn quốc, kết hợp cơ chế học tăng cường nơ-ron (Attention Model Kool et al., 2019) với chuẩn công nghiệp Google OR-Tools.
- **Nguyên tắc triệt tiêu Hardcode (Zero-Hardcoding Policy):** Tuyệt đối không hardcode tọa độ hoặc biên địa lý của bất kỳ vùng miền cụ thể nào vào mô hình AI. Áp dụng chuẩn hóa động tự thích ứng (Dynamic Min-Max Scaling) trên từng hành trình để bảo đảm tính tổng quát hóa không gian 100% trên toàn bộ 63 tỉnh thành Việt Nam.

### 1.2. Mô hình hóa bài toán (Time-Dependent TSP/VRP)
- **Không gian trạng thái:** Tập các tọa độ đã giao/chưa giao chuẩn hóa trong không gian đơn vị $[0, 1]^2$, thời điểm khởi hành $t_{\text{dep}}$, ma trận chi phí động $D(t)$ điều biến bởi hệ số kẹt xe thực nghiệm $C(t)$.
- **Không gian hành động:** Chọn tuần tự điểm giao tiếp theo thông qua cơ chế Multi-Head Attention Pointer Mechanism.
- **Hàm mục tiêu:** Tối thiểu hóa tổng thời gian hành trình bao gồm phạt kẹt xe:
  $$\min \sum_{u, v} \text{Duration}(u, v, t) \cdot C(t)$$
  với $C(t) \in [1.0, 2.25]$ phản ánh đúng nhịp điệu giao thông đô thị Việt Nam.

---

## 2. Đối Tượng Người Dùng (Personas)

1. **Điều phối viên Logistics đô thị (Logistics Dispatcher):** Quản lý lộ trình giao nhận nhiều điểm, phân bổ bưu kiện cho đội xe máy, theo dõi tuyến đường tối ưu thời gian thực tránh vùng kẹt xe.
2. **Tài xế giao hàng chặng cuối (Courier Driver):** Nhận lộ trình tối ưu hoá thứ tự ghé thăm từng bưu cục/điểm nhận để hoàn thành toàn bộ hành trình với thời gian ngắn nhất.
3. **Kỹ sư AI & Hội đồng nghiệm thu (AI Researcher & Evaluator):** Khảo sát hiệu năng giữa 4 họ mô hình (Google OR-Tools, Attention Model, Pointer Network, Dueling DQN), kiểm tra tính trung thực số liệu, kiểm chứng 4 điểm nghẽn toán học tử huyệt của DQN và khả năng phục vụ CPU tức thì < 25ms.

---

## 3. Phạm Vi Triển Khai (Scope)

### 3.1. Trong phạm vi (In-Scope)
- **Bộ Dữ Liệu Kiểm Chuẩn 100 POI Logistics Toàn Quốc (`data/benchmark_100_vietnam_pois.json`):**
  - **40 hành trình Hà Nội:** Bưu điện Bờ Hồ / Hub Long Biên, ĐH Bách Khoa HN, BV Bạch Mai, Keangnam 72, Aeon Mall Long Biên...
  - **20 hành trình Đà Nẵng:** Bưu điện Trung tâm Đà Nẵng, Cảng Tiên Sa, BV Đa Khoa ĐN, Chợ Cồn, Chợ Hàn, Bãi Biển Mỹ Khê...
  - **40 hành trình TP.HCM:** Kho Tổng Bưu điện Sài Gòn, Landmark 81, Bitexco, Chợ Bến Thành, BV Chợ Rẫy, ĐH Bách Khoa TP.HCM...
  - Phân tầng 4 bậc quy mô: 25 N10, 25 N20, 25 N30, 25 N50.
- **Chuẩn Hóa Động Thích Ứng (Dynamic Min-Max Scaling):**
  $$x'_i = \frac{x_i - \min(X)}{\max(X) - \min(X)}, \quad y'_i = \frac{y_i - \min(Y)}{\max(Y) - \min(Y)}$$
  Loại bỏ hoàn toàn lỗi lệch phân phối (Distribution Shift), giải quyết triệt để việc sai lệch tọa độ giữa các miền.
- **Môi trường Gymnasium Hợp Nhất `env/traffic_tsp_env.py`:** Hỗ trợ hàm kẹt xe $C(t)$ và Action Masking ngăn chặn chu trình rác.
- **Bộ 4 Mô Hình Đối Đầu (HotWAY Multi-Model Suite):**
  1. *Google OR-Tools (Guided Local Search):* Chuẩn mực công nghiệp tham chiếu (Optimality Gap 0.0%, 323.6m, 72.8km, 1001.74ms).
  2. *Attention Model (Kool et al., 2019):* Lõi nơ-ron chiến lược Gold Config 128-d/3L (678.1m, 142.2km, Gap 97.9% trên zero-shot weights, phục vụ CPU **21.30 ms** < 25ms SLA, 0.0% lỗi Zero-Shot).
  3. *Pointer Network (Bello et al. / Vinyals et al.):* Chuỗi Seq2Seq tham chiếu chuyển tiếp (763.7m, 169.1km, 122.9% Gap, 12.84ms CPU, 0.0% lỗi Zero-Shot).
  4. *Dueling DQN with Action Masking:* Mô hình bóc tách điểm nghẽn toán học (950.0m, 139.0km, Gap 174.3%, **thất bại Zero-Shot đúng 50.0%** trên $N > 20$ do tràn mảng $N_{\max}=20$).
- **Hạ Tầng Dự Phòng Giao Thông 3 Lớp (Fallback Router):**
  - Lớp 1: TomTom Traffic Flow & Route API.
  - Lớp 2: HERE Routing API.
  - Lớp 3: Offline OSRM / Haversine kết hợp hàm nhân động $C(t)$.
- **Hệ Thống Kiểm Thử Tự Động 56 Ca Test Toàn Diện (`pytest tests/`).**
- **Giao Diện WebGIS Điều Phối (Cổng 3001):** Bản đồ tương tác MapLibre GL JS, bảng đối soát 4 mô hình, hộp chẩn đoán tử huyệt DQN theo chuẩn thiết kế Swiss Monochromatic Executive.

### 3.2. Ngoài phạm vi (Out-of-Scope)
- Tuyệt đối không dùng cổng 3000 dưới mọi hình thức (Frontend chạy 3001, Backend chạy 8000).
- Ràng buộc nhiệt độ quán ăn đơn lẻ (đã bãi bỏ hoàn toàn).
- Dữ liệu cục bộ phường xã đơn lẻ (9 tệp `binhthanh_*` và `hanggon_*` đã được xóa sạch).
- Thanh toán điện tử hay tích hợp phần cứng máy in đơn.
