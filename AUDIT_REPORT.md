# Báo cáo Audit Độc lập — HotWAY CVRP-RL

**Ngày:** 22/10/2026  
**Phạm vi:** Đồ thị OSMnx, ma trận đường bộ, 30 benchmark instances, retrain DQN/Double DQN, benchmark 5 chiến lược trên 5 protocol, kiểm định thống kê, đối chiếu `rel_result/`.  
**Môi trường:** Windows 11, Python 3.14.6, PyTorch 2.14.1+cpu, networkx 3.7, scipy 1.18.0, pandas 3.0.6, numpy 2.5.1.  
**Nguyên tắc:** Zero-trust — không dùng lại số liệu huấn luyện/benchmark của pipeline gốc; mọi kết luận dưới đây đến từ script audit độc lập trong `audit/`.

---

## 1. Kết luận điều hành

1. **Các con số `cost_km` trong `rel_result/` là thật, không bị bịa.** Chạy lại toàn bộ 750 lượt với stock weights/seed 42 cho kết quả trùng khớp 750/750, sai khác tối đa 0,5 m (làm tròn).
2. **Nhưng methodology của benchmark sai ở nhiều điểm nghiêm trọng:** test set bị dùng để train; `time_limit` của protocol B/B2 bị bỏ qua; `evals` được tính bằng công thức chứ không đo; protocol A và A3 trùng nhau; thermal constraint không hề được kiểm tra; mọi chiến lược đều xuất phát từ Clarke-Wright và chỉ nhận 2–3 nước đi cải thiện.
3. **DQN không thắng baseline.** Trên test set, checkpoint chọn theo validation của DQN tệ hơn Greedy **0,325 km (~0,31%)**, khoảng tin cậy bootstrap 95% [0,108; 0,550] km không chứa 0. Double DQN hòa baseline trên test (chênh lệch 0,000 km) nhưng không vượt.
4. **Double DQN không có lợi thế ổn định so với DQN.** Checkpoint “best validation” của DQN rơi vào **epoch 1/150**, của Double DQN là **epoch 10/150**; validation chỉ có 4 instance và gần như không phân biệt được policy (cùng 92,871 km). Checkpoint final lại cho kết quả test khác hẳn.
5. **Phần lớn “2% cải thiện” đến từ Clarke-Wright + vài nước local search, không đến từ RL.** Random cũng đạt 2,067%, Greedy 2,077%, DQN chỉ 1,988% trên toàn bộ 30 instances. Trong 78% nhóm (protocol × instance × seed), cả 5 chiến lược cho **cùng một chi phí**.

**Trả lời trực tiếp câu hỏi trọng tâm:** không có bằng chứng DQN/Double DQN vượt baseline. DQN có xu hướng tệ hơn; Double DQN tương đương. Toàn bộ khác biệt thực nghiệm nằm trong khoảng ~0,1–0,3% quãng đường, nhỏ hơn nhiều so với sai lệch do ma trận khoảng cách và checkpoint selection gây ra.

---

## 2. Phương pháp audit

| Bước | Nội dung | Artifact |
|---|---|---|
| 1 | Kiểm tra cấu trúc đồ thị, SCC, oneway, geometry, OD paths | `audit/results/graph_audit.json` |
| 2 | Kiểm tra 30 instances: metadata, snap, capacity/fleet, thermal | `audit/results/instance_audit.json` |
| 3 | Sinh lại toàn bộ 30 instances từ source và so khớp từng trường | `audit/results/regeneration_audit.json` |
| 4 | Retrain DQN/Double DQN với split 20/4/6 và validation checkpoint | `audit/weights/`, `audit/results/training_*` |
| 5 | Benchmark độc lập 5 chiến lược × 5 protocol × 6 test instances × 3 seed | `audit/results/raw_runs_*` |
| 6 | Chạy lại toàn bộ 750 lượt stock để đối chiếu CSV gốc | `audit/results/raw_runs_stock_all_seed42.csv` |
| 7 | Tính lại Wilcoxon, Holm, bootstrap CI, W/T/L | `audit/results/paired_*` |
| 8 | Đối chiếu sai lệch methodology với `rel_result/` | `audit/results/discrepancy_report_all.json` |

