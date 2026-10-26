# Hình Thức Hóa Toán Học Bài Toán T1 – T2 – T3 (01_PROBLEM_FORMULATION.MD)

> **Tài liệu:** Đặc tả toán học giải tích, biến số, hàm mục tiêu và mục tiêu kiểm thử  
> **Phiên bản:** v7.0.0 (Route Optimization & Adaptive Motorbike Dispatch Edition)  
> **Ngày cập nhật:** 25/10/2026 | **Cổng nghiệm thu:** G1 (Tối đa 4 trang) — **DỪNG CHỜ DUYỆT**  

---

## 1. Bảng Ký Hiệu Biến Số Toán Học Chuẩn Hóa

| Ký hiệu | Ý nghĩa toán học | Đơn vị | Miền giá trị | Nguồn gốc |
|:---|:---|:---:|:---:|:---:|
| $G = (V, E)$ | Đồ thị đường bộ có hướng trích xuất từ OpenStreetMap | - | $\|V\| \le 46.055, \|E\| \le 107.224$ | Đo lường thực tế (OSMnx) |
| $L_e$ | Chiều dài vật lý của cạnh đường $e \in E$ | mét (m) | $L_e > 0$ | Đo lường thực tế (GIS) |
| $v_e(t)$ | Vận tốc lưu thông trung bình theo loại đường và khung giờ $t$ | km/h | $[8.0, 40.0]$ | Giả định hiệu chuẩn |
| $\eta_{\text{rain}}$ | Hệ số làm chậm do mưa bão đô thị | - | $1.0$ (nắng), $1.40$ (mưa) | Giả định vận hành |
| $\epsilon_e$ | Nhiễu thời gian di chuyển cạnh ngẫu nhiên: $\epsilon_e \sim \mathcal{N}(0, \sigma^2)$ | - | $\sigma = 0.20$ | Giả định mô phỏng |
| $\Delta t_{\text{left}}$ | Thời gian phạt rẽ trái cắt dòng giao thông đối diện | giây (s) | $12.0$ | Giả định vật lý |
| $\Delta t_{\text{light}}$ | Thời gian phạt chờ đèn tín hiệu giao thông tại nút | giây (s) | $25.0$ | Giả định chu kỳ đèn |
| $p = (e_1, \dots, e_k)$ | Tuyến đường di chuyển (dãy các cạnh liên tiếp hợp lệ) | - | $e_i \in E$ | Lời giải thuật toán |
| $T_{p90}(p)$ | Phân vị 90% thời gian chạy tuyến qua Monte Carlo $M$ mẫu | phút | $T_{p90} \ge \bar{T}$ | Ước lượng Monte Carlo |
| $K$ | Số lượng tài xế xe máy sẵn có tại kho/bưu cục | xe | $K \in [2, 5]$ | Giả định đội xe |
| $Q$ | Sức chứa tối đa của thùng xe máy | gói (hoặc kg) | $8$ gói (hoặc $15$ kg) | Giả định thùng xe |
| $[e_i, l_i]$ | Khung giờ nhận hàng mong muốn của khách $i$ (Earliest / Latest) | phút | $0 \le e_i \le l_i$ | Đầu vào đơn hàng |
| $s_i$ | Thời gian dừng giao hàng tại điểm $i$ (Dwell / Service time) | phút | $3.0$ phút | Giả định vận hành |
| $\text{tuổi}_i, \tau$ | Thời gian đơn $i$ chờ tồn đọng và hằng số chuẩn hóa | phút | $\text{tuổi}_i \ge 0, \tau = 60.0$ | Đầu vào hệ thống |
| $w_i$ | Trọng số ưu tiên xử lý đơn tồn: $w_i = 1 + \alpha \cdot \frac{\text{tuổi}_i}{\tau}$ | - | $w_i \ge 1.0$ ($\alpha = 1.5$) | Giả định hàm phạt trễ |
| $F_k$ | Chi phí cố định khi huy động xe máy $k$ | điểm quy đổi | $F_k = 50.0$ | Giả định kinh tế |

---

## 2. Tầng T1: Chọn Đường Đa Tiêu Chí Giữa 2 Điểm (Xe Máy Đô Thị)

