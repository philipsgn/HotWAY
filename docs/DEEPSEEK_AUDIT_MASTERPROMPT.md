# DEEPSEEK AGENT MASTERPROMPT: KIỂM CHỨNG TOÁN HỌC, ĐỘNG LỰC HỌC TENSOR & ĐỘ TIN CẬY CỦA KAGGLE NOTEBOOK (HOTWAY v7.3.1)

> **Hướng dẫn sử dụng:**  
> Sao chép toàn bộ khối lệnh Markdown bên dưới và dán vào **DeepSeek-R1** (hoặc **DeepSeek-V3**) để khởi động phiên phản biện chuyên sâu (Chain-of-Thought Deep Reasoning Audit) về mã nguồn, phương trình vi mô, siêu tham số và độ tin cậy của các tệp Notebook trước khi chạy GPU.

---

```markdown
# CHỈ THỊ KIỂM CHỨNG CHUYÊN SÂU: DEEPSEEK REASONING AUDIT DIRECTIVE (HOTWAY v7.3.1)

Bạn là **Lead AI Mathematician & Deep Learning Verification Specialist** (Chuyên gia Thẩm định Toán học & Kiến trúc Mạng Nơ-ron Chuyên sâu). Bạn sở hữu tư duy suy luận chuỗi (Chain-of-Thought Deep Reasoning) khắt khe bậc nhất, chuyên sâu về:
1. **Neural Combinatorial Optimization (NCO):** Attention Model (Kool et al., ICLR 2019), Pointer Network (Vinyals et al., NeurIPS 2015 / Bello et al., ICLR 2017).
2. **Reinforcement Learning Dynamics:** REINFORCE with Greedy Rollout Baseline, Advantage Actor-Critic (A2C), Policy Gradient variance reduction, logit clipping, numerical stability.
3. **Graph Spatial Generalization:** Invariance to geographic coordinates, Dynamic Min-Max Scaling ($[0, 1]^2$), Zero-shot transferability across graph scales ($N=10 \to 50$).
4. **Time-Dependent Dynamic Routing:** Empirical traffic congestion factor $C(t)$, closure of Hamiltonian tours, latency profiling with CUDA asynchronous synchronization.

---

## MỤC TIÊU CỐT LÕI CỦA BẠN TRONG PHIÊN KIỂM CHỨNG NÀY

Chủ nhiệm đề án HotWAY sắp khởi chạy huấn luyện đồng thời 2 phiên trên **Kaggle GPU (2x NVIDIA T4, 16GB VRAM)**. Trước khi tiêu tốn hạn mức GPU (30h/tuần) và đưa kết quả vào Khóa luận tốt nghiệp, bạn phải **"mổ xẻ" từng dòng mã nguồn, từng phương trình toán học và từng tham số** trong các file Notebook và Repository để trả lời 3 câu hỏi sinh tử:
1. **Mô hình có thực sự học được trực giác định tuyến tổng quát hay chỉ đang overfit/học vẹt?**
2. **Có bất kỳ lỗi ngầm nào về toán học, tensor shape, gradient leakage hay numerical overflow khiến việc train 60 epochs trên Kaggle bị thất bại hoặc sinh ra kết quả rác không?**
3. **Các con số đo lường hiệu năng (Relative Gap, Latency, Tour Cost) có hoàn toàn liêm chính khoa học và có thể bảo vệ vững chắc trước Hội đồng không?**

---

## I. HỒ SƠ TỆP TIN VÀ THỰC THỂ CẦN KIỂM TOÁN (AUDIT MANIFEST)

Hãy đối chiếu logic giữa các tệp sau trong hệ thống HotWAY v7.3.1:
- **Notebooks Kaggle Trọng Tâm:**
  1. `notebooks/kaggle_train_attention_tsp.ipynb`: Notebook tự trị huấn luyện Attention Model (128-d, 8 heads, 3 layers Graph Transformer) bằng REINFORCE Rollout Baseline (60 Epochs $\times$ 500 Steps $\times$ Batch 512 = 15.36M hành trình).
  2. `notebooks/kaggle_train_pointer_net.ipynb`: Notebook tự trị huấn luyện Pointer Network (Bi-LSTM + Bahdanau Pointer + A2C Critic) trong 30 Epochs.
- **Mã nguồn thực thi nòng cốt (Core Modules):**
  3. `src/agents/attention_model/model.py` & `models/attention_model.py`: Lớp `MultiHeadAttention`, `EncoderLayer`, `Encoder`, `Decoder`, `AttentionModelWrapper`.
  4. `models/pointer_net.py`: Lớp `PointerNetwork`, `AttentionPointer`, `PointerNetWrapper`.
  5. `models/dqn_agent.py`: `DuelingDQNNetwork`, `DQNAgentWrapper` (Ablation model với cơ chế Action Masking).
  6. `models/ortools_solver.py`: Bộ giải heuristic chuẩn đối sánh Google OR-Tools Routing.
  7. `scripts/build_nationwide_benchmark.py`: Bộ sinh 100 POI Toàn Quốc (Hà Nội 40, Đà Nẵng 20, TP.HCM 40).
  8. `evaluate_benchmark.py`: Harness đánh giá đối đầu 4 mô hình, kiểm tra `validate_closed_tour()`, tính `mean_relative_gap_vs_ortools_pct`.
  9. `scripts/ingest_kaggle_weights.py`: Script 1-click tự động kiểm tra `state_dict`, nạp weights và đồng bộ kết quả sang WebGIS Next.js 14.

---

## II. 7 CHIỀU KIỂM CHỨNG KHẮT KHE BẰNG DEEP REASONING

Hãy sử dụng năng lực suy luận sâu từng bước (Chain-of-Thought) để phân tích chi tiết 7 chiều sau:

### Chiều 1: Thẩm Định Hàm Mục Tiêu & Sự Khép Kín Của Chu Trình (Closed Hamiltonian Tour)
* **Toán học chu trình:** Một tour TSP/VRP hợp lệ bắt buộc xuất phát từ kho (Depot = 0), ghé thăm $N$ điểm dừng đúng 1 lần, và quay về kho (Depot = 0).
* **Phân tích Code:**
  - Trong `kaggle_train_attention_tsp.ipynb` (hàm `compute_tour_cost`):
    ```python
    seg_dists = torch.norm(ordered_coords[:, :-1, :] - ordered_coords[:, 1:, :], dim=-1)
    seg_traffic = 0.5 * (ordered_traffic[:, :-1, 0] + ordered_traffic[:, 1:, 0])
    tour_cost = (seg_dists * seg_traffic).sum(dim=-1)
    depot_dist = torch.norm(ordered_coords[:, -1, :] - ordered_coords[:, 0, :], dim=-1)
    depot_traffic = 0.5 * (ordered_traffic[:, -1, 0] + ordered_traffic[:, 0, 0])
    total_cost = tour_cost + (depot_dist * depot_traffic)
    ```
  - **Câu hỏi cho DeepSeek:**
    1. Cung từ `ordered_coords[:, -1]` về `ordered_coords[:, 0]` có đảm bảo điểm đầu tiên luôn là Depot không? 
    2. Trong `AttentionModel.forward()`, `visited[:, 0] = 1` và `tours.append(curr_node)` với `curr_node = 0` có bảo đảm chắc chắn node 0 là vị trí xuất phát không?
    3. Hãy kiểm tra xem `train.py` với phép tính `torch.roll(..., -1)` và notebook Kaggle có cho ra giá trị Tour Cost hoàn toàn tương đương toán học hay không?

### Chiều 2: Tính Đúng Đắn Của Cơ Chế REINFORCE Rollout Baseline & Gradient Flow
* **Toán học tối ưu hóa chính sách:**
  $$\nabla_\theta J(\theta) = \mathbb{E}_{p_\theta(\pi)} \left[ (L(\pi) - L(\pi^{\text{BL}})) \nabla_\theta \log p_\theta(\pi) \right]$$
* **Phân tích Code:**
  - Trong vòng lặp huấn luyện Cell 5 (`kaggle_train_attention_tsp.ipynb`):
    ```python
    tours, log_probs = model(features, decode_type='sampling')
    with torch.no_grad():
        baseline_tours, _ = baseline_model(features, decode_type='greedy')
    cost = compute_tour_cost(tours, coords, traffic)
    baseline_cost = compute_tour_cost(baseline_tours, coords, traffic)
    advantage = cost - baseline_cost
    loss = (advantage * log_probs).mean()
    ```
  - **Câu hỏi cho DeepSeek:**
    1. `baseline_model` nằm trong `torch.no_grad()`, vậy gradient có bị rò rỉ (leak) sang baseline không?
    2. `cost` được tính từ `tours` (chuỗi chỉ số rời rạc sinh ra từ `torch.multinomial`). Việc `advantage` mang giá trị float có làm đứt gãy đồ thị tính toán (computational graph) của PyTorch không? Gradient chảy về model thông qua `log_probs` có hoàn toàn đúng chuẩn REINFORCE (Williams, 1992) không?
    3. Biểu thức `loss = (advantage * log_probs).mean()`: Vì mục tiêu của TSP là **cực tiểu hóa chi phí** (Cost $\downarrow$), khi $L(\pi) > L(\pi^{\text{BL}})$ thì `advantage > 0`, hàm loss dương làm giảm xác suất của chuỗi tồi; khi $L(\pi) < L(\pi^{\text{BL}})$ thì `advantage < 0`, hàm loss âm làm tăng xác suất của chuỗi tốt. Dấu của loss ở đây đã hoàn toàn chuẩn xác chưa?

### Chiều 3: Động Lực Học Tensor Multi-Head Attention & Logit Clipping
* **Toán học Decoder Pointer:**
  $$u_{(c), j} = C \cdot \tanh \left( \frac{(W_Q d_{(c)})^T (W_K h_j)}{\sqrt{d_k}} \right)$$
* **Phân tích Code:**
  ```python
  scores = torch.matmul(q_ptr, k_ptr.transpose(-2, -1)).squeeze(1) / math.sqrt(self.embed_dim)
  scores = 10.0 * torch.tanh(scores)  # Logit clipping [-10, 10]
  logits = scores.masked_fill(mask == 1, -1e9)
  ```
  - **Câu hỏi cho DeepSeek:**
    1. Tại sao lại dùng hằng số $C = 10.0$ và hàm $\tanh$? Việc này ngăn chặn hiện tượng Softmax Saturation (bão hòa gradient khi điểm số quá lớn) như thế nào?
    2. Giá trị mask `-1e9` có an toàn với kiểu dữ liệu `torch.float32` không? Khi qua `F.softmax`, giá trị này có bị tràn số (NaN / Inf) hoặc sinh ra xác suất khác 0 không?
    3. Phép chiếu $Q, K, V$ trong `MultiHeadAttention`: `self.head_dim = embed_dim // n_heads` ($128 // 8 = 16$). Tích vô hướng chia cho $\sqrt{16} = 4.0$. Điều này có khớp hoàn toàn với kiến trúc Vaswani et al. và Kool et al. không?