Mọi script đều chạy với `PYTHONPATH="."` và không sửa `src/` (trừ việc monkeypatch có kiểm soát trong benchmark audit).

---

## 3. Đồ thị và hình học

### 3.1. Kết quả đạt

| Hạng mục | Kết quả |
|---|---|
| Loại đồ thị | `MultiDiGraph`, có hướng |
| Nodes / Edges | 46.055 / 107.224 |
| Strongly connected | Có |
| Self-loops | 120 |
| Cạnh `oneway=True` | 10.686 |
| Cặp có cạnh ngược chiều | 96.150 |
| Edge geometry thiếu | 0 |
| Edge geometry >2 điểm sai endpoint | 0 |
| Edge geometry sai length >5% | 0 |
| OD50 forward edges tồn tại | 50/50 |
| OD50 thời gian khớp | 50/50 |
| Ma trận bất đối xứng trung bình | 94,2% |

Kết luận: đồ thị có hướng, liên thông mạnh, geometry hợp lệ. Việc dùng hướng là chính đáng; không có dấu hiệu “đường thẳng nhân tạo” hàng loạt.

### 3.2. Lỗi nghiêm trọng: `dist_matrix` không phải shortest-distance

`src/services/road_matrix.py:266-267` chạy Dijkstra theo `weight="free_flow_time"`, sau đó `src/services/road_matrix.py:284-292` cộng `length` dọc theo đường đi nhanh nhất. Vì vậy `D[i][j]` là **chiều dài của đường nhanh nhất**, không phải đường ngắn nhất theo khoảng cách.

Hệ quả:

- `D` vi phạm bất đẳng thức tam giác: **2.813 / 325.321** bộ ba, vi phạm lớn nhất **5.162,1 m** (HCMC_VN_24).
- Nhiều cặp OD có `D` lớn hơn true shortest distance. Trên test set:

| Instance | Vi phạm tam giác | Max vi phạm (m) | Cặp D > shortest | Max vượt (m) |
|---|---:|---:|---:|---:|
| HCMC_VN_25 | 29 / 3.360 | 3.201,9 | 228 / 240 | 4.089,6 |
| HCMC_VN_26 | 205 / 15.600 | 4.072,8 | 630 / 650 | 5.485,1 |
| HCMC_VN_27 | 72 / 10.626 | 2.547,4 | 491 / 506 | 3.428,3 |
| HCMC_VN_28 | 113 / 15.600 | 2.757,1 | 616 / 650 | 5.147,2 |
| HCMC_VN_29 | 92 / 7.980 | 2.472,8 | 404 / 420 | 3.278,4 |
| HCMC_VN_30 | 17 / 5.814 | 1.091,8 | 325 / 342 | 2.106,6 |

- `time_matrix` thì chính xác và gần như metric (vi phạm tam giác tối đa 0,1 giây do làm tròn ở 3 instance).

Đây không làm route “bất khả thi”, nhưng làm **hàm mục tiêu CVRP không còn là tổng quãng đường ngắn nhất**. Local search có thể ưu tiên detour, và các so sánh km giữa các phương pháp vẫn nhất quán nội bộ nhưng không phản ánh chi phí đường bộ tối ưu.

**Khuyến nghị:** tính `dist_matrix` bằng Dijkstra với `weight="length"`; giữ `time_matrix` riêng bằng `free_flow_time`. Nếu mục tiêu là thời gian, đặt tên metric là `travel_time` và dùng nhất quán.

---

## 4. Instances và split

### 4.1. Kết quả đạt

- 30/30 instances sinh lại **khớp tuyệt đối**: coords, demands, `dist_matrix`, `time_matrix`, stops.
- Metadata khớp `instances_index.json`.
- Toạ độ snap vào graph ≤ 60 m; max snap 50,39 m.
- Tất cả instances đều capacity/fleet-feasible với Clarke-Wright.

### 4.2. Split

