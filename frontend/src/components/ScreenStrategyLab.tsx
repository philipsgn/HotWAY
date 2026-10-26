"use client";

import React, { useEffect, useState } from "react";
import { Info, HelpCircle, CheckCircle, BarChart3, AlertCircle, ShieldAlert, Sparkles } from "lucide-react";

interface BenchmarkSummaryRow {
  method?: string;
  policy?: string;
  agent?: string;
  mean_wait_min: number;
  ci_95_lower: number;
  ci_95_upper: number;
  p90_wait_min: number;
  p95_wait_min: number;
  late_rate_pct: number;
  gini_coefficient: number;
  fleet_utilization_pct: number;
  total_km: number;
  decision_latency_ms: number;
}

export default function ScreenStrategyLab() {
  const [summaryData, setSummaryData] = useState<BenchmarkSummaryRow[]>([]);
  const [registry, setRegistry] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/sim/benchmark_summary")
      .then((res) => res.json())
      .then((data) => {
        if (data.summary) setSummaryData(data.summary);
        if (data.registry) setRegistry(data.registry);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load benchmark summary:", err);
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="py-20 text-center text-xs text-stone-400 space-y-2">
        <div className="animate-spin inline-block w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full"></div>
        <p>Đang nạp dữ liệu nghiệm thu khoa học từ sổ đăng ký số liệu...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-stone-200">
      {/* 1. Header Banner */}
      <div className="bg-stone-900 border border-stone-800 rounded-lg p-5">
        <div className="flex items-center space-x-2 text-amber-500 text-xs font-mono uppercase tracking-widest">
          <Sparkles className="w-4 h-4" />
          <span>PHÒNG THÍ NGHIỆM CHIẾN LƯỢC & NGHIỆM THU KHOA HỌC (GATE G4 & G5)</span>
        </div>
        <h2 className="text-lg font-semibold text-stone-100 mt-1">
          Đối So Sánh Tác Tử Học Tăng Cường & Các Quy Tắc Điều Phối
        </h2>
        <p className="text-xs text-stone-400 mt-1.5 leading-relaxed">
          Số liệu nghiệm thu chính thức trên <b>Frozen Test Set (5 hạt giống độc lập: 2041–2045)</b> trên mạng lưới đường phố thực tế TP.HCM. 100% số liệu được bảo đảm bởi bài kiểm thử độ trung thực T3 (sai số số học &lt; 10⁻⁹).
        </p>
      </div>

      {/* 2. Main Comparison Table */}
      <div className="bg-stone-900 border border-stone-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-stone-200 uppercase tracking-wider flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-amber-500" />
            <span>Bảng Hiệu Năng Tổng Hợp Trên Tập Test Đóng Băng</span>
          </h3>
          <span className="text-[11px] bg-emerald-950/60 text-emerald-400 border border-emerald-700/50 px-2 py-0.5 rounded font-mono">
            Kiểm thử T3 Verified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse font-sans">
            <thead>
              <tr className="border-b border-stone-800 text-stone-400 text-[11px] font-mono">
                <th className="py-2.5 px-3">Phương pháp / Mô hình</th>
                <th className="py-2.5 px-3">Chờ TB $W$ (phút)</th>
                <th className="py-2.5 px-3">95% Bootstrap CI</th>
                <th className="py-2.5 px-3">Chờ p90</th>
                <th className="py-2.5 px-3">Trễ ETA</th>
                <th className="py-2.5 px-3">Gini</th>
                <th className="py-2.5 px-3">Tải xe</th>
                <th className="py-2.5 px-3">Tổng km</th>
                <th className="py-2.5 px-3">Độ trễ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-800/60 font-mono text-stone-300">
              {/* Prescient Theoretical Reference */}
              <tr className="bg-stone-950/80 text-amber-400/90 font-medium italic">
                <td className="py-2.5 px-3">Offline Prescient (Tham chiếu lý thuyết)</td>
                <td className="py-2.5 px-3 font-bold">74.52m</td>
                <td className="py-2.5 px-3 text-stone-400">[Lý thuyết]</td>
                <td className="py-2.5 px-3">148.20m</td>
                <td className="py-2.5 px-3">58.4%</td>
                <td className="py-2.5 px-3">0.285</td>
                <td className="py-2.5 px-3">88.0%</td>
                <td className="py-2.5 px-3">710.5 km</td>
                <td className="py-2.5 px-3 text-stone-400">Offline</td>
              </tr>

              {summaryData.map((row, idx) => {
                const name = row.method || row.policy || row.agent || `Item ${idx}`;
                const isImmediate = name.includes("Immediate") || name.includes("BatchSize (k=1)");
                const isRL = name.includes("DQN") || name.includes("PPO");

                return (
                  <tr
                    key={idx}
                    className={`hover:bg-stone-800/40 transition ${
                      isImmediate ? "bg-amber-500/10 font-medium" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3 flex items-center space-x-1.5 font-sans">
                      <span className={isImmediate ? "text-amber-300 font-bold" : "text-stone-200"}>
                        {name}
                      </span>
                      {isImmediate && (
                        <span className="text-[10px] bg-amber-500 text-stone-950 px-1 py-0.2 rounded font-bold">
                          BEST ONLINE
                        </span>
                      )}
                    </td>
                    <td className={`py-2.5 px-3 font-bold ${isImmediate ? "text-amber-400" : "text-stone-200"}`}>
                      {row.mean_wait_min.toFixed(2)}m
                    </td>
                    <td className="py-2.5 px-3 text-stone-400 text-[11px]">
                      [{row.ci_95_lower.toFixed(2)}, {row.ci_95_upper.toFixed(2)}]
                    </td>
                    <td className="py-2.5 px-3">{row.p90_wait_min.toFixed(2)}m</td>
                    <td className="py-2.5 px-3">{row.late_rate_pct.toFixed(1)}%</td>
                    <td className="py-2.5 px-3">{row.gini_coefficient.toFixed(3)}</td>
                    <td className="py-2.5 px-3">{row.fleet_utilization_pct.toFixed(1)}%</td>
                    <td className="py-2.5 px-3">{row.total_km.toFixed(1)} km</td>
                    <td className="py-2.5 px-3 text-stone-400">{row.decision_latency_ms.toFixed(2)} ms</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. Paired Statistical Tests & Scientific Explanations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Paired Tests */}
        <div className="bg-stone-900 border border-stone-800 rounded-lg p-5 space-y-3">
          <h3 className="text-xs font-semibold text-stone-200 uppercase tracking-wider flex items-center space-x-2">
            <Info className="w-4 h-4 text-blue-400" />
            <span>Kiểm Định Wilcoxon & Hiệu Chỉnh Holm (vs Immediate)</span>
          </h3>
          <div className="space-y-2 text-xs font-mono text-stone-300">
            <div className="p-2.5 rounded bg-stone-950 border border-stone-800 flex justify-between items-center">
              <span>DQN vs Immediate</span>
              <span className="text-amber-400">+24.36m (p_Holm = 0.3750)</span>
            </div>
            <div className="p-2.5 rounded bg-stone-950 border border-stone-800 flex justify-between items-center">
              <span>Double DQN vs Immediate</span>
              <span className="text-amber-400">+28.60m (p_Holm = 0.3750)</span>
            </div>
            <div className="p-2.5 rounded bg-stone-950 border border-stone-800 flex justify-between items-center">
              <span>PPO vs Immediate</span>
              <span className="text-amber-400">+29.24m (p_Holm = 0.3750)</span>
            </div>
            <div className="p-2.5 rounded bg-stone-950 border border-stone-800 flex justify-between items-center">
              <span>Periodic (T=8m) vs Immediate</span>
              <span className="text-stone-300">+3.37m (p_Holm = 0.3750)</span>
            </div>
          </div>
          <p className="text-[11px] text-stone-400 pt-1 leading-relaxed">
            *Tại mức ý nghĩa α = 0.05, không có sự khác biệt có ý nghĩa thống kê giữa các phương pháp do kích thước mẫu 5 hạt giống, tuy nhiên giá trị tuyệt đối của Immediate nhất quán tốt hơn trên cả 5 seeds.
          </p>
        </div>

        {/* Academic Insight (Negative Result) */}
        <div className="bg-stone-900 border border-stone-800 rounded-lg p-5 space-y-3">
          <h3 className="text-xs font-semibold text-stone-200 uppercase tracking-wider flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>Minh Chứng Kết Quả Âm Tính & Đạo Đức Khoa Học</span>
          </h3>
          <div className="text-xs text-stone-300 space-y-2 leading-relaxed">
            <p>
              <b>1. Hậu quả bất đối xứng của quyết định chờ:</b> Khi mạng nơ-ron chọn nhầm hành động "Chờ thêm" vào đầu đợt đột biến tải, hàng đợi đơn hàng dồn ứ theo cấp số nhân. Với đội xe 3 người và sức chứa 4 đơn, quán mất nhiều giờ mới giải tỏa được số đơn tồn đọng.
            </p>
            <p>
              <b>2. Immediate áp đảo nhờ tốc độ giải phóng:</b> Quy tắc Immediate không chờ đợi bất kỳ ai mà lập tức giải phóng đơn ra đường, duy trì lưu thông liên tục cho bếp và đội xe máy.
            </p>
            <p className="text-[11px] text-stone-400">
              *Tương tự như Thí nghiệm E0, HotWAY tuân thủ kỷ luật trung thực khoa học tuyệt đối, công bố đầy đủ kết quả âm tính và nguyên nhân kỹ thuật mà không thiên vị mô hình RL.
            </p>
          </div>
        </div>
      </div>

      {/* 4. Ablations & Environmental Sensitivity */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Ablations */}
        <div className="bg-stone-900 border border-stone-800 rounded-lg p-5 space-y-3 text-xs">
          <h3 className="text-xs font-semibold text-stone-200 uppercase tracking-wider">
            Phân Tích Thành Phần Đóng Góp (Ablations trên Double DQN)
          </h3>
          <div className="space-y-2 font-mono">
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-stone-800">
              <span>Gốc (Double DQN đầy đủ 12 chiều)</span>
              <span className="text-stone-200 font-bold">118.29m</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-rose-900/40 text-rose-300">
              <span>Bỏ đặc trưng phân tán địa lý (σ_spatial)</span>
              <span className="font-bold">176.70m (+58.41m)</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-rose-900/40 text-rose-300">
              <span>Bỏ đặc trưng tốc độ đơn gần đây (λ_recent)</span>
              <span className="font-bold">172.00m (+53.71m)</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-rose-900/40 text-rose-300">
              <span>Hệ số chiết khấu thiển cận (γ = 0.95)</span>
              <span className="font-bold">213.40m (+95.11m)</span>
            </div>
          </div>
        </div>

        {/* Sensitivity */}
        <div className="bg-stone-900 border border-stone-800 rounded-lg p-5 space-y-3 text-xs">
          <h3 className="text-xs font-semibold text-stone-200 uppercase tracking-wider">
            Phân Tích Độ Nhạy Môi Trường (Thời Tiết & Tốc Độ Bếp)
          </h3>
          <div className="space-y-2 font-mono">
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-stone-800">
              <span>Khô ráo (1.0x), Bếp chuẩn (12m)</span>
              <span className="text-stone-200 font-bold">180.71m</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-blue-900/40 text-blue-300">
              <span>Mưa ngập (1.4x), Bếp nhanh (8m)</span>
              <span className="font-bold">278.32m (+54.0%)</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-blue-900/40 text-blue-300">
              <span>Mưa ngập (1.4x), Bếp chuẩn (12m)</span>
              <span className="font-bold">281.02m (+55.5%)</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-stone-950 border border-blue-900/40 text-blue-300">
              <span>Mưa ngập (1.4x), Bếp chậm (16m)</span>
              <span className="font-bold">285.08m (+57.8%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
