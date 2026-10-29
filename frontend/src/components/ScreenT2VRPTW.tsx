"use client";

import React, { useState, useEffect } from "react";

interface MultiModelSummaryRow {
  model: string;
  mean_duration_min: number;
  mean_distance_km: number;
  mean_relative_gap_vs_ortools_pct: number | null;
  latency_mean_ms: number;
  inference_latency_mean_ms: number | null;
  latency_p99_ms: number;
  gap_N10: number;
  gap_N20: number;
  gap_N30: number;
  gap_N50: number;
  gap_Hanoi: number;
  gap_DaNang: number;
  gap_HCMC: number;
  zero_shot_failure_rate_pct: number;
  failure_rate_pct: number;
  weights_loaded: boolean | null;
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
  const [vrptwData, setVrptwData] = useState<any>(null);
  const [instancesList, setInstancesList] = useState<any[]>([]);
  const [selectedRegionFilter, setSelectedRegionFilter] = useState<"all" | "Hà Nội" | "Đà Nẵng" | "TP. Hồ Chí Minh">("all");
  const [selectedInstanceId, setSelectedInstanceId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTrack, setActiveTrack] = useState<"multi_model" | "regional_fairness" | "vrptw">("multi_model");

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch 4-model multi-model benchmark results
        const resMulti = await fetch("/data/benchmark_multi_model_results.json");
        const jsonMulti = resMulti.ok ? await resMulti.json() : { detailed_results: {} };
        if (resMulti.ok) setBenchmarkData(jsonMulti);

        // Fetch 100 POI instances list
        const resPois = await fetch("/data/benchmark_100_vietnam_pois.json");
        if (resPois.ok) {
          const jsonPois = await resPois.json();
          const insts = jsonPois.instances || [];
          setInstancesList(insts);
          if (insts.length > 0) {
            setSelectedInstanceId(insts[0].instance_id);
            const modelRoutes = jsonMulti.metadata?.schema_version === 2 ? Object.entries(jsonMulti.detailed_results || {}).flatMap(([model, rows]: [string, any]) => {
              const row = rows.find((item: any) => item.instance_id === insts[0].instance_id);
              return row?.valid ? [{ model, ...row }] : [];
            }) : [];
            if (jsonMulti.metadata?.schema_version === 2) onSelectRouteInstance?.(insts[0], modelRoutes);
          }
        }

        const resVrptw = await fetch("/data/t2_vrptw_benchmark.json");
        if (resVrptw.ok) setVrptwData(await resVrptw.json());
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
      notifyInstanceSelected(matched[0]);
    }
  };

  const filteredInstances = instancesList.filter((inst) => {
    if (selectedRegionFilter === "all") return true;
    return inst.region === selectedRegionFilter;
  });

  const notifyInstanceSelected = (instance: any) => {
    if (benchmarkData?.metadata?.schema_version !== 2) return;
    const modelRoutes = Object.entries(benchmarkData?.detailed_results || {}).flatMap(([model, rows]: [string, any]) => {
      const row = rows.find((item: any) => item.instance_id === instance.instance_id);
      return row?.valid ? [{ model, ...row }] : [];
    });
    onSelectRouteInstance?.(instance, modelRoutes);
  };

  if (isLoading || !benchmarkData) {
    return (
      <div className="py-12 text-center font-mono text-xs text-[#777777]">
        Đang nạp bộ dữ liệu kiểm định 100 POI Toàn Quốc &amp; Đối Soát 4 Mô Hình...
      </div>
    );
  }

  const summary = benchmarkData.summary || [];
  if (benchmarkData.metadata?.schema_version !== 2) {
    return (
      <div className="py-12 text-center font-mono text-xs text-[#777777]">
        Benchmark artifact is outdated. Regenerate it with evaluate_benchmark.py before presenting these results.
      </div>
    );
  }

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
                          {row.weights_loaded === false && (
                            <span className="ml-1 text-[8px] font-mono text-red-800">UNTRAINED</span>
                          )}
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
                          {row.mean_relative_gap_vs_ortools_pct ?? "N/A"}%
                        </td>
                        <td className="py-2 text-right font-mono text-[10px]">{row.inference_latency_mean_ms ?? row.latency_mean_ms} ms</td>
                        <td
                          className={`py-2 text-right font-bold ${
                            row.failure_rate_pct > 0 ? "text-red-800" : "text-emerald-800"
                          }`}
                        >
                          {row.failure_rate_pct}%
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
              {Object.entries(benchmarkData.dqn_fatal_flaws_diagnostic || {}).map(([key, finding]) => (
                <div key={key} className="border-l-2 border-red-700 pl-2 space-y-0.5">
                  <span className="font-bold text-[#111111]">{finding.title}</span>
                  <p className="text-[#555555]">{finding.finding}</p>
                </div>
              ))}
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
                        <td className="py-2 text-right">{row.mean_relative_gap_vs_ortools_pct ?? "N/A"}%</td>
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
              Regional relative gaps are calculated from the current benchmark artifact. OR-Tools is a heuristic reference, so negative values are retained.
            </div>
          </div>
        </div>
      )}

      {activeTrack === "vrptw" && (
        /* TRACK 3: 10 INSTANCES VRPTW FLEET */
        <div className="space-y-4">
          <div className="pb-1 border-b border-neutral-200 font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
            VRPTW measured benchmark summary
          </div>
          <table className="w-full text-[11px] font-mono border-t border-b border-[#111111]">
            <thead>
              <tr className="border-b border-[#e5e5e5] text-[#555555] text-[10px]">
                <th className="py-2 text-left font-semibold">Solver</th>
                <th className="py-2 text-right font-semibold">Mean Distance</th>
                <th className="py-2 text-right font-semibold">Late Rate</th>
                <th className="py-2 text-right font-semibold">Solve Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f0f0f0]">
              {Object.entries(vrptwData?.summary || {}).map(([solver, row]: [string, any]) => (
                <tr key={solver}>
                  <td className="py-2 text-left font-sans font-bold text-[#111111]">{solver}</td>
                  <td className="py-2 text-right">{row.mean_dist_km} km</td>
                  <td className="py-2 text-right">{row.mean_late_rate_pct}%</td>
                  <td className="py-2 text-right">{(row.mean_solve_time_sec * 1000).toFixed(1)} ms</td>
                </tr>
              ))}
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
              if (inst) notifyInstanceSelected(inst);
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
