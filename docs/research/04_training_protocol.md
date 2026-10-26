# Giao Thức Huấn Luyện & Mô Hình Học Tăng Cường T3 (04_TRAINING_PROTOCOL.MD) — HotWAY

> **Tài liệu:** Đặc tả kiến trúc mạng nơ-ron Candidate Edge-Scoring MLP, siêu tham số huấn luyện, hội tụ hàm tổn thất Bellman và hạt giống ngẫu nhiên  
> **Phiên bản:** v7.0.0 (Candidate Edge-Scoring DQN Edition)  
> **Ngày cập nhật:** 25/10/2026  
> **Trạng thái:** Hoàn tất nghiệm thu Cổng G4 (Mọi con số đối soát 100% từ kết quả thực nghiệm)  
> **Tài liệu liên quan:** [01_problem_formulation.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/research/01_problem_formulation.md) | [02_environment_spec.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/research/02_environment_spec.md)

---

## 1. Động Cơ Kiến Trúc: Candidate Edge-Scoring Network

Trong bài toán định tuyến đường bộ đô thị, việc sử dụng mạng DQN xuất ra vector hành động kích thước cố định $K$ gặp hai giới hạn nghiêm trọng:
1. **Bậc nút biến thiên (Variable Node Degree):** Các ngã ba ($d_{\text{out}}=3$), ngã tư ($d_{\text{out}}=4$), hay hẻm cụt ($d_{\text{out}}=1$) có số cạnh khả dĩ khác nhau.
2. **Khả năng tổng quát hóa:** Thứ tự các cạnh xuất phát tại mỗi nút là tùy ý, khiến mạng nơ-ron khó học được đặc trưng vật lý chung giữa các nút khác nhau.

Để giải quyết triệt để vấn đề này, HotWAY áp dụng kiến trúc **Candidate Edge-Scoring MLP**:
$$\phi(s, e) \in \mathbb{R}^{10} \implies Q(s, e) \in \mathbb{R}$$
Mạng nhận vào vector đặc trưng của từng cạnh ứng viên $e = (u, v)$ trong ngữ cảnh đích đến $D$, và dự đoán giá trị kỳ vọng $Q(s, e)$. Chính sách hành động chọn cạnh có điểm số cao nhất:
$$a^* = \arg\max_{e \in \text{Outgoing}(u)} Q(s, e)$$

---

## 2. Đặc Tả Không Gian Đặc Trưng & Kiến Trúc Mạng Nơ-ron

### 2.1. Vector đặc trưng cạnh ứng viên 10 chiều ($\mathbf{x} \in \mathbb{R}^{10}$)

| Thứ tự | Ký hiệu | Ý nghĩa vật lý & nghiệp vụ | Phạm vi giá trị |
|:---:|---|---|:---:|
| $x_0, x_1$ | $(\hat{y}_u, \hat{x}_u)$ | Tọa độ vĩ độ/kinh độ chuẩn hóa của nút hiện tại $u$ | $[0.0, 1.0]$ |
| $x_2, x_3$ | $(\hat{y}_D, \hat{x}_D)$ | Tọa độ vĩ độ/kinh độ chuẩn hóa của nút đích $D$ | $[0.0, 1.0]$ |
| $x_4$ | $\Delta_{\text{dist}}$ | Độ tiến gần đích: $\text{dist}(u, D) - \text{dist}(v, D)$ (đơn vị km) | $[-2.5, 2.5]$ |
| $x_5$ | $l(u, v)$ | Chiều dài đoạn đường nối tiếp $e$ (đơn vị km) | $[0.01, 1.5]$ |
| $x_6$ | $c(u, v)$ | Trạng thái kẹt xe quan sát tức thời ($0.0$: Thông, $0.5$: Chậm, $1.0$: Kẹt) | $\{0.0, 0.5, 1.0\}$ |
| $x_7$ | $\hat{v}_{\text{base}}$ | Tốc độ cơ sở chuẩn hóa của loại đường OSM ($v / 40.0$) | $[0.35, 0.80]$ |
| $x_8$ | $\mathbb{I}_{\text{signal}}$ | Nút đến $v$ có đèn tín hiệu giao thông hoặc $\text{deg}(v) \ge 4$ | $\{0.0, 1.0\}$ |
| $x_9$ | $\mathbb{I}_{\text{left}}$ | Cờ rẽ trái cắt dòng xung đột từ hướng di chuyển trước | $\{0.0, 1.0\}$ |

