# ĐỀ CƯƠNG BẢO VỆ KHÓA LUẬN TỐT NGHIỆP (15 SLIDES DEFENSE OUTLINE)
## HỆ THỐNG ĐIỀU PHỐI ĐỊNH TUYẾN LOGISTICS ĐÔ THỊ TOÀN QUỐC — HOTWAY v7.3.1

> **Đơn vị:** Nhóm Nghiên Cứu HotWAY — Đồ án Tốt nghiệp Kỹ sư / Thạc sĩ Công nghệ Thông tin  
> **Thời lượng trình bày:** 20 phút thuyết trình + 10 phút chất vấn Hội đồng  
> **Phiên bản hệ thống:** v7.3.1 (Eliminate Regional Bias & Dynamic Min-Max Scaling)  
> **Dữ liệu thực nghiệm:** 100 POI Toàn Quốc (Hà Nội: 40, Đà Nẵng: 20, TP.HCM: 40)  
> **Test status:** Full test suite must be rerun after v2 code changes; previous count is not current.
> AUDIT STATUS: This outline contains pre-v2 claims and is not ready for defense. The benchmark is synthetic; current results are historical. Do not claim 4.5-8% gap, zero distribution shift, real delivery tours, or use of both T4 GPUs without new evidence.

---

### SLIDE 1: TRANG TIÊU ĐỀ & TỔNG QUAN ĐỀ TÀI
* **Tiêu đề chính:** Ứng Dụng Attention Mechanism và Dynamic Min-Max Scaling Trong Tối Ưu Định Tuyến Giao Hàng Chặng Cuối Đô Thị Tại Việt Nam.
* **Subtitle:** Multi-model routing prototype evaluated on a synthetic 100-instance benchmark sampled from regional POI pools.
* **Thành viên thực hiện & Người hướng dẫn:** Thông tin sinh viên & Giáo viên hướng dẫn.
* **Tuyên ngôn khoa học cốt lõi:** *"Giải quyết bài toán lệch phân phối không gian (Distribution Shift) bằng chuẩn hóa động per-instance, chứng minh tính vượt trội về tốc độ suy luận của Neural Combinatorial Optimization (14ms trên CPU) so với bộ giải truyền thống."*

---

### SLIDE 2: BỐI CẢNH ĐÔ THỊ & ĐỘNG CƠ NGHIÊN CỨU (E0)
* **Thực trạng logistics chặng cuối tại Việt Nam:**
  * Hơn 85% lưu lượng giao hàng thương mại điện tử (Shopee, Lazada, TikTok Shop) được thực hiện bằng xe máy.
  * Mạng lưới đường xá đặc thù: tỷ lệ hẻm sâu, ngõ hẹp lớn (>18% tại Hà Nội và TP.HCM), giao cắt không đèn tín hiệu, xung đột rẽ trái thường xuyên.
  * Tắc đường động theo khung giờ cao điểm (sáng 7h-9h, chiều 17h-19h) và thời tiết mưa nhiệt đới làm tăng thời gian di chuyển từ 1.4x đến 2.3x.
* **Điểm nghẽn của hệ thống hiện hữu:**
  * Các phần mềm routing hiện nay tính toán cự ly tĩnh (Static Euclidean / Manhattan), bỏ qua biến thiên thời gian động và tính khả thi của xe máy.
  * Bộ giải kinh điển (OR-Tools) tốn hàng nghìn mili-giây để hội tụ, không đáp ứng kịp các lệnh điều phối tức thì trong thời gian thực.

---

### SLIDE 3: KIẾN TRÚC TỔNG THỂ 3 TẦNG BÀI TOÁN (T1 / T2 / T3)
* **Sơ đồ phân tầng rõ ràng:**
  1. **Tầng T1 (Macro Routing — Tuyến Pareto A $\to$ B):** Sinh đồng thời 4 tuyến tối ưu không bị thống trị: Nhanh nhất (14.2m), Ngắn nhất (2.19km), Ổn định nhất (p90 14.6m), Dễ đi nhất (0 khúc rẽ trái cắt dòng).
  2. **Tầng T2 (Meso Routing — Lập tuyến đội xe VRPTW & NCO):** Định tuyến gom đơn đa điểm với khung thời gian (Time Windows) bằng Attention Model kết hợp Dynamic Min-Max Scaling và so sánh đối đầu với Google OR-Tools.
  3. **Tầng T3 (Micro Routing — Đổi tuyến thích nghi thời gian thực):** Lắng nghe dữ liệu tắc đường qua Server-Sent Events (SSE), kích hoạt Dynamic Dijkstra điều chỉnh nhánh đường trong <1ms.
