"use client";

import React, { useState, useEffect } from "react";

interface SolverSummary {
  mean_dist_km: number;
  mean_duration_min: number;
  mean_wait_min: number;
  mean_late_rate_pct: number;
  mean_stoch_late_rate_pct?: number;
  mean_backlog_penalty: number;
  mean_solve_time_sec: number;
}

interface T2BenchmarkData {
  summary: Record<string, SolverSummary>;
  instances: any[];
  attribution?: string;
}

export default function ScreenT2VRPTW() {
  const [data, setData] = useState<T2BenchmarkData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<"dry" | "rain">("dry");

  useEffect(() => {
    const fetchT2Data = async () => {
      setIsLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/v1/vrptw/benchmark");
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          const fb = await fetch("/data/t2_vrptw_benchmark.json");
          if (fb.ok) {
            const json = await fb.json();
            setData(json);
          }
        }
      } catch (err) {
        try {
          const fb = await fetch("/data/t2_vrptw_benchmark.json");
          if (fb.ok) {
            const json = await fb.json();
            setData(json);
          }
        } catch (e) {
          console.error("Failed to load T2 benchmark:", e);
        }
      } finally {
        setIsLoading(false);
      }
    };
    fetchT2Data();
  }, []);

  if (isLoading || !data) {
    return (
      <div className="py-12 text-center font-mono text-xs text-[#777777]">
        Đang nạp kết quả kiểm thử lập tuyến đội xe VRPTW...
      </div>
    );
  }

  const summary = data.summary;
  const orTools = summary["Google OR-Tools"];
  const cw = summary["Clarke-Wright + LS"];
  const greedy = summary["Greedy Urgency"];

  return (
    <div className="space-y-5 text-xs text-[#111111] font-sans">
      {/* Header Info */}
      <div className="pb-3 border-b border-[#e5e5e5]">
        <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider">
          <span>TẦNG T2 — LẬP TUYẾN ĐỘI XE KHUNG GIỜ MỀM</span>
          <span>10 INSTANCES</span>
        </div>
        <h2 className="text-sm font-bold text-[#111111] mt-1">
          So Sánh Thuật Toán VRPTW &amp; Trọng Số Đơn Tồn
        </h2>
        <p className="text-[11px] text-[#555555] mt-0.5 leading-snug">
          Mô hình hóa khung giờ nhận hàng mềm, dừng 3.0 phút/điểm, trọng số: w_i = 1 + 1.5 · (tuổi_i / 60).
        </p>

        {/* View Mode Toggle: Dry vs Rain */}
        <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#f0f0f0]">
          <span className="text-[11px] text-[#666666]">Môi trường kiểm định:</span>
          <div className="inline-flex border border-[#d4d4d4] font-mono text-[10px]">
            <button
              onClick={() => setViewMode("dry")}
              className={`px-2 py-0.5 transition ${
                viewMode === "dry" ? "bg-[#111111] text-white font-bold" : "text-[#555555] hover:bg-[#f5f4f0]"
              }`}
            >
              ĐƯỜNG KHÔ
            </button>
            <button
              onClick={() => setViewMode("rain")}
              className={`px-2 py-0.5 transition ${
                viewMode === "rain" ? "bg-[#111111] text-white font-bold" : "text-[#555555] hover:bg-[#f5f4f0]"
              }`}
            >
              MƯA (1.40x)
            </button>
          </div>
        </div>
      </div>

      {/* Solver Performance Comparison (Minimal Open Table) */}
      <div className="space-y-2">
        <div className="font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
          BẢNG SO SÁNH SOLVERS (ĐỐI SOÁT TRỰC TIẾP)
        </div>

        <table className="text-[11px] font-mono border-t border-b border-[#111111]">
          <thead>
            <tr className="border-b border-[#e5e5e5] text-[#555555] text-[10px]">
              <th className="py-2 text-left font-semibold">Solver</th>
              <th className="py-2 text-right font-semibold">Tổng Km</th>
              <th className="py-2 text-right font-semibold">Tỷ Lệ Trễ</th>
              <th className="py-2 text-right font-semibold">Phạt Tồn</th>
              <th className="py-2 text-right font-semibold">Thời Gian</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#f0f0f0]">
            <tr className="bg-[#f5f4f0]">
              <td className="py-2 text-left font-sans font-bold text-[#111111]">
                Google OR-Tools
              </td>
              <td className="py-2 text-right">{orTools?.mean_dist_km.toFixed(1)} km</td>
              <td className="py-2 text-right font-bold text-[#111111]">
                {viewMode === "dry" ? `${orTools?.mean_late_rate_pct.toFixed(1)}%` : `${orTools?.mean_stoch_late_rate_pct?.toFixed(1)}%`}
              </td>
              <td className="py-2 text-right font-bold text-[#111111]">{orTools?.mean_backlog_penalty.toFixed(1)}</td>
              <td className="py-2 text-right">4.0s</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-sans text-[#333333]">Clarke-Wright + LS</td>
              <td className="py-2 text-right font-bold">{cw?.mean_dist_km.toFixed(1)} km</td>
              <td className="py-2 text-right text-red-700">
                {viewMode === "dry" ? `${cw?.mean_late_rate_pct.toFixed(1)}%` : `${cw?.mean_stoch_late_rate_pct?.toFixed(1)}%`}
              </td>
              <td className="py-2 text-right text-red-700">{cw?.mean_backlog_penalty.toFixed(1)}</td>
              <td className="py-2 text-right">1.5 ms</td>
            </tr>
            <tr>
              <td className="py-2 text-left font-sans text-[#333333]">Greedy Urgency</td>
              <td className="py-2 text-right">{greedy?.mean_dist_km.toFixed(1)} km</td>
              <td className="py-2 text-right text-red-700">
                {viewMode === "dry" ? `${greedy?.mean_late_rate_pct.toFixed(1)}%` : `${greedy?.mean_stoch_late_rate_pct?.toFixed(1)}%`}
              </td>
              <td className="py-2 text-right text-red-700">{greedy?.mean_backlog_penalty.toFixed(1)}</td>
              <td className="py-2 text-right">0.6 ms</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Insight */}
      <div className="border-l-2 border-[#111111] pl-3 py-1.5 bg-[#f5f4f0] text-[11px] text-[#333333] leading-relaxed space-y-1">
        <p>
          <strong>Đánh đổi VRPTW:</strong> Google OR-Tools chấp nhận di chuyển thêm +8.4% cự ly để giảm tỷ lệ trễ từ 30.6% xuống 7.5% (giảm 75%) và giảm 88% hình phạt tồn đọng.
        </p>
        <p className="text-[#666666]">
          Dưới mưa bão đô thị (1.40x), tỷ lệ trễ tăng lên 38.6%, khẳng định nhu cầu đổi đường thích nghi T3.
        </p>
      </div>

      {/* Traceability */}
      <div className="pt-2 font-mono text-[10px] text-[#888888] border-t border-[#f0f0f0]">
        Dữ liệu đối soát: results/baselines/t2_vrptw_benchmark.json • Hạt giống: 2026
      </div>
    </div>
  );
}