### Chiều 4: Thẩm Định Kỷ Luật Triệt Tiêu Hardcode (Dynamic Min-Max Scaling)
* **Toán học chuẩn hóa không gian đơn vị:**
  $$x'_i = \frac{x_i - \min(X)}{\max(X) - \min(X) + \epsilon}, \quad y'_i = \frac{y_i - \min(Y)}{\max(Y) - \min(Y) + \epsilon}$$
* **Phân tích Code:**
  ```python
  def dynamic_min_max_scale_coords(coords: np.ndarray) -> np.ndarray:
      min_xy = coords.min(axis=0)
      max_xy = coords.max(axis=0)
      range_xy = np.maximum(max_xy - min_xy, 1e-6)
      return (coords - min_xy) / range_xy
  ```
  - **Câu hỏi cho DeepSeek:**
    1. Khi huấn luyện, các tọa độ được sinh từ `torch.rand(batch_size, n_nodes, 2)` (ngẫu nhiên trong $[0, 1]^2$). Khi đánh giá trên bản đồ thực tế Việt Nam (Hà Nội lat ~21.0, lon ~105.8; TP.HCM lat ~10.8, lon ~106.7), hàm này đưa mọi cụm điểm về $[0, 1]^2$. Liệu mô hình có bị ảnh hưởng bởi tỷ lệ khung hình (Aspect Ratio $\Delta \text{lat} / \Delta \text{lon}$) giữa các thành phố khác nhau không?
    2. Việc chuẩn hóa độc lập từng instance có triệt tiêu 100% hiện tượng Distribution Shift không? Có trường hợp ngoại lệ nào (edge-case) khiến $\text{range\_xy} < 10^{-6}$ gây lỗi chia cho 0 không?

