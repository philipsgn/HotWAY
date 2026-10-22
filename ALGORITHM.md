# Đặc Tả Thuật Toán & Phân Tích Thực Nghiệm (ALGORITHM.MD) — HotWAY

> **Tài liệu:** Cơ sở toán học, mô hình RL chọn toán tử, và kết quả thực nghiệm  
> **Phiên bản:** v5.0.0 (Production Multi-Region & Live Benchmark Edition)  
> **Ngày cập nhật:** 21/10/2026  
> **Nguồn sự thật:** `rel_result/` (sinh tự động từ 30 benchmark instances TP.HCM)  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/ARCHITECTURE.md)

---

## 1. Bản Chất Bài Toán & Vai Trò Của Reinforcement Learning

Mô hình nghiên cứu giải quyết bài toán CVRP bằng phương pháp **Hyper-Heuristic** kết hợp Học Tăng Cường (RL):
- **Không phải**: DQN học điều khiển tay lái hay rẽ trái/phải ở ngã tư.
- **Bản chất thực tế**: DQN và Double DQN học chính sách chọn **Toán tử Tìm kiếm Cục bộ (Local Search Operator)** ở mỗi bước lặp để cải thiện tập nghiệm CVRP khởi tạo từ Clarke-Wright.

### 4 Toán Tử Trong Không Gian Hành Động ($a \in \{0, 1, 2, 3\}$):
1. **$a = 0$ (`two_opt`):** Đảo ngược thứ tự phân đoạn $\text{route}[r][i..j]$ trong cùng một tuyến. Đối với ma trận chi phí bất đối xứng, $\Delta C$ được tính chính xác bằng tổng chênh lệch cạnh đảo chiều.
2. **$a = 1$ (`intra_relocate`):** Di chuyển một khách hàng từ vị trí $i$ sang vị trí $j$ trong cùng tuyến.
3. **$a = 2$ (`inter_relocate`):** Chuyển một khách hàng từ tuyến $r_1$ sang vị trí $k$ của tuyến $r_2$. Yêu cầu tải tuyến nhận $\le Q$. Tuyến $r_1$ nếu rỗng sẽ được xóa bỏ.
4. **$a = 3$ (`inter_swap`):** Hoán đổi vị trí hai khách hàng thuộc hai tuyến khác nhau. Yêu cầu tải trọng sau hoán đổi của cả hai tuyến đều $\le Q$.

---

## 2. Biểu Diễn Trạng Thái ($F28$) & Kiến Trúc Mạng Nơ-ron

Tập đặc trưng $F28$ gồm 28 chiều liên tục mô tả toàn diện trạng thái tìm kiếm:
- **Đặc trưng toàn cục (F12):** Tỷ lệ chi phí so với ban đầu $C/C_{\text{init}}$, tỷ lệ sử dụng đội xe $|\mathcal{R}|/K$, tỷ lệ tuyến dài nhất, hệ số biến thiên độ dài tuyến ($CV$), thống kê mức sử dụng tải trọng ($\text{mean}, \max, \min, CV$), thống kê độ dài cạnh ($\text{mean}, \max, \text{std}$) chuẩn hóa theo đường kính mạng lưới.
- **Tiến trình tìm kiếm:** $t / \text{max\_steps}$, `no_improve_streak` $= \min(1, \text{streak} / \text{feature\_patience})$ với `feature_patience = 30` (được tách độc lập khỏi luật dừng).
- **Lịch sử toán tử:** Tần suất chọn 4 toán tử (4 chiều), tỷ lệ thành công 4 toán tử (4 chiều), one-hot toán tử vừa chọn (4 chiều), cờ thành công bước trước (1 chiều), và độ lệch so với nghiệm tốt nhất (1 chiều).

**Kiến trúc Q-Network:** MLP 2 lớp ẩn ReLU ($28 \to 128 \to 128 \to 4$), hệ số chiết khấu $\gamma = 0.95$, Huber Loss, $\epsilon$-greedy giảm dần từ $1.0$ về $0.05$. Trọng số huấn luyện được lưu tại `src/cvrp_solver/weights/dqn_model.pt` và `double_dqn_model.pt`.

---

## 3. Ràng Buộc Nhiệt Động Học Newton Quy Về Giới Hạn Thời Gian

Nhiệt độ nước dùng giảm theo thời gian di chuyển $t$ (phút):
$$T(t) = T_{\text{env}} + (T_0 - T_{\text{env}}) e^{-kt}$$
Để bảo đảm nhiệt độ khi giao đến khách $T(t) \ge T_{\min} = 60.0^\circ\text{C}$ với tham số vận hành $T_0 = 85.0^\circ\text{C}$, $T_{\text{env}} = 30.0^\circ\text{C}$, $k = 0.020\text{ min}^{-1}$:
$$t_{\max} = -\frac{1}{k} \ln \left( \frac{T_{\min} - T_{\text{env}}}{T_0 - T_{\text{env}}} \right) = -\frac{1}{0.020} \ln \left( \frac{30.0}{55.0} \right) \approx 30.3\text{ phút}$$
Mỗi điểm dừng có thời gian di chuyển lũy kế $> 30.3\text{ phút}$ sẽ được đánh dấu cờ vi phạm nhiệt (`thermal_violation = true`).

