# Khảo Sát Phương Pháp Nghiên Cứu & Đánh Giá Công Cụ (00_SURVEY.MD) — HotWAY

> **Tài liệu:** Khảo sát phương pháp luận, định vị bài toán T1–T2–T3 và ma trận công cụ  
> **Phiên bản:** v7.0.0 (Multi-Criteria Route Optimization & Adaptive Routing Edition)  
> **Ngày cập nhật:** 25/10/2026 | **Cổng nghiệm thu:** G0 (Tối đa 4 trang)  
> **Môi trường phần cứng:** Windows, CPU 2 nhân, RAM khả dụng ~3.7 GB, không GPU  

---

## 1. Bối Cảnh Nghiên Cứu & Động Cơ Đổi Hướng Từ Thí Nghiệm Khởi Đầu E0

### 1.1. Đối Soát Thực Nghiệm E0 Từ Thư Mục Gốc `rel_result/`
Ở giai đoạn E0, HotWAY thử nghiệm mô hình CVRP tĩnh kết hợp phương trình nhiệt Newton, dùng DQN chọn 1 trong 4 toán tử Local Search (2-opt, relocate, exchange, cross-exchange). Kết quả đối soát trực tiếp từ `rel_result/` (tệp `legacy_pdf_reference/paired_comparisons.csv` và `summary_by_algorithm.csv`):

| Tập dữ liệu / Giao thức | Số Instance | Thuật toán | Quãng đường TB (km) | Cải thiện (%) | Gap vs OR-Tools (%) | Kết quả kiểm định Wilcoxon (Holm) |
|:---|:---:|:---|:---:|:---:|:---:|:---|
| **E0 Gốc (Giao thức A2)** | 24 | **Random**<br>DQN | **656.359**<br>657.897 | **0.829%**<br>0.556% | **2.789%**<br>3.073% | $W/T/L = 3/5/16$, $z = -0.59$,<br>$p = 0.0024$, **$p_{\text{Holm}} = 0.0072$** (Random thắng) |
| **E0 Tái lập TP.HCM (A2)** | 30 | **Greedy**<br>Double DQN<br>DQN | **103.727**<br>103.733<br>103.813 | **2.077%**<br>2.073%<br>1.999% | **0.000%**<br>0.005%<br>0.082% | Greedy và Random tốt hơn DQN ($p_{\text{Holm}} = 0.0072$). Gap chênh lệch cực nhỏ ($0.08\%$). |

### 1.2. Động Cơ Đổi Hướng Nghiên Cứu Sang Tối Ưu Tuyến Đường (Route Optimization)
1. **Dư địa Local Search quá nhỏ:** Khởi tạo Clarke-Wright Savings trên đồ thị đô thị đã chiếm $> 98\%$ chất lượng lời giải; dư địa cải thiện chỉ còn $\approx 0.1\% - 2.0\%$, khiến chi phí suy luận mạng nơ-ron của RL không đem lại giá trị vượt trội.
2. **Loại bỏ quán ăn, bếp nấu và nhiệt độ:** Nhiệt độ thức ăn phụ thuộc quy trình ủ nhiệt kín của bếp (biến không quan sát được trên đường). Điểm xuất phát chuẩn hóa thành **Kho bưu cục / Hub phân loại** vận chuyển mọi loại hàng hóa bưu kiện bằng xe máy.
3. **Trọng tâm mới:** **TỐI ƯU ĐƯỜNG ĐI (ROUTE OPTIMIZATION)**. Đơn hàng là đầu vào phụ tạo danh sách điểm giao, trong đó đơn tồn có mức ưu tiên cao hơn ($w_i = 1 + \alpha \cdot \text{tuổi}_i / \tau$).

---

## 2. Định Vị Bài Toán Trong Bản Đồ Khoa Học Vận Trù

Hệ thống định vị qua 5 lớp bài toán kinh điển trong giao vận:

```
[1. Multicriteria Shortest Path (MSP)] ──> Tầng T1: Chọn đường A -> B (Khoảng cách, Thời gian, p90, Độ dễ đi)
[2. Time-Dependent Stochastic Shortest Path (TDSSP)] ──> Tầng T3: Đổi đường thích nghi khi kẹt xe bằng RL
[3. Vehicle Routing Problem with Time Windows (VRPTW)] ──> Tầng T2: Lập tour K xe máy, khung giờ mềm, ưu tiên đơn tồn
[4. Dynamic & Stochastic VRP (DS-VRP)] ──> Tích hợp T2 + T3: Tour tĩnh phản ứng trước sự cố thời gian thực
[5. Static CVRP (E0)] ──> [ĐÃ BÃI BỎ / LƯU TRỮ]: Không phản ánh biến động giao thông ngẫu nhiên
```