| Split | Số lượng | Customers TB | Demand TB | Radius TB (km) | CW cost TB (km) | Thermal feasible (CW) |
|---|---:|---:|---:|---:|---:|---:|
| Train (01–20) | 20 | 21,05 | 98,8 | 7,871 | 107,640 | 0/20 |
| Validation (21–24) | 4 | 18,25 | 85,0 | 7,841 | 95,035 | 0/4 |
| Test (25–30) | 6 | 20,83 | 95,33 | 7,913 | 107,597 | 0/6 |

Validation dễ hơn train/test rõ rệt (CW 95,0 km so với 107,6 km), chỉ có 4 instance. Đây là lý do chính khiến validation không thể xếp hạng policy.

### 4.3. Data leakage

`src/rl/train_cvrp_rl.py:263` gọi `load_benchmark_instances(args.instances_dir)` và dùng **toàn bộ 30 instances** để train, bao gồm 6 test instances. Không có split, không có validation, không có checkpoint selection. Vì vậy:

- 20% test set bị dùng trong training.
- Không có “best checkpoint” thực sự; chỉ lưu final weights.
- Kể cả khi ảnh hưởng của leakage nhỏ do model học yếu, **con số test trong `rel_result/` không còn là held-out estimate hợp lệ**.

### 4.4. Thermal constraint bị bỏ qua

- 0/30 instances thermal-feasible ngay cả với Clarke-Wright.
- Tổng 332 vi phạm nhiệt dưới CW.
- Trong 750 lượt benchmark stock: **750/750 lượt có vi phạm nhiệt**, trung bình **11,06 vi phạm/lượt**, nhiệt độ giao hàng thấp nhất **37,3°C** so với ngưỡng `min_temp=60°C`.
- `src/cvrp_solver/validator.py` chỉ kiểm tra capacity/fleet/coverage; **không hề kiểm tra thermal**. Vì vậy `feasible_rate=1.0` trong CSV là “capacity-feasible”, không phải “feasible” theo bài toán.

Đây là lỗi đặc biệt nghiêm trọng vì mục tiêu gốc có ràng buộc nhiệt. Cần hoặc (a) đưa thermal vào validator và hàm mục tiêu, hoặc (b) bỏ ràng buộc nhiệt khỏi tuyên bố khoa học. Hiện tại tài liệu đang tuyên bố một thứ mà code không thực thi.

---

## 5. Tái huấn luyện DQN / Double DQN

### 5.1. Cấu hình

| Tag | Episodes | Steps/ep | Candidates | Seed | Split | Checkpoint |
|---|---:|---:|---:|---:|---|---|
| `repro` | 30 | 50 | 64 | 2027 | 20/4/6 | best validation + final |
| `fair` | 150 | 100 | 128 | 2027 | 20/4/6 | best validation + final |

`fair` là cấu hình “hào phóng” để loại trừ khả năng model chỉ thiếu thời gian huấn luyện.

### 5.2. Kết quả

| Tag | Algo | Best val (km) | Best epoch | Test best-val (km) | Test final (km) |
|---|---|---:|---:|---:|---:|
| repro | DQN | 92,871 | 2/30 | 106,1552 | 106,0154 |
| repro | Double DQN | 92,871 | 2/30 | 106,1552 | 106,0154 |
| fair | DQN | 92,871 | **1/150** | 106,3407 | 106,0154 |
| fair | Double DQN | 92,871 | **10/150** | 106,0154 | 106,1945 |

(Test là protocol A, trung bình 3 seed 2027–2029; DQN/DDQN là chiến lược được đánh giá.)

Quan sát:

- Validation cost **giống hệt 92,871 km** cho mọi checkpoint được chọn, dù policy khác nhau.
- Validation final của DQN chỉ 92,8858 km (chênh 0,015 km), nhưng test tốt hơn best-val 0,325 km.
- Nghĩa là validation 4 instance **không đủ tín hiệu** để chọn checkpoint; “best validation” thực chất là một policy gần như chưa train.
- Kết quả test đảo chiều giữa best-val và final: DQN best-val tệ, DQN final hòa baseline; Double DQN best-val hòa, Double DQN final tệ hơn. Đây là **bất ổn định huấn luyện**, không phải một kết luận khoa học ổn định.

