# Product Requirements Document (PRD) — HotWAY

**Dự án:** HotWAY (Dynamic Thermal-Aware Food Delivery Optimization System)  
**Tổ chức / Đề tài:** Môn học Học Tăng Cường (Reinforcement Learning) & Ứng dụng WebGIS  
**Địa bàn áp dụng:** Quán Bánh Canh Gà Hàng Gòn — Xã Hàng Gòn, TP. Long Khánh, Tỉnh Đồng Nai  
**Phiên bản tài liệu:** v1.0.0  
**Ngày cập nhật:** 2026-10-19  

---

## 1. Giới thiệu & Bối cảnh dự án (Executive Summary)

### 1.1. Bối cảnh bài toán thực tế
Tại các đô thị loại 2 hoặc khu vực bán nông thôn/ngoại thành như **Hàng Gòn (Long Khánh, Đồng Nai)**, hạ tầng giao thông gồm mạng lưới đường hỗn hợp: trục lộ chính (Quốc lộ 56, đường liên xã) xen lẫn đường đất, ngõ hẹp và địa hình dốc nhẹ. Trong bối cảnh này, món ăn đặc sản địa phương như **Bánh Canh Gà Nóng** đòi hỏi tiêu chuẩn chất lượng khắt khe khi giao tận nơi:
- Nước lèo bánh canh gà phải duy trì nhiệt độ tối thiểu **$\ge 60^\circ\text{C}$** khi đến tay khách hàng để giữ trọn vị béo ngọt và hương thơm của thịt gà ta.
- Các ứng dụng giao hàng truyền thống (Grab, ShopeeFood) chủ yếu tối ưu hóa **tổng quãng đường** hoặc **thời gian di chuyển thuần túy** mà không quan tâm đến tính chất nhiệt học của thực phẩm, dẫn đến tình trạng món giao đến nơi bị nguội lạnh, dầu mỡ đông đặc hoặc thời gian chờ đợi trễ giờ cam kết.

### 1.2. Mục tiêu dự án HotWAY
HotWAY là hệ thống điều phối và định tuyến giao hàng động kết hợp công nghệ **Học Tăng Cường (Reinforcement Learning - RL)** và nền tảng **WebGIS trực quan**, giải quyết bài toán biến thể **Dynamic Vehicle Routing Problem with Time Windows and Temperature Decay (DVRP-TW-TD)**:
1. **Bảo toàn độ nóng của món ăn:** Tối đa hóa hàm giá trị nhiệt độ dựa trên **Định luật làm nguội Newton**.
2. **Cân bằng hiệu quả vận hành:** Rút ngắn thời gian giao hàng trung bình, giảm tỷ lệ trễ hạn và tối ưu hóa việc gom đơn (multi-order batching).
3. **Minh chứng khoa học trực quan:** Dashboard tương tác so sánh trực tiếp hiệu quả giữa thuật toán RL với các thuật toán nền tảng (Dijkstra, Greedy Nearest-Neighbor, Google OR-Tools).
4. **Trải nghiệm tương tác sinh động:** Tích hợp mini-game 3D Web (**HotWAY Rider**) cho phép người dùng đua xe máy giao hàng với "bóng ma" (AI Ghost) chạy theo lộ trình được agent RL học được.

---

## 2. Chân dung người dùng (User Personas)

### 2.1. Khách hàng đặt món (Customer)
- **Hồ sơ:** Người dân hoặc du khách tại khu vực Hàng Gòn muốn thưởng thức bánh canh gà nóng sốt tại nhà.
- **Nhu cầu chính:**
  - Chọn món từ menu quán bánh canh gà Hàng Gòn (Bánh canh gà tô đặc biệt, Bánh canh gà đùi, Gỏi gà xé phay, Nước sâm lạnh).
  - Ghim địa chỉ chính xác trên bản đồ số trực quan.
  - Theo dõi shipper di chuyển theo thời gian thực kèm **thước đo nhiệt độ dự kiến của món ăn** (ví dụ: *"Món đang ở mức 68°C, dự kiến giao đến lúc 62°C"*).

### 2.2. Chủ quán / Quản trị viên (Restaurant Dispatcher)
- **Hồ sơ:** Chủ quán bánh canh gà tại Hàng Gòn quản lý đơn và điều phối giao hàng.
- **Nhu cầu chính:**
  - Tiếp nhận đơn đặt hàng mới, quản lý thời gian chuẩn bị món (prep time).
  - Hệ thống tự động gom đơn thông minh và gán cho shipper theo gợi ý của AI.
  - Cho phép chuyển đổi linh hoạt chế độ định tuyến (RL Engine vs Dijkstra/OR-Tools) để đối chứng hiệu quả.

