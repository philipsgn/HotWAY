# Hướng Dẫn Chạy Dự Án HotWAY Localhost Với 1 Lệnh Duy Nhất

Tài liệu hướng dẫn khởi động toàn bộ hệ sinh thái **HotWAY** (Frontend Next.js, Backend FastAPI, PostGIS Database, Redis Cache, RL Model & 3D Game) trên máy tính cá nhân (`localhost`).

---

## ⚡ 1 Lệnh Duy Nhất Để Khởi Chạy Toàn Bộ Hệ Thống (Khuyên Dùng)

Mở terminal (PowerShell hoặc Command Prompt) tại thư mục gốc của dự án `HotWAY` và gõ **duy nhất 1 lệnh**:

```bash
docker compose up --build
```

> [!TIP]
> **Muốn chạy ngầm (chạy trong nền - Background mode)?**  
> Dùng lệnh:
> ```bash
> docker compose up -d --build
> ```

---

## 🌐 Các Đường Dẫn Truy Cập Localhost Sau Khi Chạy

Khi lệnh trên hoàn tất khởi động (khoảng 1 - 2 phút ở lần đầu tiên để build container):

| Phân hệ / Dịch vụ | Địa chỉ truy cập Localhost | Mô tả chức năng |
|---|---|---|
| 🍲 **Trang Đặt Món Khách Hàng** | [http://localhost:3001](http://localhost:3001) | Giao diện tối giản phong cách GrabFood, giỏ hàng Drawer trượt |
| 📱 **Ứng Dụng Tài Xế Shipper PWA** | [http://localhost:3001/shipper](http://localhost:3001/shipper) | Giả lập định vị GPS, đo nhiệt độ món ăn trên đường giao |
| 📊 **Studio Đối Chứng Khoa Học RL** | [http://localhost:3001/admin/comparison-studio](http://localhost:3001/admin/comparison-studio) | So sánh mô hình MaskablePPO với Greedy, Dijkstra, OR-Tools |
| 🎮 **Mini-Game 3D Đua Xe Với AI** | [http://localhost:3001/game/rider](http://localhost:3001/game/rider) | Mô phỏng xe 4 bánh/xe máy 3D chạy đua với AI Ghost Car |
| 📖 **Tài Liệu Swagger API Backend** | [http://localhost:8000/docs](http://localhost:8000/docs) | Kiểm tra trực tiếp các REST API, WebSocket & Schemas |
| 🗄️ **Cơ Sở Dữ Liệu PostGIS** | `localhost:5432` | User: `hotway_user`, Pass: `hotway_secret`, DB: `hotway` |
| ⚡ **Bộ Nhớ Đệm Redis** | `localhost:6379` | Lưu trữ telemetry định vị thời gian thực |

---

## 🛑 Cách Dừng Hệ Thống (1 Lệnh)

Khi muốn dừng toàn bộ các dịch vụ:

```bash
docker compose down
```

---

## 🛠️ Tùy Chọn Bổ Sung: Chạy Bằng File Script 1-Click

Để tiện hơn nữa, bạn có thể chạy trực tiếp file script tạo sẵn trong thư mục dự án:

### Trên Windows (Command Prompt hoặc PowerShell):
```powershell
.\run.bat
```
*hoặc nhấp đúp (double-click) chuột trực tiếp vào file [run.bat](file:///c:/Users/TanPhat/Documents/AI_E/HotWAY/run.bat).*

---

## 🔍 Kiểm Tra Trạng Thái & Log Dịch Vụ

- **Xem trạng thái các container:**
  ```bash
  docker compose ps
  ```
- **Xem log thời gian thực của Backend:**
  ```bash
  docker compose logs -f backend
  ```
- **Xem log thời gian thực của Frontend:**
  ```bash
  docker compose logs -f frontend
  ```
