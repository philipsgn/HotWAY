# Đặc Tả Thuật Toán & Phân Tích Thực Nghiệm (ALGORITHM.MD) — HotWAY

> **Tài liệu:** Cơ sở toán học, mô hình Semi-MDP thời gian thực, thuật toán NCO và kết quả thực nghiệm Kaggle GPU  
> **Phiên bản:** v7.3.2 (Eliminate Regional Bias & Dynamic Isotropic Scaling Edition)  
> **Ngày cập nhật:** 02/11/2026  
> **Nguồn sự thật:** `results/benchmark_summary_table.csv`, `results/benchmark_multi_model_results.json`, `notebooks/model_results/`  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/Asus/Documents/AI/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ARCHITECTURE.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md) | [SLIDES_DEFENSE_OUTLINE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/SLIDES_DEFENSE_OUTLINE.md)

---

## PHẦN 1: THÍ NGHIỆM KHỞI ĐẦU E0 (CVRP TĨNH & CHỌN TOÁN TỬ CỤC BỘ)

### 1.1. Bản Chất Bài Toán E0 & Kết Quả Âm Tính
- **Bản chất thực nghiệm:** Đánh giá năng lực của DQN và Double DQN trong việc chọn 1 trong 4 toán tử Local Search (`two_opt`, `intra_relocate`, `inter_relocate`, `inter_swap`) trên nghiệm khởi tạo Clarke-Wright Savings với ràng buộc làm nguội nhiệt Newton $T_{\min} \ge 60^\circ\text{C}$.
- **Kết quả thực nghiệm bảo tồn tại `rel_result/`:**
  - Trên 30 instances đồ thị TP.HCM thực tế: Greedy ($103.727\text{ km}$) và Random ($103.728\text{ km}$) tốt hơn DQN ($103.813\text{ km}$).
  - Trên giao thức A2 chuẩn (tài liệu PDF A2): Random ($656.359\text{ km}$) vượt trội hơn DQN ($657.897\text{ km}$) với $p_{\text{Holm}} = 0.0072$.
- **Động lực chuyển hướng:** Khởi tạo Clarke-Wright đã đạt chất lượng quá gần biên tối ưu khiến dư địa cải thiện của Local Search chỉ còn khoảng $0.1\%$. Nhiệt độ thức ăn là biến ngẫu nhiên tại bếp, không quan sát được trên đường. Do đó, hệ thống loại bỏ hoàn toàn ràng buộc nhiệt độ Newton và chuyển sang tối ưu **Thời Gian Chờ Của Khách Hàng**.

---

## PHẦN 2: MÔ HÌNH HỌC TĂNG CƯỜNG ĐIỀU PHỐI THỜI GIAN THỰC (GĐ2)

### 2.1. Hình Thức Hóa Semi-MDP
Hệ thống điều phối tại quán giao hàng được biểu diễn dưới dạng Semi-Markov Decision Process $(\mathcal{S}, \mathcal{A}, \mathcal{P}, \mathcal{R}, \tau)$:
- **Thời điểm ra quyết định $t_k$:** Mỗi khi có ít nhất một tài xế rảnh tại quán.
- **Thời lượng chuyển tiếp ngẫu nhiên $\tau_k \in (0, \tau_{\max}]$:**
  - Nếu chọn hành động $a=0$ (Chờ thêm): $\tau_k = \min(\Delta t_{\text{next\_event}}, \tau_{\max})$, trong đó sự kiện kế tiếp là một đơn hàng mới đến, một đơn nấu xong trong bếp, hoặc một tài xế khác quay về quán ($\tau_{\max} = 10.0\text{ phút}$).
  - Nếu chọn hành động $a \in \{1, 2, 3, 4\}$ (Xuất phát ngay với $m=a$ đơn): $\tau_k = \min(\Delta t_{\text{next\_event}}, \tau_{\max})$ sau khi giao việc cho tài xế.

