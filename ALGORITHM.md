# Đặc Tả Thuật Toán & Phân Tích Thực Nghiệm (ALGORITHM.MD) — HotWAY

> **Tài liệu:** Cơ sở toán học, mô hình Semi-MDP thời gian thực, thuật toán RL và kết quả thực nghiệm  
> **Phiên bản:** v6.1.0 (Real-Time RL Restaurant Dispatch Edition)  
> **Ngày cập nhật:** 24/10/2026  
> **Nguồn sự thật:** `results/training/`, `results/baselines/`, `rel_result/`  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/Asus/Documents/AI/HotWAY/PRD.md) | [ARCHITECTURE.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ARCHITECTURE.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md)

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

### 3.3. Phân Tích Đóng Góp Thành Phần (Ablations)
- Thiếu đặc trưng phân tán không gian ($\sigma_{\text{spatial}}$): $W$ tăng lên **$176.70\text{ phút}$** ($+58.41\text{ phút}$).
- Thiếu đặc trưng tốc độ đơn đến gần đây ($\lambda_{\text{recent}}$): $W$ tăng lên **$172.00\text{ phút}$** ($+53.70\text{ phút}$).
- Thiển cận ($\gamma=0.95$): $W$ nhảy vọt lên **$213.40\text{ phút}$** ($+95.10\text{ phút}$).

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
