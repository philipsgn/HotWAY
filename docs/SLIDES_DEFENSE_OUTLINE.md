# ĐỀ CƯƠNG BẢO VỆ KHÓA LUẬN TỐT NGHIỆP (15 SLIDES DEFENSE OUTLINE)
## HỆ THỐNG ĐIỀU PHỐI ĐỊNH TUYẾN LOGISTICS ĐÔ THỊ TOÀN QUỐC — HOTWAY v7.3.2

> **Đơn vị:** Nhóm Nghiên Cứu HotWAY — Đồ án Tốt nghiệp Kỹ sư / Thạc sĩ Công nghệ Thông tin  
> **Thời lượng trình bày:** 20 phút thuyết trình + 10 phút chất vấn Hội đồng  
> **Phiên bản hệ thống:** v7.3.2 (Eliminate Regional Bias & Dynamic Isotropic Scaling Edition)  
> **Dữ liệu thực nghiệm:** 100 POI Toàn Quốc (Hà Nội: 40, Đà Nẵng: 20, TP.HCM: 40)  
> **Trạng thái kiểm thử:** 62/62 ca kiểm thử tự động PASSED (`py -3.13 -m pytest tests/`).  
> **Trọng số thực nghiệm:** Attention Model (741,760 tham số) & PointerNet (283,137 tham số) đã huấn luyện trên Kaggle GPU T4 và nạp thành công (`weights_loaded=True`).

---

### SLIDE 1: TRANG TIÊU ĐỀ & TỔNG QUAN ĐỀ TÀI
* **Tiêu đề chính:** Ứng Dụng Attention Mechanism và Dynamic Isotropic Scaling Trong Tối Ưu Định Tuyến Giao Hàng Chặng Cuối Đô Thị Tại Việt Nam.
* **Subtitle:** Multi-model neural combinatorial routing evaluated on a 100-instance Vietnam benchmark sampled across Hanoi, Da Nang, and Ho Chi Minh City.
* **Thành viên thực hiện & Người hướng dẫn:** Thông tin sinh viên & Giáo viên hướng dẫn.
* **Tuyên ngôn khoa học cốt lõi:** *"Khắc phục hiện tượng lệch phân phối địa lý (Distribution Shift) bằng Dynamic Isotropic Scaling per-instance, chứng minh tính vượt trội về tốc độ suy luận của Attention Model (32.6 ms trên CPU, nhanh hơn ~31 lần so với Google OR-Tools) với sai số tiệm cận chỉ 3.27%."*

---

### SLIDE 2: BỐI CẢNH ĐÔ THỊ & ĐỘNG CƠ NGHIÊN CỨU (E0)
* **Thực trạng logistics chặng cuối tại Việt Nam:**
  * Hơn 85% lưu lượng giao hàng thương mại điện tử (Shopee, Lazada, TikTok Shop) được thực hiện bằng xe máy.
  * Mạng lưới đường xá đặc thù: tỷ lệ hẻm sâu, ngõ hẹp lớn (>18% tại Hà Nội và TP.HCM), giao cắt không đèn tín hiệu, xung đột rẽ trái thường xuyên.
  * Tắc đường động theo khung giờ cao điểm (sáng 7h-9h, chiều 17h-19h) làm tăng thời gian di chuyển từ 1.4x đến 2.25x.
* **Điểm nghẽn của hệ thống hiện hữu:**
  * Các giải pháp truyền thống định tuyến tĩnh theo cự ly Euclidean/Manhattan, bỏ qua biến thiên thời gian thực động $C(t)$.
  * Bộ giải kinh điển (Google OR-Tools) tốn >1,000 ms trên mỗi tour, gây tắc nghẽn khi phải điều phối đồng thời hàng nghìn đơn hàng theo thời gian thực.

---

### SLIDE 3: KIẾN TRÚC TỔNG THỂ 3 TẦNG BÀI TOÁN (T1 / T2 / T3)
* **Sơ đồ phân tầng rõ ràng:**
  1. **Tầng T1 (Macro Routing — Tuyến Pareto A $\to$ B):** Sinh đồng thời 4 tuyến tối ưu không bị thống trị: Nhanh nhất (14.2m), Ngắn nhất (2.19km), Ổn định nhất (p90 14.6m), Dễ đi nhất (0 khúc rẽ trái cắt dòng).
  2. **Tầng T2 (Meso Routing — Lập tuyến đội xe VRPTW & NCO):** Định tuyến gom đơn đa điểm với khung thời gian (Time Windows) bằng Attention Model kết hợp Dynamic Isotropic Scaling, đối soát toàn diện với PointerNet, DQN và Google OR-Tools.
  3. **Tầng T3 (Micro Routing — Đổi tuyến thích nghi thời gian thực):** Lắng nghe dữ liệu tắc đường qua Server-Sent Events (SSE), kích hoạt Dynamic Dijkstra điều chỉnh nhánh đường trong <1ms.