### 2.3. Tài xế giao hàng (Shipper / Driver)
- **Hồ sơ:** Tài xế xe máy hoạt động trong bán kính 7–10 km khu vực Hàng Gòn.
- **Nhu cầu chính:**
  - Sử dụng Web App/PWA nhẹ nhàng trên điện thoại, tự động gửi tọa độ GPS định kỳ.
  - Nhận lộ trình gợi ý thứ tự giao đơn tối ưu hóa độ nóng và tránh đoạn đường hay kẹt/xấu.

### 2.4. Hội đồng đánh giá & Giảng viên Học Tăng Cường (Academic Evaluator)
- **Hồ sơ:** Giảng viên, chuyên gia chấm đề tài nghiên cứu Học Tăng Cường.
- **Nhu cầu chính:**
  - Xem đồ thị hội tụ học tập (learning curves), hàm phần thưởng (reward design), ma trận đánh giá (ablation study).
  - Trải nghiệm Simulation Mode chạy giả lập hàng chục shipper và hàng trăm đơn hàng để kiểm chứng tính bền vững (robustness) và khả năng tổng quát hóa (generalization).

---

## 3. Mô hình toán học & Định luật nhiệt học (Core Mathematical Formulation)

### 3.1. Mô hình suy giảm nhiệt độ (Newton's Law of Cooling)
Nhiệt độ $T(t)$ của món ăn sau thời gian di chuyển $t$ (phút) tuân theo định luật:
$$T(t) = T_{\text{env}} + (T_0 - T_{\text{env}}) \cdot e^{-k \cdot t}$$

Trong đó:
- $T_0$: Nhiệt độ ban đầu của món khi hoàn thành chế biến tại quán ($^\circ\text{C}$).
- $T_{\text{env}}$: Nhiệt độ môi trường bên ngoài ($^\circ\text{C}$), phụ thuộc vào thời điểm giao (ban ngày nắng nóng $34^\circ\text{C}$, chiều mưa $25^\circ\text{C}$).
- $k$: Hệ số tản nhiệt tổng hợp ($\text{min}^{-1}$), được xác định bởi bản chất món ăn và trang bị cách nhiệt:
$$k = k_{\text{dish}} \times \alpha_{\text{container}}$$

#### Bảng thông số hệ số nhiệt độ chuẩn hóa:

| Nhóm thực phẩm | Món tiêu biểu | $T_0$ (°C) | Ngưỡng ngon tối thiểu | $k_{\text{dish}}$ ($\text{min}^{-1}$) |
|---|---|---|---|---|
| **Nước dùng nóng** | Bánh canh gà nóng sốt | $85^\circ\text{C} - 90^\circ\text{C}$ | $\ge 60^\circ\text{C}$ (Dưới $50^\circ\text{C}$ phạt nặng) | $0.038$ |
| **Món khô / Ấm** | Gỏi gà xé, Chả lụa | $55^\circ\text{C} - 60^\circ\text{C}$ | $\ge 45^\circ\text{C}$ | $0.022$ |
| **Đồ uống lạnh** | Nước sâm, Nước mía đá | $5^\circ\text{C} - 8^\circ\text{C}$ | $\le 15^\circ\text{C}$ (ấm lên theo thời gian) | $0.030$ (hướng tăng) |

#### Hệ số vật liệu thùng cách nhiệt ($\alpha_{\text{container}}$):
- **Túi giữ nhiệt bạc có khóa kéo (Thùng chuyên dụng):** $\alpha = 0.50$ (giảm tốc độ nguội 50%).
- **Thùng xốp tiêu chuẩn:** $\alpha = 0.70$.
- **Túi ni-lông treo xe không cách nhiệt:** $\alpha = 1.00$.

### 3.2. Mô hình Hóa Quá trình Quyết định Markov (MDP Formulation)

Hệ thống sử dụng mô hình **Phân cấp (Hierarchical / Decoupled Action Space)**:
- **Agent Cấp cao (High-level MDP):** Ra quyết định lựa chọn đơn hàng kế tiếp cần phục vụ hoặc quyết định gom tuyến.
- **Routing Cấp thấp (Low-level Engine):** Tính toán đường đi vật lý theo mạng lưới đường thực tế của OpenStreetMap thông qua OSRM / A*.