### 5.3. Policy collapse

Trên 750 lượt stock:

| Chiến lược | Tỷ lệ action 0 `two_opt` | Action 1 | Action 2 | Action 3 `inter_swap` |
|---|---:|---:|---:|---:|
| DQN | 78–82% | 1–1,5% | 7–10% | 7–13% |
| Double DQN | 40–44% | 2–7% | 4–5% | 49–51% |

Q-value probe trên 6 test instances (fair best):

- DQN: Q-spread trung bình chỉ **0,064**, gần như không phân biệt action; argmax ban đầu là `inter_swap` nhưng steady-state lại chủ yếu `two_opt`.
- Double DQN: Q-spread **3,775**, argmax ban đầu là `two_opt`/`intra_relocate` nhưng steady-state lại chủ yếu `inter_swap`.

Kết luận: policy bị “kẹt” vào một operator, không học được chiến lược chọn operator đa dạng. Điều này khớp với việc chỉ 2–3 nước đi được chấp nhận.

---

## 6. Benchmark độc lập trên test set

### 6.1. Kết quả fair best-val, 3 seed (n = 18 mỗi phương pháp)

| Protocol | Random | Cyclic | Greedy | DQN | Double DQN |
|---|---:|---:|---:|---:|---:|
| A2 | 106,0172 | 106,0181 | 106,0154 | 106,3407 | 106,0154 |
| A | 106,0163 | 106,0154 | 106,0154 | 106,3407 | 106,0154 |
| A3 | 106,0163 | 106,0154 | 106,0154 | 106,3407 | 106,0154 |
| B | 106,0154 | 106,0172 | 106,0154 | 106,4006 | 106,0629 |
| B2 | 106,0163 | 106,0154 | 106,0154 | 106,3407 | 106,0836 |

(Đơn vị km; trung bình 6 instances × 3 seed.)

Improvement trung bình:

| Protocol | Random | Cyclic | Greedy | DQN | Double DQN |
|---|---:|---:|---:|---:|---:|
| A2/A/A3 | 1,348% | 1,346–1,348% | 1,348% | **1,053%** | 1,348% |
| B | 1,348% | 1,347% | 1,348% | **1,003%** | 1,302% |
| B2 | 1,348% | 1,348% | 1,348% | **1,053%** | 1,292% |

### 6.2. So sánh cặp (negative = phương pháp đầu tốt hơn)

| Protocol | So sánh | Δ cost (km) | CI 95% (km) | W/T/L | Cohen dz | p raw | p Holm |
|---|---|---:|---|---|---:|---:|---:|
| A2 | DQN − Greedy | +0,3253 | [0,1084; 0,5504] | 0/12/6 | 0,684 | 0,0244 | 0,1705 |
| A | DQN − Greedy | +0,3253 | [0,1084; 0,5504] | 0/12/6 | 0,684 | 0,0244 | 0,1705 |
| A3 | DQN − Greedy | +0,3253 | [0,1084; 0,5504] | 0/12/6 | 0,684 | 0,0244 | 0,1705 |
| B | DQN − Greedy | +0,3852 | [0,1377; 0,6522] | 0/12/6 | 0,672 | 0,0269 | 0,1880 |
| B2 | DQN − Greedy | +0,3253 | [0,1084; 0,5504] | 0/12/6 | 0,684 | 0,0244 | 0,1705 |
| A2/A/A3 | Double DQN − Greedy | 0,0000 | [0; 0] | 0/18/0 | 0,000 | NaN | 1,000 |
| B | Double DQN − Greedy | +0,0475 | [0; 0,1416] | 0/16/2 | 0,240 | 0,1797 | 0,5391 |
| B2 | Double DQN − Greedy | +0,0682 | [0; 0,2045] | 0/17/1 | 0,236 | 0,3173 | 0,9519 |

Diễn giải:

