# BẢN GHI QUYẾT ĐỊNH THIẾT KẾ & KIẾN TRÚC (DECISIONS.MD) — HotWAY

> **Phiên bản:** v7.3.2 (Nationwide Multi-Model NCO & Production WebGIS Edition)  
> **Ngày cập nhật:** 02/11/2026  

---

## 1. Quyết Định Địa Điểm & Trọng Tâm Không Gian
- **Quyết định:** Sử dụng địa bàn Mặc định là **Hàng Gòn Quán**, cơ sở tại **490 Điện Biên Phủ, Phường 21, Bình Thạnh, TP. Hồ Chí Minh** (`10.8012°N, 106.7145°E`).
- **Nâng cấp v5.0:** Mở rộng từ mạng lưới 38 nút lên mạng lưới đô thị toàn diện TP.HCM bán kính 10km (**46,055 nút, 107,224 cạnh, 8,551 km đường**) qua OSMnx, vẫn duy trì chế độ khu vực Bình Thạnh (legacy) để tương thích ngược.
- **Cơ chế lưu trữ:** Toàn bộ thông số được lưu trong một file duy nhất `config/site.yaml`. Mọi module Python và giao diện đọc từ file này.

## 2. Quyết Định Về Kết Quả Thực Nghiệm & Tính Trung Thực Khoa Học
- **Quyết định:** Trung thực tuyệt đối với kết quả nghiên cứu khoa học. DQN/Double DQN trong bài toán chọn toán tử Local Search từ khởi tạo Clarke-Wright tiệm cận sát chất lượng của các heuristics mạnh (Greedy/Cyclic/Random) nhưng có chi phí suy luận lớn hơn.
- **Trưng bày trên giao diện:** Nút/nhãn "Khuyến nghị" trên giao diện tự động chọn phương pháp có kết quả tốt nhất đo được trên kịch bản chạy thật. DQN và Double DQN được trình bày với vai trò phương pháp nghiên cứu so sánh có giải thích học thuật (tại trang Strategy Lab).
- **Tự tay làm dữ liệu (AI Data Engineer):** Không copy dữ liệu tĩnh từ PDF. Toàn bộ số liệu trong `rel_result/` được sinh tự động từ pipeline benchmark 30 instances thật trên đường phố Sài Gòn, tự train weights mạng nơ-ron và tự chạy kiểm định thống kê.

## 3. Quyết Định Hình Học Mạng Lưới Đường (Geometry Discipline - D4)
- **Quyết định:** Sử dụng đồ thị có hướng OSMnx (`network_type="drive"`, giữ nguyên chiều `oneway` và hình học `geometry` của từng cạnh).
- **Cấm đoán:** Cấm tuyệt đối nối đường thẳng Euclid giữa các điểm giao, cấm nội suy toạ độ nhân tạo cắt qua dải phân cách.
- **Snap điểm:** Khoảng cách snap từ toạ độ đơn hàng tới nút giao thông gần nhất tối đa $60\text{ m}$ sử dụng **cKDTree** với tốc độ $< 0.1\text{ ms}$. Nếu vượt quá, hệ thống phát cảnh báo.
- **Kiểm thử hình học:** Tự động kiểm tra tính liên tục của các cạnh trên đồ thị có hướng (0 vi phạm đường một chiều, 5/5 tests PASS).

## 4. Quyết Định Kiến Trúc Thuật Toán & Bài Toán Local Search
- **Bản chất bài toán:** DQN / Double DQN học chọn **toán tử Local Search** (`two_opt`, `intra_relocate`, `inter_relocate`, `inter_swap`) trên nghiệm CVRP khởi tạo từ Clarke-Wright.
- **Bộ đặc trưng:** Chuẩn hóa tập đặc trưng $F28$ (28 chiều) với `feature_patience = 30` độc lập với luật dừng.
- **Q-Network:** PyTorch MLP 2 lớp ẩn ReLU ($28 \to 128 \to 128 \to 4$), $\gamma = 0.95$, Huber Loss, $\epsilon$-greedy giảm dần về $0.05$. Checkpoints được lưu tại `src/cvrp_solver/weights/`.
- **Ràng buộc nhiệt:** Chuyển đổi định luật làm nguội Newton thành ràng buộc thời gian di chuyển tối đa $t_{\max} \approx 30.3\text{ phút}$ từ lúc rời bếp để nhiệt độ khi giao $\ge T_{\min}$ (mặc định $60^\circ\text{C}$).

