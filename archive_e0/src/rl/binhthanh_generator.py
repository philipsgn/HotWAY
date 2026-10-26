"""
HotWAY Bình Thạnh Road Network & AI Ghost Trajectory Generator
Generates realistic 3.5km graph, GeoJSON roads/buildings, and ghost trajectory
for Quán Bánh Canh Gà 490 Điện Biên Phủ, Phường 21, Quận Bình Thạnh, TP.HCM.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple
import networkx as nx

DEPOT_LAT: float = 10.8012
DEPOT_LON: float = 106.7145
DEPOT_NAME: str = "Quán Bánh Canh Gà 490 Điện Biên Phủ"
DEPOT_ID: str = "depot_binhthanh_0"

EARTH_RADIUS_METERS: float = 6371000.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return EARTH_RADIUS_METERS * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def build_binhthanh_graph() -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    G.graph["name"] = "BinhThanh_RoadNetwork_Realistic"
    G.graph["crs"] = "EPSG:4326"

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Tuple[str, str, Dict[str, Any]]] = []

    # 1. Depot at 490 Điện Biên Phủ
    nodes[DEPOT_ID] = {
        "y": DEPOT_LAT,
        "x": DEPOT_LON,
        "name": DEPOT_NAME,
        "is_depot": True,
    }

    # 2. Main Corridor: Đường Điện Biên Phủ (12 nodes from Cầu Thị Nghè to Cầu Sài Gòn)
    # Span from (10.7930, 106.7020) to (10.7965, 106.7230)
    dbp_nodes = [
        ("dbp_00", 10.7930, 106.7020, "Ngã tư Điện Biên Phủ - Đinh Tiên Hoàng", "primary"),
        ("dbp_01", 10.7950, 106.7040, "Cầu Điện Biên Phủ / Kênh Nhiêu Lộc", "primary"),
        ("dbp_02", 10.7970, 106.7065, "Điện Biên Phủ - Nguyễn Cửu Vân", "primary"),
        ("dbp_03", 10.7985, 106.7085, "Cầu Văn Thánh Tây", "primary"),
        ("dbp_04", 10.8000, 106.7100, "Điện Biên Phủ - Phan Chu Trinh", "primary"),
        ("dbp_05", 10.8018, 106.7118, "Vòng Xoay Ngã Tư Hàng Xanh (Điểm Kẹt Xe)", "primary"),
        ("dbp_06", 10.8015, 106.7135, "Điện Biên Phủ - Đối diện HUTECH", "primary"),
        ("dbp_07", 10.8010, 106.7150, "Cổng Quán 490 Điện Biên Phủ", "primary"),
        ("dbp_08", 10.8000, 106.7165, "Điện Biên Phủ - D1 (Nguyễn Văn Thương)", "primary"),
        ("dbp_09", 10.7995, 106.7180, "Pearl Plaza / Điện Biên Phủ - D2 (Nguyễn Gia Trí)", "primary"),
        ("dbp_10", 10.7980, 106.7205, "Cầu Văn Thánh Đông", "primary"),
        ("dbp_11", 10.7965, 106.7230, "Chân Cầu Sài Gòn", "primary"),
    ]

    for nid, lat, lon, name, hw in dbp_nodes:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    for i in range(len(dbp_nodes) - 1):
        u, v = dbp_nodes[i][0], dbp_nodes[i + 1][0]
        edges.append((u, v, {"highway": "primary", "name": "Đường Điện Biên Phủ", "speed_kph": 60.0}))
        edges.append((v, u, {"highway": "primary", "name": "Đường Điện Biên Phủ", "speed_kph": 60.0}))

    # Connect Depot to dbp_07
    edges.append((DEPOT_ID, "dbp_07", {"highway": "residential", "name": "Lối vào Quán 490 Điện Biên Phủ", "speed_kph": 30.0}))
    edges.append(("dbp_07", DEPOT_ID, {"highway": "residential", "name": "Lối vào Quán 490 Điện Biên Phủ", "speed_kph": 30.0}))

    # 3. North-South Arterial: Xô Viết Nghệ Tĩnh (XVNT) through Hàng Xanh (10 nodes)
    xvnt_nodes = [
        ("xvnt_00", 10.7900, 106.7040, "Cầu Thị Nghè 1", "primary"),
        ("xvnt_01", 10.7940, 106.7065, "Chợ Thị Nghè", "primary"),
        ("xvnt_02", 10.7980, 106.7090, "Xô Viết Nghệ Tĩnh - Huỳnh Mẫn Đạt", "primary"),
        # dbp_05 is Hàng Xanh intersection
        ("xvnt_03", 10.8050, 106.7125, "Xô Viết Nghệ Tĩnh - Bạch Đằng", "primary"),
        ("xvnt_04", 10.8080, 106.7130, "Ngã Ba Đài Liệt Sĩ", "primary"),
        ("xvnt_05", 10.8120, 106.7135, "Bến xe Miền Đông cũ - Cổng 1", "primary"),
        ("xvnt_06", 10.8160, 106.7140, "Chân Cầu Bình Triệu 1", "primary"),
    ]

    for nid, lat, lon, name, hw in xvnt_nodes:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    # Connect XVNT south
    edges.append(("xvnt_00", "xvnt_01", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 45.0}))
    edges.append(("xvnt_01", "xvnt_00", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 45.0}))
    edges.append(("xvnt_01", "xvnt_02", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 45.0}))
    edges.append(("xvnt_02", "xvnt_01", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 45.0}))
    edges.append(("xvnt_02", "dbp_05", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("dbp_05", "xvnt_02", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))

    # Connect XVNT north from Hàng Xanh
    edges.append(("dbp_05", "xvnt_03", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_03", "dbp_05", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_03", "xvnt_04", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_04", "xvnt_03", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_04", "xvnt_05", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_05", "xvnt_04", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 40.0}))
    edges.append(("xvnt_05", "xvnt_06", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 50.0}))
    edges.append(("xvnt_06", "xvnt_05", {"highway": "primary", "name": "Đường Xô Viết Nghệ Tĩnh", "speed_kph": 50.0}))

    # 4. Arterial: Đường Bạch Đằng & Phan Đăng Lưu (Westwards to Chợ Bà Chiểu & BV Gia Định)
    west_nodes = [
        ("bd_01", 10.8035, 106.7060, "Bạch Đằng - Huỳnh Đình Hai", "secondary"),
        ("bd_02", 10.8020, 106.7020, "Bạch Đằng - Phan Chu Trinh Tây", "secondary"),
        ("bd_03", 10.8010, 106.6980, "Chợ Bà Chiểu (Ngã 3 Bạch Đằng - Lê Quang Định)", "primary"),
        ("pdl_01", 10.8030, 106.6950, "Bệnh Viện Nhân Dân Gia Định", "primary"),
        ("pdl_02", 10.8050, 106.6920, "Phan Đăng Lưu - Nơ Trang Long", "primary"),
    ]
    for nid, lat, lon, name, hw in west_nodes:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    edges.append(("xvnt_03", "bd_01", {"highway": "secondary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_01", "xvnt_03", {"highway": "secondary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_01", "bd_02", {"highway": "secondary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_02", "bd_01", {"highway": "secondary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_02", "bd_03", {"highway": "primary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_03", "bd_02", {"highway": "primary", "name": "Đường Bạch Đằng", "speed_kph": 40.0}))
    edges.append(("bd_03", "pdl_01", {"highway": "primary", "name": "Đường Phan Đăng Lưu", "speed_kph": 45.0}))
    edges.append(("pdl_01", "bd_03", {"highway": "primary", "name": "Đường Phan Đăng Lưu", "speed_kph": 45.0}))
    edges.append(("pdl_01", "pdl_02", {"highway": "primary", "name": "Đường Phan Đăng Lưu", "speed_kph": 45.0}))
    edges.append(("pdl_02", "pdl_01", {"highway": "primary", "name": "Đường Phan Đăng Lưu", "speed_kph": 45.0}))

    # 5. Smart Congestion Bypass: D2 (Nguyễn Gia Trí) & Ung Văn Khiêm
    # Connects dbp_09 to Ung Văn Khiêm, allowing bypass around Hàng Xanh
    bypass_nodes = [
        ("d2_01", 10.8030, 106.7175, "Nguyễn Gia Trí (D2) - ĐH Giao Thông Vận Tải", "tertiary"),
        ("d2_02", 10.8060, 106.7170, "Nguyễn Gia Trí - Khu Phố Ẩm Thực", "tertiary"),
        ("uvk_01", 10.8080, 106.7165, "Ngã Ba Nguyễn Gia Trí - Ung Văn Khiêm", "secondary"),
        ("uvk_02", 10.8085, 106.7145, "Ung Văn Khiêm - Xô Viết Nghệ Tĩnh (Đài Liệt Sĩ)", "secondary"),
        ("uvk_03", 10.8070, 106.7210, "Ung Văn Khiêm - Cầu Sài Gòn 2 Phụ", "tertiary"),
    ]
    for nid, lat, lon, name, hw in bypass_nodes:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    edges.append(("dbp_09", "d2_01", {"highway": "tertiary", "name": "Đường Nguyễn Gia Trí (D2)", "speed_kph": 35.0}))
    edges.append(("d2_01", "dbp_09", {"highway": "tertiary", "name": "Đường Nguyễn Gia Trí (D2)", "speed_kph": 35.0}))
    edges.append(("d2_01", "d2_02", {"highway": "tertiary", "name": "Đường Nguyễn Gia Trí (D2)", "speed_kph": 35.0}))
    edges.append(("d2_02", "d2_01", {"highway": "tertiary", "name": "Đường Nguyễn Gia Trí (D2)", "speed_kph": 35.0}))
    edges.append(("d2_02", "uvk_01", {"highway": "secondary", "name": "Đường Nguyễn Gia Trí", "speed_kph": 40.0}))
    edges.append(("uvk_01", "d2_02", {"highway": "secondary", "name": "Đường Nguyễn Gia Trí", "speed_kph": 40.0}))
    edges.append(("uvk_01", "uvk_02", {"highway": "secondary", "name": "Đường Ung Văn Khiêm", "speed_kph": 40.0}))
    edges.append(("uvk_02", "uvk_01", {"highway": "secondary", "name": "Đường Ung Văn Khiêm", "speed_kph": 40.0}))
    edges.append(("uvk_02", "xvnt_04", {"highway": "secondary", "name": "Nút giao Ung Văn Khiêm - XVNT", "speed_kph": 35.0}))
    edges.append(("xvnt_04", "uvk_02", {"highway": "secondary", "name": "Nút giao Ung Văn Khiêm - XVNT", "speed_kph": 35.0}))
    edges.append(("uvk_01", "uvk_03", {"highway": "tertiary", "name": "Đường Ung Văn Khiêm", "speed_kph": 40.0}))
    edges.append(("uvk_03", "uvk_01", {"highway": "tertiary", "name": "Đường Ung Văn Khiêm", "speed_kph": 40.0}))

    # 6. Iconic Destination: Nguyễn Hữu Cảnh & Landmark 81 / Vinhomes Central Park
    landmark_nodes = [
        ("nhc_01", 10.7930, 106.7110, "Nguyễn Hữu Cảnh - Cầu Thủ Thiêm 1", "primary"),
        ("nhc_02", 10.7940, 106.7150, "Cổng Vinhomes Central Park Tây", "primary"),
        ("lm81", 10.7950, 106.7215, "Tòa Tháp Landmark 81 (Điểm Giao Hàng Cao Cấp)", "living_street"),
        ("nhc_03", 10.7960, 106.7200, "Nguyễn Hữu Cảnh - Cầu Sài Gòn", "primary"),
    ]
    for nid, lat, lon, name, hw in landmark_nodes:
        nodes[nid] = {"y": lat, "x": lon, "name": name, "is_depot": False}

    edges.append(("dbp_02", "nhc_01", {"highway": "tertiary", "name": "Đường Nguyễn Cửu Vân", "speed_kph": 30.0}))
    edges.append(("nhc_01", "dbp_02", {"highway": "tertiary", "name": "Đường Nguyễn Cửu Vân", "speed_kph": 30.0}))
    edges.append(("nhc_01", "nhc_02", {"highway": "primary", "name": "Đường Nguyễn Hữu Cảnh", "speed_kph": 50.0}))
    edges.append(("nhc_02", "nhc_01", {"highway": "primary", "name": "Đường Nguyễn Hữu Cảnh", "speed_kph": 50.0}))
    edges.append(("nhc_02", "lm81", {"highway": "living_street", "name": "Đường nội khu Vinhomes Central Park", "speed_kph": 25.0}))
    edges.append(("lm81", "nhc_02", {"highway": "living_street", "name": "Đường nội khu Vinhomes Central Park", "speed_kph": 25.0}))
    edges.append(("nhc_02", "nhc_03", {"highway": "primary", "name": "Đường Nguyễn Hữu Cảnh", "speed_kph": 50.0}))
    edges.append(("nhc_03", "nhc_02", {"highway": "primary", "name": "Đường Nguyễn Hữu Cảnh", "speed_kph": 50.0}))
    edges.append(("nhc_03", "dbp_10", {"highway": "tertiary", "name": "Đường nhánh dẫn Cầu Sài Gòn", "speed_kph": 40.0}))
    edges.append(("dbp_10", "nhc_03", {"highway": "tertiary", "name": "Đường nhánh dẫn Cầu Sài Gòn", "speed_kph": 40.0}))
    edges.append(("lm81", "dbp_11", {"highway": "tertiary", "name": "Đường ven sông Sài Gòn", "speed_kph": 35.0}))
    edges.append(("dbp_11", "lm81", {"highway": "tertiary", "name": "Đường ven sông Sài Gòn", "speed_kph": 35.0}))

    # Add all nodes and edges to G
    for nid, data in nodes.items():
        G.add_node(nid, **data)

    for u, v, data in edges:
        u_lat, u_lon = nodes[u]["y"], nodes[u]["x"]
        v_lat, v_lon = nodes[v]["y"], nodes[v]["x"]
        length = round(haversine(u_lat, u_lon, v_lat, v_lon), 2)
        speed = data.get("speed_kph", 40.0)
        fft = round(length / (speed * 1000.0 / 3600.0), 2)
        data["length"] = length
        data["free_flow_time"] = fft
        G.add_edge(u, v, **data)

    return G


def export_binhthanh_data():
    G = build_binhthanh_graph()
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. GraphML
    graphml_path = data_dir / "binhthanh_graph.graphml"
    nx.write_graphml(G, str(graphml_path))
    print(f"Exported GraphML to {graphml_path} ({len(G.nodes)} nodes, {len(G.edges)} edges)")

    # 2. Roads GeoJSON
    road_features = []
    seen = set()
    for u, v, k, d in G.edges(keys=True, data=True):
        pair = tuple(sorted([u, v]))
        if pair in seen:
            continue
        seen.add(pair)
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        road_features.append({
            "type": "Feature",
            "properties": {
                "id": f"road_{u}_{v}",
                "name": d.get("name", "Đường"),
                "highway": d.get("highway", "residential"),
                "speed_kph": d.get("speed_kph", 30.0),
                "length_m": d.get("length", 100.0),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [u_node["x"], u_node["y"]],
                    [v_node["x"], v_node["y"]],
                ],
            },
        })

    roads_fc = {
        "type": "FeatureCollection",
        "name": "binhthanh_roads",
        "features": road_features,
    }
    roads_path = data_dir / "binhthanh_roads.geojson"
    with open(roads_path, "w", encoding="utf-8") as f:
        json.dump(roads_fc, f, indent=2, ensure_ascii=False)
    print(f"Exported Roads GeoJSON to {roads_path} ({len(road_features)} roads)")

    # 3. 3D Buildings GeoJSON (Bình Thạnh Landmarks)
    buildings = [
        (DEPOT_LAT, DEPOT_LON, "Quán Bánh Canh Gà 490 Điện Biên Phủ", "commercial", 12.0, 0.00018),
        (10.8015, 106.7142, "Đại Học HUTECH (Cơ Sở 475A Điện Biên Phủ)", "university", 45.0, 0.00035),
        (10.7995, 106.7170, "Trung Tâm Thương Mại Pearl Plaza", "commercial", 85.0, 0.00045),
        (10.7950, 106.7215, "Tòa Tháp Landmark 81 (Vinhomes)", "skyscraper", 461.0, 0.00060),
        (10.8010, 106.6980, "Chợ Bà Chiểu", "commercial", 15.0, 0.00040),
        (10.8030, 106.6950, "Bệnh Viện Nhân Dân Gia Định", "hospital", 30.0, 0.00040),
        (10.8130, 106.7110, "Bến Xe Miền Đông Cũ", "transport", 20.0, 0.00050),
        (10.8030, 106.7175, "Đại Học Giao Thông Vận Tải TP.HCM", "university", 35.0, 0.00035),
    ]

    building_features = []
    for lat, lon, name, btype, height, sz in buildings:
        building_features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "building": btype,
                "height": height,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [round(lon - sz, 6), round(lat - sz, 6)],
                        [round(lon + sz, 6), round(lat - sz, 6)],
                        [round(lon + sz, 6), round(lat + sz, 6)],
                        [round(lon - sz, 6), round(lat + sz, 6)],
                        [round(lon - sz, 6), round(lat - sz, 6)],
                    ]
                ],
            },
        })

    bldgs_fc = {
        "type": "FeatureCollection",
        "name": "binhthanh_buildings",
        "features": building_features,
    }
    bldgs_path = data_dir / "binhthanh_buildings.geojson"
    with open(bldgs_path, "w", encoding="utf-8") as f:
        json.dump(bldgs_fc, f, indent=2, ensure_ascii=False)
    print(f"Exported Buildings GeoJSON to {bldgs_path} ({len(building_features)} landmarks)")

    # 4. Realistic AI Ghost Replay Trajectory in Bình Thạnh
    # From 490 Điện Biên Phủ to Landmark 81 via Pearl Plaza & Nguyễn Hữu Cảnh
    ghost_traj = {
        "order_id": "ord_binhthanh_sample_01",
        "depot": {"lat": DEPOT_LAT, "lon": DEPOT_LON, "name": DEPOT_NAME},
        "destination": {"lat": 10.7950, "lon": 106.7215, "name": "Landmark 81 / Vinhomes Central Park"},
        "total_time_seconds": 380.0,
        "final_temperature_c": 77.2,
        "route_description": "Lộ trình tối ưu RL: 490 Điện Biên Phủ -> D1 -> D2 Pearl Plaza -> Cầu Văn Thánh Đông -> Nguyễn Hữu Cảnh -> Landmark 81 (Né kẹt xe Hàng Xanh)",
        "waypoints": [
            {"timestamp_offset": 0.0, "lat": DEPOT_LAT, "lon": DEPOT_LON, "speed_kmh": 0.0},
            {"timestamp_offset": 30.0, "lat": 10.8010, "lon": 106.7150, "speed_kmh": 32.0},
            {"timestamp_offset": 60.0, "lat": 10.8000, "lon": 106.7165, "speed_kmh": 38.5},
            {"timestamp_offset": 110.0, "lat": 10.7995, "lon": 106.7180, "speed_kmh": 42.0},
            {"timestamp_offset": 170.0, "lat": 10.7980, "lon": 106.7205, "speed_kmh": 45.0},
            {"timestamp_offset": 230.0, "lat": 10.7960, "lon": 106.7200, "speed_kmh": 35.0},
            {"timestamp_offset": 290.0, "lat": 10.7955, "lon": 106.7208, "speed_kmh": 28.0},
            {"timestamp_offset": 350.0, "lat": 10.7952, "lon": 106.7212, "speed_kmh": 15.0},
            {"timestamp_offset": 380.0, "lat": 10.7950, "lon": 106.7215, "speed_kmh": 0.0},
        ],
    }
    traj_path = Path("experiments/trajectories/best_route_ghost.json")
    traj_path.parent.mkdir(parents=True, exist_ok=True)
    with open(traj_path, "w", encoding="utf-8") as f:
        json.dump(ghost_traj, f, indent=2, ensure_ascii=False)
    print(f"Exported Ghost Trajectory to {traj_path}")


if __name__ == "__main__":
    export_binhthanh_data()
