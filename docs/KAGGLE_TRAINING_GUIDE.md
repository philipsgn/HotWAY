# HƯỚNG DẪN THỰC THI HUẤN LUYỆN TRÊN KAGGLE GPU (2x NVIDIA T4)
## QUY TRÌNH TẠO KẾT QUẢ ĐẦU RA CUỐI CÙNG (FINAL OUTPUT) CHO HOTWAY v7.3.1

> **Tài liệu:** Sổ tay hướng dẫn huấn luyện mô hình Attention Model & Pointer Network trên đám mây Kaggle  
> **Phiên bản:** v7.3.1 (Eliminate Regional Bias & Dynamic Min-Max Scaling)  
> **Tài nguyên yêu cầu:** Tài khoản Kaggle miễn phí (Kaggle cấp 30 giờ GPU/tuần, hỗ trợ chạy đồng thời 2 session GPU)  
> **Mục tiêu:** Thu hẹp chênh lệch tương đối từ ~81.62% xuống vùng tiệm cận **4.5% – 8.0%** so với Google OR-Tools.

---

## 1. Danh Mục Các Notebook Sẵn Sàng Trong Dự Án

| Tệp Notebook | Mô Hình | Mục Tiêu | Thời Gian Chạy Dự Kiến (2x T4 GPU) | Đầu Ra Chính |
|---|---|---|---|---|
| [`notebooks/kaggle_train_attention_tsp.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_attention_tsp.ipynb) | **Attention Model** (Kool et al., SOTA NCO) | Huấn luyện mạng Transformer 3 lớp, 8 heads (741,504 params) bằng REINFORCE Rollout Baseline | 3.5 – 4.5 giờ (60 Epochs) | `hotway_kaggle_final_artifacts.zip` chứa trọng số `.pt`, biểu đồ hội tụ, và kết quả 100 POI |
| [`notebooks/kaggle_train_pointer_net.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_pointer_net.ipynb) | **Pointer Network** (Vinyals et al., A2C) | Huấn luyện mô hình tuần tự Bi-LSTM để đối soát hiện tượng nghẽn độ trễ (Recurrent Latency Bottleneck) | 1.5 – 2.0 giờ (30 Epochs) | `pointer_net_kaggle_artifacts.zip` chứa trọng số `.pt` và biểu đồ hội tụ |

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
   *(Kaggle sẽ tự động chạy ngầm phiên này trên cloud trong ~3.5 giờ. Bạn có thể tắt tab hoặc tắt máy tính).*

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

## 5. Bảng So Sánh Kỳ Vọng: Trước vs Sau Huấn Luyện

| Chỉ số đo lường | Checkpoint Sơ Khởi Hiện Tại (Chưa Train) | Kỳ Vọng Sau Khi Chạy Kaggle (Final Output) |
|---|:---:|:---:|
| **Thời lượng TB (Attention Model)** | **409.29 phút** (Cự ly 142.17 km) | **~225.0 – 235.0 phút** (Cự ly ~75.0 – 78.0 km) |
| **Relative Gap vs Google OR-Tools** | **81.62%** (OR-Tools: 217.72 phút) | **4.5% – 8.0%** (Tiêu chuẩn quốc tế NCO) |
| **Độ trễ suy luận trên CPU** | **14.3 ms** (Nhanh gấp ~70 lần OR-Tools) | **14.3 ms** (Không đổi, giữ nguyên tốc độ siêu nhanh) |
| **Zero-Shot Failure Rate** | **0.0%** trên cả 100 ca | **0.0%** trên cả 100 ca |
| **Độ công bằng giữa 3 miền** | Chênh lệch $\pm 3.5\%$ (HN 84.0%, ĐN 84.8%, HCM 77.6%) | Duy trì tính bất biến không gian ($\pm 1.5\%$) |
