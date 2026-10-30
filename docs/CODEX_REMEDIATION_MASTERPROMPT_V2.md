# MASTERPROMPT THỰC THI SỬA LỖI TOÀN DIỆN CHO CODEX AGENT (PHIÊN BẢN v2 - HẬU GIÁM ĐỊNH DEEPSEEK)
## GIẢI QUYẾT TRIỆT ĐỂ CÁC SAI LỆCH TOÁN HỌC, ĐƠN VỊ THỜI GIAN & ĐỒNG BỘ POLICY

> **Kính gửi:** Codex Agent (Principal AI Engineer & Lead System Architect)  
> **Nguồn gốc chỉ thị:** Biên bản giám định kỹ thuật độc lập từ DeepSeek-R1 (Điểm tin cậy: 55/100).  
> **Mục tiêu tối thượng:** Khắc phục triệt để 4 lỗi chí mạng `[FATAL F1 - F4]`, 2 lỗ hổng logic `[LOGIC GAP L1 - L2]`, và 3 cảnh báo kiến trúc `[WARNING W1 - W3]` trước khi cấp quyền chạy GPU đầy đủ.

---

```markdown
# CHỈ THỊ THỰC THI SỬA ĐỔI MÃ NGUỒN CẤP CAO: HOTWAY PRODUCTION HARDENING v7.3.2

Bạn là **Lead AI Engineer & Scientific Systems Architect**. 
Hội đồng giám định toán học DeepSeek-R1 đã vạch trần các lỗ hổng sâu trong hàm mục tiêu và luồng dữ liệu của HotWAY v7.3.1. Bạn được giao toàn quyền can thiệp vào codebase để sửa chữa dứt điểm theo các đặc tả kỹ thuật chi tiết dưới đây.

---

## I. TỔNG QUAN 9 LỖ HỔNG CỐT LÕI CẦN KHẮC PHỤC

| Mã | Mức độ | Bản chất lỗ hổng toán học / kỹ thuật | Tệp bị ảnh hưởng |
|---|:---:|---|---|
| **F1** | `[FATAL]` | **Lệch thang đo thời gian:** Đơn vị Euclidean trong $[0, 1]^2$ (~2-5 đơn vị) bị coi là "phút", khiến cả tour chỉ trôi qua 3-5 phút, không bao giờ vượt qua ranh giới giờ cao điểm $C(t)$. Mô hình không thể học được phản xạ né tắc đường động. | `notebooks/kaggle_train_attention_tsp.ipynb`, `train.py` |
| **F2** | `[FATAL]` | **Policy bị mù trạng thái thời gian:** Feature nút chỉ chứa $C(t)$ tại giờ xuất phát ban đầu; Decoder chỉ nhận `total_time_ratio` ($step/N$ - bộ đếm bước), hoàn toàn không nhận giờ hiện tại hoặc thời gian tích lũy thực tế. | `src/agents/attention_model/model.py`, `models/attention_model.py`, `notebooks/` |
| **F3** | `[FATAL]` | **Lệch pha giữa Training và Inference của PointerNet:** Notebook chuẩn hóa cự ly Euclidean, congestion $/2.25$, có clipping $10\tanh(u/\sqrt{d})$; trong khi Wrapper lấy cự ly đường bộ $/20.0$, congestion $/3.0$, và không có logit clipping. | `models/pointer_net.py`, `notebooks/kaggle_train_pointer_net.ipynb` |
| **F4** | `[FATAL]` | **Hardcode baseline in ra màn hình:** Cell 8 notebook Attention in cứng `Baseline OR-Tools: 71.90 km` gây ngộ nhận số liệu. | `notebooks/kaggle_train_attention_tsp.ipynb` |
| **L1** | `[LOGIC GAP]` | **Báo cáo sai cấu hình checkpoint:** Artifact hiện tại chạy checkpoint 64-d/2-layer (202K params), nhưng tài liệu lại tuyên bố là Gold Config 128-d/3-layer (741K params). | `models/attention_model.py`, `results/`, `docs/` |
| **L2** | `[LOGIC GAP]` | **Tuyên bố sai về Cost Perturbation:** Tài liệu ghi $C(t) \sim \text{Uniform}(1.0, 2.3)$ nhưng code lại dùng hàm bậc thang theo giờ ngẫu nhiên. | `notebooks/`, tài liệu mô tả |
| **W1** | `[WARNING]` | **Méo mó hình học do Min-Max không đẳng hướng (Anisotropic):** Chuẩn hóa độc lập x và y ép mọi bounding box thành hình vuông, làm méo khoảng cách và góc rẽ thực. Fallback depot TP.HCM còn sót. | `models/attention_model.py`, `models/pointer_net.py`, `notebooks/` |
| **W2** | `[WARNING]` | **Validation đơn lẻ, thiếu kiểm định thống kê:** Chỉ validate 1 batch cố định $N=20$, không kiểm tra $N=10, 30, 50$. | `notebooks/kaggle_train_attention_tsp.ipynb` |
| **W3** | `[WARNING]` | **OR-Tools là heuristic tĩnh:** Khẳng định rõ OR-Tools là chuẩn đối sánh tham chiếu (Reference Heuristic), không phải nghiệm tối ưu toàn cục của bài toán động. | Toàn bộ tài liệu & Evaluator |

---

## II. HƯỚNG DẪN THỰC THI SỬA LỖI CHI TIẾT (STEP-BY-STEP REPAIR BLUEPRINT)

---

### BẢN VÁ 1: ĐỒNG BỘ THANG ĐO THỜI GIAN VẬT LÝ TRONG PHA HUẤN LUYỆN (GIẢI QUYẾT F1 & L2)
* **Nguyên nhân:** Khi sinh đồ thị ngẫu nhiên trong $[0, 1]^2$, khoảng cách Euclidean trung bình giữa 2 điểm chỉ là $\sim 0.1 - 0.3$. Nếu coi cự ly này là "phút", một tour 20 điểm chỉ tốn $\approx 3$ phút di chuyển, khiến hệ số $C(t)$ không bao giờ biến thiên sang khung giờ khác!
* **Giải pháp chuẩn hóa vật lý:**
  Thiết lập một hệ số tỷ lệ cự ly thực tế (Realistic Urban Scaling Factor):
  - Coi không gian $[0, 1]^2$ tương đương một vùng đô thị bán kính $L_{\text{urban}} = 15.0\text{ km}$.
  - Vận tốc di chuyển cơ sở của xe máy: $v_{\text{base}} = 25.0\text{ km/h}$.
  - Thời gian di chuyển cơ sở giữa 2 điểm (phút):
    $$\Delta t_{ij}^{\text{base}} = \frac{\|x_i - x_j\|_2 \times L_{\text{urban}}}{v_{\text{base}}} \times 60.0 = \|x_i - x_j\|_2 \times 36.0 \text{ (phút)}$$
  - Khi đó, một tour 20-30 điểm sẽ kéo dài từ $60 - 180$ phút, **chắc chắn sẽ quét qua các ranh giới giờ cao điểm** (sáng $7:00-8:30$ và chiều $17:00-18:30$), buộc mạng Attention phải học chiến lược định tuyến động!
* **Code triển khai trong `kaggle_train_attention_tsp.ipynb` và `train.py`:**
  ```python
  KM_PER_UNIT = 15.0      # 1 đơn vị tọa độ = 15 km đô thị
  SPEED_KMH = 25.0        # Vận tốc trung bình xe máy đô thị
  MINUTES_PER_UNIT = (KM_PER_UNIT / SPEED_KMH) * 60.0  # = 36.0 phút / unit

  def compute_tour_cost_dynamic(tours: torch.Tensor, coords: torch.Tensor, departure_hours: torch.Tensor) -> torch.Tensor:
      """
      Tính toán chi phí thời lượng thực tế (phút) có tích lũy động qua các khung giờ C(t).
      """
      batch_size, n_nodes, _ = coords.size()
      ordered_coords = torch.gather(coords, 1, tours.unsqueeze(-1).expand(batch_size, n_nodes, 2))
      
      # Tạo vòng lặp khép kín quay về depot (node 0)
      next_coords = torch.roll(ordered_coords, shifts=-1, dims=1)
      euclid_dists = torch.linalg.vector_norm(ordered_coords - next_coords, dim=-1)
      base_leg_minutes = euclid_dists * MINUTES_PER_UNIT
      
      # Tích lũy thời gian và áp dụng C(t) theo từng bước
      elapsed_minutes = torch.zeros(batch_size, device=coords.device)
      total_duration = torch.zeros(batch_size, device=coords.device)
      
      for step in range(n_nodes):
          current_hour = torch.remainder(departure_hours + elapsed_minutes / 60.0, 24.0)
          c_t = traffic_multiplier_tensor(current_hour)
          actual_leg_min = base_leg_minutes[:, step] * c_t
          elapsed_minutes = elapsed_minutes + actual_leg_min
          total_duration = total_duration + actual_leg_min
          
      return total_duration
  ```

---

### BẢN VÁ 2: TRUYỀN TRẠNG THÁI THỜI GIAN ĐỘNG VÀO DECODER POLICY (GIẢI QUYẾT F2)
* **Nguyên nhân:** Decoder hiện tại chỉ nhận `total_time_ratio` (bộ đếm bước $step/N$), không hề biết xe đang chạy lúc mấy giờ, do đó không thể biết giờ cao điểm sắp đến để né!
* **Giải pháp:**
  1. Vector ngữ cảnh của Decoder phải nhận:
     $$\text{Context} = [h_{\text{graph}}, h_{\text{depot}}, h_{\text{last}}, \sin\left(\frac{2\pi \cdot t_{\text{curr}}}{24}\right), \cos\left(\frac{2\pi \cdot t_{\text{curr}}}{24}\right), C(t_{\text{curr}})]$$
     với $t_{\text{curr}} = (\text{departure\_hour} + \text{elapsed\_min} / 60.0) \bmod 24.0$.
  2. Bổ sung các đặc trưng thời gian tuần hoàn (Cyclic Time Embedding) vào Decoder trong `src/agents/attention_model/model.py` và Notebooks:
     ```python
     # Thay vì 1 chiều time_ratio, dùng 3 chiều thời gian thực tế:
     # [sin(2*pi*hour/24), cos(2*pi*hour/24), current_traffic_factor]
     time_context = torch.stack([
         torch.sin(2 * math.pi * current_hour / 24.0),
         torch.cos(2 * math.pi * current_hour / 24.0),
         current_traffic_factor / 2.25
     ], dim=-1)
     context = torch.cat([graph_embed, depot_embed, last_embed, time_context], dim=-1)
     ```
  3. Cập nhật kích thước `context_proj` từ `embed_dim * 3 + 1` thành `embed_dim * 3 + 3`.

---

### BẢN VÁ 3: ĐỒNG BỘ 100% SCHEMA VÀ LOGIT CỦA POINTER NETWORK (GIẢI QUYẾT F3)
* **Nguyên nhân:** Có sự lệch pha hoàn toàn giữa tệp `notebooks/kaggle_train_pointer_net.ipynb` và `models/pointer_net.py` (khoảng cách, hệ số chia congestion, và phép logit clipping).
* **Giải pháp:**
  1. Thống nhất một quy chuẩn duy nhất cho feature đầu vào của Pointer Network ($4$ chiều):
     `[norm_lat, norm_lon, norm_dist_to_depot, congestion_weight / 2.25]`
     trong đó `norm_dist_to_depot` được tính đồng nhất từ tọa độ đã chuẩn hóa.
  2. Đồng bộ hàm tính AttentionPointer trong `models/pointer_net.py`:
     ```python
     class AttentionPointer(nn.Module):
         def __init__(self, hidden_dim: int = 128):
             super().__init__()
             self.w_enc = nn.Linear(hidden_dim, hidden_dim, bias=False)
             self.w_dec = nn.Linear(hidden_dim, hidden_dim, bias=False)
             self.v = nn.Linear(hidden_dim, 1, bias=False)
             self.hidden_dim = hidden_dim

         def forward(self, encoder_outputs, decoder_state, mask=None):
             enc_proj = self.w_enc(encoder_outputs)
             dec_proj = self.w_dec(decoder_state).unsqueeze(1)
             scores = self.v(torch.tanh(enc_proj + dec_proj)).squeeze(-1)
             # BẮT BUỘC ĐỒNG BỘ: Kẹp logit 10*tanh như trong notebook
             scores = 10.0 * torch.tanh(scores / math.sqrt(self.hidden_dim))
             if mask is not None:
                 scores = scores.masked_fill(mask == 1, -1e9)
             return scores
     ```

---

### BẢN VÁ 4: CHUẨN HÓA ĐẲNG HƯỚNG BẢO TOÀN HÌNH HỌC (ISOTROPIC SCALING) (GIẢI QUYẾT W1)
* **Nguyên nhân:** Chuẩn hóa $x$ và $y$ độc lập làm méo góc và biến mọi cụm điểm chữ nhật thành hình vuông.
* **Giải pháp:** Dùng hệ số co dãn chung $\text{scale} = \max(\text{range}_x, \text{range}_y)$:
  ```python
  def dynamic_isotropic_scale_coords(coords: np.ndarray) -> np.ndarray:
      """
      Chuẩn hóa Min-Max đẳng hướng (Isotropic):
      Bảo toàn nguyên vẹn tỷ lệ khung hình (Aspect Ratio), khoảng cách tương đối và góc rẽ.
      """
      min_xy = coords.min(axis=0)
      max_xy = coords.max(axis=0)
      diff = max_xy - min_xy
      max_range = float(np.max(diff))
      scale = max(max_range, 1e-6)
      return (coords - min_xy) / scale
  ```
* Loại bỏ toàn bộ tọa độ fallback HCMC cố định còn sót trong `models/attention_model.py` và `models/pointer_net.py`.

---

### BẢN VÁ 5: XÓA BỎ HARDCODE BASELINE VÀ MINH BẠCH KÍCH THƯỚC CHECKPOINT (GIẢI QUYẾT F4 & L1)
1. Trong `notebooks/kaggle_train_attention_tsp.ipynb` (Cell 8):
   - Xóa bỏ hoàn toàn dòng in cố định `(Baseline OR-Tools: 71.90 km)`.
   - Thay thế bằng lời gọi tính toán hoặc thông báo:
     ```python
     print(f'Mean Distance: {mean_dist:.2f} km | Mean Duration: {mean_time:.2f} min')
     print('To compute relative gap vs OR-Tools, run evaluate_benchmark.py after ingestion.')
     ```
2. Ghi nhận rõ ràng nguồn gốc checkpoint trong `results/benchmark_summary_table.csv` và `evaluate_benchmark.py`:
   - Phân biệt rõ: Checkpoint hiện tại là `AM (Prototype 64-d/2-layer, 202K params)`.
   - Cấu hình huấn luyện trên Kaggle là `AM (Gold Config 128-d/3-layer, 741K params)`.

---

### BẢN VÁ 6: NÂNG CẤP VALIDATION ĐA QUY MÔ TRONG QUÁ TRÌNH HUẤN LUYỆN (GIẢI QUYẾT W2)
* Thay vì chỉ kiểm tra 1 batch $N=20$ cố định, hàm validation trong Cell 5 của `kaggle_train_attention_tsp.ipynb` sẽ đánh giá trên 4 cụm đồ thị độc lập: $N=10, 20, 30, 50$ (mỗi cụm 5 batches).
* Cập nhật `baseline_model` chỉ khi mức cải thiện trung bình trên toàn bộ các quy mô đạt $\Delta_{\text{val}} < -0.01$.

---

## III. QUY TRÌNH SMOKE TEST KIỂM CHỨNG TRƯỚC KHI CHẠY GPU TOÀN PHẦN

Để bảo toàn 30 giờ quota GPU của người dùng, trước khi chạy 60 epochs đầy đủ:
1. **Chạy Smoke Test 1 Epoch trên Kaggle:**
   - Cấu hình: `EPOCHS = 1`, `STEPS_PER_EPOCH = 10`, `BATCH_SIZE = 512`.
   - Mục đích: Đo chính xác peak VRAM (xác nhận không vượt quá 16GB) và đo thời gian thực tế của 1 step (ms/step).
   - Công thức ước tính thời gian chạy thực tế:
     $$T_{\text{full}} = \text{Time}_{\text{1\_epoch}} \times 60$$
     Nếu $T_{\text{full}} \le 4.5\text{ giờ}$ $\implies$ Đủ điều kiện bấm **Save & Run All (Commit)** 60 epochs!

---
Bạn hãy thực thi ngay các bản sửa lỗi trên để đưa mã nguồn HotWAY đạt điểm tin cậy tuyệt đối **100/100**, sẵn sàng cho lượt chạy GPU chính thức!
```