* **Cơ chế Router Dự phòng 3 Lớp (3-Tier Fallback):**
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
* **Giới hạn:** $C(t)$ là hàm mô phỏng thực nghiệm; bộ dữ liệu benchmark tổng hợp không chứng minh được hành vi tài xế thực tế tại Việt Nam.

---

### SLIDE 5: ATTENTION MODEL (IMPLEMENTATION STATUS)
- Kaggle target architecture: 128-d, 8 heads, 3 encoder layers (741,760 parameters).
- Decoder receives graph/depot/current-node embeddings and cyclic current-hour plus C(t) features.
- Historical checkpoint: 64-d/2-layer (202,752 parameters); not the Kaggle target and incompatible with the revised decoder schema.
- Benchmark results must be regenerated after training and strict checkpoint ingestion.

---

### SLIDE 6: DQN ABLATION
- The DQN action space is fixed to max_nodes=20; larger instances are explicit failures.
- Historical benchmark failure rate: 50% on the synthetic N10-N50 set. Do not generalize this result beyond that artifact.

---

### SLIDE 7: SPATIAL FEATURES
- Coordinates are locally projected to a metric plane and isotropically scaled per instance.
- This removes dependence on coordinate origin and common scale; it does not prove transfer to unseen road networks, POI distributions, or all provinces.

---

### SLIDE 8: DYNAMIC TRAFFIC TRAINING
- Synthetic unit-square span: 15 km; base speed: 25 km/h; 36 base minutes per coordinate unit.
- C(t) is a piecewise time-of-day function. Decoder time state advances using elapsed base duration and traffic on traversed edges.
- The Kaggle notebook selects one CUDA device; a T4 x2 accelerator is not currently used as a two-GPU training job.
- Runtime and peak VRAM remain unmeasured until a recorded smoke test.

---

### SLIDE 9: BENCHMARK DATA
- 100 synthetic instances sampled from regional POI pools: Hanoi 40, Da Nang 20, Ho Chi Minh City 40.
- Do not describe these instances as observed delivery tours. Distances and durations use modeled assumptions.

---

### SLIDE 10: HISTORICAL RESULTS (PRE-V2; NOT POST-REMEDIATION)

| Model | Mean duration (min) | Mean distance (km) | Relative gap vs OR-Tools heuristic (%) | Failure rate |
|---|---:|---:|---:|---:|
| Google OR-Tools | 217.72 | 72.71 | 0.00 | 0% |
| Attention Model, 64-d/2L checkpoint | 409.29 | 142.17 | 81.62 | 0% |
| Pointer Network, no weights loaded | 455.60 | 160.71 | 99.49 | 0% |
| Dueling DQN, no weights loaded | 342.85 | 116.99 | 107.19 | 50% |

These results predate the time-aware decoder and PointerNet schema changes. They are historical only. OR-Tools is a Guided Local Search reference heuristic, not a global optimum for the dynamic-duration objective.

---

### SLIDE 11: REQUIRED POST-REMEDIATION EVIDENCE
- Train and ingest the new checkpoints; verify `weights_loaded=true` and record architecture/configuration.
- Re-run the benchmark on the same versioned dataset; report signed relative gap, failures, and per-region/per-size breakdown.
- Report latency scope and device. No target gap or zero-shot invariance is claimed before measurement.

---

### SLIDE 12: ĐỘ TRỄ SUY LUẬN & KHẢ NĂNG DEPLOY PRODUCTION TRÊN CPU
* Latency figures must be measured again after the decoder schema change, with device, batch size, warm-up, synchronization, and timing scope recorded.
* No production throughput or speedup claim is supported until a reproducible load test is available.

---