#### Không gian trạng thái (State Space $S_t$):
Mỗi trạng thái $s_t \in \mathcal{S}$ tại thời điểm $t$ bao gồm vector biểu diễn:
$$s_t = \langle p_{\text{shipper}}, \mathcal{O}_{\text{active}}, \tau_{\text{current}}, \mathcal{W}_{\text{env}}, \mathcal{C}_{\text{traffic}} \rangle$$
1. $p_{\text{shipper}} = (\text{lat}, \text{lon}, v)$: Vị trí địa lý và vận tốc hiện tại của shipper.
2. $\mathcal{O}_{\text{active}} = \{o_1, o_2, \dots, o_M\}$: Tập hợp các đơn hàng shipper đang giữ, mỗi đơn $o_i$ có:
   - $p_{\text{dest}}$: Vị trí giao hàng.
   - $T_i(t)$: Nhiệt độ tính toán hiện thời của món.
   - $t_{\text{deadline}}$: Thời hạn giao cam kết của đơn.
   - $k_i$: Hệ số nguội đặc thù của đơn.
3. $\tau_{\text{current}}$: Thời điểm trong ngày (phút tính từ 00:00) phản ánh giờ cao điểm.
4. $\mathcal{W}_{\text{env}}$: Trạng thái thời tiết (Nhiệt độ môi trường $T_{\text{env}}$, trời nắng / mưa).
5. $\mathcal{C}_{\text{traffic}}$: Ma trận/vector trọng số tắc nghẽn trên các tuyến đường trọng điểm xã Hàng Gòn (QL56, đường Suối Tre - Hàng Gòn, các nhánh giao lộ).

#### Không gian hành động (Action Space $A_t$):
$$a_t \in \{1, 2, \dots, M, \text{WAIT}, \text{RETURN\_DEPOT}\}$$
- Chọn đơn hàng $o_i \in \mathcal{O}_{\text{active}}$ để di chuyển tới giao tiếp theo.
- Sử dụng cơ chế **Action Masking** để loại trừ các đơn đã hoàn thành hoặc các hành động không hợp lệ.

#### Hàm phần thưởng (Reward Function $R(s_t, a_t, s_{t+1})$):
Thiết kế hàm thưởng đa mục tiêu hướng tới chất lượng dịch vụ và bảo toàn nhiệt:
$$R = R_{\text{thermal}} + R_{\text{time}} + R_{\text{penalty}}$$

1. **Phần thưởng nhiệt độ ($R_{\text{thermal}}$):**
$$R_{\text{thermal}} = \begin{cases}
+ \beta_1 \cdot \frac{T_{\text{delivered}} - 60}{25} & \text{nếu } T_{\text{delivered}} \ge 60^\circ\text{C} \\
- \beta_2 \cdot (60 - T_{\text{delivered}})^2 & \text{nếu } T_{\text{delivered}} < 60^\circ\text{C}
\end{cases}$$
2. **Thưởng/Phạt thời gian ($R_{\text{time}}$):**
$$R_{\text{time}} = - \lambda \cdot \Delta t_{\text{travel}} + \begin{cases} + \gamma_1 & \text{giao đúng hạn (trước deadline)} \\ - \gamma_2 \cdot (t_{\text{arrival}} - t_{\text{deadline}}) & \text{nếu trễ hạn} \end{cases}$$
3. **Phạt vi phạm và hao phí ($R_{\text{penalty}}$):**
Phạt hành vi đi vòng đường không cần thiết hoặc hủy bỏ đơn không hợp lệ.

---

## 4. Phân chia phạm vi chức năng (Product Scope & Feature Matrix)

### 4.1. Nhóm chức năng cốt lõi (MVP — Bắt buộc phải có)
- [x] **Quản lý Menu & Đặt món cho Quán Hàng Gòn:** Giao diện đặt món đơn giản, chọn món (bánh canh gà nóng, đồ khô, nước), ghim vị trí giao trên bản đồ số Hàng Gòn.
- [x] **Mô hình hóa Mạng lưới Đường OSMnx:** Trích xuất đồ thị đường thực tế khu vực Hàng Gòn (bán kính 6km từ tâm quán) từ OpenStreetMap.
- [x] **Gymnasium Environment:** Môi trường huấn luyện chuẩn OpenAI Gym có tích hợp mô hình nhiệt độ Newton và kẹt xe giờ cao điểm.
- [x] **Bộ thuật toán Đối chứng (Baselines):**
  - Dijkstra / A* (định tuyến đường ngắn nhất).
  - Greedy Nearest-Neighbor (ưu tiên khách gần nhất).
  - Google OR-Tools VRP Solver (tối ưu hóa quy hoạch toán học cổ điển).
