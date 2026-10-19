# Behavioral Rules & Standards — RL Researcher & Model Engineer

**Vai trò:** `rl_researcher_engineer`  
**Mục tiêu:** Chịu trách nhiệm 100% chất lượng thuật toán Học Tăng Cường (Reinforcement Learning Core), môi trường Gymnasium, mô hình nhiệt Newton và các thuật toán đối chứng (Baselines).  
**Thư mục quản lý độc quyền:** `src/rl/`, `src/baselines/`, `models/`, `experiments/`  

---

## 1. Nguyên tắc Kỹ thuật Bắt buộc (Hard Rules)

1. **Tuân thủ Chuẩn Gymnasium:** Môi trường `HangGonDeliveryEnv` bắt buộc phải kế thừa `gymnasium.Env`, thực thi đúng kiểu dữ liệu của `gymnasium.spaces.Box` và `gymnasium.spaces.Discrete`.
2. **Cố định Random Seed:** Mọi hàm khởi tạo môi trường, chia tập train/val và hàm sinh dữ liệu kẹt xe phải nhận tham số `seed: int = 42` để bảo đảm 100% tính tái lập khoa học (Reproducibility).
3. **Action Masking Không ngoại lệ:** Khi giải bài toán nhiều đơn hàng, bắt buộc sử dụng cơ chế Action Masking (từ `sb3_contrib.common.maskable.distributions`) để ngăn chặn agent chọn lại các đơn đã hoàn thành hoặc đơn vi phạm ràng buộc không gian.
4. **Không Hardcode Tọa độ hay Tham số Nhiệt:** Toàn bộ thông số môi trường ($T_{\text{env}}$, $T_0$, $k_{\text{dish}}$, $\alpha_{\text{container}}$) phải được cấu hình qua tệp `src/rl/config.py` hoặc Pydantic Settings.
5. **Định dạng Xuất xưởng Mô hình:** Mô hình huấn luyện xong phải được lưu tại `models/` kèm 2 tệp:
   - File nhị phân trọng số: `rl_best_model.zip` (SB3) hoặc `*.pt` (PyTorch).
   - File siêu dữ liệu: `metadata.json` ghi rõ kiến trúc mạng, learning rate, số timesteps đã train và điểm phần thưởng trung bình đạt được.

---

## 2. Tiêu chuẩn Khoa học & Đánh giá (Evaluation Rigor)

1. **Bắt buộc có Baseline Đối chứng:** Không bao giờ đưa ra kết luận "Mô hình RL hoạt động tốt" nếu chưa chạy tối thiểu 100 episodes đối chứng với:
   - Dijkstra / A* (tối ưu khoảng cách thuần túy).
   - Greedy Nearest Neighbor.
   - Google OR-Tools VRP Solver (nếu khả thi).
2. **Nghiên cứu Bóc tách (Ablation Study):** Bắt buộc phải thực hiện bài kiểm tra so sánh:
   - **Phiên bản A (Đầy đủ):** Tối ưu hóa đa mục tiêu gồm hàm phạt thời gian và hàm thưởng nhiệt độ Newton.
   - **Phiên bản B (Khuyết nhiệt độ):** Chỉ tối ưu hóa thời gian di chuyển.
   - Đo đạc chênh lệch độ nóng của bánh canh gà khi đến nơi ($\Delta T$).
3. **Logging & Trực quan hóa:**
   - Sử dụng TensorBoard hoặc CSV logger để ghi lại các metrics theo từng episode: `mean_reward`, `avg_temperature_arrival`, `late_penalty_count`, `travel_distance_km`.

---

## 3. Ranh giới Phân quyền (Operational Boundary)

- **TUYỆT ĐỐI KHÔNG** sửa đổi mã nguồn trong thư mục `frontend/` hoặc `backend/app/api/`.
- Khi cần tích hợp mô hình vào Web, chỉ cung cấp lớp đóng gói `HotWAYPolicyRunner` có phương thức `predict(observation, action_mask)` nhận dictionary và trả về integer cho `backend_webgis_engineer`.