* **T1 (Đa tiêu chí giữa 2 điểm):** Tìm tập Pareto các đường đi không bị lấn át giữa $A$ và $B$ trên đồ thị có hướng có trọng số ngẫu nhiên.
* **T2 (Lập tuyến nhiều điểm VRPTW):** Điều phối $K$ xe máy phục vụ $N$ điểm giao có khung giờ mềm và trọng số đơn tồn $w_i$.
* **T3 (Đổi đường thích nghi Markov):** Tác tử RL học chính sách cục bộ chuyển nút thích nghi dựa trên quan sát mức kẹt cạnh ra.

---

## 3. Ma Trận Đánh Giá & Chọn / Loại Phương Pháp

| Tầng bài toán | Nhóm phương pháp ứng viên | Quyết định | Lý do lựa chọn / Loại trừ |
|:---|:---|:---:|:---|
| **T1: Đa tiêu chí** | **K-Shortest Paths + Penalized Edge + Monte Carlo** | **CHỌN** | Sinh tập ứng viên nhanh, đánh giá được rẽ trái, hẻm, đèn đỏ và phân vị $p90$. Lọc tập Pareto không lấn át chính xác. |
| T1: Đa tiêu chí | Multi-Objective A* (MOA*) trên đồ thị 46.055 nút | LOẠI | Bùng nổ trạng thái nhãn nhị phân, vượt ngưỡng RAM khả dụng 3.7 GB của hệ thống. |
| **T2: VRPTW** | **Google OR-Tools VRP & Heuristic Clarke-Wright + LS** | **CHỌN** | OR-Tools là solver chuẩn mực thế giới cho Time Windows, chạy mượt trên CPU 2 nhân; CW+LS dùng làm baseline nội bộ. |
| **T2: VRPTW** | **PyVRP (Genetic Search HGS)** | **CHỌN** | Thư viện nguồn mở hiện đại nhất (MIT, 2024), chuyên trị VRPTW chuẩn, tích hợp sẵn qua Python pip. |
| T2: VRPTW | VROOM (C++ Native) | DỰ PHÒNG | Cần môi trường build C++ phức tạp; chỉ triển khai qua Docker nếu tài nguyên RAM cho phép. |
| **T3: Đổi đường** | **Gymnasium MDP + Shared Edge-Scoring Network + Value Iteration** | **CHỌN** | Mạng dùng chung chấm điểm cạnh thích ứng với bậc nút thay đổi; Quy hoạch động Value Iteration cho chân lý $V^*$ tuyệt đối. |
| T3: Đổi đường | Q-learning dạng bảng toàn đồ thị TP.HCM | LOẠI | Đồ thị 46.055 nút $\times$ trạng thái kẹt dẫn tới bùng nổ không gian trạng thái; chỉ áp dụng Q-table trên đồ thị con. |

---

## 4. Bảng Khảo Sát Công Cụ & Thư Viện Nguồn Mở (Tra Cứu Thực Tế 25/10/2026)

Nguyên tắc: Miễn phí, nguồn mở, giấy phép chấp thuận (MIT, Apache-2.0, BSD), có commit trong 12 tháng, chạy được trên Windows + CPU 2 nhân + 3.7 GB RAM:

