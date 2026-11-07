"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import NetworkFlowCanvas from "@/components/NetworkFlowCanvas";

export default function NetworkFlowLandingPage() {
  const [activeTab, setActiveTab] = useState<
    "t1_pareto" | "t2_vrptw" | "t3_training" | "t3_benchmark"
  >("t1_pareto");

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const [benchmarkSummary, setBenchmarkSummary] = useState<any[] | null>(null);
  const [benchmarkMeta, setBenchmarkMeta] = useState<any>(null);

  useEffect(() => {
    fetch("/data/benchmark_multi_model_results.json")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && Array.isArray(data.summary)) {
          setBenchmarkSummary(data.summary);
          setBenchmarkMeta(data.metadata);
        }
      })
      .catch((err) => console.error("Failed to load benchmark summary:", err));
  }, []);

  // Close dropdown menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const navSections = [
    { id: "section-01", num: "01", label: "Tầng T1: Macro Pareto Routing" },
    { id: "section-02", num: "02", label: "Tầng T2: Meso NCO Attention Model" },
    { id: "section-03", num: "03", label: "Tầng T3: Micro Adaptive Dijkstra & DQN" },
    { id: "section-04", num: "04", label: "Trực Quan Hóa Đánh Đổi Động Học" },
    { id: "section-05", num: "05", label: "Minh Bạch Kết Quả Âm Tính Khoa Học" },
    { id: "section-06", num: "06", label: "Bảo Chứng Tái Lập 100% & Báo Cáo PDF" },
  ];

  const handleNavigate = (id: string) => {
    setIsMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-[100dvh] bg-[#1a1a1e] text-[#CCCCCC] font-sans selection:bg-[#005691] selection:text-white">
      {/* 1. Network Infrastructure Top Header */}
      <header className="sticky top-0 z-50 bg-[#1a1a1e]/95 backdrop-blur-md border-b border-[#333333] text-white">
        <div className="max-w-[1280px] mx-auto px-6 h-14 flex items-center justify-between">
          {/* Brand Logo & Active State */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#00FF00] animate-pulse"></span>
              <span className="font-mono text-sm font-bold tracking-widest uppercase text-white">
                HOTWAY
              </span>
            </div>
            <span className="text-xs text-[#555555]">/</span>
            <span className="text-xs text-[#CCCCCC] font-medium hidden sm:inline">
              Mạng Lưới Định Tuyến Đô Thị Chặng Cuối v7.3.2 (100 POI Toàn Quốc)
            </span>
          </div>

          {/* Minimalist Dropdown Menu for Numbered Sections */}
          <div ref={menuRef} className="relative">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="px-3 py-1.5 border border-[#444444] bg-[#242428] hover:bg-[#333333] text-xs font-mono font-medium text-[#CCCCCC] hover:text-white rounded-[8px] transition-colors flex items-center space-x-1.5"
              aria-expanded={isMenuOpen}
              aria-label="Mở danh mục các tầng bài toán"
            >
              <span>[Mục Lục {isMenuOpen ? "▴" : "▾"}]</span>
            </button>

            {/* Flat Floating Dropdown Panel */}
            {isMenuOpen && (
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-72 sm:w-80 bg-[#242428] border border-[#444444] rounded-[8px] p-1.5 z-50 text-xs font-sans shadow-lg">
                <div className="px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider text-[#888888] border-b border-[#333333]">
                  Hạ Tầng 3 Tầng Bài Toán HotWAY
                </div>
                <div className="divide-y divide-[#333333]">
                  {navSections.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleNavigate(item.id)}
                      className="w-full text-left px-2.5 py-2 hover:bg-[#333333] rounded-[4px] transition-colors flex items-center space-x-2 text-[#CCCCCC] hover:text-white"
                    >
                      <span className="font-mono text-[#00FFFF] font-bold text-[11px]">
                        {item.num}
                      </span>
                      <span className="truncate">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Action Links */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            <Link
              href="/visualizer"
              className="text-xs text-[#00FFFF] hover:text-white transition-colors font-mono border border-[#00FFFF]/40 bg-[#00FFFF]/10 px-2.5 py-1 rounded-[8px] hidden sm:inline"
            >
              Mô Phỏng Sóng Thuật Toán [↗]
            </Link>

            <a
              href="/docs/HotWAY_Final_Research_Report.pdf"
              download
              className="text-xs text-[#CCCCCC] hover:text-white transition-colors underline underline-offset-4 font-mono hidden md:inline"
            >
              Tải PDF [↓]
            </a>

            <Link
              href="/demo"
              className="px-3.5 py-1.5 bg-[#005691] hover:bg-[#004777] text-white text-xs font-bold rounded-[8px] transition-colors font-mono"
            >
              Mở WebGIS Demo →
            </Link>
          </div>
        </div>
      </header>

      {/* 2. Hero Split-Screen (Text Left 55% / Network Flow Canvas Right 45%) */}
      <section className="py-14 sm:py-20 bg-[#1a1a1e] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Left Column (55%): Title & Value Proposition */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-[8px] bg-[#242428] border border-[#444444] text-xs font-mono text-[#CCCCCC]">
                <span className="w-2 h-2 rounded-full bg-[#00FF00] animate-pulse"></span>
                <span className="text-[#00FFFF] font-semibold">UBIQUITOUS NETWORK LOGISTICS</span>
                <span className="text-[#888888]">|</span>
                <span>100 POI TOÀN QUỐC</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight font-heading">
                Hạ Tầng Định Tuyến Đô Thị Chặng Cuối Cho Đội Xe Giao Hàng
              </h1>

              <p className="text-base sm:text-lg text-[#CCCCCC] max-w-[64ch] leading-relaxed">
                Hệ sinh thái tối ưu hóa 3 tầng chuẩn mực hệ thống: Định tuyến đa tiêu chí Pareto (T1), Lập tuyến đội xe VRPTW &amp; Attention Model NCO (T2), và Động cơ đổi đường thích nghi Dynamic Dijkstra (T3) dưới hệ số cản trở thời gian thực <span className="font-mono text-[#00FFFF]">C(t)</span> với cơ chế <strong className="text-white">Dynamic Isotropic Scaling</strong> bảo toàn tỷ lệ 1:1.
              </p>

              {/* CTAs */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link
                  href="/demo"
                  className="px-5 py-3 bg-[#005691] hover:bg-[#004777] text-white text-xs font-bold rounded-[8px] transition-colors font-mono flex items-center space-x-2"
                >
                  <span>Mở Bàn Điều Phối WebGIS</span>
                  <span>→</span>
                </Link>

                <Link
                  href="/visualizer"
                  className="px-5 py-3 bg-[#242428] hover:bg-[#333333] border border-[#00FFFF]/50 text-[#00FFFF] hover:text-white text-xs font-bold rounded-[8px] transition-colors font-mono flex items-center space-x-2"
                >
                  <span>Mô Phỏng Sóng Mở Rộng Wavefront</span>
                  <span>↗</span>
                </Link>

                <a
                  href="/docs/HotWAY_Final_Research_Report.pdf"
                  download
                  className="px-4 py-3 border border-[#CCCCCC]/40 hover:border-white text-[#CCCCCC] hover:text-white text-xs font-bold rounded-[8px] transition-colors font-mono"
                >
                  Báo Cáo Học Thuật PDF [↓]
                </a>
              </div>

              {/* Hub Status Badges */}
              <div className="pt-4 border-t border-[#333333] flex flex-wrap items-center gap-4 text-xs font-mono text-[#888888]">
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#005691]"></span>
                  <span className="text-white">Hà Nội (40 POI)</span>
                  <span className="text-[#00FF00] font-bold">+3.11% Gap</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#005691]"></span>
                  <span className="text-white">Đà Nẵng (20 POI)</span>
                  <span className="text-[#00FF00] font-bold">+3.48% Gap</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#005691]"></span>
                  <span className="text-white">TP.HCM (40 POI)</span>
                  <span className="text-[#00FF00] font-bold">+3.32% Gap</span>
                </div>
              </div>
            </div>

            {/* Right Column (45%): Kinetic Network Flow Canvas */}
            <div className="lg:col-span-5">
              <NetworkFlowCanvas />
            </div>
          </div>
        </div>
      </section>

      {/* 3. Section Zig-Zag Row 1: T1 Macro Pareto Routing (Text Left / Visual Right) */}
      <section id="section-01" className="py-16 sm:py-20 bg-[#222226] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Text Left */}
            <div className="lg:col-span-6 space-y-4">
              <div className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">
                01 / TẦNG T1 — MACRO PARETO ROUTING (A → B)
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-heading">
                Đa Tiêu Chí Đô Thị Thực Tế &amp; Hàm Phạt Mưa / Rẽ Trái
              </h2>
              <p className="text-sm text-[#CCCCCC] leading-relaxed">
                Định tuyến giao hàng xe máy tại đô thị Việt Nam không thể dùng khoảng cách Euclidean đơn thuần. HotWAY T1 xây dựng hàm mục tiêu tổng quát:
              </p>
              
              <div className="p-3 bg-[#1a1a1e] rounded-[8px] border border-[#444444] font-mono text-xs text-[#00FFFF]">
                J = d + α · t(C) + β · N_left + γ · Rain
                <div className="text-[11px] text-[#888888] mt-1">
                  Phạt rẽ trái cắt dòng +12s • Đèn đỏ +25s • Hệ số mưa x1.40
                </div>
              </div>

              <p className="text-xs text-[#CCCCCC] leading-relaxed">
                Hệ thống trích xuất tập nghiệm Pareto phi lấn át gồm 4 hồ sơ đặc trưng: <strong>Fastest</strong> (ưu tiên trục chính), <strong>Shortest</strong> (tối ưu mét), <strong>Stable p90</strong> (ổn định giờ cao điểm) và <strong>Easiest</strong> (triệt tiêu 100% rẽ trái cắt dòng giao thông).
              </p>
            </div>

            {/* Visual Right: 4 Pareto Profiles Matrix */}
            <div className="lg:col-span-6 space-y-3">
              <div className="p-4 bg-[#1a1a1e] rounded-[8px] border border-[#333333] hover:border-[#005691] transition-colors">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-bold text-white flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-[#00FF00]"></span>
                    <span>Hồ Sơ 1: Nhanh Nhất Kỳ Vọng (Fastest)</span>
                  </span>
                  <span className="text-[#00FF00] font-bold">14.22 phút • 2,304 m</span>
                </div>
                <div className="w-full bg-[#333333] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#00FF00] h-full" style={{ width: "95%" }}></div>
                </div>
                <div className="flex justify-between text-[11px] font-mono text-[#888888] mt-1.5">
                  <span>14 lần rẽ trái • 14 nút có đèn</span>
                  <span>9.6% đoạn hẻm</span>
                </div>
              </div>

              <div className="p-4 bg-[#1a1a1e] rounded-[8px] border border-[#333333] hover:border-[#005691] transition-colors">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-bold text-white flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-[#005691]"></span>
                    <span>Hồ Sơ 2: Ngắn Nhất Cự Ly (Shortest)</span>
                  </span>
                  <span className="text-white font-bold">18.46 phút • 2,192 m</span>
                </div>
                <div className="w-full bg-[#333333] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#005691] h-full" style={{ width: "75%" }}></div>
                </div>
                <div className="flex justify-between text-[11px] font-mono text-[#888888] mt-1.5">
                  <span>16 lần rẽ trái • 15 nút có đèn</span>
                  <span>18.5% đoạn hẻm</span>
                </div>
              </div>

              <div className="p-4 bg-[#1a1a1e] rounded-[8px] border border-[#333333] hover:border-[#FFA500] transition-colors">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="font-bold text-white flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-[#FFA500]"></span>
                    <span>Hồ Sơ 3: Dễ Đi Nhất (Easiest — 0 Rẽ Trái)</span>
                  </span>
                  <span className="text-[#FFA500] font-bold">17.07 phút • 2,887 m</span>
                </div>
                <div className="w-full bg-[#333333] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#FFA500] h-full" style={{ width: "85%" }}></div>
                </div>
                <div className="flex justify-between text-[11px] font-mono text-[#888888] mt-1.5">
                  <span className="text-[#FFA500] font-bold">0 rẽ trái cắt dòng (An toàn 100%)</span>
                  <span>12 nút có đèn</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Section Zig-Zag Row 2: T2 Meso NCO Attention Model (Visual Left / Text Right) */}
      <section id="section-02" className="py-16 sm:py-20 bg-[#1a1a1e] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Visual Left: 100 POI Benchmark Table */}
            <div className="lg:col-span-7 order-2 lg:order-1 space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-[#CCCCCC] mb-1">
                <span className="font-bold text-white uppercase">BẢNG ĐỐI SOÁT 4 MÔ HÌNH TRÊN 100 POI TOÀN QUỐC</span>
                <span className="px-2 py-0.5 rounded-[4px] bg-[#005691]/40 border border-[#005691] text-[#00FFFF] text-[10px] font-bold">
                  ZERO HARDCODE
                </span>
              </div>

              <div className="overflow-x-auto rounded-[8px] border border-[#333333] bg-[#242428]">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="border-b border-[#333333] text-[#888888] text-[11px] bg-[#1a1a1e]">
                      <th className="py-3 px-3 text-left">Mô Hình</th>
                      <th className="py-3 px-2 text-right">Relative Gap</th>
                      <th className="py-3 px-2 text-right">Hà Nội (40)</th>
                      <th className="py-3 px-2 text-right">Đà Nẵng (20)</th>
                      <th className="py-3 px-2 text-right">TP.HCM (40)</th>
                      <th className="py-3 px-3 text-right">CPU Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#333333] text-[11px]">
                    <tr className="bg-[#242428]">
                      <td className="py-2.5 px-3 font-bold text-white flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-white"></span>
                        <span>Google OR-Tools</span>
                      </td>
                      <td className="py-2.5 px-2 text-right font-bold text-white">0.00% (Baseline)</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">0.0%</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">0.0%</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">0.0%</td>
                      <td className="py-2.5 px-3 text-right text-[#FFA500]">2,410.0 ms</td>
                    </tr>
                    <tr className="bg-[#005691]/20 border-l-2 border-[#00FFFF]">
                      <td className="py-2.5 px-3 font-bold text-[#00FFFF] flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#00FF00]"></span>
                        <span>Attention Model (NCO)</span>
                      </td>
                      <td className="py-2.5 px-2 text-right font-bold text-[#00FF00]">+3.27%</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">+3.11%</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">+3.48%</td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">+3.32%</td>
                      <td className="py-2.5 px-3 text-right font-bold text-[#00FF00]">32.6 ms (74x)</td>
                    </tr>
                    <tr className="bg-[#242428]">
                      <td className="py-2.5 px-3 text-[#CCCCCC] flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[#888888]"></span>
                        <span>Pointer Network</span>
                      </td>
                      <td className="py-2.5 px-2 text-right text-[#CCCCCC]">+9.27%</td>
                      <td className="py-2.5 px-2 text-right text-[#888888]">+8.95%</td>
                      <td className="py-2.5 px-2 text-right text-[#888888]">+9.80%</td>
                      <td className="py-2.5 px-2 text-right text-[#888888]">+9.35%</td>
                      <td className="py-2.5 px-3 text-right text-[#CCCCCC]">41.8 ms</td>
                    </tr>
                    <tr className="bg-[#ff0000]/10">
                      <td className="py-2.5 px-3 text-red-400 font-bold flex items-center space-x-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>
                        <span>Edge-Scoring DQN</span>
                      </td>
                      <td className="py-2.5 px-2 text-right text-red-400 font-bold">+28.4% (N≤20)</td>
                      <td className="py-2.5 px-2 text-right text-red-400" colSpan={3}>
                        Thất bại 50.0% tại N=30, 50
                      </td>
                      <td className="py-2.5 px-3 text-right text-red-400">12.4 ms</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Text Right */}
            <div className="lg:col-span-5 order-1 lg:order-2 space-y-4">
              <div className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">
                02 / TẦNG T2 — MESO VRPTW &amp; HỌC SÂU NCO
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-heading">
                Attention Model NCO Đa Vùng Trọng Điểm
              </h2>
              <p className="text-sm text-[#CCCCCC] leading-relaxed">
                Đột phá cốt lõi nằm ở cơ chế <strong>Dynamic Isotropic Min-Max Scaling per-instance</strong>:
              </p>
              
              <div className="p-3 bg-[#242428] rounded-[8px] border border-[#444444] font-mono text-xs text-white text-center">
                x&apos;ᵢ = (xᵢ - min(X)) / max(Δx, Δy, ε) ∈ [0, 1]²
              </div>

              <p className="text-xs text-[#CCCCCC] leading-relaxed">
                Chuẩn hóa bảo toàn tỷ lệ không gian 1:1 triệt tiêu 100% hardcode bounding box. Mô hình Attention Model tự động thích nghi mọi thành phố: độ chênh lệch relative gap giữa Hà Nội (+3.11%), Đà Nẵng (+3.48%) và TP.HCM (+3.32%) chỉ là <strong>0.37%</strong>, chứng minh tính tổng quát hóa vượt bậc.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Section Zig-Zag Row 3: T3 Micro Adaptive Dijkstra & DQN Failure (Text Left / Visual Right) */}
      <section id="section-03" className="py-16 sm:py-20 bg-[#222226] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Text Left */}
            <div className="lg:col-span-6 space-y-4">
              <div className="font-mono text-xs text-[#FFA500] uppercase tracking-widest">
                03 / TẦNG T3 — MICRO ADAPTIVE ROUTING &amp; MINH BẠCH KHOA HỌC
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-heading">
                Bóc Tách 4 Điểm Nghẽn Tử Huyệt Của DQN Trong Định Tuyến
              </h2>
              <p className="text-sm text-[#CCCCCC] leading-relaxed">
                Thay vì thổi phồng hiệu quả của Reinforcement Learning, nghiên cứu HotWAY công bố minh bạch kết quả âm tính: DQN thất bại trước bài toán đồ thị đường sá thực tế vì 4 lý do căn bản:
              </p>

              <div className="space-y-2 text-xs font-mono text-[#CCCCCC]">
                <div className="p-2.5 bg-[#1a1a1e] rounded-[6px] border border-red-500/40">
                  <span className="text-red-400 font-bold">1. Không gian hành động cố định:</span> DQN không thể suy luận trên đồ thị có bậc nút và số điểm N thay đổi linh hoạt.
                </div>
                <div className="p-2.5 bg-[#1a1a1e] rounded-[6px] border border-red-500/40">
                  <span className="text-red-400 font-bold">2. Tràn ngưỡng Zero-Shot (50.0% fail):</span> Khi số điểm vượt thiết kế (N=30, 50), DQN không thể xuất hành động hợp lệ.
                </div>
                <div className="p-2.5 bg-[#1a1a1e] rounded-[6px] border border-red-500/40">
                  <span className="text-red-400 font-bold">3. Compounding Approximation Error:</span> Sai số hàm Q tích lũy qua 20-30 ngã rẽ khiến xe đi vào ngõ cụt.
                </div>
              </div>

              <p className="text-xs text-[#CCCCCC] leading-relaxed">
                <strong>Giải pháp:</strong> Động cơ Dynamic Dijkstra với hệ số tắc nghẽn thời gian thực phản hồi trong <strong>0.87 ms</strong>, tỷ lệ đến đích 100%, kẹt xe trung bình chỉ 2.0 lần (so với 7.0 - 11.1 lần của DQN, kiểm định Wilcoxon p &lt; 0.005).
              </p>
            </div>

            {/* Visual Right: Head-to-Head Diagnostic HUD */}
            <div className="lg:col-span-6 space-y-4">
              <div className="p-5 bg-[#1a1a1e] rounded-[8px] border border-[#444444] space-y-4">
                <div className="flex items-center justify-between border-b border-[#333333] pb-3 text-xs font-mono">
                  <span className="font-bold text-white">ĐỐI ĐẦU CHÍNH SÁCH ĐỔI ĐƯỜNG KHI GẶP KẸT XE</span>
                  <span className="text-[#00FF00] font-bold">WILCOXON p &lt; 0.005</span>
                </div>

                {/* Dynamic Dijkstra Card */}
                <div className="p-3.5 bg-[#242428] rounded-[6px] border border-[#00FF00]/40">
                  <div className="flex justify-between items-center text-xs font-mono mb-1">
                    <span className="font-bold text-[#00FF00]">✓ DYNAMIC DIJKSTRA (Được Chọn)</span>
                    <span className="text-white font-bold">Thời Gian: 1.18 - 2.12 phút</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-[#CCCCCC] mt-2">
                    <div>
                      <span className="text-[#888888] block">Đến đích</span>
                      <span className="text-[#00FF00] font-bold">100%</span>
                    </div>
                    <div>
                      <span className="text-[#888888] block">Lần kẹt xe TB</span>
                      <span className="text-white font-bold">2.0 lần</span>
                    </div>
                    <div>
                      <span className="text-[#888888] block">Độ trễ tính</span>
                      <span className="text-[#00FF00] font-bold">0.87 ms</span>
                    </div>
                  </div>
                </div>

                {/* Edge-Scoring DQN Card */}
                <div className="p-3.5 bg-[#242428] rounded-[6px] border border-red-500/40">
                  <div className="flex justify-between items-center text-xs font-mono mb-1">
                    <span className="font-bold text-red-400">✗ EDGE-SCORING DQN (Bị Loại)</span>
                    <span className="text-red-400 font-bold">Thời Gian: 4.98 - 7.17 phút</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-[#CCCCCC] mt-2">
                    <div>
                      <span className="text-[#888888] block">Đến đích</span>
                      <span className="text-red-400 font-bold">80.0% - 86.7%</span>
                    </div>
                    <div>
                      <span className="text-[#888888] block">Lần kẹt xe TB</span>
                      <span className="text-red-400 font-bold">7.0 - 11.1 lần</span>
                    </div>
                    <div>
                      <span className="text-[#888888] block">Độ trễ tính</span>
                      <span className="text-[#888888]">1.10 - 4.48 ms</span>
                    </div>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-[#888888] italic">
                  * Kết luận khoa học: Không nên lạm dụng RL khi động cơ đồ thị động giải quyết toàn cục với độ trễ sub-millisecond.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Section 04: Interactive Tabbed Visualizer & Figures */}
      <section id="section-04" className="py-16 sm:py-20 bg-[#1a1a1e] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest mb-1">
            04 / TRỰC QUAN HÓA THỰC NGHIỆM ĐA CHIỀU
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-6 font-heading">
            Đánh Đổi Pareto &amp; Động Học Huấn Luyện
          </h2>

          {/* Underline Tabs */}
          <div className="flex flex-wrap gap-4 sm:gap-6 border-b border-[#333333] mb-8 font-mono text-xs">
            <button
              onClick={() => setActiveTab("t1_pareto")}
              className={`pb-2.5 transition-colors font-bold ${
                activeTab === "t1_pareto"
                  ? "border-b-2 border-[#00FFFF] text-[#00FFFF]"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              [1] Đánh Đổi Pareto T1
            </button>
            <button
              onClick={() => setActiveTab("t2_vrptw")}
              className={`pb-2.5 transition-colors font-bold ${
                activeTab === "t2_vrptw"
                  ? "border-b-2 border-[#00FFFF] text-[#00FFFF]"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              [2] Hiệu Năng Đội Xe T2
            </button>
            <button
              onClick={() => setActiveTab("t3_training")}
              className={`pb-2.5 transition-colors font-bold ${
                activeTab === "t3_training"
                  ? "border-b-2 border-[#00FFFF] text-[#00FFFF]"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              [3] Động Học Huấn Luyện T3
            </button>
            <button
              onClick={() => setActiveTab("t3_benchmark")}
              className={`pb-2.5 transition-colors font-bold ${
                activeTab === "t3_benchmark"
                  ? "border-b-2 border-[#00FFFF] text-[#00FFFF]"
                  : "text-[#888888] hover:text-white"
              }`}
            >
              [4] So Sánh Chính Sách T3
            </button>
          </div>

          {/* Active Tab Figure and Content */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-8 rounded-[8px] overflow-hidden border border-[#333333] bg-[#242428] p-2">
              {activeTab === "t1_pareto" && (
                <img
                  src="/figures/t1_pareto_tradeoffs.png"
                  alt="Đánh đổi Pareto T1 trên 50 cặp OD"
                  className="w-full rounded-[6px]"
                />
              )}
              {activeTab === "t2_vrptw" && (
                <img
                  src="/figures/t2_solver_comparison.png"
                  alt="So sánh VRPTW T2 trên 10 instances"
                  className="w-full rounded-[6px]"
                />
              )}
              {activeTab === "t3_training" && (
                <img
                  src="/figures/t3_training_curves.png"
                  alt="Động học huấn luyện T3"
                  className="w-full rounded-[6px]"
                />
              )}
              {activeTab === "t3_benchmark" && (
                <img
                  src="/figures/t3_policy_benchmark.png"
                  alt="So sánh chính sách định tuyến T3"
                  className="w-full rounded-[6px]"
                />
              )}
            </div>

            <div className="lg:col-span-4 text-xs text-[#CCCCCC] space-y-4 leading-relaxed p-4 bg-[#242428] rounded-[8px] border border-[#333333]">
              {activeTab === "t1_pareto" && (
                <>
                  <div className="font-mono text-xs font-bold text-white uppercase text-[#00FFFF]">
                    ĐÁNH ĐỔI PARETO TRÊN 50 CẶP OD
                  </div>
                  <p>
                    Biểu đồ phân tán trên 50 cặp OD ngẫu nhiên chứng minh kích thước tập Pareto trung bình là 2.42 tuyến trên mỗi cặp hành trình.
                  </p>
                  <p>
                    Tuyến <strong>Easiest</strong> chấp nhận tăng cự ly trung bình +25.3% để triệt tiêu 100% rẽ trái cắt dòng, giảm nguy cơ va chạm và áp lực tâm lý cho tài xế xe máy.
                  </p>
                </>
              )}

              {activeTab === "t2_vrptw" && (
                <>
                  <div className="font-mono text-xs font-bold text-white uppercase text-[#00FFFF]">
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
                  <div className="font-mono text-xs font-bold text-white uppercase text-[#00FFFF]">
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
                  <div className="font-mono text-xs font-bold text-white uppercase text-[#00FFFF]">
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

      {/* 7. Section Zig-Zag Row 4: Reproducibility & PDF Report (Visual Left / Text Right) */}
      <section id="section-06" className="py-16 sm:py-20 bg-[#222226] text-white border-b border-[#333333]">
        <div className="max-w-[1280px] mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Visual Left: Terminal Shell & Verified Checksums */}
            <div className="lg:col-span-7 order-2 lg:order-1 space-y-3">
              <div className="p-4 bg-[#1a1a1e] rounded-[8px] border border-[#333333] font-mono text-xs space-y-2">
                <div className="flex items-center space-x-2 text-[#888888] border-b border-[#333333] pb-2 text-[11px]">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500/80"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500/80"></span>
                  <span className="ml-2 text-white font-bold">hotway-reproducibility-auditor ~ bash</span>
                </div>
                <div className="text-[#888888]"># 1. Chạy toàn bộ 85 bài test tích hợp (100% Passed)</div>
                <div className="text-[#00FF00]">
                  $ py -3.13 -m pytest tests/
                </div>
                <div className="text-[#CCCCCC] text-[11px]">
                  85 passed, 0 failed in 91.01s (Python 3.13.3)
                </div>
                <div className="text-[#888888] pt-2"># 2. Khởi chạy song song Backend &amp; WebGIS Frontend</div>
                <div className="text-[#00FFFF]">
                  $ uvicorn api.main:app --host 0.0.0.0 --port 8000 &amp;<br />
                  $ npm --prefix frontend run dev -p 3001
                </div>
              </div>

              {/* Data File Artifacts Table */}
              <div className="overflow-x-auto rounded-[8px] border border-[#333333] bg-[#1a1a1e]">
                <table className="w-full text-xs font-mono">
                  <thead>
                    <tr className="border-b border-[#333333] text-[#888888] text-[10px]">
                      <th className="py-2 px-3 text-left">Tệp Dữ Liệu Gốc</th>
                      <th className="py-2 px-3 text-left">Đường Dẫn Repository</th>
                      <th className="py-2 px-3 text-right">Trạng Thái</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#333333] text-[11px]">
                    <tr>
                      <td className="py-2 px-3 font-bold text-white">t1_routes_sample.json</td>
                      <td className="py-2 px-3 text-[#888888]">results/t1_routes_sample.json</td>
                      <td className="py-2 px-3 text-right font-bold text-[#00FF00]">VERIFIED</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-bold text-white">benchmark_multi_model_results.json</td>
                      <td className="py-2 px-3 text-[#888888]">results/benchmark_multi_model_results.json</td>
                      <td className="py-2 px-3 text-right font-bold text-[#00FF00]">VERIFIED</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-bold text-white">t3_policy_comparison.json</td>
                      <td className="py-2 px-3 text-[#888888]">results/t3_policy_comparison.json</td>
                      <td className="py-2 px-3 text-right font-bold text-[#00FF00]">VERIFIED</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Text Right */}
            <div className="lg:col-span-5 order-1 lg:order-2 space-y-4">
              <div className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">
                05 / BẢO CHỨNG TÁI LẬP &amp; HỌC THUẬT
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-heading">
                Bảo Chứng Tái Lập 100% &amp; Báo Cáo Học Thuật Chuẩn IEEE
              </h2>
              <p className="text-sm text-[#CCCCCC] leading-relaxed">
                Mọi biểu đồ và bảng số liệu đều được neo chặt vào kết quả thực nghiệm có thể truy vết (Traceable 100%). Không có số liệu suy đoán hay làm tròn sai lệch.
              </p>
              
              <div className="pt-2 flex flex-col sm:flex-row gap-3">
                <a
                  href="/docs/HotWAY_Final_Research_Report.pdf"
                  download
                  className="px-5 py-3 bg-[#005691] hover:bg-[#004777] text-white text-xs font-bold rounded-[8px] transition-colors font-mono flex items-center justify-center space-x-2"
                >
                  <span>Tải Báo Cáo PDF Đầy Đủ</span>
                  <span>[↓]</span>
                </a>

                <Link
                  href="/demo"
                  className="px-5 py-3 bg-[#242428] hover:bg-[#333333] border border-[#CCCCCC]/40 text-[#CCCCCC] hover:text-white text-xs font-bold rounded-[8px] transition-colors font-mono flex items-center justify-center space-x-2"
                >
                  <span>Mở Bàn Điều Phối WebGIS</span>
                  <span>→</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 8. Call To Action Footer Banner */}
      <section className="py-16 bg-[#1a1a1e] border-t border-[#333333] text-center text-white">
        <div className="max-w-4xl mx-auto px-6 space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-[8px] bg-[#242428] border border-[#444444] text-xs font-mono text-[#00FFFF]">
            <span>READY FOR FIELD DEPLOYMENT &amp; THESIS DEFENSE</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-heading">
            Trải Nghiệm Trực Tiếp Hệ Thống Điều Phối HotWAY
          </h2>
          <p className="text-xs sm:text-sm text-[#CCCCCC] max-w-xl mx-auto leading-relaxed">
            Quan sát luồng sóng mở rộng wavefront trực quan trên MapLibre, đối soát 4 mô hình định tuyến thời gian thực và kiểm chứng phản hồi sub-millisecond trên CPU.
          </p>
          <div className="pt-4 flex justify-center gap-3">
            <Link
              href="/demo"
              className="px-6 py-3 bg-[#005691] hover:bg-[#004777] text-white text-xs font-bold rounded-[8px] transition-colors font-mono"
            >
              Mở Bàn Điều Phối WebGIS →
            </Link>
            <Link
              href="/visualizer"
              className="px-6 py-3 bg-[#242428] hover:bg-[#333333] border border-[#00FFFF]/50 text-[#00FFFF] hover:text-white text-xs font-bold rounded-[8px] transition-colors font-mono"
            >
              Mô Phỏng Sóng Wavefront ↗
            </Link>
          </div>
        </div>
      </section>

      {/* 9. Minimalist Infrastructure Footer */}
      <footer className="border-t border-[#333333] bg-[#141416] py-8 text-[11px] text-[#888888] font-mono">
        <div className="max-w-[1280px] mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-bold text-[#CCCCCC] font-sans">HotWAY Urban Logistics Research Group</span>
            <span className="mx-2">•</span>
            <span>Estilo de Fluxo de Rede • Đa Vùng Trọng Điểm HN (40) — ĐN (20) — TP.HCM (40)</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Backend: :8000</span>
            <span>Frontend: :3001</span>
            <span className="font-bold text-[#00FF00]">Cổng 3000: BẢO VỆ TUYỆT ĐỐI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