- DQN tệ hơn Greedy một cách **nhất quán về dấu** (12/18 hòa, 6/18 tệ hơn, 0/18 tốt hơn), bootstrap CI loại trừ 0.
- Tuy nhiên sau hiệu chỉnh Holm, p = 0,17–0,19 → **chưa đạt ý nghĩa 0,05** vì nhiều tie và n nhỏ. Đây là “consistent underperformance, not Holm-significant”.
- Double DQN hòa tuyệt đối ở A/A2/A3 (0/18 khác biệt), chênh không đáng kể ở B/B2.
- Protocol A và A3 cho kết quả **giống hệt từng instance** (xem mục 7.3).

### 6.3. Độ nhạy với checkpoint

Cùng một thuật toán, chỉ đổi best-val → final:

- DQN: 106,3407 → 106,0154 km (tốt hơn 0,325 km).
- Double DQN: 106,0154 → 106,1945 km (tệ hơn 0,179 km).

Nếu báo cáo chỉ chọn một trong hai, có thể tạo ra kết luận “DQN thắng” hoặc “DQN thua” tùy ý. Đây là lý do phải báo cáo cả hai và phải cải thiện validation.

### 6.4. Toàn bộ 30 instances (stock weights, seed 42, n = 30)

| So sánh | Δ cost (km) | CI 95% (km) | W/T/L | p raw | p Holm |
|---|---:|---|---|---:|---:|
| DQN − Greedy | +0,0854 | [0; 0,2273] | 0/27/3 | 0,1088 | 0,7617 |
| Double DQN − Greedy | +0,0052 | [0; 0,0136] | 0/28/2 | 0,1797 | 1,0000 |
| DQN − Double DQN | +0,0802 | [−0,0080; 0,2232] | 2/25/3 | 0,5002 | 1,0000 |

Trên toàn bộ 30 instances, DQN cũng không tốt hơn; chênh lệch nhỏ hơn test set nhưng cùng dấu. Không có bằng chứng RL vượt baseline.

---

## 7. Đối chiếu `rel_result/`

### 7.1. Tái lập chi phí: ĐẠT

| Hạng mục | Kết quả |
|---|---|
| Số dòng đối chiếu | 750/750 |
| Max |Δ cost| | 0,0005 km |
| Số dòng trong sai số 1 m | 750/750 |
| Max |Δ improvement| | 4,4×10⁻⁵ pp |

Kết luận: CSV gốc không bịa chi phí. Các lỗi nằm ở cách đo và cách thiết kế thí nghiệm, không phải ở việc sửa số.

### 7.2. `evals` bị bịa bằng công thức

`src/benchmark/runner.py:103-104`:

```python
steps_count = len(solution.search_trace)
evals_count = steps_count * max_candidates
```

Đối chiếu:

| Hạng mục | Giá trị |
|---|---:|
| Số dòng đúng công thức `decisions × candidates` | **750/750** |
| Tổng evals shipped | 17.385.600 |
| Tổng evals thực đo | 15.777.549 |
| Tỷ lệ thực/shipped | 0,9075 |
| Trung vị tỷ lệ theo dòng | 0,8257 |
| Min / max tỷ lệ | 0,2287 / 2,9851 |

Vậy con số `evals` không phải “số candidate đã đánh giá”; nó chỉ là `số bước × ngân sách candidate`. Có dòng thực tế chỉ dùng 23% ngân sách, có dòng dùng gần 300%.

### 7.3. Protocol A và A3 trùng nhau

`src/benchmark/runner.py:145-149`: A và A3 cùng `max_steps=100`, `max_candidates=128`, `time_limit=None`; `feature_patience` không được truyền.

Đối chiếu 150 cặp A/A3:

- Cost giống nhau: **150/150**.
- Evals giống nhau: **150/150**.
- Max |Δ cost| = 0,0 km.

Vậy “5 protocol” thực chất chỉ còn 4; báo cáo A và A3 như hai thí nghiệm độc lập là **double counting**, làm sai lệch hiệu chỉnh Holm.

### 7.4. Time budget B/B2 bị bỏ qua

`src/benchmark/runner.py:167-179` lấy `t_limit` nhưng không truyền vào solver; `run_strategy_on_instance` nhận `time_limit_sec` nhưng không dùng.