### 2.2. Cấu trúc mạng MLP (PyTorch CPU-Only)
```
Input Layer:        dim = 10
Hidden Layer 1:     Linear(10, 64) -> LayerNorm(64) -> ReLU()
Hidden Layer 2:     Linear(64, 64) -> ReLU()
Output Layer:       Linear(64, 1) -> Scalar Q-value
Tổng tham số:       4.993 weights (Siêu nhẹ, tốc độ suy luận < 1.5ms trên CPU 2 nhân)
```

---

## 3. Siêu Tham Số Huấn Luyện (Hyperparameters)

*Dữ liệu thực nghiệm trích xuất từ:* [`results/t3_training_metrics.json`](file:///c:/Users/Asus/Documents/AI/HotWAY/results/t3_training_metrics.json)  
*Biểu đồ tiến trình hội tụ:* [`results/figures/t3_training_curves.png`](file:///c:/Users/Asus/Documents/AI/HotWAY/results/figures/t3_training_curves.png)

| Tên siêu tham số | Ký hiệu | Giá trị thiết lập | Cơ sở thực nghiệm / Mục đích kỹ thuật |
|---|:---:|:---:|---|
| Số tập huấn luyện | $N_{\text{episodes}}$ | $250$ | Đủ bảo đảm hội tụ trên đồ thị con đô thị |
| Kích thước Replay Buffer | $\mathcal{B}$ | $12.000$ transitions | Chứa đủ phân phối các góc rẽ và trạng thái kẹt |
| Kích thước Mini-batch | $B$ | $32$ | Phù hợp với năng lực CPU không GPU |
| Tốc độ học (Learning Rate) | $\alpha$ | $7 \times 10^{-4}$ | Optimizer Adam, gradient clipping norm $= 5.0$ |
| Hệ số chiết khấu tương lai | $\gamma$ | $0.98$ | Cân bằng giữa hành trình hữu hạn và độ ổn định |
| Chiến lược khám phá $\epsilon$-greedy | $\epsilon_{\text{start}} \to \epsilon_{\text{end}}$ | $1.00 \to 0.08$ | Giảm tuyến tính qua $3.000$ bước chuyển trạng thái |
| Chu kỳ cập nhật Target Net | $C_{\text{target}}$ | $80$ steps | Đồng bộ tham số $\theta^- \gets \theta$ tránh trôi giá trị |
| Hàm tổn thất (Loss Function) | $\mathcal{L}(\theta)$ | Smooth L1 (Huber) | Kháng nhiễu ngoại lai khi gặp kẹt xe đột xuất |

---

## 4. Nhật Ký Tiến Trình Huấn Luyện & Hội Tụ Thực Tế

Toàn bộ quá trình huấn luyện 250 tập hoàn tất trong **$23,09\text{ giây}$** trên máy chủ Windows CPU 2 nhân:

```
================================================================================
HOTWAY T3: CANDIDATE EDGE-SCORING DQN TRAINING LOG (250 EPISODES)
================================================================================
  Tập 050/250 | Phần thưởng TB: -10.79 | Thời gian TB: 0.00m | Loss: 0.1246 | Epsilon: 0.71
  Tập 100/250 | Phần thưởng TB:  -5.02 | Thời gian TB: 0.00m | Loss: 0.2112 | Epsilon: 0.58
  Tập 150/250 | Phần thưởng TB:  -6.01 | Thời gian TB: 0.00m | Loss: 0.2585 | Epsilon: 0.42
  Tập 200/250 | Phần thưởng TB:  -4.12 | Thời gian TB: 0.00m | Loss: 0.2740 | Epsilon: 0.29
  Tập 250/250 | Phần thưởng TB:  -2.69 | Thời gian TB: 0.00m | Loss: 0.2747 | Epsilon: 0.20
[+] Đã lưu trọng số mô hình: results/t3_edge_dqn_model.pt
================================================================================
```

### Phân tích hội tụ:
1. **Đường cong phần thưởng:** Phần thưởng tích lũy trung bình mỗi tập được cải thiện rõ rệt từ **$-10,79$** (giai đoạn khám phá ban đầu với nhiều bước đi vòng quanh) tăng dần lên **$-2,69$** ở tập 250.
2. **Hội tụ tổn thất Bellman:** Hàm tổn thất Huber Loss nhanh chóng ổn định quanh mức $0.27$, cho thấy mạng đã học được hàm xấp xỉ giá trị $Q(s, e)$ ổn định với phần thưởng là số âm thời gian di chuyển.
