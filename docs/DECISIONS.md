# BẢN GHI QUYẾT ĐỊNH THIẾT KẾ & KIẾN TRÚC (DECISIONS.MD) — HotWAY

> **Phiên bản:** v5.0.0 (Production Multi-Region & Live Benchmark Edition)  
> **Ngày cập nhật:** 21/10/2026  

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
