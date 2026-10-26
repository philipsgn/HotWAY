# So Sánh Kết Quả & Phân Tích Thực Nghiệm T3 (05_RESULTS_COMPARISON.MD) — HotWAY

> **Tài liệu:** Đánh giá đối soát chính sách Định tuyến thích nghi T3 trên 30 cặp OD chưa từng thấy, kiểm định thống kê Wilcoxon và Báo cáo trung thực kết quả âm tính  
> **Phiên bản:** v7.0.0 (Scientific Integrity & Empirical Evaluation Edition)  
> **Ngày cập nhật:** 25/10/2026  
> **Trạng thái:** Hoàn tất nghiệm thu Cổng G4 (100% số liệu đối soát trực tiếp từ JSON thực nghiệm)  
> **Tài liệu liên quan:** [03_baselines.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/research/03_baselines.md) | [04_training_protocol.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/research/04_training_protocol.md)

---

## 1. Thiết Kế Thực Nghiệm Kiểm Chứng Chính Sách T3

Để đánh giá năng lực thích nghi thời gian thực của tác tử học tăng cường **Edge-Scoring DQN** so với các thuật toán định tuyến kinh điển, hệ thống tiến hành kiểm thử trên **30 cặp OD phân tán hoàn toàn chưa từng thấy trong tập huấn luyện** (`seed=9999`) qua 3 kịch bản vận hành thực tế:
1. **Kịch bản A (Giờ bình thường, đường khô):** Khung giờ 10:00 sáng ($t=600\text{m}$), mật độ giao thông thông thoáng, xác suất sự cố $p=0.00$, thời tiết không mưa.
2. **Kịch bản B (Cao điểm sáng, đường khô):** Khung giờ 8:00 sáng ($t=480\text{m}$), các trục lộ chính chuyển trạng thái kẹt xe theo phân phối Markov cao điểm, xác suất sự cố $p=0.02$.
3. **Kịch bản C (Cao điểm chiều, Mưa bão & Tai nạn):** Khung giờ 17:30 chiều ($t=1050\text{m}$), hệ số cản thời tiết $\eta_{\text{rain}} = 1.40$, xác suất sự cố va chạm đột xuất $p=0.05$.

---

## 2. Bảng Đối Soát Số Liệu Thực Nghiệm Toàn Diện

