"""
Build Nationwide Multi-Region Benchmark Dataset (v7.3.0).
Generates 100 Production-Grade Multi-Stop Delivery Itineraries across 3 Major Vietnamese Logistics Clusters:
- Hanoi Cluster: 40 instances (10 N10, 10 N20, 10 N30, 10 N50)
- Da Nang Cluster: 20 instances (5 N10, 5 N20, 5 N30, 5 N50)
- Ho Chi Minh City Cluster: 40 instances (10 N10, 10 N20, 10 N30, 10 N50)
Total: 100 instances.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from env.traffic_tsp_env import compute_traffic_multiplier


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


# ==============================================================================
# 1. POI POOLS FOR 3 REGIONS
# ==============================================================================

HANOI_DEPOT = {
    "id": 0,
    "node_id": "HN_DEPOT",
    "lat": 21.0285,
    "lon": 105.8542,
    "name": "Bưu Điện Trung Tâm Bờ Hồ / Hub Long Biên",
    "address": "75 Đinh Tiên Hoàng, Tràng Tiền, Hoàn Kiếm, Hà Nội"
}

HANOI_POIS = [
    ("HN_01", 21.0333, 105.8500, "Chợ Đồng Xuân, Hoàn Kiếm"),
    ("HN_02", 21.0245, 105.8512, "Vincom Center Bà Triệu, Hai Bà Trưng"),
    ("HN_03", 21.0031, 105.8431, "Bệnh Viện Bạch Mai, Giải Phóng"),
    ("HN_04", 21.0048, 105.8458, "Đại Học Bách Khoa Hà Nội, Đại Cồ Việt"),
    ("HN_05", 21.0368, 105.8347, "Lăng Chủ Tịch Hồ Chí Minh, Ba Đình"),
    ("HN_06", 21.0322, 105.8143, "Lotte Center Hà Nội, 54 Liễu Giai"),
    ("HN_07", 21.0172, 105.7839, "Keangnam Hanoi Landmark Tower, Nam Từ Liêm"),
    ("HN_08", 21.0282, 105.7778, "Bến Xe Mỹ Đình, Phạm Hùng"),
    ("HN_09", 21.0375, 105.7820, "Đại Học Quốc Gia Hà Nội, Cầu Giấy"),
    ("HN_10", 21.0425, 105.8920, "Aeon Mall Long Biên, Cổ Linh"),
    ("HN_11", 21.0267, 105.8411, "Ga Hà Nội, Văn Miếu, Đống Đa"),
    ("HN_12", 21.0160, 105.8430, "Công Viên Thống Nhất, Hai Bà Trưng"),
    ("HN_13", 21.0298, 105.8480, "Bệnh Viện Hữu Nghị Việt Đức, Tràng Thi"),
    ("HN_14", 21.0315, 105.7980, "Công Viên Cầu Giấy, Duy Tân"),
    ("HN_15", 21.0020, 105.8230, "Đại Học Thủy Lợi, Chùa Bộc, Đống Đa"),
    ("HN_16", 20.9850, 105.8670, "Khu Đô Thị Times City, Minh Khai"),
    ("HN_17", 20.9780, 105.8330, "Bến Xe Giáp Bát, Hoàng Mai"),
    ("HN_18", 21.0500, 105.8150, "Hồ Tây - Phủ Tây Hồ, Quảng An"),
    ("HN_19", 21.0220, 105.8010, "Trung Tâm Hội Nghị Quốc Gia, Mễ Trì"),
    ("HN_20", 21.0110, 105.7950, "Big C Thăng Long, Trần Duy Hưng"),
    ("HN_21", 21.0350, 105.8200, "Viện Hàn Lâm KH&CN Việt Nam, Hoàng Quốc Việt"),
    ("HN_22", 21.0480, 105.7900, "Học Viện Kỹ Thuật Quân Sự, Bắc Từ Liêm"),
    ("HN_23", 20.9720, 105.7760, "Khu Đô Thị Văn Quán, Hà Đông"),
    ("HN_24", 20.9800, 105.7920, "Học Viện An Ninh Nhân Dân, Hà Đông"),
    ("HN_25", 21.0380, 105.8650, "Bến Xe Gia Lâm, Long Biên"),
    ("HN_26", 21.0190, 105.8580, "Bệnh Viện Trung Ương Quân Đội 108, Trần Hưng Đạo"),
    ("HN_27", 21.0250, 105.8300, "Văn Miếu - Quốc Tử Giám, Đống Đa"),
    ("HN_28", 21.0070, 105.8150, "Royal City Hà Nội, Nguyễn Trãi"),
    ("HN_29", 21.0140, 105.8270, "Bệnh Viện Đại Học Y Hà Nội, Tôn Thất Tùng"),
    ("HN_30", 21.0450, 105.8400, "Chợ Bưởi, Hoàng Hoa Thám, Tây Hồ"),
    ("HN_31", 21.0300, 105.7600, "Sân Vận Động Quốc Gia Mỹ Đình, Lê Đức Thọ"),
    ("HN_32", 21.0550, 105.8750, "Vincom Plaza Long Biên, Phúc Lợi"),
    ("HN_33", 20.9950, 105.8000, "Đại Học Hà Nội, Nguyễn Trãi, Thanh Xuân"),
    ("HN_34", 21.0080, 105.8500, "Chợ Mơ, Bạch Mai, Hai Bà Trưng"),
    ("HN_35", 21.0390, 105.8050, "Bảo Tàng Dân Tộc Học Việt Nam, Cầu Giấy"),
    ("HN_36", 21.0210, 105.7700, "Kho Hub Shopee Express Nam Từ Liêm"),
    ("HN_37", 21.0150, 105.8380, "Viettel Post Đống Đa, Thái Hà"),
    ("HN_38", 21.0420, 105.8280, "Bệnh Viện Đa Khoa Thu Cúc, Thụy Khuê"),
    ("HN_39", 20.9880, 105.8450, "Khu Đô Thị Linh Đàm, Hoàng Mai"),
    ("HN_40", 21.0270, 105.8360, "Bệnh Viện Đa Khoa Xanh Pôn, Ba Đình"),
    ("HN_41", 21.0050, 105.8350, "Đại Học Kinh Tế Quốc Dân, Trần Đại Nghĩa"),
    ("HN_42", 21.0180, 105.7890, "The Manor Hanoi, Mễ Trì, Nam Từ Liêm"),
    ("HN_43", 21.0490, 105.8350, "Chùa Trấn Quốc, Đường Thanh Niên, Tây Hồ"),
    ("HN_44", 20.9700, 105.7850, "Bưu Điện Hà Đông, Quang Trung, Hà Đông"),
    ("HN_45", 21.0340, 105.7750, "Bệnh Viện 19-8 Bộ Công An, Trần Bình"),
    ("HN_46", 21.0260, 105.8220, "Hồ Đống Đa - Hoàng Cầu, Đống Đa"),
    ("HN_47", 21.0380, 105.8550, "Cầu Long Biên, Hoàn Kiếm - Long Biên"),
    ("HN_48", 21.0120, 105.8650, "Cảng Hà Nội, Bạch Đằng, Hai Bà Trưng"),
    ("HN_49", 21.0000, 105.8550, "Bệnh Viện Thanh Nhàn, Hai Bà Trưng"),
    ("HN_50", 21.0410, 105.7650, "Đại Học Thương Mại, Hồ Tùng Mậu, Cầu Giấy"),
    ("HN_51", 21.0230, 105.8450, "Viện Tim Mạch Quốc Gia, Phương Mai"),
    ("HN_52", 21.0520, 105.8000, "Khu Ngoại Giao Đoàn, Bắc Từ Liêm"),
    ("HN_53", 20.9820, 105.8200, "Đại Học Thăng Long, Kim Giang, Hoàng Mai"),
    ("HN_54", 21.0160, 105.7780, "Sở Giao Thông Vận Tải Hà Nội, Khuất Duy Tiến"),
    ("HN_55", 21.0320, 105.8600, "Bệnh Viện Đa Khoa Tâm Anh, Long Biên"),
]

DANANG_DEPOT = {
    "id": 0,
    "node_id": "DN_DEPOT",
    "lat": 16.0678,
    "lon": 108.2208,
    "name": "Bưu Điện Trung Tâm Đà Nẵng",
    "address": "271 Nguyễn Văn Linh, Vĩnh Trung, Hải Châu, Đà Nẵng"
}

DANANG_POIS = [
    ("DN_01", 16.0610, 108.2235, "Cầu Rồng Đà Nẵng, Hải Châu"),
    ("DN_02", 16.0720, 108.2250, "Cầu Sông Hàn, An Hải Bắc, Sơn Trà"),
    ("DN_03", 16.0685, 108.2160, "Chợ Cồn, Hùng Vương, Hải Châu"),
    ("DN_04", 16.0690, 108.2240, "Chợ Hàn, Trần Phú, Hải Châu"),
    ("DN_05", 16.0715, 108.2380, "Vincom Plaza Ngô Quyền, Sơn Trà"),
    ("DN_06", 16.0590, 108.2460, "Bãi Biển Mỹ Khê, Võ Nguyên Giáp, Sơn Trà"),
    ("DN_07", 16.0730, 108.2140, "Bệnh Viện Đa Khoa Đà Nẵng, Hải Châu"),
    ("DN_08", 16.0780, 108.2210, "Trung Tâm Hành Chính Đà Nẵng, Bạch Đằng"),
    ("DN_09", 16.0420, 108.2220, "Công Viên Châu Á Sun World Danang Wonders, Hải Châu"),
    ("DN_10", 16.0560, 108.1820, "Bến Xe Trung Tâm Đà Nẵng, Cẩm Lệ"),
    ("DN_11", 16.0750, 108.1530, "Đại Học Bách Khoa Đà Nẵng, Liên Chiểu"),
    ("DN_12", 16.1200, 108.2280, "Cảng Tiên Sa Đà Nẵng, Thọ Quang, Sơn Trà"),
    ("DN_13", 16.0350, 108.2480, "Bệnh Viện Phụ Sản - Nhi Đà Nẵng, Ngũ Hành Sơn"),
    ("DN_14", 16.0040, 108.2610, "Danh Thắng Ngũ Hành Sơn, Hòa Hải"),
    ("DN_15", 16.0540, 108.2150, "Sân Bay Quốc Tế Đà Nẵng (Nhà ga T1)"),
    ("DN_16", 16.0640, 108.2120, "Viettel Post Hải Châu, Nguyễn Tri Phương"),
    ("DN_17", 16.0790, 108.2320, "Bưu Điện Sơn Trà, Ngô Quyền"),
    ("DN_18", 16.0320, 108.1960, "Kho Hub Giao Nhận Cẩm Lệ, Hòa Thọ Đông"),
    ("DN_19", 16.0660, 108.2260, "Bảo Tàng Điêu Khắc Chăm, Hải Châu"),
    ("DN_20", 16.0850, 108.1700, "Khu Công Nghiệp Hòa Khánh, Liên Chiểu"),
    ("DN_21", 16.0600, 108.2300, "Cầu Trần Thị Lý, Bắc Mỹ Phú"),
    ("DN_22", 16.0480, 108.2440, "Bãi Tắm T20, Mỹ An, Ngũ Hành Sơn"),
    ("DN_23", 16.0700, 108.2050, "Đại Học Duy Tân, Nguyễn Văn Linh"),
    ("DN_24", 16.0740, 108.1950, "Ga Đà Nẵng, Hải Châu 2"),
    ("DN_25", 16.0820, 108.2100, "Chợ Đống Đa, Lương Ngọc Quyến"),
    ("DN_26", 16.0950, 108.2450, "Bán Đảo Sơn Trà - Chùa Linh Ứng"),
    ("DN_27", 16.0520, 108.2210, "Cung Thể Thao Tiên Sơn, Hải Châu"),
    ("DN_28", 16.0630, 108.1880, "Bệnh Viện Quân Y 17, Nguyễn Phước Nguyên"),
    ("DN_29", 16.0380, 108.2100, "Siêu Thị Mega Market Đà Nẵng, Cách Mạng Tháng 8"),
    ("DN_30", 16.0280, 108.2350, "Đại Học Kinh Tế Đà Nẵng, Ngũ Hành Sơn"),
    ("DN_31", 16.0760, 108.2230, "Khách Sạn Novotel Danang Premier Han River"),
    ("DN_32", 16.0650, 108.2350, "Cầu Thuận Phước, Nại Hiên Đông"),
    ("DN_33", 16.0450, 108.1750, "Đại Học Ngoại Ngữ Đà Nẵng, Cẩm Lệ"),
    ("DN_34", 16.0580, 108.2000, "Công Viên 29 Tháng 3, Điện Biên Phủ"),
    ("DN_35", 16.0880, 108.2200, "Cảng Sông Hàn, Như Nguyệt"),
    ("DN_36", 16.0500, 108.2350, "Khu Biệt Thự Euro Village Đà Nẵng"),
    ("DN_37", 16.0150, 108.2450, "Làng Đá Mỹ Nghệ Non Nước, Hòa Hải"),
    ("DN_38", 16.0800, 108.1600, "Bến Xe Buýt Kim Liên, Liên Chiểu"),
    ("DN_39", 16.0620, 108.2180, "Trường THPT Chuyên Lê Quý Đôn, Hải Châu"),
    ("DN_40", 16.0300, 108.2200, "Chợ Đầu Mối Hòa Cường, Cẩm Lệ"),
    ("DN_41", 16.0710, 108.2280, "Indochina Riverside Mall, Bạch Đằng"),
    ("DN_42", 16.0570, 108.2400, "Bưu Điện Ngũ Hành Sơn, Lê Văn Hiến"),
    ("DN_43", 16.0400, 108.1850, "Cầu Cẩm Lệ, Hòa Thọ Đông"),
    ("DN_44", 16.0900, 108.2500, "Cảng Cá Thọ Quang, Sơn Trà"),
    ("DN_45", 16.0200, 108.2150, "Trung Tâm Hành Chính Huyện Hòa Vang"),
    ("DN_46", 16.0680, 108.1900, "Bệnh Viện Giao Thông Vận Tải Đà Nẵng"),
    ("DN_47", 16.0750, 108.2400, "Bệnh Viện Sơn Trà, Nguyễn Trung Trực"),
    ("DN_48", 16.0490, 108.2250, "Lotte Mart Đà Nẵng, Nại Nam, Hải Châu"),
    ("DN_49", 16.0360, 108.2550, "Bệnh Viện Ung Bướu Đà Nẵng cơ sở 2"),
    ("DN_50", 16.0850, 108.2300, "Chợ Mai, Thọ Quang, Sơn Trà"),
    ("DN_51", 16.0550, 108.1700, "Khu Đô Thị Phước Lý, Hòa Minh"),
    ("DN_52", 16.0630, 108.2050, "Trung Tâm Y Tế Thanh Khê"),
    ("DN_53", 16.0720, 108.1800, "Đại Học Thể Dục Thể Thao Đà Nẵng"),
    ("DN_54", 16.0250, 108.2500, "Trường Đại Học FPT Đà Nẵng, Hòa Hải"),
    ("DN_55", 16.0800, 108.2000, "Cảng Sông Thu, Thanh Khê"),
]

HCMC_DEPOT = {
    "id": 0,
    "node_id": "HCM_DEPOT",
    "lat": 10.8012,
    "lon": 106.7145,
    "name": "Kho Tổng Bưu Điện Sài Gòn / Hàng Xanh Hub",
    "address": "490 Điện Biên Phủ, Phường 21, Bình Thạnh, TP. Hồ Chí Minh"
}

HCMC_POIS = [
    ("HCM_01", 10.7950, 106.7215, "Landmark 81, Vinhomes Central Park, Bình Thạnh"),
    ("HCM_02", 10.7715, 106.7042, "Bitexco Financial Tower, Quận 1"),
    ("HCM_03", 10.7725, 106.6980, "Chợ Bến Thành, Lê Lợi, Quận 1"),
    ("HCM_04", 10.7769, 106.7009, "Nhà Hát Thành Phố, Đồng Khởi, Quận 1"),
    ("HCM_05", 10.7550, 106.6600, "Bệnh Viện Chợ Rẫy, Nguyễn Chí Thanh, Quận 5"),
    ("HCM_06", 10.7520, 106.6530, "Chợ Lớn / Chợ Bình Tây, Tháp Mười, Quận 6"),
    ("HCM_07", 10.7720, 106.6580, "Đại Học Bách Khoa TP.HCM (CS1), Lý Thường Kiệt, Q10"),
    ("HCM_08", 10.7290, 106.7220, "Crescent Mall, Phú Mỹ Hưng, Quận 7"),
    ("HCM_09", 10.8270, 106.7100, "Trung Tâm Thương Mại Gigamall, Phạm Văn Đồng, Thủ Đức"),
    ("HCM_10", 10.8000, 106.6660, "Sân Bay Quốc Tế Tân Sơn Nhất (Ga T1), Tân Bình"),
    ("HCM_11", 10.8520, 106.7720, "Đại Học Sư Phạm Kỹ Thuật TP.HCM, Võ Văn Ngân, Thủ Đức"),
    ("HCM_12", 10.7830, 106.6960, "Dinh Độc Lập, Nam Kỳ Khởi Nghĩa, Quận 1"),
    ("HCM_13", 10.7798, 106.6990, "Nhà Thờ Đức Bà, Công Xã Paris, Quận 1"),
    ("HCM_14", 10.7870, 106.6780, "Bệnh Viện Tai Mũi Họng TP.HCM, Trần Quốc Thảo, Quận 3"),
    ("HCM_15", 10.7630, 106.6820, "Đại Học Sư Phạm TP.HCM, An Dương Vương, Quận 5"),
    ("HCM_16", 10.7570, 106.6750, "Chợ An Đông, An Dương Vương, Quận 5"),
    ("HCM_17", 10.7480, 106.6780, "Bệnh Viện Quận 8, Cao Lỗ, Quận 8"),
    ("HCM_18", 10.7380, 106.7050, "Đại Học Tôn Đức Thắng, Nguyễn Hữu Thọ, Quận 7"),
    ("HCM_19", 10.7600, 106.6950, "Chợ Dân Sinh, Yersin, Quận 1"),
    ("HCM_20", 10.8150, 106.6880, "Công Viên Gia Định, Hoàng Minh Giám, Gò Vấp"),
    ("HCM_21", 10.8380, 106.6650, "Chợ Hạnh Thông Tây, Quang Trung, Gò Vấp"),
    ("HCM_22", 10.8030, 106.6800, "Bệnh Viện Nhân Dân Gia Định, Nơ Trang Long, Bình Thạnh"),
    ("HCM_23", 10.7920, 106.6820, "Chợ Tân Định, Hai Bà Trưng, Quận 1"),
    ("HCM_24", 10.8050, 106.6400, "Khu Công Nghiệp Tân Bình, Tây Thạnh, Tân Phú"),
    ("HCM_25", 10.7880, 106.6350, "Aeon Mall Tân Phú Celadon, Bờ Bao Tân Thắng"),
    ("HCM_26", 10.7650, 106.6670, "Bệnh Viện Đại Học Y Dược TP.HCM, Hồng Bàng, Quận 5"),
    ("HCM_27", 10.7680, 106.6450, "Đầm Sen Park, Lạc Long Quân, Quận 11"),
    ("HCM_28", 10.8120, 106.7130, "Bến Xe Miền Đông (cũ), Đinh Bộ Lĩnh, Bình Thạnh"),
    ("HCM_29", 10.8650, 106.8100, "Bến Xe Miền Đông Mới, Long Bình, TP. Thủ Đức"),
    ("HCM_30", 10.8750, 106.8000, "Đại Học Quốc Gia TP.HCM (Khu Đô Thị ĐHQG), Thủ Đức"),
    ("HCM_31", 10.8450, 106.7900, "Khu Công Nghệ Cao TP.HCM (SHTP), Xa Lộ Hà Nội"),
    ("HCM_32", 10.7900, 106.7350, "Khu Đô Thị Mới Sala, Mai Chí Thọ, TP. Thủ Đức"),
    ("HCM_33", 10.7800, 106.7450, "Đảo Kim Cương, Bình Trưng Tây, TP. Thủ Đức"),
    ("HCM_34", 10.7700, 106.6720, "Vạn Hạnh Mall, Sư Vạn Hạnh, Quận 10"),
    ("HCM_35", 10.7650, 106.6550, "Bệnh Viện Hùng Vương, Lý Thường Kiệt, Quận 5"),
    ("HCM_36", 10.7420, 106.6350, "Bến Xe Miền Tây, Kinh Dương Vương, Bình Tân"),
    ("HCM_37", 10.8250, 106.6300, "Bưu Cục Viettel Post Quận 12, Tô Ký"),
    ("HCM_38", 10.8500, 106.6450, "Công Viên Phần Mềm Quang Trung, Quận 12"),
    ("HCM_39", 10.7980, 106.6950, "Thảo Cầm Viên Sài Gòn, Nguyễn Bỉnh Khiêm, Quận 1"),
    ("HCM_40", 10.7850, 106.7100, "Cầu Ba Son (Thủ Thiêm 2), Tôn Đức Thắng"),
    ("HCM_41", 10.7930, 106.7020, "Đài Truyền Hình TP.HCM (HTV), Nguyễn Thị Minh Khai"),
    ("HCM_42", 10.8080, 106.7000, "Chợ Bà Chiểu, Bạch Đằng, Bình Thạnh"),
    ("HCM_43", 10.8300, 106.6850, "Đại Học Công Nghiệp TP.HCM, Nguyễn Văn Bảo, Gò Vấp"),
    ("HCM_44", 10.7820, 106.6600, "Công Viên Lê Thị Riêng, Cách Mạng Tháng 8, Quận 10"),
    ("HCM_45", 10.7580, 106.7150, "Bến Nhà Rồng / Bảo Tàng Hồ Chí Minh, Nguyễn Tất Thành, Q4"),
    ("HCM_46", 10.7320, 106.7150, "Trung Tâm Triển Lãm SECC, Nguyễn Văn Linh, Quận 7"),
    ("HCM_47", 10.8200, 106.7400, "Chợ Thủ Đức, Kha Vạn Cân, TP. Thủ Đức"),
    ("HCM_48", 10.7900, 106.6700, "Chợ Phú Nhuận, Phan Đình Phùng, Phú Nhuận"),
    ("HCM_49", 10.7750, 106.6850, "Bệnh Viện Mắt TP.HCM, Bà Huyện Thanh Quan, Quận 3"),
    ("HCM_50", 10.8100, 106.6500, "Chợ Hoàng Hoa Thám, Tân Bình"),
    ("HCM_51", 10.8350, 106.7550, "Chợ Đầu Mối Nông Sản Thủ Đức, Hiệp Bình Phước"),
    ("HCM_52", 10.7680, 106.6880, "Bưu Điện Trung Tâm Bến Nghé, Hai Bà Trưng, Quận 1"),
    ("HCM_53", 10.7450, 106.6500, "Bệnh Viện Triều An, Kinh Dương Vương, Bình Tân"),
    ("HCM_54", 10.8040, 106.7200, "Văn Thánh Park, Điện Biên Phủ, Bình Thạnh"),
    ("HCM_55", 10.7600, 106.6620, "Đại Học Y Dược TP.HCM, Trần Hưng Đạo, Quận 5"),
]


def generate_matrices(
    coords: List[Tuple[float, float]],
    departure_hour: float,
    tortuosity: float = 1.32,
    base_speed_kmh: float = 26.0
) -> Tuple[List[List[float]], List[List[float]]]:
    n = len(coords)
    dist_matrix = [[0.0] * n for _ in range(n)]
    duration_matrix = [[0.0] * n for _ in range(n)]
    
    traffic_factor = compute_traffic_multiplier(departure_hour)

    for i in range(n):
        lat1, lon1 = coords[i]
        for j in range(n):
            if i == j:
                continue
            lat2, lon2 = coords[j]
            # Haversine with street tortuosity
            d_km = haversine_km(lat1, lon1, lat2, lon2) * tortuosity
            dist_matrix[i][j] = round(d_km, 3)

            # Travel time in minutes
            dur_min = (d_km / base_speed_kmh) * 60.0 * traffic_factor
            duration_matrix[i][j] = round(dur_min, 2)

    return dist_matrix, duration_matrix


def generate_region_instances(
    region_code: str,
    region_name: str,
    depot_dict: Dict[str, Any],
    poi_pool: List[Tuple[str, float, float, str]],
    tier_counts: Dict[str, int],
    seed: int
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    instances = []

    hours_pool = [8.0, 8.25, 9.5, 11.5, 12.0, 14.0, 15.5, 17.25, 17.75, 18.5, 20.0]

    for tier, count in tier_counts.items():
        n_stops = int(tier[1:])  # N10 -> 10
        for i in range(1, count + 1):
            inst_id = f"{region_code}_PROD_{tier}_{i:02d}"
            dep_hour = rng.choice(hours_pool)

            # Sample n_stops from POI pool (with replacement if n_stops > len(poi_pool))
            if n_stops <= len(poi_pool):
                sampled = rng.sample(poi_pool, n_stops)
            else:
                sampled = rng.sample(poi_pool, len(poi_pool))
                while len(sampled) < n_stops:
                    sampled.append(rng.choice(poi_pool))

            stops = []
            for idx, (p_id, lat, lon, name) in enumerate(sampled, 1):
                # Add minor jitter for repeated nodes to ensure realistic distinct dropoffs
                lat_jitter = lat + (rng.random() - 0.5) * 0.0008
                lon_jitter = lon + (rng.random() - 0.5) * 0.0008
                stops.append({
                    "id": idx,
                    "node_id": f"{p_id}_{idx:02d}",
                    "lat": round(lat_jitter, 6),
                    "lon": round(lon_jitter, 6),
                    "name": name,
                    "region": region_name
                })

            # Full coordinate sequence: 0 is depot, 1..n are stops
            all_coords = [(depot_dict["lat"], depot_dict["lon"])] + [(s["lat"], s["lon"]) for s in stops]
            dist_matrix, dur_matrix = generate_matrices(all_coords, dep_hour)

            depot_entry = {
                "id": 0,
                "node_id": depot_dict["node_id"],
                "lat": depot_dict["lat"],
                "lon": depot_dict["lon"],
                "name": depot_dict["name"],
                "address": depot_dict["address"],
                "region": region_name
            }

            inst_dict = {
                "instance_id": inst_id,
                "region": region_name,
                "region_code": region_code,
                "tier": tier,
                "num_stops": n_stops,
                "depot": depot_entry,
                "stops": stops,
                "matrix_indices": list(range(n_stops + 1)),
                "departure_hour": dep_hour,
                "dist_matrix_km": dist_matrix,
                "duration_matrix_min": dur_matrix
            }
            instances.append(inst_dict)

    return instances


def main():
    print("Building Nationwide Multi-Region Benchmark Dataset (Hanoi 40, Da Nang 20, HCMC 40)...")

    # Seed 2026 for complete scientific reproducibility
    seed = 2026

    # 1. Hanoi: 40 instances (10 N10, 10 N20, 10 N30, 10 N50)
    hn_instances = generate_region_instances(
        region_code="HN",
        region_name="Hà Nội",
        depot_dict=HANOI_DEPOT,
        poi_pool=HANOI_POIS,
        tier_counts={"N10": 10, "N20": 10, "N30": 10, "N50": 10},
        seed=seed + 1
    )

    # 2. Da Nang: 20 instances (5 N10, 5 N20, 5 N30, 5 N50)
    dn_instances = generate_region_instances(
        region_code="DN",
        region_name="Đà Nẵng",
        depot_dict=DANANG_DEPOT,
        poi_pool=DANANG_POIS,
        tier_counts={"N10": 5, "N20": 5, "N30": 5, "N50": 5},
        seed=seed + 2
    )

    # 3. HCMC: 40 instances (10 N10, 10 N20, 10 N30, 10 N50)
    hcm_instances = generate_region_instances(
        region_code="HCM",
        region_name="TP. Hồ Chí Minh",
        depot_dict=HCMC_DEPOT,
        poi_pool=HCMC_POIS,
        tier_counts={"N10": 10, "N20": 10, "N30": 10, "N50": 10},
        seed=seed + 3
    )

    all_instances = hn_instances + dn_instances + hcm_instances
    print(f"Total instances generated: {len(all_instances)}")
    assert len(all_instances) == 100, f"Expected 100 instances, got {len(all_instances)}"

    dataset = {
        "metadata": {
            "description": "100 Production-Grade Multi-Stop Delivery Itineraries across 3 Major Vietnamese Logistics Hubs (Hanoi 40, Da Nang 20, HCMC 40)",
            "total_instances": 100,
            "regional_distribution": {
                "Hanoi": 40,
                "Da Nang": 20,
                "Ho Chi Minh City": 40
            },
            "tiers": {
                "N10": 25,
                "N20": 25,
                "N30": 25,
                "N50": 25
            },
            "traffic_context": "Empirical urban congestion multiplier C(t) calibrated for Vietnamese peak hours",
            "logistics_profile": "Motorbike urban courier (VNPost, Viettel Post, SPX Express, J&T)",
            "seed": seed,
            "version": "7.3.0-nationwide-production"
        },
        "instances": all_instances
    }

    out_path = Path("data/benchmark_100_vietnam_pois.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Saved dataset to {out_path} ({round(out_path.stat().st_size / (1024*1024), 2)} MB)")

    # Also copy to frontend/public/data
    fe_path = Path("frontend/public/data/benchmark_100_vietnam_pois.json")
    fe_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fe_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Synced dataset to {fe_path}")


if __name__ == "__main__":
    main()
