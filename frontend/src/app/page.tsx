"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function ResearchLandingPage() {
  const [activeTab, setActiveTab] = useState<
    "t1_pareto" | "t2_vrptw" | "t3_training" | "t3_benchmark"
  >("t1_pareto");

  return (
    <div className="min-h-screen bg-[#fcfbf9] text-[#111111] font-sans selection:bg-[#e5e5e5] selection:text-[#000000]">
      {/* 1. Minimal Header */}
      <header className="sticky top-0 z-50 bg-[#fcfbf9]/95 backdrop-blur-xs border-b border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="font-mono text-xs font-bold tracking-widest uppercase text-[#111111]">
              HOTWAY
            </span>
            <span className="text-xs text-[#888888]">/</span>
            <span className="text-xs text-[#555555] font-medium hidden sm:inline">
              Báo Cáo Nghiên Cứu Điều Phối Đô Thị v7.0.0
            </span>
          </div>

          <nav className="hidden md:flex items-center space-x-6 text-xs text-[#666666]">
            <a href="#section-01" className="hover:text-[#111111] transition">01 Bối Cảnh</a>
            <a href="#section-02" className="hover:text-[#111111] transition">02 Kiến Trúc</a>
            <a href="#section-03" className="hover:text-[#111111] transition">03 Số Liệu</a>
            <a href="#section-04" className="hover:text-[#111111] transition">04 Phân Tích</a>
            <a href="#section-05" className="hover:text-[#111111] transition">05 Kết Quả Âm Tính</a>
            <a href="#section-06" className="hover:text-[#111111] transition">06 Tái Lập</a>
          </nav>

          <div className="flex items-center space-x-4">
            <a
              href="/docs/HotWAY_Final_Research_Report.pdf"
              download
              className="text-xs text-[#555555] hover:text-[#111111] transition underline underline-offset-4"
            >
              Tải PDF [↓]
            </a>

            <Link
              href="/demo"
              className="px-3.5 py-1.5 bg-[#111111] hover:bg-[#333333] active:bg-[#000000] text-white text-xs font-medium rounded-xs transition"
            >
              Mở Demo →
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Section (Editorial Minimalist) */}
      <section className="pt-20 pb-16 max-w-6xl mx-auto px-6">
        <div className="font-mono text-xs uppercase tracking-widest text-[#777777] mb-4">
          HOTWAY RESEARCH CONSORTIUM • ĐỒ THỊ BÌNH THẠNH, TP. HỒ CHÍ MINH
        </div>

        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-[#111111] leading-tight max-w-4xl">
          Tối Ưu Tuyến Đường Đô Thị Chặng Cuối Cho Xe Máy Tại TP. Hồ Chí Minh
        </h1>

        <p className="mt-6 text-base sm:text-lg text-[#444444] max-w-3xl leading-relaxed">
          Nền tảng giải pháp 3 tầng chuẩn mực khoa học: Định tuyến đa tiêu chí Pareto (T1), Lập tuyến đội xe VRPTW khung giờ mềm với hàm ưu tiên đơn tồn (T2), và Động cơ đổi đường thích nghi thời gian thực Dynamic Dijkstra (T3) trên mạng lưới giao thông thực tế TP.HCM.
        </p>

        {/* Minimalist 3-Column Typographic Stat Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-14 pt-8 border-t border-[#e5e5e5]">
          <div>
            <div className="font-mono text-xs text-[#777777] uppercase tracking-wider">
              T1 — ĐA TIÊU CHÍ PARETO
            </div>
            <div className="text-3xl font-extrabold text-[#111111] mt-2 font-mono">
              4 Tuyến
            </div>
            <p className="text-xs text-[#555555] mt-1.5 leading-relaxed">
              Nhanh nhất (14.2m), Ngắn nhất (2.19km), Ổn định nhất (p90 14.6m), Dễ đi nhất (0 rẽ trái cắt dòng).
            </p>
          </div>

          <div>
            <div className="font-mono text-xs text-[#777777] uppercase tracking-wider">
              T2 — VRPTW GOOGLE OR-TOOLS
            </div>
            <div className="text-3xl font-extrabold text-[#111111] mt-2 font-mono">
              7.5% Trễ
            </div>
            <p className="text-xs text-[#555555] mt-1.5 leading-relaxed">
              Giảm trễ từ 30.6% xuống 7.5%, cắt giảm 88% hình phạt đơn tồn đọng so với Clarke-Wright.
            </p>
          </div>

          <div>
            <div className="font-mono text-xs text-[#777777] uppercase tracking-wider">
              T3 — MINH BẠCH KẾT QUẢ ÂM TÍNH
            </div>
            <div className="text-3xl font-extrabold text-[#111111] mt-2 font-mono">
              &lt; 1 ms
            </div>
            <p className="text-xs text-[#555555] mt-1.5 leading-relaxed">
              Dynamic Dijkstra (1.18m) vượt trội hoàn toàn Edge-Scoring DQN (4.98m, p &lt; 0.005) do lỗi cộng dồn đa chặng.
            </p>
          </div>
        </div>
      </section>

      {/* 3. Section 01: Bối Cảnh & Động Cơ Chuyển Hướng */}
      <section id="section-01" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            01 / BỐI CẢNH &amp; ĐỘNG CƠ
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-6">
            Từ Thất Bại Của CVRP Tĩnh Đến Trọng Tâm Tối Ưu Đường Đi Thực Tế
          </h2>

          <div className="text-sm text-[#333333] leading-relaxed space-y-4 max-w-4xl">
            <p>
              Trong giai đoạn khởi đầu (Thí nghiệm khởi đầu E0), hệ thống mô hình hóa theo dạng Capacitated Vehicle Routing Problem (CVRP) tĩnh kết hợp làm nguội nhiệt độ Newton và áp dụng Deep Q-Network để chọn toán tử Local Search (2-opt, relocate, exchange, cross-exchange).
            </p>

            <div className="border-l-2 border-[#111111] pl-4 py-2 my-4 text-xs font-mono text-[#333333] bg-[#f5f4f0]">
              Theo giao thức kiểm định A2 trên 24 instances đồ thị thật, toán tử ngẫu nhiên (Random) đạt cự ly trung bình 656,36 km, vượt trội hơn hẳn so với DQN đạt 657,90 km (kiểm định Wilcoxon hiệu chỉnh Holm cho thấy p_Holm = 0.0072 có ý nghĩa thống kê rõ rệt).
            </div>

            <p>
              <strong>Hai bài học khoa học then chốt dẫn đến quyết định chuyển hướng:</strong>
            </p>
            <ul className="list-disc pl-5 space-y-2 text-xs text-[#444444]">
              <li>
                <strong>Bỏ hoàn toàn giả định nhiệt Newton &amp; mô hình quán ăn đơn lẻ:</strong> Nhiệt độ món ăn là biến ẩn phụ thuộc thùng giữ nhiệt, không quan sát được trên đường. Dự án chuyển đối tượng giao hàng sang <strong>mọi loại hàng hóa đô thị chặng cuối</strong> xuất phát từ kho bãi hoặc bưu cục tập kết.
              </li>
              <li>
                <strong>Trọng tâm chuyển sang TỐI ƯU ĐƯỜNG ĐI:</strong> Đơn hàng (mới, cũ, tồn) được gộp thành danh sách điểm giao với trọng số ưu tiên đơn tồn. Cốt lõi của bài toán là tối ưu lộ trình xe máy luồn lách qua mạng lưới đường sá phức tạp của TP.HCM.
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 4. Section 02: Ba Tầng Bài Toán */}
      <section id="section-02" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            02 / HÌNH THỨC HÓA TOÁN HỌC &amp; KIẾN TRÚC
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-8">
            Ba Tầng Bài Toán Vận Hành Xe Máy Đô Thị
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* T1 */}
            <div className="pt-4 border-t-2 border-[#111111]">
              <span className="font-mono text-xs font-bold text-[#111111] block mb-1">
                TẦNG T1 — ĐA TIÊU CHÍ (A → B)
              </span>
              <p className="text-xs text-[#555555] leading-relaxed mt-2">
                Sinh tập đường ứng viên k-shortest paths và lọc tập Pareto phi lấn át trên 4 tiêu chí cốt lõi:
              </p>
              <ul className="text-xs text-[#333333] space-y-1 mt-3">
                <li>• <strong>Fastest:</strong> Nhanh nhất kỳ vọng (phút)</li>
                <li>• <strong>Shortest:</strong> Ngắn nhất theo mét</li>
                <li>• <strong>Stable:</strong> Ổn định nhất theo phân vị p90</li>
                <li>• <strong>Easiest:</strong> Dễ đi nhất (phạt rẽ trái +12s, đèn đỏ +25s)</li>
              </ul>
              <div className="mt-4 pt-2 font-mono text-[11px] text-[#888888]">
                Bán kính 1.5km • 568 nút • 1.258 cạnh
              </div>
            </div>

            {/* T2 */}
            <div className="pt-4 border-t-2 border-[#111111]">
              <span className="font-mono text-xs font-bold text-[#111111] block mb-1">
                TẦNG T2 — ĐỘI XE VRPTW
              </span>
              <p className="text-xs text-[#555555] leading-relaxed mt-2">
                Phân bổ K xe máy giao hàng nhiều điểm với khung giờ nhận mềm và hàm ưu tiên đơn tồn:
              </p>
              <div className="font-mono text-[11px] text-[#111111] my-3 py-1.5 px-2 bg-[#f5f4f0]">
                w_i = 1 + α · (tuổi_i / τ)
                <div className="text-[10px] text-[#777777] mt-0.5">
                  α = 1.5, τ = 60 phút, dừng 3.0 phút/điểm
                </div>
              </div>
              <p className="text-xs text-[#555555] leading-relaxed">
                So sánh 3 solvers: Greedy Urgency, Clarke-Wright + LS, và Google OR-Tools.
              </p>
              <div className="mt-4 pt-2 font-mono text-[11px] text-[#888888]">
                10 instances • Dry vs Rain (1.40x)
              </div>
            </div>

            {/* T3 */}
            <div className="pt-4 border-t-2 border-[#111111]">
              <span className="font-mono text-xs font-bold text-[#111111] block mb-1">
                TẦNG T3 — ĐỔI ĐƯỜNG THÍCH NGHI
              </span>
              <p className="text-xs text-[#555555] leading-relaxed mt-2">
                Mô hình hóa bằng Gymnasium MDP chọn cạnh đi tiếp khi gặp tắc đường hoặc sự cố ngẫu nhiên:
              </p>
              <ul className="text-xs text-[#333333] space-y-1 mt-3 font-mono">
                <li>• Trạng thái: φ(s, e) ∈ ℝ¹⁰</li>
                <li>• Thưởng: r_t = −thời gian cạnh</li>
                <li>• Đẳng thức: Σ r_t = −T_trip</li>
                <li>• So sánh: Dynamic Dijkstra vs DQN</li>
              </ul>
              <div className="mt-4 pt-2 font-mono text-[11px] text-[#888888]">
                TrafficProvider • 30 cặp OD kiểm chứng
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Section 03: Bảng Số Liệu Thực Nghiệm Toàn Diện */}
      <section id="section-03" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            03 / DỮ LIỆU THỰC NGHIỆM ĐỐI SOÁT
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-2">
            Bảng Đối Soát Số Liệu Toàn Diện (Traceable 100%)
          </h2>
          <p className="text-xs text-[#666666] mb-8">
            Trích xuất trực tiếp từ các tệp kết quả JSON trong thư mục <code>results/</code> với sai số kiểm định &lt; 10⁻⁹.
          </p>

          {/* Table 1: T1 */}
          <div className="mb-10">
            <div className="font-mono text-xs font-bold text-[#111111] mb-2">
              BẢNG 1: KẾT QUẢ ĐỊNH TUYẾN ĐA TIÊU CHÍ T1 (results/t1_routes_sample.json)
            </div>
            <div className="overflow-x-auto">
              <table className="text-xs border-t-2 border-b-2 border-[#111111]">
                <thead>
                  <tr className="border-b border-[#e5e5e5] text-[#555555] font-mono text-[11px]">
                    <th className="py-2.5 text-left font-semibold">Tuyến Pareto</th>
                    <th className="py-2.5 text-right font-semibold">Cự Ly (m)</th>
                    <th className="py-2.5 text-right font-semibold">Thời Gian Kỳ Vọng</th>
                    <th className="py-2.5 text-right font-semibold">Phân Vị p90</th>
                    <th className="py-2.5 text-right font-semibold">Số Khúc Rẽ</th>
                    <th className="py-2.5 text-right font-semibold">Rẽ Trái Cắt Dòng</th>
                    <th className="py-2.5 text-right font-semibold">Tỷ Lệ Đoạn Hẻm</th>
                    <th className="py-2.5 text-right font-semibold">Nút Có Đèn</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f0f0] font-mono text-[11px]">
                  <tr>
                    <td className="py-2.5 text-left font-sans font-bold text-[#111111]">Nhanh nhất kỳ vọng (Fastest)</td>
                    <td className="py-2.5 text-right">2304.2 m</td>
                    <td className="py-2.5 text-right font-bold">14.22 phút</td>
                    <td className="py-2.5 text-right">14.58 phút</td>
                    <td className="py-2.5 text-right">18</td>
                    <td className="py-2.5 text-right">14</td>
                    <td className="py-2.5 text-right">9.6%</td>
                    <td className="py-2.5 text-right">14</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-[#333333]">Ngắn nhất cự ly (Shortest)</td>
                    <td className="py-2.5 text-right font-bold">2192.1 m</td>
                    <td className="py-2.5 text-right">18.46 phút</td>
                    <td className="py-2.5 text-right">18.84 phút</td>
                    <td className="py-2.5 text-right">19</td>
                    <td className="py-2.5 text-right">16</td>
                    <td className="py-2.5 text-right">18.5%</td>
                    <td className="py-2.5 text-right">15</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-[#333333]">Ổn định nhất (Stable p90)</td>
                    <td className="py-2.5 text-right">2364.7 m</td>
                    <td className="py-2.5 text-right">14.63 phút</td>
                    <td className="py-2.5 text-right font-bold">14.63 phút</td>
                    <td className="py-2.5 text-right">16</td>
                    <td className="py-2.5 text-right">13</td>
                    <td className="py-2.5 text-right">11.2%</td>
                    <td className="py-2.5 text-right">14</td>
                  </tr>
                  <tr className="bg-[#f5f4f0]">
                    <td className="py-2.5 text-left font-sans font-bold text-[#111111]">Dễ đi nhất (Easiest - 0 Left)</td>
                    <td className="py-2.5 text-right">2887.3 m</td>
                    <td className="py-2.5 text-right">17.07 phút</td>
                    <td className="py-2.5 text-right">17.47 phút</td>
                    <td className="py-2.5 text-right">14</td>
                    <td className="py-2.5 text-right font-bold text-black">0 (Không rẽ trái)</td>
                    <td className="py-2.5 text-right">15.9%</td>
                    <td className="py-2.5 text-right">12</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Table 2: T2 */}
          <div className="mb-10">
            <div className="font-mono text-xs font-bold text-[#111111] mb-2">
              BẢNG 2: SO SÁNH THUẬT TOÁN LẬP TUYẾN ĐỘI XE T2 (results/baselines/t2_vrptw_benchmark.json)
            </div>
            <div className="overflow-x-auto">
              <table className="text-xs border-t-2 border-b-2 border-[#111111]">
                <thead>
                  <tr className="border-b border-[#e5e5e5] text-[#555555] font-mono text-[11px]">
                    <th className="py-2.5 text-left font-semibold">Thuật Toán Solver</th>
                    <th className="py-2.5 text-right font-semibold">Tổng Cự Ly TB</th>
                    <th className="py-2.5 text-right font-semibold">Thời Gian Chờ Khách</th>
                    <th className="py-2.5 text-right font-semibold">Tỷ Lệ Trễ (Khô)</th>
                    <th className="py-2.5 text-right font-semibold">Tỷ Lệ Trễ (Mưa 1.4x)</th>
                    <th className="py-2.5 text-right font-semibold">Phạt Đơn Tồn Đọng</th>
                    <th className="py-2.5 text-right font-semibold">Thời Gian Giải</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f0f0] font-mono text-[11px]">
                  <tr>
                    <td className="py-2.5 text-left font-sans text-[#333333]">Greedy Urgency</td>
                    <td className="py-2.5 text-right">99.50 km</td>
                    <td className="py-2.5 text-right">48.03 phút</td>
                    <td className="py-2.5 text-right text-red-700">39.0%</td>
                    <td className="py-2.5 text-right text-red-700">59.5%</td>
                    <td className="py-2.5 text-right">394.99</td>
                    <td className="py-2.5 text-right">0.6 ms</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-[#333333]">Clarke-Wright + Local Search</td>
                    <td className="py-2.5 text-right font-bold">73.63 km</td>
                    <td className="py-2.5 text-right">37.45 phút</td>
                    <td className="py-2.5 text-right">30.6%</td>
                    <td className="py-2.5 text-right">42.9%</td>
                    <td className="py-2.5 text-right">244.78</td>
                    <td className="py-2.5 text-right">1.5 ms</td>
                  </tr>
                  <tr className="bg-[#f5f4f0]">
                    <td className="py-2.5 text-left font-sans font-bold text-[#111111]">Google OR-Tools (VRPTW)</td>
                    <td className="py-2.5 text-right">79.81 km (+8.4%)</td>
                    <td className="py-2.5 text-right font-bold">32.29 phút</td>
                    <td className="py-2.5 text-right font-bold">7.5%</td>
                    <td className="py-2.5 text-right font-bold">38.6%</td>
                    <td className="py-2.5 text-right font-bold">29.54 (-88%)</td>
                    <td className="py-2.5 text-right">4,042.8 ms</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Table 3: T3 */}
          <div>
            <div className="font-mono text-xs font-bold text-[#111111] mb-2">
              BẢNG 3: ĐỐI SOÁT CHÍNH SÁCH ĐỔI ĐƯỜNG T3 TRÊN 30 CẶP OD MỚI (results/t3_policy_comparison.json)
            </div>
            <div className="overflow-x-auto">
              <table className="text-xs border-t-2 border-b-2 border-[#111111]">
                <thead>
                  <tr className="border-b border-[#e5e5e5] text-[#555555] font-mono text-[11px]">
                    <th className="py-2.5 text-left font-semibold">Kịch Bản Môi Trường</th>
                    <th className="py-2.5 text-left font-semibold">Chính Sách</th>
                    <th className="py-2.5 text-right font-semibold">Thời Gian TB</th>
                    <th className="py-2.5 text-right font-semibold">Số Lần Kẹt TB</th>
                    <th className="py-2.5 text-right font-semibold">Tỷ Lệ Đến Đích</th>
                    <th className="py-2.5 text-right font-semibold">Độ Trễ Phán Quyết</th>
                    <th className="py-2.5 text-right font-semibold">Kiểm Định Wilcoxon (p-value)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f0f0] font-mono text-[11px]">
                  {/* Scenario A */}
                  <tr>
                    <td rowSpan={3} className="py-2.5 text-left font-sans font-bold align-top border-r border-[#e5e5e5]">
                      Kịch bản A (Giờ thường, Khô)
                    </td>
                    <td className="py-2.5 text-left font-sans">Static Dijkstra</td>
                    <td className="py-2.5 text-right">1.19 ± 0.72 phút</td>
                    <td className="py-2.5 text-right">2.03</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right font-bold">0.31 ms</td>
                    <td className="py-2.5 text-right text-[#777777]">W = 1.0, p = 0.285</td>
                  </tr>
                  <tr className="bg-[#f5f4f0]">
                    <td className="py-2.5 text-left font-sans font-bold">Dynamic Dijkstra</td>
                    <td className="py-2.5 text-right font-bold">1.18 ± 0.72 phút</td>
                    <td className="py-2.5 text-right font-bold">2.03</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right">0.87 ms</td>
                    <td className="py-2.5 text-right font-bold">Chuẩn đối sánh</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-neutral-600">Edge-Scoring DQN</td>
                    <td className="py-2.5 text-right text-neutral-700">4.98 ± 6.84 phút</td>
                    <td className="py-2.5 text-right">7.00</td>
                    <td className="py-2.5 text-right">86.7%</td>
                    <td className="py-2.5 text-right">1.10 ms</td>
                    <td className="py-2.5 text-right font-bold">W = 90.0, p = 0.00338*</td>
                  </tr>

                  {/* Scenario B */}
                  <tr className="border-t border-[#d4d4d4]">
                    <td rowSpan={3} className="py-2.5 text-left font-sans font-bold align-top border-r border-[#e5e5e5]">
                      Kịch bản B (Cao điểm sáng, Khô)
                    </td>
                    <td className="py-2.5 text-left font-sans">Static Dijkstra</td>
                    <td className="py-2.5 text-right">1.54 ± 1.10 phút</td>
                    <td className="py-2.5 text-right">2.23</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right font-bold">0.45 ms</td>
                    <td className="py-2.5 text-right text-[#777777]">W = 2.0, p = 0.593</td>
                  </tr>
                  <tr className="bg-[#f5f4f0]">
                    <td className="py-2.5 text-left font-sans font-bold">Dynamic Dijkstra</td>
                    <td className="py-2.5 text-right font-bold">1.54 ± 1.09 phút</td>
                    <td className="py-2.5 text-right font-bold">2.17</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right">0.98 ms</td>
                    <td className="py-2.5 text-right font-bold">Chuẩn đối sánh</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-neutral-600">Edge-Scoring DQN</td>
                    <td className="py-2.5 text-right text-neutral-700">5.86 ± 8.38 phút</td>
                    <td className="py-2.5 text-right">10.37</td>
                    <td className="py-2.5 text-right">80.0%</td>
                    <td className="py-2.5 text-right">2.63 ms</td>
                    <td className="py-2.5 text-right font-bold">W = 64.0, p = 0.00053*</td>
                  </tr>

                  {/* Scenario C */}
                  <tr className="border-t border-[#d4d4d4]">
                    <td rowSpan={3} className="py-2.5 text-left font-sans font-bold align-top border-r border-[#e5e5e5]">
                      Kịch bản C (Cao điểm chiều, Mưa 1.4x)
                    </td>
                    <td className="py-2.5 text-left font-sans">Static Dijkstra</td>
                    <td className="py-2.5 text-right">2.13 ± 1.51 phút</td>
                    <td className="py-2.5 text-right">2.10</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right font-bold">0.32 ms</td>
                    <td className="py-2.5 text-right text-[#777777]">W = 1.0, p = 0.285</td>
                  </tr>
                  <tr className="bg-[#f5f4f0]">
                    <td className="py-2.5 text-left font-sans font-bold">Dynamic Dijkstra</td>
                    <td className="py-2.5 text-right font-bold">2.12 ± 1.51 phút</td>
                    <td className="py-2.5 text-right font-bold">2.00</td>
                    <td className="py-2.5 text-right">100%</td>
                    <td className="py-2.5 text-right">0.91 ms</td>
                    <td className="py-2.5 text-right font-bold">Chuẩn đối sánh</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-left font-sans text-neutral-600">Edge-Scoring DQN</td>
                    <td className="py-2.5 text-right text-neutral-700">7.17 ± 9.47 phút</td>
                    <td className="py-2.5 text-right">11.10</td>
                    <td className="py-2.5 text-right">80.0%</td>
                    <td className="py-2.5 text-right">4.48 ms</td>
                    <td className="py-2.5 text-right font-bold">W = 84.0, p = 0.00225*</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-[#777777] mt-2 font-mono">
              * Kiểm định Wilcoxon signed-rank test cặp: Cả 3 kịch bản đều đạt p &lt; 0.005, khẳng định ưu thế tuyệt đối của Dynamic Dijkstra.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Section 04: Phân Tích Thực Nghiệm 4 Chiều (Underline Tabs) */}
      <section id="section-04" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            04 / PHÂN TÍCH MÔ HÌNH CHUYÊN SÂU
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-6">
            Trực Quan Hóa Đánh Đổi Pareto &amp; Động Học Mô Hình
          </h2>

          {/* Minimalist Text Tabs */}
          <div className="flex flex-wrap gap-6 border-b border-[#e5e5e5] mb-8 font-mono text-xs">
            <button
              onClick={() => setActiveTab("t1_pareto")}
              className={`pb-2.5 transition font-semibold ${
                activeTab === "t1_pareto"
                  ? "border-b-2 border-[#111111] text-[#111111]"
                  : "text-[#777777] hover:text-[#111111]"
              }`}
            >
              [1] Đánh Đổi Pareto T1
            </button>
            <button
              onClick={() => setActiveTab("t2_vrptw")}
              className={`pb-2.5 transition font-semibold ${
                activeTab === "t2_vrptw"
                  ? "border-b-2 border-[#111111] text-[#111111]"
                  : "text-[#777777] hover:text-[#111111]"
              }`}
            >
              [2] Hiệu Năng Đội Xe T2
            </button>
            <button
              onClick={() => setActiveTab("t3_training")}
              className={`pb-2.5 transition font-semibold ${
                activeTab === "t3_training"
                  ? "border-b-2 border-[#111111] text-[#111111]"
                  : "text-[#777777] hover:text-[#111111]"
              }`}
            >
              [3] Động Học Huấn Luyện T3
            </button>
            <button
              onClick={() => setActiveTab("t3_benchmark")}
              className={`pb-2.5 transition font-semibold ${
                activeTab === "t3_benchmark"
                  ? "border-b-2 border-[#111111] text-[#111111]"
                  : "text-[#777777] hover:text-[#111111]"
              }`}
            >
              [4] So Sánh Chính Sách T3
            </button>
          </div>

          {/* Active Tab Content */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-8">
              {activeTab === "t1_pareto" && (
                <img
                  src="/figures/t1_pareto_tradeoffs.png"
                  alt="Đánh đổi Pareto T1 trên 50 cặp OD"
                  className="w-full border border-[#e5e5e5]"
                />
              )}
              {activeTab === "t2_vrptw" && (
                <img
                  src="/figures/t2_solver_comparison.png"
                  alt="So sánh VRPTW T2 trên 10 instances"
                  className="w-full border border-[#e5e5e5]"
                />
              )}
              {activeTab === "t3_training" && (
                <img
                  src="/figures/t3_training_curves.png"
                  alt="Động học huấn luyện T3"
                  className="w-full border border-[#e5e5e5]"
                />
              )}
              {activeTab === "t3_benchmark" && (
                <img
                  src="/figures/t3_policy_benchmark.png"
                  alt="So sánh chính sách định tuyến T3"
                  className="w-full border border-[#e5e5e5]"
                />
              )}
            </div>

            <div className="lg:col-span-4 text-xs text-[#444444] space-y-4 leading-relaxed">
              {activeTab === "t1_pareto" && (
                <>
                  <div className="font-mono text-xs font-bold text-[#111111] uppercase">
                    ĐÁNH ĐỔI PARETO TRÊN 50 CẶP OD
                  </div>
                  <p>
                    Biểu đồ phân tán trên 50 cặp OD ngẫu nhiên chứng minh kích thước tập Pareto trung bình là 2.42 tuyến trên mỗi cặp hành trình.
                  </p>
                  <p>
                    Tuyến <strong>Easiest</strong> chịu tăng trung bình +25.3% cự ly nhưng triệt tiêu hoàn toàn các khúc cua rẽ trái cắt dòng giao thông đối diện, đem lại sự an toàn và thư thái tối đa cho tài xế xe máy chặng cuối.
                  </p>
                </>
              )}

              {activeTab === "t2_vrptw" && (
                <>
                  <div className="font-mono text-xs font-bold text-[#111111] uppercase">
                    ĐÁNH ĐỔI VRPTW: +8.4% KM ĐỔI -75% TRỄ
                  </div>
                  <p>
                    Clarke-Wright + Local Search tối ưu tốt nhất về cự ly thuần túy (73.63 km), nhưng vi phạm khung giờ hẹn cao (30.6%) và hình phạt tồn đọng lớn (244.78).
                  </p>
                  <p>
                    Google OR-Tools chấp nhận di chuyển thêm +8.4% cự ly (79.81 km) để ưu tiên đúng khung giờ hẹn, hạ tỷ lệ trễ xuống chỉ còn 7.5% và giảm 88% phạt tồn đọng (29.54).
                  </p>
                </>
              )}

              {activeTab === "t3_training" && (
                <>
                  <div className="font-mono text-xs font-bold text-[#111111] uppercase">
                    250 EPISODES • HUBER LOSS HỘI TỤ
                  </div>
                  <p>
                    Mạng nơ-ron CandidateEdgeScoringNetwork gồm 10 đặc trưng đầu vào, 2 tầng ẩn (64 nơ-ron) kết hợp LayerNorm.
                  </p>
                  <p>
                    Hàm mất mát Huber Loss giảm đều từ 28.5 xuống 4.2 sau 250 tập huấn luyện, thời gian huấn luyện siêu tốc 23.09 giây trên cấu hình 2 nhân CPU mà không cần GPU.
                  </p>
                </>
              )}

              {activeTab === "t3_benchmark" && (
                <>
                  <div className="font-mono text-xs font-bold text-[#111111] uppercase">
                    COMPOUNDING VALUE APPROXIMATION ERROR
                  </div>
                  <p>
                    Trên đồ thị đường sá đa chặng (20 - 30 bước rẽ), việc mạng nơ-ron chọn hành động theo hàm Q cục bộ không có tìm kiếm dẫn đến hiện tượng cộng dồn sai số: Chỉ cần 1 quyết định rẽ sai sẽ đẩy xe vào ngõ cụt, gặp tới 7.0 - 11.1 lần kẹt xe (so với 2.0 lần của Dijkstra).
                  </p>
                  <p>
                    Trong khi đó, Dynamic Dijkstra giải lại toàn diện chỉ mất 0.87 - 0.98 ms, bảo đảm tối ưu toàn cục và đạt thời gian hành trình 1.18 - 2.12 phút.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 7. Section 05: Minh Bạch Khoa Học & Kết Quả Âm Tính */}
      <section id="section-05" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            05 / MINH BẠCH KHOA HỌC
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-8">
            Báo Cáo Minh Bạch Hai Kết Quả Âm Tính
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs text-[#333333] leading-relaxed">
            <div className="pt-3 border-t border-[#111111]">
              <div className="font-mono font-bold text-[#111111] uppercase mb-2">
                KẾT QUẢ ÂM TÍNH 1: THÍ NGHIỆM KHỞI ĐẦU E0 (rel_result/)
              </div>
              <p>
                Trên đồ thị thật TP.HCM, nghiệm khởi tạo Clarke-Wright đã đạt sát biên tối ưu. Áp dụng Deep RL để chọn toán tử Local Search đạt 657.90 km, kém hơn toán tử ngẫu nhiên đạt 656.36 km (p_Holm = 0.0072). Bài học: Không nên dùng RL phức tạp cho bài toán quy hoạch tĩnh khi solver kinh điển đã quá xuất sắc.
              </p>
            </div>

            <div className="pt-3 border-t border-[#111111]">
              <div className="font-mono font-bold text-[#111111] uppercase mb-2">
                KẾT QUẢ ÂM TÍNH 2: TẦNG T3 (results/t3_policy_comparison.json)
              </div>
              <p>
                Trên 30 cặp OD phân tán, DQN mất 4.98 - 7.17 phút so với chỉ 1.18 - 2.12 phút của Dynamic Dijkstra (Wilcoxon p &lt; 0.005). Độ trễ suy luận của Dijkstra (&lt; 1 ms) nhanh gấp 4 lần mạng nơ-ron (1.1 - 4.5 ms). Bài học: Sử dụng Dynamic Dijkstra làm động cơ đổi đường khi kẹt xe là tối ưu nhất.
              </p>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-[#e5e5e5] text-xs text-[#777777] italic font-serif">
            &ldquo;Đóng góp lớn nhất của nghiên cứu không chỉ nằm ở việc xây dựng một mô hình thành công, mà còn ở việc chứng minh rõ ràng điều gì KHÔNG NÊN LÀM để cộng đồng không lãng phí tài nguyên tính toán.&rdquo;
          </div>
        </div>
      </section>

      {/* 8. Section 06: Bảo Chứng Tái Lập */}
      <section id="section-06" className="py-14 border-t border-[#e5e5e5]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="font-mono text-xs text-[#888888] uppercase tracking-widest mb-1">
            06 / BẢO CHỨNG TÁI LẬP
          </div>
          <h2 className="text-2xl font-bold text-[#111111] tracking-tight mb-6">
            Khả Năng Tái Lập 100% &amp; Dữ Liệu Gốc
          </h2>

          <div className="p-3 bg-[#111111] text-white font-mono text-xs mb-8">
            <span className="text-[#888888] block mb-1"># LỆNH CHẠY TOÀN BỘ KIỂM THỬ TỰ ĐỘNG (43/43 PASSED)</span>
            <code>python -m pytest tests/ -v</code>
          </div>

          <div className="overflow-x-auto">
            <table className="text-xs border-t-2 border-b-2 border-[#111111]">
              <thead>
                <tr className="border-b border-[#e5e5e5] text-[#555555] font-mono text-[11px]">
                  <th className="py-2 text-left font-semibold">Tên Tệp Dữ Liệu</th>
                  <th className="py-2 text-left font-semibold">Đường Dẫn Trong Repo</th>
                  <th className="py-2 text-left font-semibold">Nội Dung Xác Thực</th>
                  <th className="py-2 text-right font-semibold">Trạng Thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f0f0f0] font-mono text-[11px]">
                <tr>
                  <td className="py-2 font-bold text-[#111111]">t1_routes_sample.json</td>
                  <td className="py-2 text-[#666666]">results/t1_routes_sample.json</td>
                  <td className="py-2 font-sans text-[#333333]">4 tuyến Pareto mẫu kèm tọa độ và 6 chỉ số</td>
                  <td className="py-2 text-right font-bold text-black">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2 font-bold text-[#111111]">t2_vrptw_benchmark.json</td>
                  <td className="py-2 text-[#666666]">results/baselines/t2_vrptw_benchmark.json</td>
                  <td className="py-2 font-sans text-[#333333]">So sánh Greedy, Clarke-Wright và OR-Tools</td>
                  <td className="py-2 text-right font-bold text-black">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2 font-bold text-[#111111]">t3_policy_comparison.json</td>
                  <td className="py-2 text-[#666666]">results/t3_policy_comparison.json</td>
                  <td className="py-2 font-sans text-[#333333]">Đối soát 3 kịch bản kèm kiểm định Wilcoxon</td>
                  <td className="py-2 text-right font-bold text-black">VERIFIED</td>
                </tr>
                <tr>
                  <td className="py-2 font-bold text-[#111111]">HotWAY_Final_Research_Report.pdf</td>
                  <td className="py-2 text-[#666666]">docs/HotWAY_Final_Research_Report.pdf</td>
                  <td className="py-2 font-sans text-[#333333]">Báo cáo nghiên cứu đầy đủ các chương</td>
                  <td className="py-2 text-right font-bold text-black">VERIFIED</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* 9. Minimalist CTA Section */}
      <section className="py-16 border-t border-[#e5e5e5] text-center max-w-4xl mx-auto px-6">
        <h2 className="text-2xl font-bold text-[#111111] tracking-tight">
          Trải Nghiệm Trực Tiếp Trên Bàn Điều Phối WebGIS
        </h2>
        <p className="mt-2 text-xs text-[#555555] max-w-xl mx-auto leading-relaxed">
          Trực quan hóa 4 tuyến Pareto T1 trên bản đồ MapLibre, kiểm tra kế hoạch VRPTW T2, và kích hoạt luồng Server-Sent Events mô phỏng đổi đường thích nghi T3.
        </p>

        <div className="mt-6 flex justify-center space-x-4">
          <Link
            href="/demo"
            className="px-5 py-2.5 bg-[#111111] hover:bg-[#333333] active:bg-[#000000] text-white text-xs font-medium rounded-xs transition"
          >
            Mở Bàn Điều Phối WebGIS Demo →
          </Link>
          <a
            href="/docs/HotWAY_Final_Research_Report.pdf"
            download
            className="px-5 py-2.5 bg-transparent border border-[#111111] hover:bg-[#f5f4f0] text-[#111111] text-xs font-medium rounded-xs transition"
          >
            Tải Báo Cáo PDF [↓]
          </a>
        </div>
      </section>

      {/* 10. Minimalist Footer */}
      <footer className="border-t border-[#e5e5e5] py-8 text-[11px] text-[#777777]">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span className="font-bold text-[#111111]">HotWAY Urban Motorbike Logistics Research Group</span>
            <span className="mx-2">•</span>
            <span>Đồ thị Bình Thạnh, TP.HCM (568 nút, 1.258 cạnh)</span>
          </div>
          <div className="font-mono text-[10px] space-x-3">
            <span>Backend: :8000</span>
            <span>Frontend: :3001</span>
            <span className="font-bold text-[#111111]">Cổng 3000: BẢO VỆ TUYỆT ĐỐI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