### 2.1. Vector Tiêu Chí Đánh Giá Tuyến
Với mỗi tuyến đường $p$ từ gốc $A$ đến đích $B$, vector tiêu chí $\mathbf{C}(p) \in \mathbb{R}^7$ được xác định:
$$\mathbf{C}(p) = \Big( D(p),\, \mathbb{E}[T(p)],\, T_{p90}(p),\, N_{\text{turn}}(p),\, N_{\text{left}}(p),\, R_{\text{alley}}(p),\, N_{\text{signal}}(p) \Big)$$

1. **Tổng cự ly vật lý:** $D(p) = \sum_{e \in p} L_e$ (mét).
2. **Thời gian kỳ vọng:** $\mathbb{E}[T(p)] = \sum_{e \in p} \left( \frac{L_e}{v_e(t)} \cdot \eta_{\text{rain}} \cdot e^{\frac{\sigma^2}{2}} \right) + N_{\text{left}}(p)\cdot \Delta t_{\text{left}} + N_{\text{signal}}(p)\cdot \Delta t_{\text{light}}$ (phút).
3. **Độ ổn định phân vị $p90$:** Đánh giá qua mô phỏng Monte Carlo $M = 200$ lần lấy mẫu nhiễu:
   $$T^{(m)}(p) = \sum_{e \in p} \left( \frac{L_e}{v_e^{(m)}(t)} \cdot \eta_{\text{rain}} \cdot e^{\epsilon_e^{(m)}} \right) + \text{Phạt rẽ & đèn}, \quad T_{p90}(p) = \text{Quantile}_{0.90}\left(\{T^{(m)}(p)\}_{m=1}^M\right)$$
4. **Số lần rẽ trái cắt dòng ($N_{\text{left}}$):** Góc lái giữa 2 cạnh liên tiếp $\theta(e_i, e_{i+1}) \in [200^\circ, 340^\circ]$.
5. **Tỷ lệ đoạn hẻm ($R_{\text{alley}}$):** Tỷ lệ chiều dài qua các đoạn hẻm proxy (`highway` $\in$ {`service`, `residential`, `living_street`}): $R_{\text{alley}}(p) = \frac{\sum_{e \in p, \text{is\_alley}(e)} L_e}{D(p)}$.
6. **Số nút có đèn tín hiệu ($N_{\text{signal}}$):** Số nút giao trên tuyến có thuộc tính `highway=traffic_signals`.

### 2.2. Lọc Tập Pareto & Dán 4 Nhãn Tuyến Đặc Trưng
Tuyến $p_1$ lấn át tuyến $p_2$ ($p_1 \succ p_2$) nếu $\forall i: C_i(p_1) \le C_i(p_2)$ và $\exists j: C_j(p_1) < C_j(p_2)$. Sau khi lọc tập Pareto phi lấn át $\mathcal{P}^*$, chọn ra 4 tuyến đại diện:
* **Tuyến 1 (Nhanh nhất kỳ vọng):** $p_{\text{fastest}} = \arg\min_{p \in \mathcal{P}^*} \mathbb{E}[T(p)]$.
* **Tuyến 2 (Ngắn nhất cự ly):** $p_{\text{shortest}} = \arg\min_{p \in \mathcal{P}^*} D(p)$.
* **Tuyến 3 (Ổn định nhất):** $p_{\text{stable}} = \arg\min_{p \in \mathcal{P}^*} T_{p90}(p)$.
* **Tuyến 4 (Dễ đi nhất):** $p_{\text{easiest}} = \arg\min_{p \in \mathcal{P}^*} \left( N_{\text{turn}} + 2 N_{\text{left}} + 3 N_{\text{signal}} + 5 R_{\text{alley}} \right)$.

---

## 3. Tầng T2: Lập Tuyến Giao Nhiều Điểm (VRPTW Chuẩn Kèm Ưu Tiên Đơn Tồn)

### 3.1. Mô Hình Tối Ưu Hóa VRPTW
Xét đồ thị hoàn chỉnh giữa Kho bưu cục ($0$) và $N$ điểm giao hàng ($1, \dots, N$). Đội xe gồm $K$ xe máy đồng nhất sức chứa $Q$. Biến quyết định: $x_{ijk} \in \{0, 1\}$ (xe $k$ đi từ $i$ đến $j$), $y_k \in \{0, 1\}$ (xe $k$ được sử dụng), $a_i$ (thời điểm xe đến phục vụ điểm $i$).

