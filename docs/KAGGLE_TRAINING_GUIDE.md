# HƯỚNG DẪN THỰC THI HUẤN LUYỆN TRÊN KAGGLE GPU (2x NVIDIA T4)
## QUY TRÌNH TẠO KẾT QUẢ ĐẦU RA CUỐI CÙNG (FINAL OUTPUT) CHO HOTWAY v7.3.1

> **Tài liệu:** Sổ tay hướng dẫn huấn luyện mô hình Attention Model & Pointer Network trên đám mây Kaggle  
> **Phiên bản:** v7.3.1 (Eliminate Regional Bias & Dynamic Min-Max Scaling)  
> **Tài nguyên yêu cầu:** Tài khoản Kaggle miễn phí (Kaggle cấp 30 giờ GPU/tuần)  
> **Mục tiêu:** Thu hẹp Optimality Gap từ ~97.90% xuống vùng tiệm cận **4.5% – 8.0%** so với Google OR-Tools.

---

## 1. Danh Mục Các Notebook Sẵn Sàng Trong Dự Án

| Tệp Notebook | Mô Hình | Mục Tiêu | Thời Gian Chạy Dự Kiến (2x T4 GPU) | Đầu Ra Chính |
|---|---|---|---|---|
| [`notebooks/kaggle_train_attention_tsp.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_attention_tsp.ipynb) | **Attention Model** (Kool et al., SOTA NCO) | Huấn luyện mạng Transformer 3 lớp, 8 heads (741,504 params) bằng REINFORCE Rollout Baseline | 3.5 – 4.5 giờ (60 Epochs) | `hotway_kaggle_final_artifacts.zip` chứa trọng số `.pt`, biểu đồ hội tụ, và kết quả 100 POI |
| [`notebooks/kaggle_train_pointer_net.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_pointer_net.ipynb) | **Pointer Network** (Vinyals et al., A2C) | Huấn luyện mô hình tuần tự Bi-LSTM để đối soát hiện tượng nghẽn độ trễ (Recurrent Latency Bottleneck) | 1.5 – 2.0 giờ (30 Epochs) | `pointer_net_kaggle_artifacts.zip` chứa trọng số `.pt` và biểu đồ hội tụ |

---

## 2. Các Bước Thao Tác Chi Tiết Trên Kaggle