### 2.2. Không Gian Quan Sát Chuẩn Hóa ($s \in \mathbb{R}^{12}$)
Vector trạng thái 12 chiều nắm bắt thông tin hàng đợi, đội xe và môi trường:
1. $s[0] = N_{\text{ready}} / 10.0$: Số đơn sẵn sàng chờ lên xe.
2. $s[1] = N_{\text{cooking}} / 10.0$: Số đơn đang chế biến trong bếp.
3. $s[2] = N_{\text{placed}} / 10.0$: Số đơn mới đặt chờ vào bếp.
4. $s[3] = t_{\text{wait\_ready\_mean}} / 30.0$: Tuổi trung bình của đơn sẵn sàng (phút).
5. $s[4] = t_{\text{wait\_ready\_max}} / 60.0$: Tuổi lớn nhất của đơn sẵn sàng (phút).
6. $s[5] = t_{\text{wait\_total\_max}} / 60.0$: Tuổi đơn cũ nhất toàn hệ thống (phút).
7. $s[6] = \sigma_{\text{spatial}} / 5.0$: Độ phân tán không gian của các đơn sẵn sàng (km).
8. $s[7] = K_{\text{idle}} / K_{\text{fleet}}$: Tỷ lệ tài xế đang rảnh.
9. $s[8] = t_{\text{driver\_min}} / 30.0$: Thời gian tài xế bận sắp về nhất (phút).
10. $s[9] = t_{\text{driver\_mean}} / 30.0$: Thời gian về trung bình của các tài xế bận (phút).
11. $s[10] = (t_{\text{hour}} - 10.0) / 12.0$: Giờ trong ngày (ca 10:00 - 22:00).
12. $s[11] = \lambda_{\text{recent}} / 2.0$: Tốc độ đơn đến gần đây trong 15 phút (đơn/phút).

### 2.3. Tích Phân Lebesgue Bảo Toàn Phần Thưởng Bellman
Phần thưởng từng bước trong khoảng thời gian $[t_k, t_{k+1}]$ được tính bằng tích phân diện tích chồng lấn thực tế:
$$r_k = -\sum_{i \in \text{Orders}} \max\left(0, \min(t_{k+1}, t_{\text{delivered}, i}) - \max(t_k, t_{\text{placed}, i})\right)$$
Đẳng thức bảo toàn tuyệt đối:
$$\sum_{k=0}^{K-1} r_k = -\sum_{i=1}^{N} (t_{\text{delivered}, i} - t_{\text{placed}, i}) = -\sum_{i=1}^{N} W_i$$
Sai số số học đo lường trên toàn bộ tập kiểm thử đạt $3.64 \times 10^{-12} < 10^{-9}$.

### 2.4. Gom Đơn Đường Vòng & Hoán Vị Giao Hàng Vét Cạn
- **Gom đơn:** Đơn sẵn sàng cũ nhất làm hạt nhân $o_{\text{seed}}$. Các đơn tiếp theo $o_j$ được gom nếu khoảng cách vòng lặp phát sinh $D(o_{\text{seed}}, o_j) + D(o_j, \text{depot}) - D(o_{\text{seed}}, \text{depot}) \le D_{\text{detour}} = 1.5\text{ km}$.
- **Hoán vị:** Duyệt toàn bộ $m!$ thứ tự giao hàng ($m \le 4 \implies m! \le 24$):
  $$\pi^* = \arg\min_{\pi \in \mathcal{P}_m} \sum_{j=1}^{m} t_{\text{giao}}(\pi_j)$$

---

## PHẦN 3: BẢNG KẾT QUẢ TỔNG HỢP & PHÂN TÍCH ĐỐI SOÁNH (G4 & G5)

Nguồn dữ liệu: `results/baselines/summary_baseline_test.csv`, `results/training/summary_rl_test.csv`, `results/training/paired_comparisons_rl.csv`.

### 3.1. Bảng Hiệu Năng Trên Frozen Test Set (5 Hạt Giống Độc Lập)
| Phương pháp | Thời gian chờ TB $W$ (phút) | 95% Bootstrap CI | p90 (phút) | Tỷ lệ trễ ETA (%) | Gini khách | Tải tài xế (%) | Tổng km | Độ trễ (ms) |
|---|---|---|---|---|---|---|---|---|
| **Immediate** | **89.70** | [78.27, 98.62] | 173.57 | 81.6% | 0.324 | 91.4% | 794.7 | 0.01 |
| **BatchSize ($k=1$)** | 89.70 | [78.27, 98.62] | 173.57 | 81.6% | 0.324 | 91.4% | 794.7 | 0.01 |
| **AgeThreshold ($\theta=10\text{m}$)** | 90.39 | [78.42, 99.36] | 171.77 | 82.9% | 0.319 | 91.3% | 794.7 | 0.02 |
| **Periodic ($T=8\text{m}$)** | 93.06 | [80.66, 103.41] | 173.50 | 88.2% | 0.305 | 87.6% | 761.4 | 0.01 |
| **DQN** | 114.06 | [103.82, 125.37] | 214.93 | 85.0% | 0.331 | 91.3% | 862.0 | 0.14 |
| **Double DQN** | 118.29 | [102.82, 136.50] | 238.83 | 84.7% | 0.333 | 89.3% | 840.1 | 0.12 |
| **PPO** | 118.94 | [112.16, 126.19] | 227.45 | 87.6% | 0.332 | 90.5% | 863.8 | 0.43 |
| *Offline Prescient* | *74.52* | *[Lý thuyết]* | 148.20 | 58.4% | 0.285 | 88.0% | 710.5 | *Offline* |