* **Cơ chế Router Dự phòng 3 Lớp (3-Tier Fallback Router):**
  * Lớp 1 (L1): TomTom Traffic API.
  * Lớp 2 (L2): HERE Maps Routing API.
  * Lớp 3 (L3): OSRM Client kết hợp hàm phạt tắc đường nội sinh $C(t)$.

---

### SLIDE 4: MÔ HÌNH TOÁN HỌC & HÀM CHI PHÍ GIAO THÔNG $C(t)$
* **Công thức trọng số cạnh động:**
  $$w_{ij}(t) = \frac{d_{ij}}{v_{\text{base}}} \cdot C_{ij}(t) \cdot \Phi_{\text{weather}} + \text{Penalty}_{\text{left\_turn}}$$
* **Hàm phạt rẽ trái cắt dòng đô thị:**
  $$\text{Penalty}_{\text{left\_turn}} = \begin{cases} 45.0 \text{ giây} & \text{nếu giao cắt không có đèn tín hiệu} \\ 15.0 \text{ giây} & \text{nếu có pha đèn riêng} \end{cases}$$
* **Hàm suy biến tốc độ do mưa nhiệt đới:**
  $$\Phi_{\text{weather}} = 1.40 \quad (\text{khi lượng mưa } > 20\text{mm/h})$$
* **Hàm tắc đường $C(t)$:** Hàm điều biến thời gian theo chu kỳ ngày với đỉnh cao điểm sáng (7h30-8h30: $2.1\times$) và chiều (17h00-18h30: $2.25\times$).

---

### SLIDE 5: KIẾN TRÚC MÔ HÌNH ATTENTION MODEL (CHAMPION CORE)
* **Kiến trúc Graph Transformer:**
  * Encoder: 3 lớp Multi-Head Attention (8 heads, embedding dim 128, tổng 741,760 tham số).
  * Decoder Pointer: Tự động điều kiện hóa trên Graph context, node hiện tại, depot và trạng thái thời gian động $\sin/\cos(2\pi \cdot t / 24)$ kết hợp $C(t)$.
* **Huấn luyện tăng cường REINFORCE với Rollout Baseline:**
  * 60 epoch huấn luyện trên Kaggle GPU T4 với 12,000 instance tổng hợp.
  * Hàm loss REINFORCE: $\mathcal{L}(\theta) = \mathbb{E}\left[(C(\pi) - C(\pi^{\text{BL}})) \sum \log p_\theta(\pi_t)\right]$.
  * Chi phí tour giảm đều đặn từ $299.68$ xuống $199.87$ đơn vị thời gian.

---