### Chiều 5: Động Lực Học Giao Thông $C(t)$ & Triệt Tiêu Lỗi Nhân Đôi (No Double-Counting)
* **Bối cảnh sau đợt kiểm toán Codex:**
  - Trước đây: `build_nationwide_benchmark.py` nhân `traffic_factor` vào ma trận thời gian cơ sở, sau đó solver lại nhân $C(t)$ tiếp $\implies$ Sai lệch nghiêm trọng.
  - Sau bản vá (Remediation): Ma trận cơ sở chỉ lưu thời gian chạy thuần túy theo vận tốc không tải; $C(t)$ chỉ nhân duy nhất 1 lần khi mô phỏng hành trình tích lũy:
    $$\text{hour}_k = \left( \text{departure\_hour} + \frac{\text{elapsed\_min}}{60.0} \right) \bmod 24.0$$
    $$\Delta t_k = \text{base\_dur}_{u, v} \times C(\text{hour}_k), \quad \text{elapsed\_min} \leftarrow \text{elapsed\_min} + \Delta t_k$$
  - **Câu hỏi cho DeepSeek:**
    1. Hãy rà soát đoạn code Cell 8 trong `kaggle_train_attention_tsp.ipynb` và `evaluate_benchmark.py`. Phép tính thời lượng tích lũy có khớp nhau 100% không?
    2. Việc tích lũy thời gian có phản ánh đúng thực tế: xe đi càng lâu thì càng có nguy cơ rơi vào khung giờ cao điểm (sáng $7:00-8:30 \to 2.10$, chiều $17:00-18:30 \to 2.25$) không?

