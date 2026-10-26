# Bản Đặc Tả Yêu Cầu Sản Phẩm (PRD) — HotWAY

> **Tài liệu:** Yêu cầu sản phẩm hệ thống học tăng cường điều phối giao vận thời gian thực  
> **Phiên bản:** v6.1.0 (Real-Time RL Restaurant Dispatch Edition)  
> **Ngày cập nhật:** 24/10/2026  
> **Tài liệu liên quan:** [README.md](file:///c:/Users/Asus/Documents/AI/HotWAY/README.md) | [ARCHITECTURE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ARCHITECTURE.md) | [ALGORITHM.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ALGORITHM.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md)

---

## 1. Bài Toán & Mục Tiêu Sản Phẩm

### 1.1. Bối cảnh bài toán & Lý do đổi hướng
Quán ăn đô thị tại TP.HCM phục vụ hàng trăm đơn hàng mỗi ngày trong điều kiện giao thông đông đúc, có mưa ngập và lưu lượng khách đỉnh nhọn vào giờ trưa (11:30 - 13:00) và tối (18:00 - 20:00).
- **Hạn chế của mô hình CVRP cũ (Thí nghiệm E0):** Giả định bài toán tĩnh với ma trận chi phí cố định và ràng buộc làm nguội Newton. Kết quả thực nghiệm E0 chứng minh thuật toán ngẫu nhiên tốt hơn DQN trên lựa chọn toán tử Local Search, và nhiệt độ thức ăn là biến không quan sát được trên đường.
- **Mục tiêu sản phẩm mới:** Chuyển trọng tâm hoàn toàn sang **Thời Gian Chờ Của Khách Hàng** ($W_i = t_{\text{giao}, i} - t_{\text{đặt}, i}$) và độ trễ so với lời hứa $\max(0, W_i - \text{ETA}_{\text{hứa}, i})$.

### 1.2. Mô hình hóa bài toán (Semi-MDP Thời Gian Thực)
Bài toán được hình thức hóa dưới dạng Semi-Markov Decision Process tại một quán ăn với đội xe máy $K=3$, sức chứa thùng hàng $Q=4$ đơn/chuyến:
- **Thời điểm ra quyết định:** Bất cứ khi nào có ít nhất một tài xế rảnh tại quán.
- **Hành động:** Chờ thêm ($\tau \le 10\text{ phút}$) để gom thêm đơn đang nấu, hoặc xuất phát ngay với $m \in \{1, 2, 3, 4\}$ đơn sẵn sàng.
- **Quy tắc gom & giao hàng:** Gom đơn dựa trên đơn sẵn sàng cũ nhất và cự ly đường vòng $D_{\text{detour}} \le 1.5\text{ km}$; thứ tự giao hàng được giải tối ưu bằng vét cạn $m!$ hoán vị để tối thiểu hóa tổng thời điểm bàn giao $\sum_{i} t_{\text{giao}, i}$.
- **Hàm mục tiêu:** Tối thiểu hóa tổng thời gian chờ tích lũy:
  $$\min \mathbb{E}\left[ \sum_{i=1}^{N} W_i \right] \iff \max \mathbb{E}\left[ \sum_{t} r_t \right]$$
  với phần thưởng từng bước $r_t = -\int_{t_k}^{t_{k+1}} N_{\text{active}}(t) \, dt$.

---

## 2. Đối Tượng Người Dùng (Personas)

1. **Người điều phối quán ăn (Restaurant Dispatcher):** Theo dõi luồng đơn hàng thời gian thực, trạng thái tài xế, lý do hệ thống quyết định "chờ gom" hay "xuất bến ngay", và chủ động can thiệp khi có biến động thời tiết hoặc đơn dồn ứ.
2. **Khách hàng nhận món (Customer):** Nhận được thông báo thời gian giao hàng dự kiến (Promised ETA) chính xác, hạn chế tình trạng trễ hẹn quá cam kết.
3. **Kỹ sư AI & Hội đồng nghiệm thu (AI Researcher & Evaluator):** Khảo sát hiệu năng giữa các mô hình RL (DQN, Double DQN, PPO) và các quy tắc heuristic (Immediate, Periodic, AgeThreshold), kiểm tra độ trung thực dữ liệu, tính khả thi của lộ trình và khả năng chịu tải đột biến (Surge stress test).

---

## 3. Phạm Vi Triển Khai (Scope)

### 3.1. Trong phạm vi (In-Scope)
- **Môi trường mô phỏng chuẩn Gymnasium:**
  - `RoutingEnv` (GĐ1): Đồ thị con 12 nút SCC Bình Thạnh, so sánh Q-learning và DQN với chân lý Exact Value Iteration.
  - `DispatchEnv` (GĐ2): Semi-MDP mô phỏng nhà hàng với thời gian bếp ngẫu nhiên, nhiễu giao thông log-normal, mưa bão, xung đơn đột biến, và tích phân Lebesgue bảo toàn phần thưởng Bellman sai số $< 10^{-9}$.
- **Hệ thống tác tử & quy tắc đối chiếu:**
  - 4 Baseline heuristic: Immediate, Periodic ($T=8\text{m}$), BatchSize ($k=1$), AgeThreshold ($\theta=10\text{m}$).
  - 1 Tham chiếu lý thuyết: Offline Prescient Reference ($74.52\text{m}$).
  - 3 Tác tử RL PyTorch: DQN, Double DQN, PPO với $\ge 5$ hạt giống huấn luyện và kiểm định Wilcoxon có hiệu chỉnh Holm.
- **Tập dữ liệu địa lý chuẩn hóa:** 401 địa chỉ giao hàng snap chuẩn và 151 địa chỉ ngoại vi (OOD).
- **Hệ thống kiểm thử tự động 4 tầng (T1 - T7):** Bao gồm kiểm thử độ trung thực tài liệu T3 đảm bảo 100% số liệu trong tài liệu sinh ra từ file kết quả.
- **Giao diện WebGIS điều phối (Triển khai sau khi qua Cổng G5):** Cổng 3001, bảng điều khiển 5 trạng thái đơn, biểu đồ tải và replay trực quan.

### 3.2. Ngoài phạm vi (Out-of-Scope)
- Tuyệt đối không dùng cổng 3000 dưới mọi hình thức.
- Ràng buộc nhiệt độ Newton và slogan "để món còn nóng" (đã bãi bỏ hoàn toàn).
- Đội xe linh hoạt kiểu gọi xe ngoài (chỉ tập trung đội xe riêng $K=3$ của nhà hàng).
- Thanh toán ví điện tử hay tích hợp máy in hóa đơn phần cứng.

---

## 4. Tiêu Chí Nghiệm Thu Đo Được (Measurable Acceptance Criteria)

1. **Bảo toàn phần thưởng Bellman:** Sai số tuyệt đối giữa tổng phần thưởng tích lũy và âm tổng thời gian chờ $\left| \sum r_t - (-\sum W_i) \right| < 10^{-9}$ trên mọi episode.
2. **Trung thực khoa học:** 100% số liệu đối sánh trong tài liệu khớp tuyệt đối với tệp kết quả CSV/JSON, được bảo đảm bởi bài test tự động `tests/test_report_fidelity.py`.
3. **Kỷ luật hình học & Vận tốc xe máy:** Mọi chặng di chuyển tuân thủ hình học có hướng đồ thị TP.HCM, áp dụng đúng profile xe máy (giữ hẻm, bỏ đường cấm xe máy, thời gian dừng giao hàng, phạt đèn đỏ và rẽ).
4. **Độ trễ suy luận online:** Mọi quyết định điều phối của tác tử RL phải thực thi trong thời gian $< 1.0\text{ ms}$ trên CPU luồng đơn.
5. **Kỷ luật cổng mạng:** Cổng 3000 được bảo vệ nguyên vẹn; Backend cổng 8000; Frontend cổng 3001 (không chỉnh sửa mã frontend/backend trước khi nghiệm thu Cổng G5).
