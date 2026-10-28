"use client";

import React, { useState } from "react";
import { ROUTE_COLORS } from "./OptimoMap";
import { Play, RotateCcw, AlertTriangle, CheckCircle, Info } from "lucide-react";

interface PlanMetrics {
  total_distance_km: number;
  total_duration_min: number;
  cw_initial_distance_km: number;
  improvement_pct: number;
  vehicles_used: number;
  thermal_violations_count: number;
  is_feasible: boolean;
}

interface VehicleRouteItem {
  vehicle_id: number;
  distance_km: number;
  duration_min: number;
  total_load: number;
  thermal_violations_count: number;
  customer_indices: number[];
  stops: {
    node_idx: number;
    order_id: string;
    arrival_time_sec: number;
    elapsed_time_min: number;
    demand: number;
    estimated_temp_c: number;
    thermal_violation: boolean;
  }[];
}

interface ScreenPlanningProps {
  onRunPlan: (params: {
    strategy: string;
    num_vehicles: number;
    capacity: number;
    min_temp: number;
  }) => void;
  isLoading: boolean;
  planMetrics: PlanMetrics | null;
  routes: VehicleRouteItem[];
  selectedVehicleId: number | null;
  onSelectVehicle: (vId: number | null) => void;
  strategyUsed?: string;
  isFallback?: boolean;
}