## 5. Quyết Định Cơ Sở Dữ Liệu & Giao Thức Backend
- **Quyết định:** Sử dụng bộ nhớ đệm nhị phân (pickle) và GeoJSON chuẩn cho ứng dụng. Không bắt buộc Redis/PostGIS để giảm thiểu độ phức tạp môi trường và đảm bảo tính gọn nhẹ độc lập.
- **Cổng mạng:** Frontend cố định cổng `3001`, Backend cố định cổng `8000`. Cấm đụng chạm tới cổng `3000` (được bảo lưu cho ứng dụng riêng của người dùng).
- **Xử lý sự cố:** Nếu DQN gặp ngoại lệ hoặc quá thời gian xử lý (timeout), backend tự động rơi về (fallback) phương pháp Cyclic hoặc OR-Tools và trả về trường `fallback: true` trong API response.

## 6. Quyết Định Loại Bỏ Thành Phần Thừa & Định Dạng Giao Diện
- **Loại bỏ:** Xóa bỏ hoàn toàn game 3D lái xe ô tô (`frontend/src/game`, Three.js, R3F, Rapier physics, Ghost AI, voucher ảo).
- **Thay thế:** Thay bằng màn hình **Search Replay** (trực quan hóa từng bước chọn toán tử của Local Search, đường cong hội tụ hàm mục tiêu và biến thiên tuyến đường theo từng bước chấp nhận).
- **Phong cách UI:** Thiết kế theo mô hình điều phối của **OptimoRoute** (sidebar trái, bảng dữ liệu ở giữa, bản đồ MapLibre bên phải). Sử dụng bảng màu thương hiệu nhận diện `#19100a`, `#c99a4a`, `#f4ede2`, kiểu chữ rõ ràng, không tính từ tiếp thị, không emoji.

## 7. Quyết Định Về Tính Khả Lặp & Bàn Giao Dữ Liệu Thực Nghiệm
- **Pipeline tự động:** 100% dữ liệu có thể tái tạo qua 3 lệnh: `python -m src.benchmark.instance_generator`, `python -m src.rl.train_cvrp_rl`, `python -m src.benchmark.runner`, và `python -m src.benchmark.analysis`.
- **Bản lưu trữ lịch sử:** Toàn bộ bảng số liệu trích xuất từ PDF gốc được lưu trữ cẩn thận tại `rel_result/legacy_pdf_reference/` để phục vụ công tác thanh tra khoa học khi cần đối chiếu.
- **Jupyter Notebook:** Cung cấp notebook `notebooks/cvrp_benchmark.ipynb` tương tác trực tiếp với đồ thị, phân bố khách hàng và kết quả kiểm định thống kê.

## 8. Chuyển Hướng Nghiên Cứu v6.0: Từ CVRP Tĩnh Sang Điều Phối Động & Chọn Đường Thích Nghi
- **Bối cảnh:** Kết quả nghiệm thu E0 xác nhận rằng đối với CVRP tĩnh khởi tạo từ Clarke-Wright, không gian cải thiện chỉ khoảng ~2%, dẫn đến việc tác tử RL (DQN) không có lợi thế vượt trội so với Random/Greedy ($p_{\text{Holm}} = 0,0072$). Hơn nữa, ràng buộc nhiệt độ Newton dựa trên giả định không quan sát được nhiệt độ bếp thực tế.
- **Lựa chọn chuyển hướng:**
  1. Bảo lưu toàn bộ thư mục `rel_result/` làm "Thí nghiệm khởi đầu E0" và minh chứng khoa học cho bước chuyển hướng.
  2. Bỏ hoàn toàn ràng buộc nhiệt độ Newton và câu chủ đạo "để món còn nóng".
  3. Đặt mục tiêu cốt lõi vào **Thời gian chờ của khách hàng ($W_i = t_{\text{giao}, i} - t_{\text{đặt}, i}$)**, độ trễ ETA cam kết, và hệ số Gini công bằng.
