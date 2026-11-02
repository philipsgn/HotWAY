# HƯỚNG DẪN THỰC THI HUẤN LUYỆN TRÊN KAGGLE GPU (2x NVIDIA T4)
## QUY TRÌNH QUẢN LÝ KẾT QUẢ ĐẦU RA (FINAL OUTPUT) & ĐÁNH GIÁ MÔ HÌNH NCO HOTWAY v7.3.2

> **Tài liệu:** Sổ tay hướng dẫn huấn luyện & nạp trọng số thực nghiệm Attention Model & Pointer Network từ Kaggle GPU  
> **Phiên bản:** v7.3.2 (Eliminate Regional Bias & Dynamic Isotropic Scaling Edition)  
> **Trạng thái thực nghiệm:** Cả 2 mô hình đã hoàn tất huấn luyện 60 epochs trên Kaggle GPU T4 và nạp thành công vào hệ thống.  
> **Thư mục lưu trữ chuẩn tắc:** `notebooks/model_results/`

---

## 1. Thông Số Huấn Luyện & Thời Gian Thực Tế Đo Đạc Tại Kaggle GPU T4

| Mô hình | Cấu trúc mạng | Thời gian train trên GPU T4 | Bộ trọng số đầu ra | Biểu đồ hội tụ |
|---|---|---|---|---|
| **Attention Model (AM)** | 128-d, 3 layers, 8 heads, 741,760 params; REINFORCE Rollout Baseline | **~3.5 giờ (~12,600s)** | `notebooks/model_results/attention_tsp/hotway_attention_model_nationwide.pt` | `training_convergence_curves.png` |
| **Pointer Network (A2C)** | Bi-LSTM hidden=128, 283,137 params; Advantage Actor-Critic (MLP Critic) | **~14.8 phút (891s)** | `notebooks/model_results/pointer_net/pointer_net_nationwide.pt` | `pointer_net_convergence_curves.png` |

---

## 2. Vì Sao Attention Model Huấn Luyện Lâu Hơn Pointer Network ~14 Lần?

1. **Greedy Rollout Baseline (Kool et al. 2019):**  
   Mỗi epoch, Attention Model phải chạy suy luận trên $10,000$ đồ thị kiểm định độc lập cho cả mạng hiện tại và mạng baseline để kiểm định $t$-test. PointerNet sử dụng mạng Critic MLP $V(s)$ tính toán tức thì trong cùng một lượt forward của batch, không cần rollout.
2. **24 Attention Heads ($3 \text{ layers} \times 8 \text{ heads}$):**  
   Attention Model tính ma trận vuông tương quan không gian $N \times N$ giữa tất cả các cặp điểm giao. Bi-LSTM của PointerNet chỉ duyệt tuần tự chuỗi điểm với độ phức tạp tuyến tính $O(N)$.
3. **Số lượng tham số gấp 2.6 lần:**  
   741,760 tham số so với 283,137 tham số.

---

## 3. Cấu Trúc Thư Mục Kết Quả Chuẩn Tắc (`notebooks/model_results/`)

Khi tải kết quả từ Kaggle về, lưu trữ theo đúng cấu trúc chuẩn:
```text
notebooks/model_results/
├── attention_tsp/
│   ├── hotway_attention_model_nationwide.pt  (Trọng số mô hình 741,760 tham số)
│   ├── training_convergence_curves.png       (Biểu đồ Loss & Tour Cost hội tụ)
│   ├── training_history.csv                  (Dữ liệu 60 epoch)
│   └── benchmark_evaluation_summary.json     (Tóm tắt đánh giá sau train)
├── pointer_net/
│   ├── pointer_net_nationwide.pt             (Trọng số mô hình 283,137 tham số)
│   └── pointer_net_convergence_curves.png    (Biểu đồ hội tụ Actor-Critic)
```

---

## 4. Tự Động Nạp Dữ Liệu Thực Tế Vào HotWAY (1-Click Ingestion)

Chạy lệnh nạp tự động (tự nhận diện thư mục `notebooks/model_results/`):

```bash
# Nạp Attention Model
python scripts/ingest_kaggle_weights.py --weights-path notebooks/model_results/attention_tsp/hotway_attention_model_nationwide.pt

# Nạp Pointer Network
python scripts/ingest_kaggle_weights.py --weights-path notebooks/model_results/pointer_net/pointer_net_nationwide.pt
```

Script này tự động:
1. Xác thực schema trọng số PyTorch và nạp vào `results/checkpoints/` và `models/`.
2. Đồng bộ biểu đồ hội tụ vào `frontend/public/images/`.
3. Kích hoạt `evaluate_benchmark.py` trên toàn bộ 100 POI Toàn Quốc.
4. Đồng bộ kết quả sang Frontend Next.js 14 (`frontend/public/data/`).

---

## 5. Bảng Kết Quả Đối Soát Đạt Được Sau Khi Huấn Luyện

| Mô hình | Quãng đường (km) | Thời lượng (phút) | Optimality Gap vs OR-Tools | Độ trễ CPU (ms) | Tỷ lệ lỗi (%) |
|---|---:|---:|---:|---:|---:|
| **Google OR-Tools** (Reference) | 72.69 | 217.78 | **0.00%** | 1,002.16 | 0.0% |
| **Attention Model (AM)** (Champion) | 75.63 | 225.67 | **+3.27%** | **32.63** | **0.0%** |
| **Pointer Network (A2C)** (Baseline) | 80.99 | 239.59 | **+9.27%** | **24.19** | **0.0%** |
| **Dueling DQN (Masked)** (Ablation) | 115.77 | 340.13 | **+105.45%** | **4.29** | **50.0%** |

*Ghi chú khoa học:* Kết quả đo lường trực tiếp trên 100 POI tổng hợp phân bố đều 3 miền (Hà Nội: 40, Đà Nẵng: 20, TP.HCM: 40). Độ trễ đo trên môi trường CPU đơn nhân Intel/AMD thương mại chuẩn.