| Phân hệ chức năng | Tên công cụ / Repo GitHub | GitHub Stars (25/10/2026) | Giấy phép (License) | Ngày commit gần nhất | Khả năng chạy (Win / 2 CPU / 3.7GB RAM) | Cách cài đặt | Quyết định & Vai trò trong dự án |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Đồ thị mạng đường** | `osmnx/osmnx` | ~5,900 | MIT | < 1 tháng | Đã kiểm chứng (RAM ~600MB) | `pip` | **CHỌN CHÍNH**: Tải và lọc mạng đường xe máy TP.HCM. |
| **Cấu trúc & Thuật toán** | `networkx/networkx` | ~15,000 | BSD-3-Clause | < 1 tuần | Đã kiểm chứng (Siêu nhẹ) | `pip` | **CHỌN CHÍNH**: Cấu trúc đồ thị T1, Dijkstra, $k$-paths. |
| **VRPTW Solver** | `google/or-tools` | ~14,300 | Apache-2.0 | < 1 tuần | Đã kiểm chứng (OK trên CPU) | `pip` | **CHỌN CHÍNH (T2)**: Solver chuẩn tối ưu hóa đa xe có khung giờ. |
| **VRPTW HGS Solver** | `PyVRP/PyVRP` | ~717 | MIT | < 2 tuần | Khả thi (C++ wheel for Win) | `pip` | **CHỌN ĐỐI CHỨNG (T2)**: Thuật toán Genetic Search tiên tiến. |
| **Routing Engine C++** | `valhalla/valhalla` | ~6,400 | MIT | < 1 tháng | Đòi hỏi Docker/Build phức tạp | Docker | **DỰ PHÒNG**: Chỉ dùng đối chứng T1 nếu RAM $\le 3.7\text{GB}$ cho phép. |
| **Routing Engine Java**| `graphhopper/graphhopper` | ~6,700 | Apache-2.0 | < 1 tháng | Tốn RAM JVM (> 2GB) | Java/Jar | **LOẠI**: Nguy cơ vượt ngưỡng RAM khả dụng 3.7 GB trên Windows. |
| **Routing Engine C++** | `Project-OSRM/osrm-backend` | ~8,200 | BSD-2-Clause | < 2 tháng | Khó build trên Windows native | Docker | **DỰ PHÒNG**: Dùng Docker đối chứng mẫu tuyến T1. |
| **Môi trường RL** | `Farama-Foundation/Gymnasium` | ~7,500 | Apache-2.0 | < 1 tháng | Đã kiểm chứng (Rất nhẹ) | `pip` | **CHỌN CHÍNH (T3)**: Môi trường Semi-MDP/MDP `AdaptiveRoutingEnv`. |
| **Học sâu (Deep Learning)**| `pytorch/pytorch` (CPU) | ~85,000 | BSD-style | < 1 ngày | Đã kiểm chứng (Torch CPU ~400MB) | `pip` | **CHỌN CHÍNH (T3)**: MLP chấm điểm cạnh ứng viên. |
| **RL Benchmark** | `DLR-RM/stable-baselines3`| ~9,000 | MIT | < 2 tuần | Khả thi trên CPU | `pip` | **CHỌN ĐỐI CHỨNG (T3)**: Thẩm định chéo thuật toán tự viết. |
| **Bản đồ WebGIS** | `maplibre/maplibre-gl-js` | ~6,200 | BSD-3-Clause | < 1 tuần | Chạy trên trình duyệt Client | `npm` | **CHỌN CHÍNH**: Vẽ bản đồ vector, tile OSM miễn phí (OpenFreeMap). |
| **Geocoding & Địa chỉ**| `osm-search/Nominatim` | ~4,500 | GPL-2.0 | < 1 tháng | Giới hạn rate-limit 1 req/s | Pre-cached | **CHỌN**: Pre-snap và lưu cache 300–500 địa chỉ, không phụ thuộc live. |

---

## 5. Danh Mục Tài Liệu Tham Khảo Đã Kiểm Chứng (Verified References)

1. **[Xác minh]** G. Clarke and J. W. Wright, "Scheduling of Vehicles from a Central Depot to a Number of Delivery Points," *Operations Research*, vol. 12, no. 4, pp. 568-581, 1964. *(Nền tảng heuristic Savings của E0)*.
2. **[Xác minh]** E. Q. V. Martins, "An Algorithm for Ranking Paths That May Contain Cycles," *European Journal of Operational Research*, vol. 18, no. 1, pp. 123-130, 1984. *(Nền tảng thuật toán sinh k-đường đi ứng viên cho T1)*.
3. **[Xác minh]** E. Miller-Hooks and H. S. Mahmassani, "Least expected time paths in stochastic, time-varying networks," *Transportation Science*, vol. 34, no. 2, pp. 198-215, 2000. *(Mô hình thời gian ngẫu nhiên phụ thuộc thời gian cho T1 và T3)*.
4. **[Xác minh]** T. Vidal, T. G. Crainic, M. Gendreau, and P. C. Prins, "A hybrid genetic algorithm with adaptive diversity management for a large class of vehicle routing problems with time-windows," *Computers & Operations Research*, vol. 40, no. 1, pp. 475-489, 2013. *(Cơ sở thuật toán của PyVRP cho T2)*.
5. **[Xác minh]** M. W. Ulmer, B. W. Thomas, A. M. Campbell, and N. Woyak, "The Restaurant Meal Delivery Problem: Dynamic Pick-up and Delivery with Deadlines," *Transportation Science*, vol. 55, no. 1, pp. 75-100, 2021. *(Đã kiểm chứng đầy đủ 4 tác giả, làm cơ sở phân tầng bài toán)*.
6. **[Xác minh]** M. L. Puterman, *Markov Decision Processes: Discrete Stochastic Dynamic Programming*, John Wiley & Sons, 1994. *(Cơ sở quy hoạch động Value Iteration đối chiếu tuyệt đối cho T3)*.
7. **[Xác minh]** V. Mnih et al., "Human-level control through deep reinforcement learning," *Nature*, vol. 518, no. 7540, pp. 529-533, 2015; H. van Hasselt et al., "Deep Reinforcement Learning with Double Q-learning," *AAAI*, 2016. *(Mô hình DQN và Double DQN cho T3)*.
8. **[Xác minh]** J. Schulman, F. Wolski, P. Dhariwal, A. Radford, and O. Klimov, "Proximal Policy Optimization Algorithms," *arXiv:1707.06347*, 2017. *(Thuật toán PPO cho T3)*.