*Dữ liệu truy xuất trực tiếp từ tệp:* [`results/t3_policy_comparison.json`](file:///c:/Users/Asus/Documents/AI/HotWAY/results/t3_policy_comparison.json)  
*Biểu đồ đối soát trực quan:* [`results/figures/t3_policy_benchmark.png`](file:///c:/Users/Asus/Documents/AI/HotWAY/results/figures/t3_policy_benchmark.png)

| Kịch bản môi trường | Chính sách định tuyến | Thời gian hành trình TB (phút) | Độ lệch chuẩn (phút) | Số lần gặp kẹt xe TB | Tỷ lệ đến đích (%) | Độ trễ ra quyết định (ms) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Kịch bản A**<br>*(Giờ thường, Khô)* | **Static Dijkstra** | $1,19$ | $\pm 0,72$ | $2,03$ | $100\%$ | **$0,31\text{ ms}$** |
| | **Dynamic Dijkstra** | **$1,18$** | $\pm 0,72$ | **$2,03$** | $100\%$ | $0,87\text{ ms}$ |
| | **Edge-Scoring DQN** | $4,98$ | $\pm 6,84$ | $7,00$ | $86,7\%$ | $1,10\text{ ms}$ |
| **Kịch bản B**<br>*(Cao điểm, Khô)* | **Static Dijkstra** | $1,54$ | $\pm 1,10$ | $2,23$ | $100\%$ | **$0,45\text{ ms}$** |
| | **Dynamic Dijkstra** | **$1,54$** | $\pm 1,09$ | **$2,17$** | $100\%$ | $0,98\text{ ms}$ |
| | **Edge-Scoring DQN** | $5,86$ | $\pm 8,38$ | $10,37$ | $80,0\%$ | $2,63\text{ ms}$ |
| **Kịch bản C**<br>*(Cao điểm, Mưa & Sự cố)* | **Static Dijkstra** | $2,13$ | $\pm 1,51$ | $2,10$ | $100\%$ | **$0,32\text{ ms}$** |
| | **Dynamic Dijkstra** | **$2,12$** | $\pm 1,51$ | **$2,00$** | $100\%$ | $0,91\text{ ms}$ |
| | **Edge-Scoring DQN** | $7,17$ | $\pm 9,47$ | $11,10$ | $80,0\%$ | $4,48\text{ ms}$ |

---

## 3. Kiểm Định Ý Nghĩa Thống Kê Wilcoxon (Signed-Rank Test)

Để kiểm chứng tính vững chắc của kết quả, kiểm định phi tham số cặp Wilcoxon được tính toán giữa các chính sách trên cùng 30 tập hành trình:

| Kịch bản thử nghiệm | Cặp kiểm định so sánh | Thống kê $W$ | Trị số $p$-value | Kết luận thống kê ($\alpha = 0.01$) |
|---|---|:---:|:---:|---|
| **Kịch bản A** | **DQN vs Dynamic Dijkstra** | $3.0$ | **$3,38 \times 10^{-3}$** | Có ý nghĩa thống kê ($p < 0.01$): Dynamic Dijkstra vượt trội |
| | **DQN vs Static Dijkstra** | $3.0$ | **$3,85 \times 10^{-3}$** | Có ý nghĩa thống kê ($p < 0.01$): Static Dijkstra vượt trội |
| **Kịch bản B** | **DQN vs Dynamic Dijkstra** | $0.0$ | **$5,28 \times 10^{-4}$** | Có ý nghĩa thống kê ($p < 0.001$): Dynamic Dijkstra vượt trội |
| | **DQN vs Static Dijkstra** | $0.0$ | **$5,28 \times 10^{-4}$** | Có ý nghĩa thống kê ($p < 0.001$): Static Dijkstra vượt trội |
| **Kịch bản C** | **DQN vs Dynamic Dijkstra** | $1.0$ | **$2,25 \times 10^{-3}$** | Có ý nghĩa thống kê ($p < 0.01$): Dynamic Dijkstra vượt trội |
| | **DQN vs Static Dijkstra** | $1.0$ | **$2,25 \times 10^{-3}$** | Có ý nghĩa thống kê ($p < 0.01$): Static Dijkstra vượt trội |

---

## 4. Báo Cáo & Phân Tích Khoa Học Kết Quả Âm Tính (Scientific Integrity)

Theo đúng quy tắc trung thực khoa học của dự án:
> **KẾT QUẢ ÂM TÍNH ĐƯỢC XÁC LẬP RÕ RÀNG:**  
> Tác tử học tăng cường thuần túy không tìm kiếm (Pure End-to-End RL) **THUA** baseline thuật toán kinh điển *"Tính lại Dijkstra tại mỗi nút"* (Dynamic Dijkstra) trên bài toán tìm đường thích nghi.

### Ba nguyên nhân bản chất giải thích kết quả âm tính:
1. **Tính tối ưu toàn cục của thuật toán Dijkstra:** Dijkstra có độ phức tạp thuật toán cực nhỏ $O(|\mathcal{V}| \log |\mathcal{V}| + |\mathcal{E}|)$ trên đồ thị mạng đường bộ, bảo đảm tính cộng dồn chi phí chính xác tuyệt đối từ vị trí hiện tại đến đích mà không có sai số tích lũy.
2. **Sai số xấp xỉ giá trị tích lũy qua nhiều bước (Compounding Value Errors):** Mạng nơ-ron học giá trị $Q(s, e)$ dựa trên vector đặc trưng cục bộ. Trong hành trình kéo dài $15 - 30$ bước rẽ, chỉ cần $1$ bước đưa ra quyết định sai lầm (ví dụ: chọn nhầm nhánh rẽ dẫn vào đường vòng) sẽ khiến xe máy mất thêm nhiều thời gian và gặp nhiều điểm nghẽn hơn ($7,0 - 11,1$ lần kẹt so với $2,0$ lần của Dijkstra).
3. **Hiệu năng thời gian thực:** Thuật toán Dynamic Dijkstra chỉ mất **$0,87 - 0,98\text{ ms}$** để giải lại đường đi ngắn nhất toàn diện, nhanh hơn đáng kể so với việc trích xuất đặc trưng và suy luận qua mạng nơ-ron (**$1,10 - 4,48\text{ ms}$**).

### Đóng góp thực tiễn cho Kiến trúc HotWAY:
Kết quả âm tính này mang giá trị định hướng công nghệ then chốt: **Không nên dùng RL để thay thế Dijkstra trong việc tìm đường đơn thuần**. Thay vào đó, sức mạnh thực sự của mô hình định tuyến thời gian thực HotWAY nằm ở:
* **Tầng T1:** Lọc tập Pareto đa tiêu chí (đánh đổi giữa cự ly, thời gian, và độ an toàn rẽ trái).
* **Tầng T2:** Lập tuyến và phân bổ đội xe VRPTW khung giờ mềm (nơi các solver kết hợp mang lại ưu thế vượt bậc).
* **Tầng T3:** Sử dụng **Dynamic Dijkstra kết hợp quan sát giao thông thời gian thực** làm động cơ đổi đường thích nghi chuẩn mực khi gặp mưa bão hoặc sự cố bất ngờ.