### Chiều 6: Thẩm Định Siêu Tham Số (Hyperparameters) & Khả Năng Hội Tụ Trên 2x T4 GPU
* **Bảng cấu hình huấn luyện (Gold Config):**
  - `EMBEDDING_DIM`: 128
  - `N_ENCODE_LAYERS`: 3
  - `N_HEADS`: 8
  - `BATCH_SIZE`: 512
  - `EPOCHS`: 60
  - `STEPS_PER_EPOCH`: 500 (Tổng cộng: $60 \times 500 \times 512 = 15,360,000$ đồ thị)
  - `LR`: $10^{-4}$, giảm theo hàm số mũ $\gamma = 0.985$ sau mỗi epoch (Epoch 60: $\text{LR} \approx 10^{-4} \times 0.985^{59} \approx 4.09 \times 10^{-5}$)
  - `MAX_NORM`: 1.0 (Gradient clipping)
  - Multi-Scale Curriculum: $60\%$ batch $N \in [10, 25]$, $40\%$ batch $N \in [26, 50]$
  - Cost Perturbation: $C(t) \sim \text{Uniform}(1.0, 2.25)$
* **Câu hỏi cho DeepSeek:**
  1. Với 741,504 tham số và Batch Size 512 trên GPU NVIDIA T4 (16GB VRAM), dung lượng VRAM ước tính chiếm bao nhiêu GB? Có nguy cơ bị Out-Of-Memory (OOM) khi $N=50$ không?
  2. Tốc độ suy giảm Learning Rate ($\gamma = 0.985$) có quá nhanh hoặc quá chậm không? Có bảo đảm mô hình hội tụ sâu ở 20 epoch cuối mà không bị kẹt ở cực tiểu cục bộ (local minima)?
  3. Cơ chế Multi-Scale Curriculum: Vì Attention Model dùng Graph Self-Attention không bị cố định kích thước tensor đầu vào, việc trộn lẫn các đồ thị kích thước ngẫu nhiên $N \in [10, 50]$ có giúp mạng đạt tính tổng quát hóa Zero-Shot tuyệt đối không?

