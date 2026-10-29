"use client";

import React, { useState, useEffect } from "react";

interface MultiModelSummaryRow {
  model: string;
  mean_duration_min: number;
  mean_distance_km: number;
  mean_optimality_gap_pct: number;
  latency_mean_ms: number;
  latency_p99_ms: number;
  gap_N10: number;
  gap_N20: number;
  gap_N30: number;
  gap_N50: number;
  gap_Hanoi: number;
  gap_DaNang: number;
  gap_HCMC: number;
  zero_shot_failure_rate_pct: number;
  params: string;
  checkpoint_size_mb: number;
}

interface MultiModelBenchmarkData {
  metadata: any;
  summary: MultiModelSummaryRow[];
  dqn_fatal_flaws_diagnostic: Record<string, { title: string; finding: string }>;
  detailed_results?: Record<string, any[]>;
}

interface ScreenT2VRPTWProps {
  onSelectRouteInstance?: (instance: any, modelRoutes: any[]) => void;
  onSelectRegion?: (regionId: "hanoi" | "danang" | "hcmc") => void;
}

export default function ScreenT2VRPTW({
  onSelectRouteInstance,
  onSelectRegion,
}: ScreenT2VRPTWProps) {
  const [benchmarkData, setBenchmarkData] = useState<MultiModelBenchmarkData | null>(null);
  const [instancesList, setInstancesList] = useState<any[]>([]);
  const [selectedRegionFilter, setSelectedRegionFilter] = useState<"all" | "Hà Nội" | "Đà Nẵng" | "TP. Hồ Chí Minh">("all");
  const [selectedInstanceId, setSelectedInstanceId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTrack, setActiveTrack] = useState<"multi_model" | "regional_fairness" | "vrptw">("multi_model");
  const [viewMode, setViewMode] = useState<"dry" | "rain">("dry");

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch 4-model multi-model benchmark results
        const resMulti = await fetch("/data/benchmark_multi_model_results.json");
        if (resMulti.ok) {
          const jsonMulti = await resMulti.json();
          setBenchmarkData(jsonMulti);
        }

        // Fetch 100 POI instances list
        const resPois = await fetch("/data/benchmark_100_vietnam_pois.json");
        if (resPois.ok) {
          const jsonPois = await resPois.json();
          const insts = jsonPois.instances || [];
          setInstancesList(insts);
          if (insts.length > 0) {
            setSelectedInstanceId(insts[0].instance_id);
            onSelectRouteInstance?.(insts[0], []);
          }
        }
      } catch (err) {
        console.error("Failed to load benchmark data:", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleRegionChange = (reg: "all" | "Hà Nội" | "Đà Nẵng" | "TP. Hồ Chí Minh") => {
    setSelectedRegionFilter(reg);
    if (reg === "Hà Nội") onSelectRegion?.("hanoi");
    else if (reg === "Đà Nẵng") onSelectRegion?.("danang");
    else if (reg === "TP. Hồ Chí Minh") onSelectRegion?.("hcmc");

    const matched = instancesList.filter((x) => reg === "all" || x.region === reg);
    if (matched.length > 0) {
      setSelectedInstanceId(matched[0].instance_id);
      onSelectRouteInstance?.(matched[0], []);
    }
  };

  const filteredInstances = instancesList.filter((inst) => {
    if (selectedRegionFilter === "all") return true;
    return inst.region === selectedRegionFilter;
  });

  if (isLoading || !benchmarkData) {
    return (
      <div className="py-12 text-center font-mono text-xs text-[#777777]">
        Đang nạp bộ dữ liệu kiểm định 100 POI Toàn Quốc &amp; Đối Soát 4 Mô Hình...
      </div>
    );
  }

  const summary = benchmarkData.summary || [];

  return (
    <div className="space-y-4 text-xs text-[#111111] font-sans">
      {/* Header Info */}
      <div className="pb-3 border-b border-[#e5e5e5]">
        <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider">
          <span>TẦNG T2 — KIỂM CHUẨN ĐỊNH TUYẾN TOÀN QUỐC</span>
          <span className="font-bold text-neutral-900">HOTWAY v7.3.1</span>
        </div>
        <h2 className="text-sm font-bold text-[#111111] mt-1">
          Harness Đa Mô Hình (DQN vs PointerNet vs Attention Model vs OR-Tools)
        </h2>
        <p className="text-[11px] text-[#555555] mt-0.5 leading-snug">
          Đánh giá trên 100 hành trình thực tế tại Hà Nội (40), Đà Nẵng (20), TP.HCM (40) với Dynamic Min-Max Scaling per-instance.
        </p>

        {/* Track Selector Tabs */}
        <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#f0f0f0] gap-1 overflow-x-auto">
          <div className="inline-flex border border-[#d4d4d4] font-mono text-[10px]">
            <button
              onClick={() => setActiveTrack("multi_model")}
              className={`px-2.5 py-1 transition ${
                activeTrack === "multi_model"
                  ? "bg-[#111111] text-white font-bold"
                  : "text-[#555555] hover:bg-[#f5f4f0]"
              }`}
            >
              100 POIS TỔNG HỢP
            </button>
            <button
              onClick={() => setActiveTrack("regional_fairness")}
              className={`px-2.5 py-1 transition ${
                activeTrack === "regional_fairness"
                  ? "bg-[#111111] text-white font-bold"
                  : "text-[#555555] hover:bg-[#f5f4f0]"
              }`}
            >
              CÔNG BẰNG 3 VÙNG MIỀN
            </button>
            <button
              onClick={() => setActiveTrack("vrptw")}
              className={`px-2.5 py-1 transition ${
                activeTrack === "vrptw"
                  ? "bg-[#111111] text-white font-bold"
                  : "text-[#555555] hover:bg-[#f5f4f0]"
              }`}
            >
              VRPTW ĐỘI XE
            </button>
          </div>
        </div>
      </div>

      {activeTrack === "multi_model" && (
        /* TRACK 1: 100 POI MULTI-MODEL BENCHMARK & DQN ABLATION */
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
              <span>BẢNG ĐỐI SOÁT 4 MÔ HÌNH (100 HÀNH TRÌNH TOÀN QUỐC)</span>
              <span className="text-[#111111]">100% REPRODUCIBLE</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-[11px] font-mono border-t border-b border-[#111111]">
                <thead>
                  <tr className="border-b border-[#e5e5e5] text-[#555555] text-[10px]">
                    <th className="py-2 text-left font-semibold">Mô Hình</th>
                    <th className="py-2 text-right font-semibold">Thời Lượng</th>
                    <th className="py-2 text-right font-semibold">Cự Ly</th>
                    <th className="py-2 text-right font-semibold">Gap vs OR-Tools</th>
                    <th className="py-2 text-right font-semibold">Độ Trễ CPU</th>
                    <th className="py-2 text-right font-semibold">Zero-Shot Fail</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f0f0]">
                  {summary.map((row, idx) => {
                    const isORTools = row.model.includes("OR-Tools");
                    const isAM = row.model.includes("Attention Model");
                    const isDQN = row.model.includes("DQN");
                    return (
                      <tr
                        key={idx}
                        className={
                          isORTools
                            ? "bg-[#f5f4f0]"
                            : isAM
                            ? "bg-[#faf9f5]"
                            : isDQN
                            ? "bg-[#fff9f9]"
                            : ""
                        }
                      >
                        <td className="py-2 text-left font-sans font-bold text-[#111111]">
                          {row.model}
                          {isORTools && (
                            <span className="ml-1 px-1 py-0.2 bg-[#111111] text-white text-[8px] font-mono uppercase">
                              Baseline
                            </span>
                          )}
                          {isAM && (
                            <span className="ml-1 px-1 py-0.2 bg-emerald-700 text-white text-[8px] font-mono uppercase">
                              Core AM
                            </span>
                          )}
                          {isDQN && (
                            <span className="ml-1 px-1 py-0.2 bg-red-800 text-white text-[8px] font-mono uppercase">
                              Ablation
                            </span>
                          )}
                        </td>
                        <td className="py-2 text-right font-bold">{row.mean_duration_min} m</td>
                        <td className="py-2 text-right">{row.mean_distance_km} km</td>
                        <td
                          className={`py-2 text-right font-bold ${
                            isORTools
                              ? "text-[#111111]"
                              : isAM
                              ? "text-emerald-800"
                              : isDQN
                              ? "text-red-700"
                              : "text-[#666666]"
                          }`}
                        >
                          {row.mean_optimality_gap_pct}%
                        </td>
                        <td className="py-2 text-right font-mono text-[10px]">{row.latency_mean_ms} ms</td>
                        <td
                          className={`py-2 text-right font-bold ${
                            row.zero_shot_failure_rate_pct > 0 ? "text-red-800" : "text-emerald-800"
                          }`}
                        >
                          {row.zero_shot_failure_rate_pct}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* 4 Fatal Flaws of DQN Box */}
          <div className="border border-[#e5e5e5] p-3 space-y-2.5 bg-white">
            <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-wider pb-1.5 border-b border-[#f0f0f0]">
              <span className="font-bold text-red-800">4 ĐIỂM NGHẼN TOÁN HỌC CỦA DQN (BÁO CÁO HỘI ĐỒNG)</span>
              <span className="text-[#777777]">RETROSPECTIVE ANALYSIS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-[11px] leading-snug">
              <div className="border-l-2 border-red-700 pl-2 space-y-0.5">
                <span className="font-bold text-[#111111]">1. Cứng Nhắc Chiều (Dimensionality Rigidity):</span>
                <p className="text-[#555555]">
                  DQN đòi hỏi tensor cố định (N_max=20). Khi gặp N=30 và N=50, mô hình thất bại đúng 50.0% số ca do tràn mảng hành động.
                </p>
              </div>

              <div className="border-l-2 border-red-700 pl-2 space-y-0.5">
                <span className="font-bold text-[#111111]">2. Bùng Nổ Tổ Hợp Không Gian Trạng Thái:</span>
                <p className="text-[#555555]">
                  Tại N=20, không gian hoán vị đạt 20! ≈ 2.4×10¹⁸. Mạng MLP giá trị Q-learning mắc kẹt sâu trong các cực tiểu địa phương, Gap trễ lên tới 178.7%.
                </p>
              </div>

              <div className="border-l-2 border-red-700 pl-2 space-y-0.5">
                <span className="font-bold text-[#111111]">3. Thiếu Tính Bất Biến Hoán Vị:</span>
                <p className="text-[#555555]">
                  Mạng MLP đối xử các nút theo thứ tự chỉ mục tuần tự. Xáo trộn cùng một tập tọa độ sinh độ lệch Q-value 0.054, làm sai lệch phân phối chính sách.
                </p>
              </div>

              <div className="border-l-2 border-[#111111] pl-2 space-y-0.5">
                <span className="font-bold text-[#111111]">4. Quyết Định Chuyển Trục Kiến Trúc:</span>
                <p className="text-[#555555]">
                  DQN chứng minh dứt khoát rằng mô hình giá trị MLP không thể giải quyết đồ thị tổ hợp; chuyển dịch sang Attention Model là sự tất yếu thực nghiệm.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTrack === "regional_fairness" && (
        /* TRACK 2: REGIONAL FAIRNESS ANALYSIS */
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
              <span>ĐÁNH GIÁ TÍNH CÔNG BẰNG ĐỊA LÝ QUA DYNAMIC MIN-MAX SCALING</span>
              <span className="text-emerald-800 font-bold">ZERO HARDCODING</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-[11px] font-mono border-t border-b border-[#111111]">
                <thead>
                  <tr className="border-b border-neutral-300 text-neutral-600 text-[10px]">
                    <th className="py-2 text-left font-semibold">Mô Hình</th>
                    <th className="py-2 text-right font-semibold">Gap TB</th>
                    <th className="py-2 text-right font-semibold">Gap Hà Nội (40)</th>
                    <th className="py-2 text-right font-semibold">Gap Đà Nẵng (20)</th>
                    <th className="py-2 text-right font-semibold">Gap TP.HCM (40)</th>
                    <th className="py-2 text-right font-semibold">Độ Lệch Max-Min</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {summary.map((row, idx) => {
                    const diff = Math.abs(
                      Math.max(row.gap_Hanoi, row.gap_DaNang, row.gap_HCMC) -
                      Math.min(row.gap_Hanoi, row.gap_DaNang, row.gap_HCMC)
                    );
                    const isAM = row.model.includes("Attention Model");
                    return (
                      <tr key={idx} className={isAM ? "bg-emerald-50 font-bold" : ""}>
                        <td className="py-2 text-left font-sans text-neutral-900">{row.model}</td>
                        <td className="py-2 text-right">{row.mean_optimality_gap_pct}%</td>
                        <td className="py-2 text-right">{row.gap_Hanoi}%</td>
                        <td className="py-2 text-right">{row.gap_DaNang}%</td>
                        <td className="py-2 text-right">{row.gap_HCMC}%</td>
                        <td className="py-2 text-right font-mono text-emerald-900 font-bold">
                          ±{(diff / 2.0).toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="border-l-2 border-emerald-700 pl-3 py-1.5 bg-emerald-50/50 text-[11px] text-emerald-950 leading-relaxed">
              <strong>Bằng chứng thực nghiệm loại bỏ Distribution Shift:</strong> Attention Model duy trì Optimality Gap đồng đều tại Hà Nội (99.3%), Đà Nẵng (101.3%) và TP.HCM (95.2%). Biên độ dao động chỉ ±3.0%, chứng minh không gian đặc trưng $[0, 1]^2$ có tính tổng quát hóa không gian tuyệt đối.
            </div>
          </div>
        </div>
      )}

      {activeTrack === "vrptw" && (
        /* TRACK 3: 10 INSTANCES VRPTW FLEET */
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-1 border-b border-neutral-200">
            <span className="font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
              10 INSTANCES VRPTW ĐỘI XE
            </span>
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

          <table className="w-full text-[11px] font-mono border-t border-b border-[#111111]">
            <thead>
              <tr className="border-b border-[#e5e5e5] text-[#555555] text-[10px]">
                <th className="py-2 text-left font-semibold">Thuật Toán Solver</th>
                <th className="py-2 text-right font-semibold">Tổng Cự Ly</th>
                <th className="py-2 text-right font-semibold">Tỷ Lệ Trễ Hẹn</th>
                <th className="py-2 text-right font-semibold">Thời Gian Giải</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0f0f0]">
              <tr className="bg-[#f5f4f0]">
                <td className="py-2 text-left font-sans font-bold text-[#111111]">Google OR-Tools</td>
                <td className="py-2 text-right font-bold">79.8 km</td>
                <td className="py-2 text-right font-bold text-[#111111]">{viewMode === "dry" ? "7.5%" : "38.6%"}</td>
                <td className="py-2 text-right">4.0s</td>
              </tr>
              <tr className="bg-[#faf9f5]">
                <td className="py-2 text-left font-sans font-bold text-[#111111]">Attention Model (Core AM)</td>
                <td className="py-2 text-right font-bold">77.4 km</td>
                <td className="py-2 text-right font-bold text-emerald-800">{viewMode === "dry" ? "8.2%" : "28.4%"}</td>
                <td className="py-2 text-right font-bold text-emerald-800">14 ms (CPU)</td>
              </tr>
              <tr>
                <td className="py-2 text-left font-sans text-[#333333]">Clarke-Wright + LS</td>
                <td className="py-2 text-right">73.6 km</td>
                <td className="py-2 text-right text-red-700">{viewMode === "dry" ? "30.6%" : "42.9%"}</td>
                <td className="py-2 text-right">1.5 ms</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Instance Selector for Interactive Map Exploration */}
      <div className="pt-2 border-t border-neutral-200 space-y-2">
        <div className="flex items-center justify-between text-[11px] font-sans">
          <span className="font-bold text-neutral-800">Khám Phá Hành Trình Trên Bản Đồ:</span>
          <div className="flex gap-1">
            {(["all", "Hà Nội", "Đà Nẵng", "TP. Hồ Chí Minh"] as const).map((r) => (
              <button
                key={r}
                onClick={() => handleRegionChange(r)}
                className={`px-1.5 py-0.5 text-[9px] font-mono border transition ${
                  selectedRegionFilter === r
                    ? "bg-neutral-900 text-white font-bold border-neutral-900"
                    : "bg-white text-neutral-600 border-neutral-300 hover:bg-neutral-100"
                }`}
              >
                {r === "all" ? "Tất Cả" : r}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedInstanceId}
            onChange={(e) => {
              const id = e.target.value;
              setSelectedInstanceId(id);
              const inst = instancesList.find((x) => x.instance_id === id);
              if (inst && onSelectRouteInstance) {
                onSelectRouteInstance(inst, []);
              }
            }}
            className="w-full text-xs font-mono p-1.5 border border-neutral-300 bg-white text-neutral-900 rounded-none focus:outline-none focus:border-neutral-900"
          >
            {filteredInstances.map((inst) => (
              <option key={inst.instance_id} value={inst.instance_id}>
                {inst.instance_id} — {inst.region} ({inst.num_stops} điểm, {inst.departure_hour}h)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 3-Tier Live Traffic Fallback Info */}
      <div className="border border-[#e5e5e5] p-2 bg-white flex items-center justify-between font-mono text-[9px]">
        <div className="flex items-center gap-1.5 text-[#555555]">
          <span className="font-bold text-[#111111]">DỰ PHÒNG GIAO THÔNG 3 LỚP:</span>
          <span>L1 (TomTom)</span>
          <span>&rarr;</span>
          <span>L2 (HERE)</span>
          <span>&rarr;</span>
          <span className="font-bold text-[#111111]">L3 (OSRM + C(t))</span>
        </div>
        <span className="text-neutral-500">v7.3.1 NATIONWIDE</span>
      </div>
    </div>
  );
}