export default function ScreenPlanning({
  onRunPlan,
  isLoading,
  planMetrics,
  routes,
  selectedVehicleId,
  onSelectVehicle,
  strategyUsed,
  isFallback,
}: ScreenPlanningProps) {
  const [strategy, setStrategy] = useState("best");
  const [numVehicles, setNumVehicles] = useState("5");
  const [capacity, setCapacity] = useState("40");
  const [minTemp, setMinTemp] = useState("60.0");

  const handlePlanClick = () => {
    onRunPlan({
      strategy,
      num_vehicles: parseInt(numVehicles) || 5,
      capacity: parseInt(capacity) || 40,
      min_temp: parseFloat(minTemp) || 60.0,
    });
  };

  return (
    <div className="space-y-4">
      {/* Parameter Control Card */}
      <div className="p-3.5 bg-surface border border-border-warm rounded-warm shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-primary-text uppercase tracking-wider">
            Cấu hình giải thuật
          </span>
          <button
            onClick={handlePlanClick}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-brand-gold hover:bg-brand-gold-hover active:bg-brand-gold-pressed text-primary-text font-bold text-xs shadow-soft transition disabled:opacity-50 flex items-center space-x-1.5"
          >
            <Play className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : "fill-current"}`} />
            <span>{isLoading ? "Đang tính..." : "Lập tuyến"}</span>
          </button>
        </div>

        {/* Strategy Selector - Full Width so no text is truncated */}
        <div>
          <label className="text-[11px] font-bold text-secondary-text block mb-1">
            Phương pháp chọn toán tử Local Search:
          </label>
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="w-full bg-sunken border border-border-warm rounded-xl px-3 py-2 text-xs text-primary-text font-medium focus:outline-none focus:border-brand-gold"
          >
            <option value="best">Khuyến nghị (Tự chọn thuật toán tốt nhất)</option>
            <option value="clarke_wright">Clarke-Wright (Khởi tạo tiết kiệm)</option>
            <option value="random">Random Local Search (Hiệu quả cao nhất)</option>
            <option value="cyclic">Cyclic Local Search (Tuần tự toán tử)</option>
            <option value="greedy">Greedy Local Search (Cải thiện lớn nhất)</option>
            <option value="dqn">DQN (Deep Q-Network F28)</option>
            <option value="double_dqn">Double DQN (Khử phóng đại Q)</option>
          </select>
        </div>

        {/* 3 Parameter Numeric Inputs */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <label className="text-[10px] text-secondary-text block mb-1 font-medium">
              Số xe tối đa:
            </label>
            <input
              type="number"
              value={numVehicles}
              onChange={(e) => setNumVehicles(e.target.value)}
              min="1"
              max="10"
              className="w-full bg-sunken border border-border-warm rounded-xl p-1.5 text-primary-text text-center font-mono focus:outline-none focus:border-brand-gold"
            />
          </div>

          <div>
            <label className="text-[10px] text-secondary-text block mb-1 font-medium">
              Sức chứa (tô):
            </label>
            <input
              type="number"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              min="10"
              max="100"
              className="w-full bg-sunken border border-border-warm rounded-xl p-1.5 text-primary-text text-center font-mono focus:outline-none focus:border-brand-gold"
            />
          </div>

          <div>
            <label className="text-[10px] text-secondary-text block mb-1 font-medium">
              Nhiệt độ min (°C):
            </label>
            <input
              type="number"
              step="0.5"
              value={minTemp}
              onChange={(e) => setMinTemp(e.target.value)}
              className="w-full bg-sunken border border-border-warm rounded-xl p-1.5 text-primary-text text-center font-mono focus:outline-none focus:border-brand-gold"
            />
          </div>
        </div>

        {/* Fallback Notice if triggered */}
        {isFallback && (
          <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-[11px] font-mono flex items-center space-x-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-status-warning shrink-0" />
            <span>Tự động chuyển sang {strategyUsed} để đảm bảo thời gian phản hồi.</span>
          </div>
        )}

        {/* Road graph notice */}
        <div className="flex items-start space-x-1.5 text-[10px] text-secondary-text pt-1 border-t border-border-warm/60">
          <Info className="w-3.5 h-3.5 text-brand-gold shrink-0 mt-0.5" />
          <span>Mạng đường có hướng OSMnx Bình Thạnh (R=3.5km), bảo đảm không rẽ ngược chiều.</span>
        </div>
      </div>

      {/* Plan Metrics Summary Strip */}
      {planMetrics && (
        <div className="p-3 bg-sunken/70 border border-border-warm rounded-warm grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
          <div className="p-1.5 bg-surface rounded-xl border border-border-warm/60">
            <span className="text-[9px] font-mono uppercase text-secondary-text block">
              Tổng quãng đường
            </span>
            <span className="text-sm font-bold font-mono text-primary-text">
              {planMetrics.total_distance_km} km
            </span>
          </div>

          <div className="p-1.5 bg-surface rounded-xl border border-border-warm/60">
            <span className="text-[9px] font-mono uppercase text-secondary-text block">
              Thời gian di chuyển
            </span>
            <span className="text-sm font-bold font-mono text-primary-text">
              {planMetrics.total_duration_min} ph
            </span>
          </div>

          <div className="p-1.5 bg-surface rounded-xl border border-border-warm/60">
            <span className="text-[9px] font-mono uppercase text-secondary-text block">
              Cải thiện so với CW
            </span>
            <span className="text-sm font-bold font-mono text-status-success">
              +{planMetrics.improvement_pct}%
            </span>
          </div>

          <div className="p-1.5 bg-surface rounded-xl border border-border-warm/60">
            <span className="text-[9px] font-mono uppercase text-secondary-text block">
              Đơn dưới 60°C
            </span>
            <span
              className={`text-sm font-bold font-mono ${
                planMetrics.thermal_violations_count === 0
                  ? "text-status-success"
                  : "text-status-danger"
              }`}
            >
              {planMetrics.thermal_violations_count}
            </span>
          </div>
        </div>
      )}

      {/* Route Cards */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-secondary-text uppercase tracking-wider">
            Tuyến đường theo xe ({routes.length})
          </span>
          {selectedVehicleId !== null && (
            <button
              onClick={() => onSelectVehicle(null)}
              className="text-[11px] text-brand-gold hover:underline font-bold"
            >
              Hiện tất cả các xe
            </button>
          )}
        </div>

        {routes.length === 0 ? (
          <div className="p-8 text-center bg-surface border border-dashed border-border-warm rounded-warm space-y-2">
            <p className="text-xs text-secondary-text">Chưa có kế hoạch tuyến.</p>
            <p className="text-[11px] text-secondary-text/80 italic">
              Bấm nút &quot;Lập tuyến&quot; ở trên để bắt đầu tối ưu.
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-0.5">
            {routes.map((r) => {
              const color = ROUTE_COLORS[(r.vehicle_id - 1) % ROUTE_COLORS.length];
              const isSelected = selectedVehicleId === r.vehicle_id;

              return (
                <div
                  key={`route-card-${r.vehicle_id}`}
                  onClick={() => onSelectVehicle(isSelected ? null : r.vehicle_id)}
                  className={`p-3 rounded-warm border transition cursor-pointer space-y-2 ${
                    isSelected
                      ? "bg-brand-gold-soft/50 border-brand-gold shadow-soft"
                      : "bg-surface border-border-warm hover:bg-sunken/60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span
                        className="w-3 h-3 rounded-full shrink-0 border border-white"
                        style={{ backgroundColor: color }}
                      />
                      <h4 className="text-xs font-bold text-primary-text">
                        Xe {r.vehicle_id} ({r.stops.length} điểm giao)
                      </h4>
                    </div>

                    <div className="flex items-center space-x-2 text-[11px] font-mono text-secondary-text">
                      <span>{r.distance_km} km</span>
                      <span>•</span>
                      <span>{r.duration_min} ph</span>
                      <span>•</span>
                      <span className="font-bold text-primary-text">{r.total_load} tô</span>
                    </div>
                  </div>

                  {/* Stop Sequence Chain */}
                  <div className="flex items-center space-x-1 text-[10px] font-mono overflow-x-auto pb-1 text-secondary-text">
                    <span className="font-bold text-brand-brown">Depot</span>
                    {r.stops.map((s, idx) => (
                      <React.Fragment key={`st-${idx}`}>
                        <span className="text-secondary-text/50">→</span>
                        <span
                          className={`px-1.5 py-0.5 rounded font-medium whitespace-nowrap ${
                            s.thermal_violation
                              ? "bg-red-50 text-status-danger border border-red-200"
                              : "bg-sunken text-primary-text"
                          }`}
                        >
                          {s.order_id} ({s.estimated_temp_c}°C)
                        </span>
                      </React.Fragment>
                    ))}
                    <span className="text-secondary-text/50">→</span>
                    <span className="text-brand-brown">Depot</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