- [x] **Agent Học Tăng Cường (RL Core):**
  - Tabular Q-learning (kiểm chứng trên subgraph/lưới mẫu).
  - Deep Q-Network (DQN / Double DQN) cho bài toán 1 shipper đơn lẻ.
  - Proximal Policy Optimization (PPO) với Action Masking cho gom nhiều đơn.
- [x] **Dashboard So sánh Hiệu năng (Academic Benchmark Screen):**
  - Trực quan hóa lộ trình cạnh nhau giữa RL Agent và Dijkstra/OR-Tools.
  - Thống kê định lượng: Nhiệt độ trung bình lúc giao, Tỷ lệ trễ hạn (%), Thời gian hoàn thành episode, Tổng quãng đường (km).
- [x] **Shipper PWA & Live Web Map:** Bản đồ MapLibre GL JS theo dõi vị trí shipper di chuyển và hiển thị nhiệt độ món ăn suy giảm theo thời gian thực.

### 4.2. Nhóm chức năng giá trị gia tăng cao (Nice-to-have)
- [x] **Simulation Mode (Chế độ giả lập số lượng lớn):** Khả năng kích hoạt 5–10 shipper ảo và 30–50 đơn hàng phát sinh ngẫu nhiên để biểu diễn năng lực điều phối của hệ thống tại buổi thuyết trình.
- [x] **Mini-game 3D HotWAY Rider:**
  - Game Web xây dựng bằng Three.js / React Three Fiber + Rapier physics.
  - Người chơi lái xe máy giao hàng trên mô hình 3D dựng từ dữ liệu OSM Hàng Gòn.
  - Chế độ **Ghost AI:** Đua với "bóng ma" xe máy chạy đúng theo lộ trình mà agent RL tối ưu được.
  - Tính điểm theo nhiệt độ tô bánh canh khi về đích; tặng voucher ưu đãi cho người chơi đạt điểm cao.
- [x] **Ablation Study Logging:** Ghi nhận và xuất biểu đồ so sánh: *"Khi tắt phần thưởng nhiệt độ trong hàm reward, điều gì xảy ra với thời gian và nhiệt độ món ăn?"*

### 4.3. Nhóm chức năng TUYỆT ĐỐI KHÔNG LÀM (Out-of-Scope)
Để tập trung tối đa nguồn lực vào phần RL (chiếm 60% công số môn học), hệ thống lược bỏ triệt để:
- ❌ **Không tích hợp cổng thanh toán trực tuyến thật:** Chỉ dùng giả lập COD (tiền mặt khi nhận hàng).
- ❌ **Không làm Marketplace đa nhà hàng:** Chỉ phục vụ duy nhất 1 quán bánh canh gà Hàng Gòn.
- ❌ **Không xây dựng App Native iOS/Android:** Toàn bộ client tài xế chạy trên Web PWA.
- ❌ **Không dùng Unreal Engine / Pixel Streaming:** Mini-game chỉ làm đồ họa Low-poly trên Three.js trình duyệt để tối ưu tài nguyên.
- ❌ **Không kiến trúc Microservices phân tán phức tạp:** Toàn bộ backend gói gọn trong cấu trúc FastAPI Monolith đóng gói bằng Docker Compose.

---

## 5. Yêu cầu phi chức năng (Non-Functional Requirements)

1. **Hiệu năng suy luận (Inference Latency):** Thời gian tính toán hành động của mô hình RL phải nhỏ hơn $50\,\text{ms}$ trên mỗi bước để đảm bảo phản hồi tức thời trên WebSockets.
2. **Độ chính xác bản đồ:** Tọa độ nút giao và đường sá Hàng Gòn bám sát 100% dữ liệu thực tế OpenStreetMap (OSM node ID, độ dài đoạn đường, vận tốc tối đa theo quy chuẩn đường bộ Việt Nam).
3. **Tính tái lập khoa học (Reproducibility):** Toàn bộ seed ngẫu nhiên trong môi trường Gymnasium được cố định để các bài kiểm thử benchmark cho ra kết quả nhất quán.
4. **Khả năng tương thích trình duyệt:** Web client và Mini-game 3D chạy mượt mà trên Google Chrome, Microsoft Edge, Safari hỗ trợ WebGL 2.0 ở tốc độ tối thiểu 30 FPS.