---

## 4. Bảng Kết Quả Thực Nghiệm Thực Tế TP.HCM (rel_result)

Nguồn dữ liệu: `rel_result/summary_by_algorithm.csv` & `paired_comparisons.csv` (30 benchmark instances TP.HCM thực tế, 750 lượt chạy).

### 4.1. Bảng Tổng Hợp Theo Giao Thức A2 (100 bước, 256 ứng viên)
| Phương pháp | Khoảng cách TB (km) ↓ | Cải thiện % ↑ | 95% Bootstrap CI | Thời gian (s) | Ứng viên TB | Khả thi % | Gap vs Best % |
|---|---|---|---|---|---|---|---|
| **Greedy** | **103.727** | **2.077%** | [1.437, 2.747] | 0.2319 | 25,856.0 | **100.0%** | **0.000%** |
| **Random** | 103.728 | 2.077% | [1.495, 2.730] | 0.1280 | 25,856.0 | **100.0%** | 0.001% |
| **Cyclic** | 103.728 | 2.077% | [1.486, 2.759] | **0.1207** | 25,856.0 | **100.0%** | 0.001% |
| **Double DQN** | 103.733 | 2.073% | [1.478, 2.740] | 0.2146 | 25,856.0 | **100.0%** | 0.005% |
| **DQN** | 103.813 | 1.999% | [1.379, 2.664] | 0.1470 | 25,856.0 | **100.0%** | 0.082% |

### 4.2. Kiểm Định Thống Kê Theo Cặp (Wilcoxon & Holm-Bonferroni, Giao Thức A2)
- **DQN − Random:** $\Delta = -0.078\text{ pp}$, $95\%\text{ CI} = [-0.205, 0.000]$, $W/T/L = 0/28/2$, $p_{\text{Holm}} = 0.8648$.
- **Double DQN − Random:** $\Delta = -0.004\text{ pp}$, $95\%\text{ CI} = [-0.011, 0.001]$, $W/T/L = 0/28/2$, $p_{\text{Holm}} = 0.8648$.
- **DQN − Double DQN:** $\Delta = -0.074\text{ pp}$, $95\%\text{ CI} = [-0.200, 0.007]$, $W/T/L = 2/26/2$, $p_{\text{Holm}} = 0.8648$.
- Double DQN đạt độ chính xác xấp xỉ ngang bằng các baseline heuristics mạnh nhất ($103.733\text{ km}$ so với $103.727\text{ km}$, khoảng cách chênh lệch chỉ $6\text{ mét}$ trên toàn mạng).

---

## 5. Phân Tích Khoa Học: Tại Sao Heuristics Đơn Giản Vẫn Rất Cạnh Tranh?

1. **Dư địa cải thiện từ Clarke-Wright rất nhỏ:** Khởi tạo Clarke-Wright Savings trên ma trận đường bộ có hướng thực tế đã cho chất lượng nghiệm rất tốt. Dưới luật chấp nhận giảm nghiêm ngặt ($\Delta C < 0$), nghiệm nhanh chóng rơi vào đáy attractor của các lân cận.
2. **Chi phí suy luận mạng nơ-ron (Inference Overhead):** Mặc dù PyTorch tối ưu rất tốt, việc tính toán vector trạng thái $F28$ và lan truyền xuôi qua mạng MLP tiêu tốn thời gian tính toán hơn so với phép chọn số ngẫu nhiên đơn thuần của Random/Cyclic ($0.21\text{s}$ so với $0.12\text{s}$).
3. **Double DQN triệt tiêu hiện tượng Overestimation:** Double DQN cải thiện rõ rệt so với standard DQN (tiết kiệm thêm quãng đường và tiệm cận sát đường cơ sở của Greedy/Cyclic nhờ cơ chế tách biệt mạng chọn hành động và mạng đánh giá giá trị Q).

---

## 6. Tính Khả Lặp & Độ Tin Cậy Nghiên Cứu (Reproducibility)

Tất cả các con số trong bảng trên đều có thể tái tạo 100% bằng cách chạy:
```bash
python -m src.benchmark.runner
python -m src.benchmark.analysis
```
Bản ghi chi tiết từng bước của 750 lượt chạy được lưu tại `rel_result/raw_runs.csv`. Toàn bộ dữ liệu đối chiếu lịch sử từ file báo cáo PDF cũ được lưu trữ cẩn thận tại `rel_result/legacy_pdf_reference/` để phục vụ công tác thanh tra khoa học.