$$\min \quad \sum_{k=1}^K \sum_{i=0}^N \sum_{j=0}^N c_{ij}(t) \cdot x_{ijk} + \sum_{i=1}^N w_i \cdot \max(0,\, a_i - l_i) + \sum_{k=1}^K F_k \cdot y_k$$

**Các ràng buộc kỹ thuật cốt lõi:**
1. **Phục vụ duy nhất:** $\sum_{k=1}^K \sum_{j=0, j \ne i}^N x_{ijk} = 1, \quad \forall i \in \{1, \dots, N\}$.
2. **Bảo toàn luồng tại kho:** $\sum_{j=1}^N x_{0jk} = y_k \le 1$ và $\sum_{i=1}^N x_{i0k} = y_k, \quad \forall k \in \{1, \dots, K\}$.
3. **Giới hạn sức chứa xe máy:** $\sum_{i=1}^N q_i \sum_{j=0}^N x_{ijk} \le Q \cdot y_k, \quad \forall k$.
4. **Tiến trình thời gian chặng:** $a_j \ge a_i + s_i + t_{ij}(a_i) - M(1 - x_{ijk}), \quad \forall i, j, k$.
5. **Trọng số phạt trễ đơn tồn:** Đơn tồn đọng có trọng số $w_i = 1 + \alpha \cdot \frac{\text{tuổi}_i}{\tau}$. Đơn càng tồn lâu, hệ thống càng ưu tiên phục vụ sớm để triệt tiêu thời gian trễ.

---

## 4. Tầng T3: Đổi Đường Thích Nghi Khi Kẹt Xe (Reinforcement Learning MDP)

### 4.1. Không Gian Trạng Thái, Hành Động & Hàm Thưởng
Mô hình hóa bài toán dẫn đường xe máy thích ứng khi gặp tắc đường dưới dạng MDP trên đồ thị con $\mathcal{G}_{\text{sub}} = (\mathcal{V}_{\text{sub}}, \mathcal{E}_{\text{sub}})$:
* **Trạng thái $s_t \in \mathcal{S}$:** $s_t = \big( u,\, d,\, \mathbf{c}_{\text{out}}(u),\, t_{\text{tod}} \big)$ trong đó $u$ là nút hiện tại, $d$ là đích đến, $\mathbf{c}_{\text{out}}(u) \in \{0, 1, 2\}^{\text{deg}(u)}$ là mức kẹt đo được tại các cạnh xuất phát từ $u$ (0: Thông, 1: Chậm, 2: Kẹt), $t_{\text{tod}}$ là khung giờ trong ngày.
* **Hành động $a_t \in \mathcal{A}(s_t)$:** Chọn chỉ số cạnh xuất phát $e = (u, v) \in \text{Out}(u)$.
* **Phần thưởng chuyển trạng thái:** $r(s_t, a_t) = - T_e(s_t)$ (âm thời gian di chuyển thực tế trên cạnh vừa đi).
* **Điều kiện dừng (Terminal):** Khi tài xế đến đích ($u = d$), nhận thưởng $r_{\text{terminal}} = 0$.

### 4.2. Mạng Nơ-ron Dùng Chung Chấm Điểm Cạnh & Đối Chiếu Tuyệt Đối
1. **Kiến trúc mạng dùng chung (Shared Edge-Scoring Network):** Bậc của các nút giao thay đổi (từ 2 đến 5 cạnh ra). Để mạng tổng quát hóa giữa mọi nút, mạng nơ-ron nhận đầu vào là vector ghép nối giữa đặc trưng ngữ cảnh $(u, d, t_{\text{tod}})$ và đặc trưng cạnh ứng viên $(e_j, \text{congestion}_j, L_{e_j})$, xuất ra điểm giá trị $Q(s, e_j)$. Tác tử chọn cạnh có điểm cao nhất:
   $$a^* = \arg\max_{e_j \in \text{Out}(u)} Q_\theta(s, e_j)$$
