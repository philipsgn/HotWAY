"use client";

import React, { useEffect, useState } from "react";
import { Info, HelpCircle, CheckCircle, BarChart3, AlertCircle } from "lucide-react";

interface BenchmarkData {
  title: string;
  provenance: string;
  summary_by_algorithm: {
    protocol: string;
    method: string;
    mean_distance: string;
    mean_improvement_pct: string;
    ci_lower: string;
    ci_upper: string;
    feasible_rate: string;
    runtime_sec: string;
    mean_evals: string;
    gap_vs_ortools_pct: string;
  }[];
  paired_comparisons: {
    protocol: string;
    comparison: string;
    delta_impr_pp: string;
    ci_lower: string;
    ci_upper: string;
    w_t_l: string;
    dz: string;
    p_wilcoxon: string;
    p_holm: string;
  }[];
  per_decision_cost: {
    method: string;
    runtime_sec: string;
    decisions_mean: string;
    candidates_mean: string;
    ms_per_decision: string;
    candidates_per_decision: string;
  }[];
  academic_conclusions: {
    dqn_wins: boolean;
    best_heuristics: string;
    why_dqn_did_not_win: {
      reason: string;
      detail: string;
    }[];
  };
}

export default function ScreenStrategyLab() {
  const [data, setData] = useState<BenchmarkData | null>(null);
  const [selectedProtocol, setSelectedProtocol] = useState<string>("A2");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/strategies/benchmark")
      .then((res) => res.json())
      .then((resData) => {
        setData(resData);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Lỗi tải dữ liệu benchmark:", err);
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="p-8 text-center text-secondary-text text-xs flex flex-col items-center justify-center space-y-2">
        <div className="w-5 h-5 border-2 border-brand-gold border-t-transparent rounded-full animate-spin" />
        <span>Đang nạp bảng kết quả thực nghiệm rel_result...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-warm text-status-danger text-xs space-y-1">
        <div className="flex items-center space-x-1.5 font-bold">
          <AlertCircle className="w-4 h-4" />
          <span>Không thể kết nối đến máy chủ backend (cổng 8000).</span>
        </div>
        <p className="text-[11px] text-secondary-text">
          Vui lòng kiểm tra dịch vụ backend hoặc thử lại sau giây lát.
        </p>
      </div>
    );
  }

  const filteredSummary = data.summary_by_algorithm.filter(
    (r) => r.protocol === selectedProtocol
  );
  const filteredPaired = data.paired_comparisons.filter(
    (r) => r.protocol === selectedProtocol
  );

  return (
    <div className="space-y-4">
      {/* Scope Clarification Banner */}
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-warm text-xs text-amber-900 space-y-1">
        <div className="flex items-center space-x-1.5 font-bold text-amber-900">
          <Info className="w-4 h-4 text-brand-gold shrink-0" />
          <span>Bản chất bài toán:</span>
        </div>
        <p className="text-[11px] text-amber-950/90 leading-relaxed">
          DQN học cách <strong>chọn toán tử Local Search</strong> (2-opt, relocate, swap) để cải thiện tập tuyến CVRP; hình học đường đi trên bản đồ do đồ thị đường bộ quyết định. DQN không điều khiển hướng rẽ ngã tư.
        </p>
      </div>

      {/* Protocol Selection Tabs */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
        <span className="text-[10px] font-bold text-secondary-text uppercase tracking-wider shrink-0 mr-1">
          Giao thức:
        </span>
        {["A2", "A", "A3", "B", "B2"].map((proto) => (
          <button
            key={proto}
            onClick={() => setSelectedProtocol(proto)}
            className={`px-3 py-1 rounded-xl text-xs font-mono font-bold transition shrink-0 ${
              selectedProtocol === proto
                ? "bg-brand-gold text-primary-text shadow-soft"
                : "bg-sunken text-secondary-text hover:bg-border-warm/60"
            }`}
          >
            {proto}
          </button>
        ))}
      </div>

      {/* Table 1: Summary By Algorithm */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-primary-text">
            Bảng 1: Kết quả tổng hợp (Giao thức {selectedProtocol})
          </span>
          <span className="text-[10px] font-mono text-secondary-text">
            24 bài toán cố định
          </span>
        </div>

        {/* Scroll Container with sticky first column */}
        <div className="overflow-x-auto rounded-warm border border-border-warm bg-surface shadow-soft">
          <table className="w-full text-left text-xs divide-y divide-border-warm">
            <thead className="bg-sunken/60 text-[10px] font-mono text-secondary-text uppercase">
              <tr>
                <th className="py-2 px-3 sticky left-0 bg-sunken z-10">Phương pháp</th>
                <th className="py-2 px-3 text-right">Quãng đường</th>
                <th className="py-2 px-3 text-right">Cải thiện %</th>
                <th className="py-2 px-3 text-center">95% CI</th>
                <th className="py-2 px-3 text-right">Thời gian (s)</th>
                <th className="py-2 px-3 text-right">Số ứng viên</th>
                <th className="py-2 px-3 text-right">Gap OR-Tools</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-warm/60 font-sans">
              {filteredSummary.map((row, idx) => {
                const isDqn = row.method.includes("DQN");
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-sunken/40 transition ${
                      isDqn ? "bg-amber-50/60" : ""
                    }`}
                  >
                    <td className={`py-2 px-3 font-semibold sticky left-0 z-10 ${
                      isDqn ? "bg-amber-50 text-brand-brown" : "bg-surface text-primary-text"
                    }`}>
                      {row.method}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-primary-text">
                      {row.mean_distance}
                    </td>
                    <td className="py-2 px-3 text-right font-mono font-bold text-status-success">
                      +{row.mean_improvement_pct}%
                    </td>
                    <td className="py-2 px-3 text-center font-mono text-[10px] text-secondary-text whitespace-nowrap">
                      [{row.ci_lower}, {row.ci_upper}]
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-secondary-text">
                      {row.runtime_sec}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-secondary-text">
                      {row.mean_evals}
                    </td>
                    <td className="py-2 px-3 text-right font-mono text-brand-gold font-semibold">
                      {row.gap_vs_ortools_pct}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Table 2: Paired Comparisons (Wilcoxon + Holm) */}
      {filteredPaired.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-xs font-bold text-primary-text">
            Bảng 2: Kiểm định thống kê cặp (Giao thức {selectedProtocol})
          </span>

          <div className="overflow-x-auto rounded-warm border border-border-warm bg-surface shadow-soft">
            <table className="w-full text-left text-xs divide-y divide-border-warm">
              <thead className="bg-sunken/60 text-[10px] font-mono text-secondary-text uppercase">
                <tr>
                  <th className="py-2 px-3 sticky left-0 bg-sunken z-10">So sánh</th>
                  <th className="py-2 px-3 text-right">Δ Cải thiện (pp)</th>
                  <th className="py-2 px-3 text-center">95% CI</th>
                  <th className="py-2 px-3 text-center">W / T / L</th>
                  <th className="py-2 px-3 text-right">p Wilcoxon</th>
                  <th className="py-2 px-3 text-right">p Holm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-warm/60 font-sans">
                {filteredPaired.map((row, idx) => {
                  const isSignificant = parseFloat(row.p_holm) < 0.05;
                  const isNegative = parseFloat(row.delta_impr_pp) < 0;
                  return (
                    <tr key={idx} className="hover:bg-sunken/40 transition">
                      <td className="py-2 px-3 font-semibold text-primary-text sticky left-0 bg-surface z-10">
                        {row.comparison}
                      </td>
                      <td
                        className={`py-2 px-3 text-right font-mono font-bold ${
                          isNegative ? "text-status-danger" : "text-status-success"
                        }`}
                      >
                        {row.delta_impr_pp}
                      </td>
                      <td className="py-2 px-3 text-center font-mono text-[10px] text-secondary-text whitespace-nowrap">
                        [{row.ci_lower}, {row.ci_upper}]
                      </td>
                      <td className="py-2 px-3 text-center font-mono text-secondary-text">
                        {row.w_t_l}
                      </td>
                      <td className="py-2 px-3 text-right font-mono text-secondary-text">
                        {row.p_wilcoxon}
                      </td>
                      <td
                        className={`py-2 px-3 text-right font-mono font-bold ${
                          isSignificant ? "text-brand-brown underline" : "text-secondary-text"
                        }`}
                      >
                        {row.p_holm}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sourced Section: Why DQN Did Not Win */}
      <div className="p-3.5 bg-surface border border-border-warm rounded-warm shadow-soft space-y-2.5">
        <div className="flex items-center space-x-1.5">
          <BarChart3 className="w-4 h-4 text-brand-gold shrink-0" />
          <h3 className="text-xs font-bold text-primary-text uppercase tracking-wider">
            Vì sao DQN không thắng các baseline trong thực nghiệm?
          </h3>
        </div>

        <p className="text-[11px] text-secondary-text leading-relaxed">
          Kết quả âm tính này phản ánh trung thực bản chất nghiên cứu. Ba nguyên nhân chính được ghi nhận từ báo cáo:
        </p>

        <div className="space-y-2 pt-1">
          {data.academic_conclusions.why_dqn_did_not_win.map((item, idx) => (
            <div
              key={idx}
              className="p-2.5 bg-sunken/50 border border-border-warm/80 rounded-xl space-y-1"
            >
              <div className="flex items-center space-x-1.5">
                <span className="w-4 h-4 rounded-full bg-brand-gold-soft text-brand-brown font-mono font-bold text-[10px] flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <h4 className="text-xs font-bold text-primary-text">{item.reason}</h4>
              </div>
              <p className="text-[11px] text-secondary-text pl-5 leading-snug">
                {item.detail}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
