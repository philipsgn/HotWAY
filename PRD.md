# Bản Đặc Tả Yêu Cầu Sản Phẩm (PRD) — HotWAY

> **Tài liệu:** Yêu cầu sản phẩm hệ thống lập lịch & điều phối giao hàng CVRP  
> **Phiên bản:** v5.0.0 (Production Multi-Region & Live Benchmark Edition)  
> **Ngày cập nhật:** 21/10/2026  
> **Tài liệu liên quan:** [README.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/README.md) | [ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ARCHITECTURE.md) | [ALGORITHM.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ALGORITHM.md)

---

## 1. Bài Toán & Mục Tiêu Sản Phẩm

### 1.1. Bối cảnh bài toán
Quán bánh canh Hàng Gòn (cơ sở 490 Điện Biên Phủ, Quận Bình Thạnh, TP.HCM) phục vụ món ăn nóng có đặc tính suy giảm nhiệt nhanh theo thời gian. Mục tiêu vận hành là lập kế hoạch tuyến đường cho đội xe giao hàng đồng nhất sao cho tổng chi phí di chuyển là nhỏ nhất trên mạng lưới đường phố thực tế TP.HCM, đồng thời bảo đảm nhiệt độ khi giao đến tay khách hàng không thấp hơn ngưỡng cho phép ($T_{\min} = 60.0^\circ\text{C}$).

### 1.2. Mô hình toán học
Bài toán được mô hình hóa dưới dạng **Capacitated Vehicle Routing Problem (CVRP)** kết hợp ràng buộc thời gian di chuyển suy dẫn từ Định luật làm nguội Newton:
$$\min \sum_{r \in \mathcal{R}} \text{dist}(r)$$
Thỏa mãn:
1. Mỗi khách hàng $i \in \{1..n\}$ được phục vụ đúng một lần.
2. Tổng tải trọng mỗi tuyến $\sum_{i \in r} q_i \le Q$ (sức chứa xe $Q = 40$ tô).
3. Số tuyến hoạt động $|\mathcal{R}| \le K$ (số xe tối đa).
4. Mọi tuyến bắt đầu và kết thúc tại Depot (node $0$).
5. Ràng buộc nhiệt độ: Thời gian trên xe $t_i \le t_{\max}$ để $T(t_i) \ge 60^\circ\text{C}$.

---

## 2. Đối Tượng Người Dùng (Personas)

1. **Người điều phối giao hàng (Dispatcher):** Nhập danh sách đơn hàng trong ca, cấu hình số xe và sức chứa, bấm nút "Lập tuyến", xem thứ tự điểm dừng và theo dõi tiến độ giao hàng mô phỏng trên bản đồ MapLibre.
2. **Tài xế giao hàng (Driver):** Xem danh sách điểm dừng của xe mình trên giao diện di động (PWA), xem thời gian dự kiến đến (ETA), số tô cần bàn giao, và bấm nút xác nhận hoàn thành đơn.
3. **Kỹ sư dữ liệu & Hội đồng nghiệm thu (AI Data Engineer & Evaluator):** Khảo sát cấu trúc mạng lưới giao thông thực, chạy bộ sinh 30 benchmark instances, huấn luyện tác tử RL, tái tạo kết quả đối soát học thuật qua Jupyter Notebook, xác nhận tính trung thực khoa học tuyệt đối.

---

## 3. Phạm Vi Triển Khai (Scope)

### 3.1. Trong phạm vi (In-Scope)
- **Đồ thị đường bộ chuẩn Production:** Mạng lưới giao thông có hướng thực tế toàn diện TP.HCM tải từ OpenStreetMap (OSMnx: **46,055 nút, 107,224 cạnh, 8,551 km đường**) cùng cơ chế fallback đồ thị Bình Thạnh (demo nhỏ).
- **Spatial Indexing & On-Demand Dijkstra:** Dịch vụ ma trận khoảng cách/thời gian bất đối xứng gia tốc bằng cKDTree ($< 0.1\text{ms}$) và Dijkstra đơn nguồn.
- **Thuật toán giải tối ưu:** Khởi tạo Clarke-Wright Savings và 4 toán tử tìm kiếm cục bộ (Two-opt, Intra-relocate, Inter-relocate, Inter-swap) điều phối bởi 5 chiến lược (Random, Cyclic, Greedy, DQN, Double DQN).
- **Hệ thống Benchmark & RL:** Pipeline tự động sinh 30 instances thực tế, tự huấn luyện mạng Q-Network trên PyTorch và lưu checkpoint `.pt`.
- **Giao diện điều phối OptimoRoute:** 6 màn hình chuyên biệt (Đơn hàng, Lập kế hoạch, Chi tiết tuyến, Strategy Lab, Search Replay, Điều phối Live) cùng Jupyter Notebook (`notebooks/cvrp_benchmark.ipynb`).

### 3.2. Ngoài phạm vi (Out-of-Scope)
- Game 3D lái xe, vật lý phản trọng lực, mô hình xe ảo, voucher khuyến mãi (đã xóa bỏ hoàn toàn).
- Hệ thống định vị GPS phần cứng thực tế trên xe thật (thay bằng cơ chế mô phỏng vị trí toán học bám sát đồ thị đường).
- Hệ thống thanh toán trực tuyến qua cổng ngân hàng.

---

## 4. Tiêu Chí Chấp Nhận Đo Được (Acceptance Criteria)

1. **Khả thi 100%:** Nghiệm sinh ra từ mọi thuật toán phải được xác nhận hợp lệ bởi validator độc lập (phủ đủ khách, không lặp, tải $\le Q$, xe $\le K$).
2. **Kỷ luật hình học:** 100% chặng di chuyển bám sát cạnh đồ thị có hướng; 0 đoạn thẳng nhân tạo; khoảng cách snap $\le 60\text{ m}$.
3. **Trung thực số liệu:** Số liệu tại Strategy Lab khớp chính xác với kết quả chạy live của bộ benchmark (được ghi nhận trong `rel_result/summary_by_algorithm.csv`).
4. **Hiệu năng:** Thời gian lập tuyến cho 20-30 đơn $\le 0.5\text{ s}$ trên đồ thị thật.
5. **Cổng mạng:** Cổng 3000 được bảo toàn nguyên vẹn; Frontend chạy cổng 3001, Backend chạy cổng 8000.