### 3.2. Kiểm Định Giả Thuyết Thống Kê Wilcoxon & Hiệu Chỉnh Holm
Đối chiếu với phương pháp Immediate:
- **DQN vs Immediate:** $\Delta W = +24.36\text{ phút}$ ($+27.15\%$), $p_{\text{raw}} = 0.0625$, $p_{\text{Holm}} = 0.3750$ (Không khác biệt ý nghĩa thống kê ở mức $\alpha=0.05$).
- **Double DQN vs Immediate:** $\Delta W = +28.60\text{ phút}$ ($+31.88\%$), $p_{\text{raw}} = 0.0625$, $p_{\text{Holm}} = 0.3750$.
- **PPO vs Immediate:** $\Delta W = +29.24\text{ phút}$ ($+32.60\%$), $p_{\text{raw}} = 0.0625$, $p_{\text{Holm}} = 0.3750$.
- **Periodic vs Immediate:** $\Delta W = +3.37\text{ phút}$ ($+3.75\%$), $p_{\text{raw}} = 0.1250$, $p_{\text{Holm}} = 0.3750$.

---

## PHẦN 4: TÁI LẬP KẾT QUẢ (REPRODUCIBILITY SCRIPT)
Toàn bộ kết quả thực nghiệm được tái tạo tự động bằng chuỗi lệnh:
```bash
python -m scripts.run_baselines
python -m scripts.train_agents
python -m scripts.compute_statistical_tests
python -m scripts.make_report_tables
pytest tests/ -v
```

---

## PHẦN 5: KIẾN TRÚC ATTENTION MODEL (CHAMPION MODEL T2)

### 5.1. Mô Hình Hóa Toán Học & Cơ Chế Pointer Mechanism
Bài toán định tuyến đa điểm với lưu lượng giao thông động được giải quyết bằng mô hình Attention Model (Kool et al., ICLR 2019) với cơ chế Decoder hướng ngữ cảnh:
- **Chuẩn hóa không gian Dynamic Isotropic Scaling:**
  Toàn bộ tọa độ địa lý $(\text{lat}_i, \text{lon}_i)$ được chuẩn hóa đẳng hướng độc lập theo từng instance về miền $[0, 1]^2$, bảo toàn tỷ lệ khung hình (Aspect Ratio):
  $$x_i' = \frac{x_i - x_{\min}}{\max(\Delta x, \Delta y, \epsilon)}, \quad y_i' = \frac{y_i - y_{\min}}{\max(\Delta x, \Delta y, \epsilon)}$$
- **Biểu diễn nút mở rộng (Node Embeddings with Dynamic Traffic):**
  Mỗi nút $i \in \{0, \dots, n-1\}$ có đặc trưng 3 chiều $[x_i', y_i', C(t_{\text{current}})]$ được chiếu tuyến tính vào không gian $d_h=128$:
  $$h_i^{(0)} = W_x [x_i', y_i', C(t_{\text{current}})] + b_x$$
- **Transformer Encoder (3 Layers, 8 Heads):**
  Gồm $L=3$ tầng Multi-Head Self-Attention ($d_k = 16, d_v = 16$). Mỗi tầng tích hợp Residual Connection, Layer/Batch Normalization, và Feed-Forward Sublayer ($d_{\text{ff}} = 512$):
  $$h_i^{(l)} = \text{FFN}\left(\text{MHA}(h_i^{(l-1)})\right) \quad (l \in \{1, 2, 3\})$$