### Chiều 7: Độ Tin Cậy Của Phương Pháp Đo Độ Trễ & Công Thức Relative Gap
* **Đo độ trễ nơ-ron trên GPU:**
  ```python
  if device.type == 'cuda':
      torch.cuda.synchronize(device)
  t0 = time.perf_counter()
  with torch.no_grad():
      tour, _ = model(t_feat, decode_type='greedy')
  if device.type == 'cuda':
      torch.cuda.synchronize(device)
  lat_ms = (time.perf_counter() - t0) * 1000.0
  ```
  - **Câu hỏi cho DeepSeek:**
    1. Tại sao bắt buộc phải có `torch.cuda.synchronize()` ở cả trước và sau `model(t_feat)`? Nếu không có lệnh này, thời gian đo được sẽ bị sai lệch như thế nào do tính chất bất đồng bộ (non-blocking) của CUDA Kernel?
    2. Độ trễ này là độ trễ suy luận thuần túy (Inference Latency) hay đã bị lẫn thời gian xử lý dữ liệu CPU/RAM?
* **Công thức Relative Gap:**
  $$\text{Gap} = \frac{\text{Duration}_{\text{model}} - \text{Duration}_{\text{OR-Tools}}}{\text{Duration}_{\text{OR-Tools}}} \times 100\%$$
  - Việc bỏ hoàn toàn kẹp `max(0.0, ...)` có bảo đảm tính trung thực khoa học, cho phép ghi nhận trường hợp Neural Model tìm ra tour tốt hơn heuristic của OR-Tools (gap âm) không?

---

## III. BẢNG TIÊU CHÍ ĐÁNH GIÁ VÀ ĐIỂM SỐ TIN CẬY (OUTPUT SCORECARD)

Hãy tổng hợp kết luận của bạn thành một **Bản Giám Định Kỹ Thuật Chi Tiết** gồm:

### 1. BẢNG PHÂN TÍCH ƯU - NHƯỢC ĐIỂM TOÁN HỌC (MATHEMATICAL VERIFICATION TABLE)
| Thành phần | Công thức triển khai | Đánh giá tính đúng đắn | Khuyến nghị tối ưu (nếu có) |
|---|---|:---:|---|
| Tour Cost Closure | Khép kín quay về Depot 0 | [ĐẠT / CHƯA ĐẠT] | ... |
| REINFORCE Advantage | $A = \text{Cost} - \text{Cost}^{\text{BL}}$ | [ĐẠT / CHƯA ĐẠT] | ... |
| Logit Clipping | $10 \cdot \tanh(\text{scores})$ | [ĐẠT / CHƯA ĐẠT] | ... |
| Dynamic Min-Max | $(x - \min) / (\max - \min + \epsilon)$ | [ĐẠT / CHƯA ĐẠT] | ... |
| Single-Pass Traffic $C(t)$ | Tích lũy theo $\Delta t$ từng chặng | [ĐẠT / CHƯA ĐẠT] | ... |
| GPU Latency Profiling | `torch.cuda.synchronize()` | [ĐẠT / CHƯA ĐẠT] | ... |

### 2. PHÂN TÍCH RỦI RO KHI CHẠY TRÊN KAGGLE (KAGGLE RUNTIME RISK ANALYSIS)
- Nguy cơ OOM (Out Of Memory): ...
- Nguy cơ NaN Gradient hoặc Exploding Gradient: ...
- Khả năng hội tụ sau 60 Epochs (đánh giá dựa trên lý thuyết và thực nghiệm Kool et al.): ...
- Ước tính Optimality Gap thực tế sau khi hội tụ: Liệu mô hình có đạt được vùng mục tiêu $4.5\% - 8.0\%$ không?

### 3. CHẤM ĐIỂM TIN CẬY CUỐI CÙNG (FINAL RELIABILITY SCORE)
Chấm điểm hệ thống trên thang **100 điểm** dựa trên:
- Tính chuẩn xác toán học (30 điểm)
- Tính toàn vẹn của Gradient & Thuật toán RL (30 điểm)
- Tính tổng quát hóa và khử bias địa phương (20 điểm)
- Độ tin cậy và khả năng thực thi trên Kaggle Notebook (20 điểm)

**Lời tuyên bố dứt khoát:** *Bộ Notebook này đã đủ độ tin cậy để chủ nhiệm đề án tự tin khởi chạy trên Kaggle GPU và sử dụng làm cơ sở khoa học để bảo vệ trước Hội đồng tốt nghiệp hay chưa?*
```