- **Phương án bị loại:** Tiếp tục tối ưu siêu tham số trên bài toán CVRP tĩnh chọn toán tử Local Search (bị loại vì bản chất bài toán không có đủ dư địa cho RL tạo đột phá).

## 9. Quyết Định Kiến Trúc GĐ1: Chọn Đường Thích Nghi (Adaptive Routing)
- **Bối cảnh:** Cần một bài toán nền tảng nơi Quy hoạch động (Value Iteration) giải được nghiệm giải tích tối ưu $100\%$ làm thước đo đối chiếu tuyệt đối (Ground Truth).
- **Lựa chọn:** Trích xuất đồ thị con 10–15 nút thực tế từ OpenStreetMap TP.HCM quanh Hàng Gòn Quán (Bình Thạnh) với 3 trạng thái tắc nghẽn (Thông, Chậm, Kẹt) theo mô hình chuyển trạng thái Markov. Đồ thị con được tinh chỉnh bảo đảm tính liên thông mạnh (Strongly Connected Component).
- **Lý do:** Vừa bảo đảm bám sát địa lý thực tế Sài Gòn, vừa bảo đảm tính hội tụ chính xác của Value Iteration.
- **Phương án bị loại:** Đồ thị lưới nhân tạo (bị loại để bám sát bản đồ OSM thực tế).

## 10. Quyết Định Kiến Trúc GĐ2: Điều Phối Đơn Hàng Tại Quán Ăn (Dynamic Restaurant Dispatch)
- **Mô phỏng thời gian:** Áp dụng mô phỏng sự kiện rời rạc (**Event-driven Simulation**). Môi trường nhảy bước trực tiếp đến các thời điểm quyết định (khi tài xế rảnh hoặc có đơn mới khi có tài xế rảnh). Thưởng bước: $r_t = -\Delta t \times n_{\text{undelivered}}(t)$.
- **Lý do:** Tăng tốc độ mô phỏng gấp 20–50 lần so với fixed-tick từng phút, tối ưu hóa triệt để cho môi trường tính toán 2 cores CPU / 3.7GB RAM.
- **Quy tắc xuất phát:** Khi chọn xuất phát với $m$ đơn ($1 \le m \le Q$), áp dụng quy tắc **FIFO** (chọn $m$ đơn có thời gian chờ lâu nhất) kết hợp định tuyến chặng giao bằng **Nearest Insertion** trên ma trận đường bộ có hướng OSMnx. Quy tắc gom cụm địa lý (Spatial Clustering) được kiểm chứng trong phần Ablation Study.
- **Xử lý cuối ca (End-of-Episode):** Áp dụng **Pha xả sạch đơn (Drain Phase)** sau 22:00 (không nhận thêm đơn mới, mô phỏng tiếp tục đến khi toàn bộ đơn được phục vụ). Bảo đảm tổng thưởng Bellman bằng ĐÚNG tổng thời gian chờ của 100% khách hàng với sai số $< 10^{-9}$.

## 11. Các Quyết Định Kỹ Thuật Bổ Sung Cho Hoàn Thiện Cổng G1 (v6.1.0)
1. **Hành động Chờ & Semi-MDP:** Hành động $a=0$ là bước nhảy tới sự kiện kế tiếp với trần thời gian chờ tối đa $\tau_{\max} = 10\text{ phút}$. Mô hình hóa theo Semi-MDP. Đẳng thức Bellman $\sum r_k = -\sum W_i$ được bảo toàn tuyệt đối (sai số $< 10^{-9}$).
2. **Máy trạng thái đơn hàng 5 bước:** `PLACED` $\to$ `COOKING` $\to$ `READY` $\to$ `DELIVERING` $\to$ `DELIVERED`.
3. **Quy tắc gom đơn & Hoán vị định tuyến:** Gom cụm dựa trên detour $\le 1.5\text{ km}$, vét cạn $m! \le 24$ thứ tự giao.
4. **Profile xe máy đô thị:** Tốc độ 32/22/14 km/h; phạt đèn đỏ 25s; phạt rẽ trái 12s; mưa bão $\eta_{\text{rain}} = 1.40$; thùng xe $Q = 4$ đơn.