### SLIDE 6: BÓC TÁCH 4 TỬ HUYỆT CỦA DUELING DQN (ABLATION STUDY)
1. **Không gian hành động cố định (Fixed Action Space):** DQN giới hạn `max_nodes=20`, sụp đổ hoàn toàn (Failure rate 50.0%) trên các bài toán $N=30$ và $N=50$.
2. **Phá vỡ bất biến hoán vị (Permutation Invariance Violation):** MLP phẳng phụ thuộc thứ tự đầu vào của tọa độ các điểm.
3. **Ảo giác giá trị Q do Action Masking:** Trừ $-10^9$ làm méo mó nghiêm trọng hàm mục tiêu Bellman $\max_{a'} Q(s', a')$.
4. **Độ lệch khoảng cách (Distance Gap):** Chênh lệch thời gian +105.45% so với OR-Tools ngay cả ở quy mô nhỏ $N=10, 20$.

---

### SLIDE 7: CƠ CHẾ DYNAMIC ISOTROPIC SCALING (TRIỆT TIÊU LỆCH VÙNG MIỀN)
* **Vấn đề phân phối tọa độ:** Hà Nội ($\approx 21.0^\circ\text{N}, 105.8^\circ\text{E}$), Đà Nẵng ($\approx 16.0^\circ\text{N}, 108.2^\circ\text{E}$), TP.HCM ($\approx 10.8^\circ\text{N}, 106.6^\circ\text{E}$). Huấn luyện tại một thành phố sẽ thất bại ở thành phố khác nếu dùng tọa độ thô.
* **Giải pháp Dynamic Isotropic Scaling:**
  $$x_{\text{scaled}} = \frac{x - x_{\min}}{\max(\Delta x, \Delta y, \epsilon)}, \quad y_{\text{scaled}} = \frac{y - y_{\min}}{\max(\Delta x, \Delta y, \epsilon)}$$
* Chuẩn hóa đẳng hướng bảo toàn tỷ lệ co dãn hình học (Aspect Ratio), cho phép mô hình chuyển giao zero-shot qua mọi miền địa lý mà không cần retrain.

---

### SLIDE 8: HUẤN LUYỆN ĐỘNG & BẢO TOÀN THỜI GIAN VẬT LÝ
* Đưa thời gian vật lý có ý nghĩa vào huấn luyện: $15\text{ km}$ quy ước trong unit-square với vận tốc cơ sở $25\text{ km/h}$, tương ứng $36\text{ phút/đơn vị tọa độ}$.
* Quá trình huấn luyện trải nghiệm đầy đủ sự thay đổi giữa khung giờ bình thường và giờ cao điểm.
* Checkpoint được xuất tự động cùng biểu đồ hội tụ `training_convergence_curves.png`.

---

### SLIDE 9: BỘ DỮ LIỆU ĐỐI SOÁT 100 POI TOÀN QUỐC
* 100 kịch bản định tuyến đa điểm tổng hợp trải đều 3 miền kinh tế:
  * **Hà Nội (40 instances):** Cụm Hoàn Kiếm, Cầu Giấy, Nam Từ Liêm, Đống Đa.
  * **Đà Nẵng (20 instances):** Cụm Hải Châu, Sơn Trà, Ngũ Hành Sơn.
  * **TP. Hồ Chí Minh (40 instances):** Cụm Quận 1, Bình Thạnh, Thủ Đức, Quận 7.
* Phân tầng quy mô: $N=10$ (30 bài), $N=20$ (30 bài), $N=30$ (20 bài), $N=50$ (20 bài).

---

### SLIDE 10: BẢNG KẾT QUẢ ĐỐI SOÁT THỰC NGHIỆM CHÍNH THỨC (100 POI)

| Mô hình | Thời gian (phút) | Khoảng cách (km) | Optimality Gap vs OR-Tools | HN Gap | DN Gap | HCM Gap | Độ trễ CPU (ms) | Tỷ lệ lỗi (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Google OR-Tools** (Heuristic) | 217.78 | 72.69 | **0.00%** | 0.00% | 0.00% | 0.00% | 1002.16 | 0.0% |
| **Attention Model (AM)** (Đề xuất) | 225.67 | 75.63 | **+3.27%** | **3.11%** | **3.48%** | **3.32%** | **32.63** | **0.0%** |
| **Pointer Network (A2C)** (Baseline) | 239.59 | 80.99 | **+9.27%** | 8.57% | 8.66% | 10.27% | **24.19** | **0.0%** |
| **Dueling DQN (Masked)** (Ablation) | 340.13 | 115.77 | **+105.45%** | 114.08% | 104.19% | 97.44% | **4.29** | **50.0%** |

*Số liệu trích xuất trực tiếp từ file kiểm chuẩn tái lập `results/benchmark_summary_table.csv`.*

---

### SLIDE 11: PHÂN TÍCH TÍNH CÔNG BẰNG ĐỊA LÝ & CHUYỂN GIAO ZERO-SHOT
* **Tính công bằng địa lý (Geographic Fairness):**
  * Độ chênh lệch giữa các vùng cực thấp: Hà Nội (3.11%), Đà Nẵng (3.48%), TP.HCM (3.32%) $\implies$ Độ lệch phương sai $< 0.37\%$.
  * Minh chứng đanh thép cho hiệu quả của Dynamic Isotropic Scaling.
* **Khả năng mở rộng quy mô Zero-Shot:**
  * Huấn luyện ở quy mô trung bình ($N=20$).
  * Khi suy luận: $N=10$ đạt gap **0.94%**, $N=20$ đạt gap **3.37%**, $N=30$ đạt gap **3.48%**, $N=50$ đạt gap **5.30%**. Không có bất kỳ hiện tượng sụp đổ bộ nhớ hay suy giảm tour.

---

### SLIDE 12: ĐỘ TRỄ SUY LUẬN & ĐÁP ỨNG THỰC TẾ PRODUCTION TRÊN CPU
* **Đo đạc độ trễ chuẩn xác trên CPU (Intel/AMD Core i5/i7 thương mại):**
  * Attention Model: **32.63 ms** (nhanh hơn Google OR-Tools **30.7 lần**).
  * Pointer Network: **24.19 ms** (nhanh hơn Google OR-Tools **41.4 lần**).
  * Google OR-Tools: **1,002.16 ms** (bị chậm do vòng lặp tìm kiếm cục bộ Guided Local Search).
* **Ý nghĩa thực tiễn:** Khả năng xử lý hơn **30 lượt lập tuyến mỗi giây** trên 1 CPU lõi đơn, loại bỏ yêu cầu trang bị GPU đắt đỏ tại trung tâm điều vận kho bãi.

---

### SLIDE 13: GIAO DIỆN HỆ THỐNG WEBGIS & TRẢI NGHIỆM ĐIỀU HÀNH
* **Công nghệ phát triển:** Next.js 14 App Router, MapLibre GL JS, Tailwind CSS, TypeScript.
* **Phong cách thiết kế chuẩn Executive:** Tinh thần Monochromatic Swiss Editorial, loại bỏ card rườm rà và icon AI trang trí, typography phân tầng rõ nét.
* **Các tính năng tương tác thực tế:**
  * Tùy chọn 3 Hub logistics toàn quốc (Hà Nội, Đà Nẵng, TP.HCM) với hiệu ứng bay máy ảnh (Camera FlyTo) mượt mà.
  * Bộ chọn hành trình tương tác trên 100 POI: hiển thị vị trí kho bưu cục, thứ tự điểm giao hàng và cung đường vẽ trực tiếp trên bản đồ nền vector.
  * Bảng so sánh 4 mô hình thời gian thực lấy dữ liệu trực tiếp từ `/data/benchmark_multi_model_results.json`.

---

### SLIDE 14: BẢO CHỨNG TÁI LẬP KHOA HỌC & KIỂM THỬ TOÀN DIỆN
* **Tính minh bạch và tái lập:**
  * Toàn bộ mã nguồn, cấu hình seed ngẫu nhiên (2026), tập dữ liệu JSON và trọng số kiểm chuẩn được lưu trữ đồng bộ tại Git repository.
  * Không có dữ liệu giả lập bịa đặt: Mọi số liệu trên Slide, Landing Page và Báo cáo PDF đều đối soát trùng khớp 100% với `results/benchmark_summary_table.csv`.
* **Bộ kiểm thử tự động:**
  * **62/62 bài kiểm thử tự động vượt qua thành công** (`tests/test_adaptive_routing_env.py`, `tests/test_multi_model_benchmark.py`, `tests/test_neural_tsp.py`, `tests/test_report_fidelity.py`,...).
  * Kiểm thử nghiêm ngặt tính hợp lệ của chu trình đóng (depot ở hai đầu, mỗi điểm ghé thăm đúng 1 lần).

---

### SLIDE 15: KẾT LUẬN, ĐÓNG GÓP CỐT LÕI & HƯỚNG PHÁT TRIỂN
* **3 Đóng góp học thuật & kỹ thuật then chốt:**
  1. Chứng minh tính hiệu quả của **Dynamic Isotropic Scaling** trong việc triệt tiêu hiện tượng lệch phân phối địa lý cho Neural Combinatorial Optimization tại Việt Nam.
  2. Đạt độ chính xác tiệm cận bộ giải công nghiệp với **Optimality Gap chỉ 3.27%**, trong khi giảm độ trễ tính toán hơn **30 lần** (32.6 ms trên CPU).
  3. Bóc tách và chứng minh định lượng 4 điểm nghẽn tử huyệt của kiến trúc DQN trong bài toán định tuyến tổ hợp.
* **Hướng mở rộng tương lai:**
  * Mở rộng Attention Model sang bài toán có ràng buộc sức chứa xe (Capacitated VRP - CVRP) và định tuyến đội xe hỗn hợp (Fleet Dispatch).
  * Ứng dụng mô hình vào logistics xe tải điện (EVRPTW) có trạm sạc pin.

---

### GỢI Ý TRẢ LỜI CHẤT VẤN HỘI ĐỒNG (Q&A CHEAT SHEET)
1. *Tại sao Optimality Gap của Attention Model đạt 3.27% so với OR-Tools?*
   $\to$ Nhờ kiến trúc Graph Transformer học trực tiếp sự tương quan không gian kết hợp hàm chú ý nhúng biến thiên thời gian động $C(t)$, mô hình tìm ra các đường đi gần như tương đương với giải thuật tìm kiếm cục bộ có định hướng (Guided Local Search) của OR-Tools mà không cần lặp hàng nghìn bước.
2. *Tại sao không dùng OR-Tools luôn mà phải dùng Attention Model?*
   $\to$ OR-Tools mất ~1 giây cho mỗi bài toán 50 điểm và tăng phi tuyến theo số điểm. Trong điều phối động hàng vạn đơn hàng đồng thời, độ trễ 32ms của Attention Model cho phép phản hồi tức thì và hỗ trợ dynamic batching cực tốt trên CPU.
3. *Chuẩn hóa Min-Max có làm méo mó tỷ lệ khoảng cách địa lý thực không?*
   $\to$ Không, vì HotWAY sử dụng **Isotropic Scaling** chia cho $\max(\Delta x, \Delta y)$, giữ nguyên tỷ lệ khung hình 1:1, bảo toàn hoàn hảo hình học không gian.