Đối chiếu 300 dòng B/B2:

| Hạng mục | Giá trị |
|---|---:|
| Số dòng vượt limit | **300/300** |
| Tỷ lệ vi phạm | 100% |
| Max runtime | 4,60693 s |
| Max overrun | 4,50693 s |
| Hệ số vượt lớn nhất | **46,07×** |
| Trung vị runtime | 0,29288 s |

Ví dụ B2 có limit 0,10 s nhưng chạy tới 4,6 s. Vì vậy mọi so sánh “B/B2 real-time” là không hợp lệ. Khi audit bật `--enforce-time`, mọi run B/B2 đều chạm deadline và dừng, chi phí thay đổi rõ rệt.

### 7.5. Thermal feasible 0% nhưng báo 100%

| Hạng mục | Giá trị |
|---|---:|
| Số dòng có vi phạm nhiệt | 750/750 |
| Tỷ lệ vi phạm nhiệt | 100% |
| Capacity/fleet feasible | 100% |
| Mean thermal violations | 11,06 |
| Min delivery temp | 37,3°C |
| Ngưỡng yêu cầu | 60,0°C |

`feasible_rate=1.0` chỉ có nghĩa capacity/fleet/coverage. Không được gọi là “feasible” trong báo cáo có ràng buộc nhiệt.

### 7.6. Các chiến lược gần như giống nhau

Trên 750 lượt stock:

| Hạng mục | Giá trị |
|---|---:|
| Nhóm (protocol × instance × seed) | 150 |
| Nhóm cả 5 chiến lược cùng cost | **117/150 (78%)** |
| Số cost khác nhau trung bình trong 5 chiến lược | 1,227 |
| Mean applied steps | 2,32–2,40 / 100 (hoặc 200/400) |
| Max applied steps | 6 |

Nguyên nhân:

- `src/cvrp_solver/search.py:127` khởi tạo mọi chiến lược từ Clarke-Wright.
- `src/cvrp_solver/operators.py:250` chỉ chấp nhận `delta < -1e-9`.
- Không có perturbation/restart; sau 2–3 nước đi tốt nhất, mọi operator đều thất bại.
- Vì vậy Random cũng đạt 2,067%, Greedy 2,077%, DQN 1,988%.

Đây là lỗi thiết kế thí nghiệm, không phải lỗi của RL. Việc so sánh operator-selection policy trên một search space gần như đã cạn là vô nghĩa.

### 7.7. Các lỗi metric khác

- `improvement_pct` bị chặn `max(0.0, ...)` tại `src/benchmark/runner.py:105`; nếu một chiến lược làm xấu nghiệm, nó sẽ hiển thị 0% thay vì số âm.
- `gap_vs_ortools_pct` tại `src/benchmark/runner.py:216` thực chất là `(mean_dist − best_mean)/best_mean`, tức gap so với chiến lược tốt nhất, **không phải OR-Tools**. Tên cột sai.
- `rel_result/training_curves.csv` có 25 episode/algorithm, trong khi README dùng `--episodes 25`; mission yêu cầu 30. Audit đã retrain cả 30 và 150 episode.

### 7.8. Test coverage

`pytest tests -q` → **15 passed**, nhưng:

- `tests/test_geometry.py:18` dùng `data/binhthanh_graph.pickle` (graph 38 nodes cũ), không phải `hcmc_compact_graph.pickle` 46.055 nodes.
- Test “0 artificial straight lines” chỉ kiểm tra toạ độ nằm trong bounding box, không kiểm tra geometry thực tế.
- Không có test nào phát hiện triangle inequality, thermal, time limit, hay eval counting.

---

## 8. Bảng lỗi và mức độ