## 12. Chuyển Hướng Nghiên Cứu v7.0: Tối Ưu Tuyến Đường Đa Tiêu Chí & Thích Nghi (T1 - T2 - T3)
- Trọng tâm chuyển sang **TỐI ƯU TUYẾN ĐƯỜNG (ROUTE OPTIMIZATION)**.
- Kiến trúc phân 3 tầng bài toán:
  - **T1:** Chọn đường đa tiêu chí Pareto giữa 2 điểm (Nhanh nhất, Ngắn nhất, Ổn định nhất, Dễ đi nhất).
  - **T2:** Lập tuyến nhiều điểm VRPTW có tính biến thiên thời gian thực $C(t)$.
  - **T3:** Đổi đường thích nghi khi tắc nghẽn bằng Dynamic Dijkstra (< 1ms).

## 13. Quyết Định Nâng Cấp Neural TSP (Kool et al., 2019) & Fallback Router 3 Lớp (v7.1.0)
- Áp dụng Attention Model của Kool et al. (ICLR 2019) với Transformer Encoder (128-d, 8 heads, 3 layers) kết hợp MHA Pointer Mechanism Decoder.
- Chiến lược dự phòng giao thông 3 lớp (3-Layer Traffic Fallback):
  1. Lớp 1: TomTom Traffic Flow & Route API.
  2. Lớp 2: HERE Routing API khi TomTom chạm quota.
  3. Lớp 3: Ma trận khoảng cách OSRM/OSMnx kết hợp hàm nhân giờ cao điểm $C(t)$.

## 14. Quyết Định Nghiệm Thu Thực Nghiệm v7.3.2: Nạp Trọng Số Kaggle GPU & Chuẩn Hóa Dynamic Isotropic Scaling
- **Bối cảnh:** Sau đợt kiểm toán kỹ thuật v7.3.1, hệ thống đã chuẩn hóa toàn bộ hàm mục tiêu huấn luyện, đồng bộ schema decoder, triệt tiêu hardcode tọa độ cục bộ bằng **Dynamic Isotropic Scaling** chuẩn tỷ lệ 1:1, và hoàn thành 60 epoch huấn luyện trên Kaggle GPU T4 cho cả hai mô hình Attention Model và Pointer Network.
- **Quyết định:**
  1. **Lựa chọn Attention Model làm Mô hình Chủ lực (Champion Core):** Đạt **Optimality Gap +3.27%** so với Google OR-Tools (duration: 225.67m vs 217.78m, distance: 75.63km vs 72.69km), chạy trong **32.63 ms trên CPU** (nhanh hơn OR-Tools **30.7 lần**), tỷ lệ lỗi 0.0%, và bảo đảm tính công bằng địa lý vững chắc (sai số giữa Hà Nội 3.11%, Đà Nẵng 3.48%, TP.HCM 3.32% có độ lệch $< 0.37\%$).
  2. **Định vị Pointer Network làm Baseline phụ:** Train siêu tốc trong 14.8 phút (891s) bằng A2C, đạt Gap +9.27% trong 24.19 ms CPU.
  3. **Định vị Dueling DQN làm Thực nghiệm Phủ định (Ablation Focus):** Tỷ lệ lỗi 50.0% trên $N \ge 30$, minh chứng không thể chối cãi cho giới hạn của không gian hành động rời rạc cố định.
  4. **Chuẩn hóa thư mục mô hình:** Quản lý toàn bộ checkpoint và log tại `notebooks/model_results/attention_tsp/` và `notebooks/model_results/pointer_net/`.
  5. **Bảo toàn 62/62 ca kiểm thử tự động:** Vượt qua toàn bộ kiểm thử hồi quy `pytest tests/` và biên dịch Next.js 14 sạch sẽ trên cổng 3001.