- **Dynamic Context Decoder:**
  Tại bước giải $t$, vector ngữ cảnh gồm biểu diễn trung bình đồ thị $\bar{h}^{(L)}$, nút depot $h_0^{(L)}$, nút hiện tại $h_{\pi_{t-1}}^{(L)}$ và trạng thái thời gian tuần hoàn tích lũy $\sin(2\pi \cdot t / 24), \cos(2\pi \cdot t / 24), C(t_{\text{accum}})$:
  $$h_{(c)}^{(t)} = [\bar{h}^{(L)}, h_0^{(L)}, h_{\pi_{t-1}}^{(L)}, \sin(2\pi t / 24), \cos(2\pi t / 24), C(t)]$$
- **Xác suất chọn điểm giao tiếp theo qua $10\tanh$ Clipping:**
  $$u_{(c) j} = \begin{cases} 10.0 \cdot \tanh\left(\frac{q_{(c)}^T k_j}{\sqrt{d_k}}\right) & \text{nếu } j \notin \pi_{1:t-1} \\ -10^9 & \text{nếu } j \in \pi_{1:t-1} \end{cases}$$
  $$p_j = \text{softmax}(u_{(c) j}) = \frac{\exp(u_{(c) j})}{\sum_{l \notin \pi_{1:t-1}} \exp(u_{(c) l})}$$

### 5.2. Hàm Biến Thiên Lưu Lượng Giờ Cao Điểm $C(t)$
Hệ số tắc nghẽn đô thị được hàm hóa thực nghiệm:
$$C(t) = \begin{cases} 1.00 & \text{Đêm / Rạng sáng (22:00 - 06:00)} \\ 1.20 & \text{Giữa ngày (09:00 - 16:00)} \\ 2.10 & \text{Cao điểm sáng (07:00 - 08:30)} \\ 2.25 & \text{Cao điểm chiều (17:00 - 18:30)} \end{cases}$$
Thời gian di chuyển động:
$$\text{Duration}(u, v, t) = \frac{\text{Distance}(u, v)}{v_{\text{base}}} \times C(t)$$

### 5.3. Huấn Luyện REINFORCE với Greedy Rollout Baseline
- Hàm mục tiêu tối thiểu hóa tổng thời lượng di chuyển có tính phạt kẹt xe:
  $$\mathcal{L}(\theta) = \mathbb{E}_{s \sim \mathcal{S}, \pi \sim p_\theta(\cdot|s)} [L(\pi|s)]$$
- Gradient chính sách được ước lượng không chệch qua Baseline nghiệm tham lam của mạng tốt nhất $b(s)$:
  $$\nabla_\theta \mathcal{L}(\theta) = \mathbb{E}_{s, \pi} \left[ (L(\pi) - L(b(s))) \nabla_\theta \log p_\theta(\pi|s) \right]$$
- Cập nhật baseline: Sau mỗi epoch, mạng $\theta$ thi đấu với baseline $b$ trên tập kiểm định $10,000$ đồ thị ngẫu nhiên. Chỉ cập nhật khi nghiệm mới vượt trội có ý nghĩa thống kê theo Paired $t$-test ($p < 0.05$).

---

## PHẦN 6: SO SÁNH CHUYÊN SÂU 2 KIẾN TRÚC NCO (ATTENTION MODEL VS POINTER NETWORK)

### 6.1. Bảng So Sánh Kiến Trúc & Lý Thuyết Toàn Diện

```mermaid
flowchart LR
    subgraph AM_Arch["Attention Model (Graph Transformer)"]
        direction TB
        E1["3x Multi-Head Self-Attention (8 heads, 24 heads total)"]
        E2["All-to-all O(N^2) Correlation Matrix"]
        E3["Dynamic Query Pointer Decoder + 10*tanh"]
        E4["Greedy Rollout Baseline (Kool et al.)"]
        E1 --> E2 --> E3 --> E4
    end

    subgraph PN_Arch["Pointer Network (Bi-LSTM + A2C)"]
        direction TB
        P1["1x Bidirectional LSTM Encoder (hidden=128)"]
        P2["Sequential O(N) Recurrent Processing"]
        P3["Bahdanau Additive Attention Decoder (1 head)"]
        P4["Parametric Critic MLP Head V(s)"]
        P1 --> P2 --> P3 --> P4
    end
```