### Bước 1: Tạo Notebook Mới Trên Kaggle
1. Truy cập [https://www.kaggle.com](https://www.kaggle.com) và đăng nhập tài khoản.
2. Nhấn vào nút **`+ Create`** ở thanh menu bên trái $\to$ Chọn **`New Notebook`**.

### Bước 2: Tải File Notebook Từ Máy Tính Lên
1. Trên giao diện thanh công cụ của Notebook Kaggle, chọn **`File`** $\to$ **`Import Notebook`**.
2. Chọn tab **`Upload`** $\to$ Kéo thả tệp [`notebooks/kaggle_train_attention_tsp.ipynb`](file:///c:/Users/Asus/Documents/AI/HotWAY/notebooks/kaggle_train_attention_tsp.ipynb) từ máy tính của bạn lên.

### Bước 3: Cấu Hình Phần Cứng GPU (Cực Kỳ Quan Trọng)
Tại bảng điều khiển **Notebook options** ở góc phải màn hình:
* **Accelerator:** Chọn **`GPU T4 x2`** *(hoặc `GPU P100` nếu khả dụng)*.
* **Language:** `Python`.
* **Environment:** `Always use latest environment`.
* **Internet:** **`Internet on`** *(bắt buộc bật ON để notebook tự động tải bộ dữ liệu kiểm chuẩn 100 POI từ GitHub)*.

### Bước 4: Khởi Chạy Huấn Luyện

Bạn có thể chọn 1 trong 2 cách sau:

* **Cách 1 (Chạy trực tiếp trên trình duyệt):**
  * Nhấn nút **`Run All`** (biểu tượng hai hình tam giác `>>`).
  * Màn hình sẽ hiển thị tiến độ huấn luyện từng Epoch:
    ```text
    Epoch 01/60 (215.4s) | Loss: -0.0412 | Tour Cost: 18.4210 | Val Diff: +0.0120
    ...
    Epoch 45/60 (210.1s) | Loss: -0.0018 | Tour Cost: 12.1054 | Val Diff: -0.0450 [BASELINE UPDATED]
    ```
* **Cách 2 (Chạy ngầm trên Cloud — Khuyên dùng):**
  * Nhấn vào nút **`Save Version`** ở góc trên cùng bên phải.
  * Chọn **`Save & Run All (Commit)`** $\to$ Nhấn **`Save`**.
  * **Ưu điểm:** Bạn có thể tắt trình duyệt hoặc tắt máy tính, máy chủ Kaggle vẫn sẽ tự động chạy liên tục trong 4 tiếng cho đến khi hoàn thành.

---

## 3. Tải Về Gói Kết Quả Đầu Ra (Artifacts)

Khi quá trình chạy hoàn tất:
1. Vào tab **`Output`** ở thanh điều khiển bên phải (thư mục `/kaggle/working/`).
2. Bạn sẽ thấy tệp:
   * **`hotway_kaggle_final_artifacts.zip`**
3. Nhấn vào dấu 3 chấm `...` bên cạnh tệp $\to$ Chọn **`Download`** về máy tính của bạn.

> [!NOTE]
> Gói `hotway_kaggle_final_artifacts.zip` bao gồm:
> - `hotway_attention_model_nationwide.pt`: Trọng số mô hình Attention Model đã hội tụ.
> - `training_convergence_curves.png`: Đồ thị sắc nét Loss, Tour Cost và Validation Advantage.
> - `training_history.csv`: Lịch sử thông số chi tiết qua 60 Epochs.
> - `benchmark_evaluation_summary.json`: Bảng đo lường thực tế trên 100 POI Toàn Quốc.

---

## 4. Tự Động Nạp Dữ Liệu Thực Tế Vào HotWAY (1-Click Ingestion)

Sau khi tải tệp `hotway_kaggle_final_artifacts.zip` về máy, bạn chỉ cần đặt tệp zip này vào thư mục gốc của dự án `HotWAY/` và chạy lệnh:

```bash
python scripts/ingest_kaggle_weights.py --zip hotway_kaggle_final_artifacts.zip
```

Script này sẽ tự động:
1. Giải nén trọng số mới vào `models/attention_model_weights.pt`.
2. Sao chép đồ thị hội tụ vào `results/` và `frontend/public/images/`.
3. Chạy lại bộ đánh giá `evaluate_benchmark.py` trên 100 POI toàn quốc để xác nhận Optimality Gap mới.
4. Tự động đồng bộ số liệu Final Output sang Frontend Next.js 14 (`frontend/public/data/`).
5. Cập nhật Bảng 4 trên Landing Page và Màn hình T2 WebGIS với số liệu thật 100%.

---

## 5. Bảng So Sánh Kỳ Vọng: Trước vs Sau Huấn Luyện

| Chỉ số đo lường | Checkpoint Sơ Khởi Hiện Tại (Chưa Train) | Kỳ Vọng Sau Khi Chạy Kaggle (Final Output) |
|---|:---:|:---:|
| **Optimality Gap so với OR-Tools** | **97.90%** (142.2 km) | **4.5% – 8.0%** (~75.0 – 77.5 km) |
| **Độ trễ suy luận trên CPU** | **14.1 ms** (Nhanh gấp 72x OR-Tools) | **14.1 ms** (Không đổi, giữ nguyên tốc độ siêu nhanh) |
| **Zero-Shot Failure Rate** | **0.0%** trên cả 100 ca | **0.0%** trên cả 100 ca |
| **Độ công bằng giữa 3 miền** | Chênh lệch $\pm 3.0\%$ (HN 99.3%, ĐN 101.3%, HCM 95.2%) | Duy trì tính bất biến không gian ($\pm 1.5\%$) |