| # | Lỗi | Mức độ | Bằng chứng | Ảnh hưởng |
|---|---|---|---|---|
| 1 | Test set dùng để train, không có val split | Critical | `train_cvrp_rl.py:263`; 6/30 test instances | Test metric không hợp lệ |
| 2 | `dist_matrix` là fastest-path length, không phải shortest distance | Critical | 2.813/325.321 tam giác; max 5,162 km | Sai hàm mục tiêu CVRP |
| 3 | Thermal constraint không được kiểm tra | Critical | 750/750 vi phạm; validator không có thermal | “Feasible” sai bản chất |
| 4 | B/B2 bỏ qua time limit | Critical | 300/300 vượt; max 46× | Protocol real-time không hợp lệ |
| 5 | Protocol A = A3 | High | 150/150 giống hệt | Double counting, sai Holm |
| 6 | `evals` bịa bằng công thức | High | 750/750 đúng công thức; thực tế 0,23–2,99× | Không thể so sánh chi phí tính toán |
| 7 | Mọi chiến lược khởi tạo CW, chỉ 2–3 move | High | 78% nhóm cùng cost; applied steps ~2,3 | Không phân biệt được policy |
| 8 | Validation 4 instance, best checkpoint epoch 1/10 | High | best val 92,871; best episode 1 và 10 | Checkpoint selection vô hiệu |
| 9 | `improvement_pct` clamp, `gap_vs_ortools` mislabel | Medium | runner.py:105,216 | Metric sai tên/sai dấu |
| 10 | Test geometry dùng graph cũ | Medium | tests/test_geometry.py:18 | Không bảo vệ graph production |
| 11 | Policy collapse (DQN 80% two_opt, DDQN 50% inter_swap) | Medium | action distribution; Q-spread 0,064 | RL không học được operator selection |

---

## 9. Khuyến nghị

### 9.1. Sửa tính đúng đắn của bài toán

1. Tính `dist_matrix` bằng Dijkstra `weight="length"`; giữ `time_matrix` riêng. Kiểm tra bất đẳng thức tam giác trong CI.
2. Đưa thermal vào `validate_cvrp_solution` và hàm mục tiêu (hoặc loại bỏ ràng buộc nhiệt khỏi tuyên bố).
3. Tách rõ capacity/fleet-feasible và thermal-feasible trong mọi báo cáo.

### 9.2. Sửa thí nghiệm

4. Split cố định 20/4/6; không load test trong training; dùng validation lớn hơn hoặc cross-validation.
5. Không chọn checkpoint trên 4 instance; dùng ít nhất 8–12 instance hoặc nested CV.
6. Bỏ protocol A3 hoặc làm cho nó khác thật sự; hiệu chỉnh Holm trên số protocol thực.
7. Enforce time limit **bên trong** vòng lặp `best_move`, không chỉ trước mỗi bước.
8. Đo `evals` bằng counter trong `best_move`; không suy ra từ `steps × candidates`.
9. Bỏ clamp `max(0.0, ...)`; báo cáo cả improvement âm.
10. Đổi tên `gap_vs_ortools_pct` thành `gap_vs_best_strategy_pct`, hoặc chạy OR-Tools thật.

### 9.3. Sửa thiết kế search

11. Thêm perturbation/restart hoặc cho phép move trung tính để thoát CW local optimum.
12. Đánh giá policy trên trace có nhiều quyết định thực sự (hiện chỉ 2–3 move được apply).
13. Nếu mục tiêu là chứng minh RL hữu ích, cần bài toán mà operator selection thay đổi được kết quả; hiện tại random cũng đạt xấp xỉ greedy.

### 9.4. Sửa test

14. Thay `binhthanh_graph.pickle` bằng graph production trong test geometry.
15. Thêm test: triangle inequality, thermal feasibility, time-limit enforcement, eval counter, A ≠ A3.

---

## 10. Artifact và lệnh tái lập

### 10.1. Artifact chính