2. **Đáp án đối chiếu chân lý giải tích (Ground Truth Value Iteration):**
   Trên đồ thị con nhỏ với xác suất chuyển trạng thái Markov $P(\mathbf{c}' \mid \mathbf{c})$, thuật toán Quy hoạch động Value Iteration hội tụ về hàm giá trị tối ưu chính xác $V^*(s)$:
   $$V_{k+1}(s) = \max_{a \in \text{Out}(u)} \left[ \mathbb{E}[r(s,a)] + \gamma \sum_{s'} P(s' \mid s, a) V_k(s') \right]$$
   Đây là thước đo chuẩn tắc tuyệt đối để định cỡ khoảng cách chính sách của Q-learning, DQN và PPO.

---

## 5. Mô Hình Giao Thông `TrafficProvider` & Ma Trận Chuyển Trạng Thái Markov

Mô hình giao thông tổng hợp `SyntheticProvider` sử dụng chuỗi Markov 3 trạng thái với ma trận chuyển xác suất thời gian rời rạc $\mathbf{P}$:
$$\mathbf{P}_{\text{normal}} = \begin{bmatrix} 0.85 & 0.12 & 0.03 \\ 0.20 & 0.65 & 0.15 \\ 0.05 & 0.35 & 0.60 \end{bmatrix}, \quad \mathbf{P}_{\text{peak}} = \begin{bmatrix} 0.60 & 0.30 & 0.10 \\ 0.10 & 0.60 & 0.30 \\ 0.02 & 0.28 & 0.70 \end{bmatrix}$$

* Vận tốc theo trạng thái và cấp đường:
  $$v(e, \text{state}) = v_{\text{base}}(e) \cdot \Big[ \mathbf{1}_{\{\text{Thông}\}} \cdot 1.0 + \mathbf{1}_{\{\text{Chậm}\}} \cdot 0.55 + \mathbf{1}_{\{\text{Kẹt}\}} \cdot 0.25 \Big]$$
* Thời gian di chuyển cạnh: $T_e = \frac{L_e}{v(e, \text{state})} \cdot \eta_{\text{rain}} \cdot e^{\epsilon_e}$ với $\epsilon_e \sim \mathcal{N}(0, 0.20^2)$.

---

## 6. Mục Tiêu Kiểm Thử Định Lượng Cho Từng Công Thức Toán (Testable Assertions)

| Công thức / Khái niệm | Mục tiêu kiểm thử tự động (Unit Test Assertion) | Ngưỡng sai số chấp nhận |
|:---|:---|:---:|
| **T1: Không âm cự ly & thời gian** | $\forall p: D(p) > 0, \, \mathbb{E}[T(p)] > 0, \, T_{p90}(p) \ge \mathbb{E}[T(p)]$ | Tuyệt đối ($> 0$) |
| **T1: Tính Pareto không lấn át** | $\forall p_i, p_j \in \mathcal{P}^*, \, i \ne j \implies \neg(p_i \succ p_j) \land \neg(p_j \succ p_i)$ | Tuyệt đối (0 cặp lấn át) |
| **T1: Phạt rẽ trái & đèn** | Đi thẳng $N_{\text{left}} = 0$; rẽ trái góc $[200^\circ, 340^\circ] \implies \Delta t \ge 12.0\text{s}$ | Sai số $< 10^{-6}$ |
| **T2: Bảo toàn luồng xe & đơn** | $\sum_{k,j} x_{0jk} = \sum_{k,i} x_{i0k} \le K$; Mỗi đơn $i$ giao đúng 1 lần | Sai số $= 0$ (nguyên) |
| **T2: Giới hạn sức chứa $Q$** | $\forall k: \sum_{i} q_i \sum_j x_{ijk} \le Q$ | Tuyệt đối ($\le Q$) |
| **T2: Trọng số đơn tồn $w_i$** | $\text{tuổi}_i = 0 \implies w_i = 1.0$; $\text{tuổi}_i = 60\text{m} \implies w_i = 1.0 + 1.5 = 2.5$ | Sai số $< 10^{-9}$ |
| **T3: Hội tụ Value Iteration** | $\|V_{k+1} - V_k\|_\infty < 10^{-7}$ trong tối đa 500 vòng lặp | Sai số $< 10^{-7}$ |
| **T3: Khử nhiễu Q-Learning $\to V^*$** | Khi triệt tiêu nhiễu ($\sigma = 0, \text{state cố định}$), $Q^*(s, a) \equiv V^*(s)$ | Sai số $< 10^{-5}$ |
| **T3: Bảo toàn phần thưởng Bellman** | $\sum_{t=0}^H r(s_t, a_t) = - \sum_{e \in \text{path}} T_e$ | Sai số $< 10^{-11}$ |
| **Độ trung thực số liệu T3** | Mọi số liệu trong báo cáo khớp registry JSON/CSV | Sai số $< 10^{-9}$ |