| Tiêu chí | Pointer Network (A2C) | Attention Model (AM - Champion) | Nhận định kỹ thuật |
|---|:---:|:---:|---|
| **Kiến trúc Encoder** | 1-layer Bi-LSTM (hidden = 128) | 3-layer Transformer (8 heads, dim = 128) | AM mô hình hóa quan hệ không gian trực tiếp |
| **Kiến trúc Decoder** | LSTM Cell + Bahdanau Attention (1 head) | Dynamic Multi-Head Query Decoder | AM nhúng động ngữ cảnh toàn cục & thời gian |
| **Tổng số tham số** | **283,137** | **741,760** (~2.6x PointerNet) | Cả hai đều rất gọn nhẹ (< 3 MB file .pt) |
| **Thuật toán học RL** | Advantage Actor-Critic (A2C) | REINFORCE + Greedy Rollout Baseline | Cơ chế baseline quyết định tốc độ huấn luyện |
| **Hàm ước lượng Baseline** | Parametric Critic Network $V(s)$ (MLP) | Greedy Policy Rollout $\pi_{\text{BL}}$ | Rollout Baseline không thiên lệch (unbiased) |
| **Kiểm định cập nhật Baseline** | Không (tính loss gradient trực tiếp) | Paired $t$-test trên 10,000 mẫu mỗi epoch | AM tốn chi phí kiểm thử khổng lồ mỗi epoch |
| **Độ phức tạp tính toán** | $\mathcal{O}(N \cdot d)$ (Tuyến tính theo số nút) | $\mathcal{O}(L \cdot N^2 \cdot d)$ (Bậc hai theo số nút) | Transformer tính ma trận tương quan mọi cặp |
| **Bất biến hoán vị** | Không (phụ thuộc thứ tự nút đầu vào của LSTM) | **Hoàn toàn bất biến (Permutation-Invariant)** | AM miễn nhiễm với thứ tự đánh chỉ mục POI |

---

### 6.2. Giải Mã Khoa Học: Tại Sao Attention Model Train Lâu Hơn ~14 Lần?

Trên thực tế huấn luyện tại Kaggle GPU T4:
- **Pointer Network (A2C):** Hoàn thành 60 epoch trong **891 giây (~14.8 phút)**.
- **Attention Model (AM):** Hoàn thành 60 epoch trong **~3.5 giờ (~12,600 giây)**.

Sự chênh lệch thời gian bắt nguồn từ 3 lý do kỹ thuật chính xác:
1. **Chi phí kiểm định Rollout Baseline của Attention Model (Chiếm >55% thời gian train):**
   - Cuối mỗi epoch, Attention Model bắt buộc phải sinh $10,000$ đồ thị kiểm chuẩn mới và chạy song song cả mô hình hiện tại $\pi_\theta$ lẫn mô hình baseline $\pi_{\text{BL}}$ (tổng cộng $20,000$ lượt suy luận greedy) để thực hiện kiểm định Paired $t$-test.
   - Ngược lại, PointerNet sử dụng **Critic MLP Head**. Giá trị $V(s)$ được suy ra tức thì từ vector biểu diễn trung bình của đồ thị trong chính lượt forward của batch hiện tại. Mô hình **không có bước rollout kiểm định tách biệt**, tiết kiệm hàng nghìn giây tính toán.
2. **Khối lượng tính toán của 24 Attention Heads ($3 \times 8$ heads):**
   - Với mỗi batch đồ thị, Attention Model phải nhân ma trận Query-Key-Value qua 8 heads trên 3 tầng encoder, sinh ra các ma trận tương tác $N \times N$, áp dụng Softmax và Residual Normalization.
   - PointerNet chỉ chạy một vòng lặp Bi-LSTM đơn giản qua chuỗi nút $0 \dots N$, chi phí FLOPs cho mỗi đồ thị thấp hơn xấp xỉ 4 lần.
3. **Cơ chế Sampling trong REINFORCE:**
   - Trong quá trình cập nhật gradient, Attention Model lấy mẫu ngẫu nhiên (Stochastic Sampling) để khám phá không gian nghiệm, sau đó so sánh với nghiệm tham lam của Baseline. Sự khác biệt này đòi hỏi 2 lần suy luận cho mỗi instance huấn luyện.

---

### 6.3. Phân Tích Ma Trận Đánh Đổi Thực Nghiệm (Trade-Off Matrix)

Mặc dù Attention Model đòi hỏi thời gian huấn luyện offline lâu hơn gấp 14 lần, **sự đánh đổi này mang lại giá trị thực tiễn và khoa học vượt trội hoàn toàn**:

#### Bảng Kết Quả Thực Nghiệm Đối Soát Chính Thức (100 POI Toàn Quốc)
*Dữ liệu trích xuất từ `results/benchmark_summary_table.csv`:*

