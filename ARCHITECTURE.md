# Bản Thiết Kế Kiến Trúc Hệ Thống (ARCHITECTURE.MD) — HotWAY

> **Tài liệu:** Thiết kế kiến trúc tổng thể, phân rã module, luồng dữ liệu & kiểm định chất lượng  
> **Phiên bản:** v7.3.0 (Nationwide Multi-Region Logistics Hub Benchmark Edition)  
> **Ngày cập nhật:** 29/10/2026  
> **Tài liệu liên quan:** [PRD.md](file:///c:/Users/Asus/Documents/AI/HotWAY/PRD.md) | [ALGORITHM.md](file:///c:/Users/Asus/Documents/AI/HotWAY/ALGORITHM.md) | [DECISIONS.md](file:///c:/Users/Asus/Documents/AI/HotWAY/docs/DECISIONS.md)

---

## 1. Sơ Đồ Khối Kiến Trúc Tổng Thể

```mermaid
flowchart TD
    subgraph S1["Tầng Dữ Liệu Địa Lý Toàn Quốc (data/)"]
        Bench["data/benchmark_100_vietnam_pois.json\n(100 hành trình Logistics: HN 40, ĐN 20, HCM 40)"]
        UrbanGraph["data/urban_routing_subgraph.pickle\n(12 nút SCC liên thông mạnh trích xuất từ OSM)"]
        MatPre["Precomputed Matrices (.npz)\n(Ma trận cự ly & thời gian di chuyển chuẩn hóa)"]
    end

    subgraph S2["Môi Trường Mô Phỏng Gymnasium (env/ & src/envs/)"]
        T_TSP["env/traffic_tsp_env.py\n(TD-TSP với C(t) theo giờ cao điểm đô thị VN & Action Masking)"]
        R_Env["src/envs/routing_env.py\n(Định tuyến ngẫu nhiên A->B trên đồ thị con)"]
        D_Env["src/envs/dispatch_env.py\n(Semi-MDP hàng đợi đơn hàng, tích phân Lebesgue)"]
        
        Bench --> T_TSP
        UrbanGraph --> R_Env
        MatPre --> D_Env
    end

    subgraph S3["Tầng Thuật Toán & 4 Mô Hình Đối Đầu (models/)"]
        ORTools["models/ortools_solver.py\n(Google OR-Tools Guided Local Search - 0.0% Gap Chuẩn công nghiệp)"]
        AM["models/attention_model.py\n(Graph Attention Transformer Kool et al. - Phục vụ CPU < 20ms)"]
        PtrNet["models/pointer_net.py\n(Pointer Network Bi-LSTM + A2C)"]
        DQN["models/dqn_agent.py\n(Dueling DQN Masked - Bóc tách 4 điểm nghẽn tử huyệt)"]
        
        T_TSP --> ORTools
        T_TSP --> AM
        T_TSP --> PtrNet
        T_TSP --> DQN
    end

    subgraph S4["Tầng Đánh Giá, Kiểm Định & Phục Vụ API"]
        BenchEval["evaluate_benchmark.py\n(Đánh giá toàn diện 100 POI, xuất CSV & JSON)"]
        Fallback["services/fallback_router.py\n(Hạ tầng dự phòng 3 lớp: TomTom -> HERE -> Offline C(t))"]
        FastAPI["backend/app/ & api/main.py\n(FastAPI Server Cổng 8000)"]
        NextUI["frontend/ Next.js 14 WebGIS\n(Executive Monochromatic Cổng 3001)"]
        
        ORTools & AM & PtrNet & DQN --> BenchEval
        BenchEval --> Results["results/benchmark_summary_table.csv\nresults/benchmark_multi_model_results.json"]
        Results --> NextUI
        Fallback --> FastAPI
        FastAPI --> NextUI
    end
```

---

## 2. Phân Tầng Dữ Liệu & Hợp Đồng Giao Tiếp

### 2.1. Bộ Dữ Liệu 100 POI Logistics Toàn Quốc
- File: `data/benchmark_100_vietnam_pois.json`
- Phân bố:
  - Hà Nội: 40 hành trình (10 N10, 10 N20, 10 N30, 10 N50) với Depot Bưu điện Bờ Hồ / Hub Long Biên.
  - Đà Nẵng: 20 hành trình (5 N10, 5 N20, 5 N30, 5 N50) với Depot Bưu điện Trung tâm Đà Nẵng.
  - TP. Hồ Chí Minh: 40 hành trình (10 N10, 10 N20, 10 N30, 10 N50) với Depot Bưu điện Sài Gòn / Hàng Xanh Hub.
- Mỗi hành trình chứa tọa độ địa lý thực, ma trận cự ly thực tế có tính độ uốn lượn đường phố đô thị (tortuosity 1.32x) và ma trận thời gian di chuyển phụ thuộc giờ khởi hành thông qua hàm kẹt xe thực nghiệm $C(t)$.

### 2.2. Kết Quả Đo Đạc Thực Nghiệm Trên CPU (`results/benchmark_summary_table.csv`)
| Mô hình | Thời gian (phút) | Cự ly (km) | Optimality Gap (%) | Độ trễ CPU (ms) | Lỗi Zero-Shot (%) | Số tham số | Checkpoint |
|---|---|---|---|---|---|---|---|
| **Google OR-Tools** | 323.17 | 72.66 | 0.0% | 1001.48 | 0.0% | N/A (C++) | 0.0 MB |
| **Attention Model (AM)** | 705.77 | 156.60 | 108.77% | **14.13** | **0.0%** | 202,752 | **0.786 MB** |
| **Pointer Network (A2C)** | 834.59 | 184.93 | 137.08% | 8.63 | 0.0% | 281,601 | 0.0 MB |
| **Dueling DQN (Masked)** | 931.99 | 138.20 | 170.63% | 6.01 | **50.0%** | 310,934 | 0.0 MB |

---

## 3. Kỷ Luật Cổng Mạng & Môi Trường
- **Cổng 8000:** FastAPI Backend (`api/main.py` và `backend/app/main.py`).
- **Cổng 3001:** Next.js 14 Frontend WebGIS.
- **Cổng 3000:** Tuyệt đối cấm sử dụng nhằm bảo vệ cổng mặc định của hệ thống.
- **Môi trường:** Python 3.13, PyTorch CPU, OR-Tools, Next.js 14 (Node.js).
