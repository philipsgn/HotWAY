# HƯỚNG DẪN THỰC THI HUẤN LUYỆN TRÊN KAGGLE GPU (2x NVIDIA T4)
## QUY TRÌNH TẠO KẾT QUẢ ĐẦU RA CUỐI CÙNG (FINAL OUTPUT) CHO HOTWAY v7.3.1

> **Tài liệu:** Sổ tay hướng dẫn huấn luyện mô hình Attention Model & Pointer Network trên đám mây Kaggle  
> **Phiên bản:** v7.3.1 (Eliminate Regional Bias & Dynamic Min-Max Scaling)  
> **Tài nguyên yêu cầu:** Tài khoản Kaggle miễn phí (Kaggle cấp 30 giờ GPU/tuần, hỗ trợ chạy đồng thời 2 session GPU)  
> **Evidence rule:** The 4.5-8.0% value is not a supported target and must not be presented as an expected result. Runtime is also unmeasured.

---

## 1. Kaggle notebooks and execution expectations

| Notebook | Model/configuration | Runtime | Artifact |
|---|---|---|---|
| `notebooks/kaggle_train_attention_tsp.ipynb` | Attention target 128-d/3L/8-head; REINFORCE rollout baseline | Not measured; smoke test first | `.pt` checkpoint and training curves |
| `notebooks/kaggle_train_pointer_net.ipynb` | PointerNet with dynamic-time decoder and A2C critic | Not measured; smoke test first | `.pt` checkpoint and training curves |

The notebook code currently selects one CUDA device. Selecting a Kaggle T4 x2 accelerator does not make this code use both GPUs. Record peak VRAM and seconds/step at N=50 before a full run. No target gap or runtime is promised.

---

## 2. Hướng Dẫn Khởi Chạy Song Song 2 Phiên Trên Kaggle (Concurrent Sessions)

Kaggle cho phép bạn mở 2 tab trình duyệt và chạy cùng lúc 2 phiên GPU.

### Phiên 1: Attention Model (Mô hình trọng tâm SOTA)
1. Truy cập [https://www.kaggle.com](https://www.kaggle.com) $\to$ Đăng nhập $\to$ Bấm **`+ Create`** $\to$ Chọn **`New Notebook`**.
2. Chọn **`File`** $\to$ **`Import Notebook`** $\to$ Chọn tab **`Upload`** $\to$ Tải lên tệp:  
   [`notebooks/kaggle_train_attention_tsp.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_attention_tsp.ipynb).
3. Tại bảng điều khiển bên phải (**Notebook options**):
   * **Accelerator:** Chọn **`GPU T4 x2`** *(hoặc `GPU P100`)*.
   * **Language:** `Python`.
   * **Environment:** `Always use latest environment`.
   * **Internet:** **`Internet on`** *(bắt buộc bật ON để notebook tự động tải bộ dữ liệu kiểm chuẩn 100 POI từ GitHub)*.
4. Bấm **`Save Version`** (ở góc trên cùng bên phải) $\to$ Chọn **`Save & Run All (Commit)`** $\to$ Bấm **`Save`**.  
   *(The notebook currently uses one CUDA device. Run a short profile at N=50 and record peak VRAM and seconds/step before committing the full job.)*

---

### Phiên 2: Pointer Network (Mô hình đối đầu Recurrent A2C)
1. Mở một tab trình duyệt mới trên Kaggle $\to$ Bấm **`+ Create`** $\to$ Chọn **`New Notebook`**.
2. Chọn **`File`** $\to$ **`Import Notebook`** $\to$ Chọn tab **`Upload`** $\to$ Tải lên tệp:  
   [`notebooks/kaggle_train_pointer_net.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_pointer_net.ipynb).
3. Tại bảng điều khiển bên phải (**Notebook options**):
   * **Accelerator:** Chọn **`GPU T4 x2`**.
   * **Language:** `Python`.
   * **Internet:** **`Internet on`**.
4. Bấm **`Save Version`** $\to$ Chọn **`Save & Run All (Commit)`** $\to$ Bấm **`Save`**.  
   *(Kaggle sẽ tự động chạy song song phiên thứ 2 này trong ~1.5 giờ).*

---

## 3. Tải Về Gói Kết Quả Đầu Ra (Artifacts)

Khi máy chủ Kaggle hoàn tất quá trình huấn luyện:
1. Mở lại notebook trên Kaggle $\to$ Vào tab **`Output`** ở thanh điều khiển bên phải (thư mục `/kaggle/working/`).
2. Tải về 2 tệp:
   * **`hotway_kaggle_final_artifacts.zip`** (từ Notebook Attention Model)
   * **`pointer_net_kaggle_artifacts.zip`** (từ Notebook Pointer Network)
3. Đặt các tệp zip này vào thư mục gốc của dự án `HotWAY/`.

> [!NOTE]
> Gói `hotway_kaggle_final_artifacts.zip` bao gồm:
> - `hotway_attention_model_nationwide.pt`: Trọng số mô hình Attention Model đã hội tụ.
> - `training_convergence_curves.png`: Đồ thị sắc nét Loss, Tour Cost và Validation Advantage.
> - `training_history.csv`: Lịch sử thông số chi tiết qua 60 Epochs.
> - `benchmark_evaluation_summary.json`: Bảng đo lường thực tế trên 100 POI Toàn Quốc.

---

## 4. Tự Động Nạp Dữ Liệu Thực Tế Vào HotWAY (1-Click Ingestion)

Sau khi tải tệp về thư mục dự án, chạy lệnh:

```bash
python scripts/ingest_kaggle_weights.py --zip hotway_kaggle_final_artifacts.zip
```

Script này sẽ tự động:
1. Kiểm tra cấu trúc tham số và nạp trọng số mới vào `models/attention_model_weights.pt` (hoặc `results/attention_tsp50_hcmc.pt`).
2. Sao chép đồ thị hội tụ vào `results/` và `frontend/public/images/`.
3. Tự động kích hoạt `evaluate_benchmark.py` trên 100 POI toàn quốc để đo lường Relative Gap mới.
4. Tự động đồng bộ số liệu Final Output sang Frontend Next.js 14 (`frontend/public/data/`).
5. Cập nhật Bảng 4 trên Landing Page và Màn hình T2 WebGIS với số liệu thật 100%.

---

## 5. Reporting status

| Metric | Historical pre-v2 artifact | Post-remediation |
|---|---|---|
| Attention architecture | 64-d/2-layer, 202,752 params | Kaggle target 128-d/3-layer/8-head; pending training |
| Relative gap vs OR-Tools heuristic | 81.62% on synthetic data | Re-measure after training; no target is promised |
| Inference latency | Historical CPU measurement only | Re-measure with device and timing scope documented |
| Failure rate / regional breakdown | Historical synthetic benchmark | Re-measure after training; no invariance claim |

Do not interpret relative gap against Guided Local Search as an optimality certificate. The current OR-Tools solver optimizes a static surrogate and scores the resulting route under the dynamic simulator.