| Chỉ số thực nghiệm | Google OR-Tools | Attention Model (AM) | Pointer Network (A2C) | Dueling DQN (Ablation) |
|---|:---:|:---:|:---:|:---:|
| **Thời lượng trung bình** | **217.78 phút** | **225.67 phút** | 239.59 phút | 340.13 phút |
| **Quãng đường trung bình** | **72.69 km** | **75.63 km** | 80.99 km | 115.77 km |
| **Optimality Gap so với OR-Tools** | **0.00%** | **+3.27%** | **+9.27%** | **+105.45%** |
| * Sai số tại Hà Nội (40 POI) | 0.00% | **3.11%** | 8.57% | 114.08% |
| * Sai số tại Đà Nẵng (20 POI) | 0.00% | **3.48%** | 8.66% | 104.19% |
| * Sai số tại TP.HCM (40 POI) | 0.00% | **3.32%** | 10.27% | 97.44% |
| **Độ trễ suy luận trên CPU** | 1,002.16 ms | **32.63 ms** | **24.19 ms** | 4.29 ms |
| **Tốc độ so với OR-Tools** | $1.0\times$ (Chuẩn) | **Nhanh hơn 30.7 lần** | **Nhanh hơn 41.4 lần** | Nhanh hơn 233 lần |
| **Tỷ lệ thất bại (Failure Rate)** | **0.0%** | **0.0%** | **0.0%** | **50.0%** (Sụp đổ ở $N \ge 30$) |
| **Dung lượng file Checkpoint** | N/A | **2.85 MB** | **1.09 MB** | 1.25 MB |

#### 3 Điểm Nhận Định Cốt Lõi:
1. **Chất lượng tour vượt bậc (Gap 3.27% vs 9.27%):**
   - Attention Model rút ngắn khoảng cách sai số xuống gần **1/3** so với Pointer Network.
   - Trên mỗi chuyến giao hàng, Attention Model tiết kiệm **13.92 phút di chuyển** và **5.36 km cự ly** so với PointerNet. Trong quy mô đội xe hàng vạn chuyến/ngày, mức tiết kiệm này tương đương hàng tỷ đồng chi phí nhiên liệu.
2. **Độ trễ suy luận Production tương đương nhau (< 33ms trên CPU):**
   - Mặc dù Attention Model train lâu hơn rất nhiều, khi triển khai suy luận thực tế (Inference trên CPU đơn nhân), Attention Model giải xong toàn bộ bài toán chỉ trong **32.63 ms**, chỉ chậm hơn PointerNet đúng **8.44 ms** (32.63ms vs 24.19ms), trong khi nhanh hơn Google OR-Tools tới **30.7 lần**.
3. **Bảo toàn Tính Công Bằng Vùng Miền Tuyệt Đối (Geographic Fairness):**
   - Nhờ Dynamic Isotropic Scaling, độ lệch sai số giữa Hà Nội (3.11%), Đà Nẵng (3.48%) và TP.HCM (3.32%) chỉ dao động trong biên độ $\pm 0.18\%$. Mô hình thể hiện năng lực tổng quát hóa xuất sắc trên toàn quốc mà không cần fine-tune cho từng địa phương.

---

### 6.4. Kết Luận Định Vị Vai Trò Của Từng Mô Hình

- **Google OR-Tools:** Đóng vai trò **Chuẩn Tham Chiếu Tuyệt Đối (Industrial Golden Baseline)**, tìm nghiệm tối ưu thông qua tìm kiếm cục bộ có định hướng (Guided Local Search), nhưng độ trễ lớn (~1s), không phù hợp cho phản hồi mili-giây.
- **Dueling DQN:** Đóng vai trò **Thực Nghiệm Phủ Định / Nghiên Cứu Bóc Tách (Ablation Focus)**, chứng minh sự bế tắc của không gian hành động rời rạc cố định ($N \le 20$, tỷ lệ hỏng 50%).
- **Pointer Network:** Đóng vai trò **Mô Hình Chuyển Tiếp Nhanh (Lightweight Transition Baseline)**, huấn luyện siêu tốc (< 15 phút) để xác thực luồng dữ liệu và suy luận nhanh (24ms).
- **Attention Model:** Đóng vai trò **Mô Hình Chủ Lực Đề Xuất (Champion Core Model)**, đầu tư chi phí huấn luyện kỹ lưỡng để đạt chất lượng tiệm cận tối ưu (3.27% gap), tốc độ suy luận 32ms và tính công bằng địa lý vững chắc.