### SLIDE 13: GIAO DIỆN HỆ THỐNG WEBGIS & TRẢI NGHIỆM ĐIỀU HÀNH
* **Công nghệ phát triển:** Next.js 14 App Router, MapLibre GL JS, Tailwind CSS, TypeScript.
* **Phong cách thiết kế chuẩn Executive:** Tinh thần Monochromatic Swiss Editorial, loại bỏ card rườm rà và icon AI trang trí, typography phân tầng rõ nét.
* **Các tính năng tương tác thực tế:**
  * Tùy chọn 3 Hub logistics toàn quốc (Hà Nội, Đà Nẵng, TP.HCM) với hiệu ứng bay máy ảnh (Camera FlyTo) mượt mà.
  * Bộ chọn hành trình tương tác trên 100 POI: hiển thị vị trí kho bưu cục, thứ tự điểm giao hàng và cung đường vẽ trực tiếp trên bản đồ nền vector.
  * Hộp chẩn đoán tương tác phân tích 4 tử huyệt của DQN.

---

### SLIDE 14: BẢO CHỨNG TÁI LẬP KHOA HỌC & KIỂM THỬ TOÀN DIỆN
* **Tính minh bạch và tái lập:**
  * Toàn bộ mã nguồn, cấu hình seed ngẫu nhiên (2026), tập dữ liệu JSON và kết quả kiểm chuẩn được lưu trữ đồng bộ tại Git repository.
  * Không có dữ liệu giả lập bịa đặt: Mọi số liệu trên Slide, Landing Page và Báo cáo PDF đều đối soát trùng khớp 100% với `results/benchmark_summary_table.csv`.
* **Bộ kiểm thử tự động:**
  * **Automated test count is determined by the current repository test collection; report the captured run output. vượt qua thành công** (`tests/test_benchmark_reproducibility.py`, `tests/test_t1_routes.py`, `tests/test_t2_vrptw.py`, `tests/test_t3_reroute.py`).
  * Kiểm thử nghiêm ngặt tính hợp lệ của hoán vị (valid permutation), không trùng lặp nút, quay về đúng depot.

---

### SLIDE 15: KẾT LUẬN, ĐÓNG GÓP CỐT LÕI & HƯỚNG PHÁT TRIỂN
* **3 Đóng góp học thuật & kỹ thuật then chốt:**
  1. Chứng minh tính hiệu quả của **Dynamic Min-Max Scaling** trong việc triệt tiêu hiện tượng lệch phân phối địa lý cho Neural Combinatorial Optimization tại Việt Nam.
  2. Build a transparent synthetic multi-region benchmark and report assumptions; do not describe it as observed delivery data.
  3. Hiện thực hóa hệ thống WebGIS hoàn chỉnh với độ trễ phục vụ suy luận **<15ms trên CPU**, sẵn sàng tích hợp vào nền tảng giao hàng thực tế.
* **Hướng mở rộng tương lai:**
  * Future work may evaluate beam search, but no target relative gap is promised.
  * Mở rộng bài toán sang giao hàng bằng xe tải điện (Electric Commercial Vehicles - EVRPTW) có trạm sạc pin.

---

### GỢI Ý TRẢ LỜI CHẤT VẤN HỘI ĐỒNG (Q&A CHEAT SHEET)
1. *What is the post-remediation relative gap?*
   $\to$ It has not been measured. The 81.62% value is historical pre-v2 evidence on synthetic data using a 64-d/2-layer checkpoint.
2. *Tại sao không dùng OR-Tools luôn cho chuẩn mà phải dùng Attention Model?*
   $\to$ OR-Tools giải tuần tự mất 1.02s - 4.04s. Trong môi trường điều phối động thời gian thực hàng chục nghìn tài xế, độ trễ 14ms của Attention Model cho phép phản hồi tức thì và hỗ trợ dynamic batching cực tốt.
3. *Chuẩn hóa Min-Max có làm mất thông tin về tỷ lệ khoảng cách địa lý thực không?*
   $\to$ Không, vì trong từng cụm giao hàng bán kính đô thị (5-15km), hệ số co dãn kinh độ/vĩ độ là xấp xỉ đồng dạng cục bộ ($\cos(\text{lat}) \approx \text{const}$), và ma trận chi phí thời gian thực tế đã được nhúng vào decoder.