| File | Nội dung |
|---|---|
| `audit/results/graph_audit.json` | Cấu trúc graph, SCC, geometry, OD50, asym, triangle count |
| `audit/results/triangle_check.json` | Vi phạm tam giác và excess so với shortest path trên test set |
| `audit/results/instance_audit.json` | Metadata, snap, capacity/fleet, thermal của 30 instances |
| `audit/results/regeneration_audit.json` | Sinh lại 30/30 instances khớp tuyệt đối |
| `audit/results/training_info_repro.json` | Best val/epoch, seed, thời gian của cấu hình 30/50/64 |
| `audit/results/training_info_fair.json` | Best val/epoch, seed, thời gian của cấu hình 150/100/128 |
| `audit/results/eval_splits.csv` | Cost theo train/val/test cho best/final |
| `audit/results/q_probe.json` | Q-value ban đầu trên 6 test instances |
| `audit/results/raw_runs_stock_all_seed42.csv` | 750 lượt stock tái lập |
| `audit/results/raw_runs_fair_test_enforced_2027_2028_2029.csv` | 450 lượt fair best-val, 3 seed |
| `audit/results/raw_runs_fairfinal_test_enforced.csv` | 450 lượt fair final, 3 seed |
| `audit/results/raw_runs_repro_test_enforced.csv` | 450 lượt repro best-val, 3 seed |
| `audit/results/paired_*.csv` | Wilcoxon, Holm, bootstrap CI, W/T/L |
| `audit/results/discrepancy_report_all.json` | Đối chiếu 750 dòng với CSV gốc |
| `audit/weights/` | 8 checkpoint retrain (repro/fair × dqn/ddqn × best/final) |

### 10.2. Lệnh tái lập

```powershell
$env:PYTHONPATH="."

# Audit graph + instances
python audit/graph_audit.py
python audit/instance_audit.py
python audit/regenerate_all.py
python audit/check_triangle.py

# Retrain (strict split)
python audit/retrain.py --tag repro --episodes 30 --steps 50 --candidates 64
python audit/retrain.py --tag fair --episodes 150 --steps 100 --candidates 128

# Đánh giá split
python audit/eval_splits.py
python audit/q_probe.py

# Benchmark 3 seed, enforce time
python audit/benchmark_audit.py --tag fair --weights-suffix best --instances test --seeds 2027,2028,2029 --enforce-time
python audit/benchmark_audit.py --tag fair --weights-suffix final --instances test --seeds 2027,2028,2029 --enforce-time --out-prefix fairfinal_test_enforced
python audit/benchmark_audit.py --tag repro --weights-suffix best --instances test --seeds 2027,2028,2029 --enforce-time --out-prefix repro_test_enforced

# Tái lập toàn bộ CSV gốc
python audit/benchmark_audit.py --tag stock --instances all --seeds 42 --out-prefix stock_all_seed42

# Đối chiếu
python audit/compare_discrepancies.py
```

---

## 11. Hạn chế của audit

- Test set chỉ có 6 instance × 3 seed = 18 cặp; Wilcoxon có nhiều tie nên p-value kém ổn định. Đã báo cáo bootstrap CI và W/T/L thay vì chỉ p-value.
- Chưa chạy OR-Tools độc lập; chỉ xác nhận cột `gap_vs_ortools` bị đặt tên sai.
- Chưa kiểm chứng mô hình thermal (hệ số k, nhiệt độ môi trường) so với dữ liệu thực; audit chỉ kiểm tra code có enforce hay không, và kết quả là không.
- Runtime phụ thuộc máy; các kết luận về “vượt time limit” dùng chính runtime do pipeline ghi lại, nên càng đáng tin.
- Không đánh giá frontend/backend; phạm vi chỉ là pipeline dữ liệu, RL, benchmark và tài liệu số liệu.

---

## 12. Kết luận cuối

Pipeline hiện tại tạo ra **số liệu tái lập được nhưng không hợp lệ về mặt phương pháp**. Điểm mạnh là đồ thị có hướng/geometry tốt, instances sinh lại chính xác, và CSV không bịa chi phí. Điểm yếu chí mạng là test leakage, ma trận khoảng cách phi metric, thermal không được enforce, time limit bị bỏ qua, protocol trùng nhau, evals bị bịa, và search space gần như cạn sau 2–3 move.

Về câu hỏi khoa học trọng tâm: **DQN không vượt baseline; DQN có xu hướng tệ hơn khoảng 0,1–0,3%; Double DQN tương đương baseline.** Không có cơ sở để tuyên bố RL cải thiện CVRP trong thiết lập hiện tại. Cần sửa các lỗi mục 9 trước khi có thể so sánh lại một cách khoa học.
