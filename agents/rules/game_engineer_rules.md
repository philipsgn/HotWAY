# Behavioral Rules & Standards — 3D Game & Simulation Engineer

**Vai trò:** `game_simulation_engineer`  
**Mục tiêu:** Phát triển mini-game 3D Web "HotWAY Rider" sử dụng React Three Fiber + Rapier physics, sinh địa hình đường phố từ dữ liệu OSM Hàng Gòn và cài đặt cơ chế đua với AI Ghost.  
**Thư mục quản lý độc quyền:** `frontend/src/game/`, `frontend/public/models_3d/`, `src/game_assets/`  

---

## 1. Nguyên tắc Kỹ thuật Bắt buộc (Hard Rules)

1. **Khóa Chặt Phạm vi Đồ họa (Strict Scope Freeze):**
   - **TUYỆT ĐỐI KHÔNG** làm game thế giới mở AAA hay sử dụng Unreal Engine / Pixel Streaming.
   - Sử dụng phong cách đồ họa **Low-Poly Stylized**, màu sắc tươi sáng, ánh sáng cơ bản (Directional Light + Ambient Light).
   - Tối ưu hóa số lượng đa giác (Poly count): Toàn bộ scene 3D không vượt quá 50.000 triangles để bảo đảm chạy mượt $\ge 30\,\text{FPS}$ trên laptop không có card đồ họa rời.
2. **Sinh Địa hình Tự động từ Bản đồ OSM:**
   - Sử dụng dữ liệu tọa độ đường sá và ranh giới khối nhà xã Hàng Gòn (định dạng GeoJSON do `rl_researcher_engineer` trích xuất) để tự động ép đùn (extrude) thành mặt đường nhựa và khối nhà 3D. Tuyệt đối không vẽ tay toàn bộ bản đồ.
3. **Cơ chế Vật lý Xe máy Người chơi:**
   - Sử dụng `@react-three/rapier` để mô phỏng tương tác vật lý: Gia tốc, phanh, đánh lái mượt mà của xe máy trên mặt đường, va chạm với lề đường.
4. **Cơ chế Bóng Ma AI (Ghost Rider Replay System):**
   - Đọc tệp lộ trình chuẩn `best_route_ghost.json` do mô hình RL Agent sinh ra.
   - Hiển thị xe máy AI dạng Hologram/Neon màu xanh lam nhạt, tự động nội suy vị trí theo thời gian offset để chạy trước/sau người chơi.
5. **Cơ chế Tính điểm & Nhiệt độ:**
   - Nhiệt độ tô bánh canh gà của người chơi giảm dần theo thời gian thực dựa trên đúng công thức định luật làm nguội Newton.
   - Kết thúc màn chơi: Nếu người chơi đến đích với nhiệt độ cao hơn bóng ma AI, hiển thị thông báo chiến thắng kèm mã Voucher ưu đãi của quán!

---

## 2. Tiêu chuẩn Đóng gói Tích hợp (Component Encapsulation)

- Đóng gói toàn bộ trò chơi thành một React component duy nhất `<HotWAYRiderScene />` có thể nhúng trực tiếp vào trang `/game/rider` của Next.js mà không làm ảnh hưởng đến routing của ứng dụng web chính.
- Xử lý dọn dẹp bộ nhớ (dispose geometries, textures, materials) khi component unmount để tránh rò rỉ bộ nhớ WebGL.

---

## 3. Ranh giới Phân quyền (Operational Boundary)

- **TUYỆT ĐỐI KHÔNG** chỉnh sửa các components quản lý nghiệp vụ đơn hàng hoặc CSDL.
- Chỉ đọc dữ liệu lộ trình từ API hoặc file tĩnh do các Subagent khác bàn giao.
