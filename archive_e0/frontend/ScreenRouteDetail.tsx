"use client";

import React from "react";
import { ROUTE_COLORS } from "./OptimoMap";
import { Thermometer, Clock, PackageCheck, AlertCircle } from "lucide-react";

interface RouteStop {
  node_idx: number;
  order_id: string;
  arrival_time_sec: number;
  elapsed_time_min: number;
  demand: number;
  remaining_load: number;
  estimated_temp_c: number;
  thermal_violation: boolean;
}

interface VehicleRouteDetail {
  vehicle_id: number;
  distance_km: number;
  duration_min: number;
  total_load: number;
  thermal_violations_count: number;
  stops: RouteStop[];
}

interface ScreenRouteDetailProps {
  routes: VehicleRouteDetail[];
  selectedVehicleId: number;
  onSelectVehicle: (vId: number) => void;
}

export default function ScreenRouteDetail({
  routes,
  selectedVehicleId,
  onSelectVehicle,
}: ScreenRouteDetailProps) {
  if (routes.length === 0) {
    return (
      <div className="p-8 text-center bg-surface border border-dashed border-border-warm rounded-warm space-y-2">
        <AlertCircle className="w-8 h-8 text-secondary-text mx-auto opacity-40" />
        <p className="text-xs text-secondary-text">Chưa có dữ liệu tuyến đường.</p>
        <p className="text-[11px] text-secondary-text/80 italic">
          Vui lòng chọn tab &quot;Lập kế hoạch&quot; và bấm &quot;Lập tuyến&quot;.
        </p>
      </div>
    );
  }

  const activeRoute = routes.find((r) => r.vehicle_id === selectedVehicleId) || routes[0];
  const color = ROUTE_COLORS[(activeRoute.vehicle_id - 1) % ROUTE_COLORS.length];

  return (
    <div className="space-y-4">
      {/* Vehicle Selector Tabs */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
        {routes.map((r) => {
          const isSelected = r.vehicle_id === activeRoute.vehicle_id;
          const rColor = ROUTE_COLORS[(r.vehicle_id - 1) % ROUTE_COLORS.length];
          return (
            <button
              key={`veh-btn-${r.vehicle_id}`}
              onClick={() => onSelectVehicle(r.vehicle_id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold flex items-center space-x-2 transition shrink-0 ${
                isSelected
                  ? "bg-surface text-primary-text border border-brand-gold shadow-soft"
                  : "bg-sunken text-secondary-text hover:bg-border-warm/60"
              }`}
            >
              <span className="w-2.5 h-2.5 rounded-full border border-white" style={{ backgroundColor: rColor }} />
              <span>Xe {r.vehicle_id}</span>
            </button>
          );
        })}
      </div>

      {/* Route Summary Card */}
      <div className="p-3 bg-surface border border-border-warm rounded-warm shadow-soft flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <span className="w-3.5 h-3.5 rounded-full border border-white shrink-0" style={{ backgroundColor: color }} />
          <div>
            <h3 className="text-xs font-bold text-primary-text">
              Tuyến Xe {activeRoute.vehicle_id}
            </h3>
            <p className="text-[11px] text-secondary-text">
              {activeRoute.stops.length} điểm giao • {activeRoute.total_load}/40 tô
            </p>
          </div>
        </div>

        <div className="text-right font-mono text-xs">
          <div className="font-bold text-primary-text">{activeRoute.distance_km} km</div>
          <div className="text-secondary-text text-[11px]">{activeRoute.duration_min} phút</div>
        </div>
      </div>

      {/* Temperature Decay Line Visualization T(t) */}
      <div className="p-3.5 bg-surface border border-border-warm rounded-warm shadow-soft space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1.5 font-bold text-primary-text">
            <Thermometer className="w-3.5 h-3.5 text-brand-gold" />
            <span>Nhiệt độ món ăn T(t) theo điểm dừng</span>
          </div>
          <span className="font-mono text-status-success font-bold text-[10px]">
            Ngưỡng an toàn: 60°C
          </span>
        </div>

        {/* SVG Chart */}
        <div className="h-28 bg-sunken/60 rounded-xl border border-border-warm p-2 relative flex flex-col justify-between">
          <svg className="w-full h-full" viewBox="0 0 100 40" preserveAspectRatio="none">
            {/* 60°C threshold guideline */}
            <line
              x1="0"
              y1="25"
              x2="100"
              y2="25"
              stroke="#D98A1F"
              strokeDasharray="2"
              strokeWidth="0.5"
            />

            {/* Temperature points line */}
            {(() => {
              const pts = [
                { x: 0, temp: 85.0 }, // Depot
                ...activeRoute.stops.map((s, idx) => ({
                  x: ((idx + 1) / (activeRoute.stops.length + 1)) * 100,
                  temp: s.estimated_temp_c,
                })),
              ];

              const pathStr = pts
                .map((p, i) => {
                  const y = 4 + ((85.0 - p.temp) / (85.0 - 50.0)) * 32;
                  return `${i === 0 ? "M" : "L"} ${p.x} ${y}`;
                })
                .join(" ");

              return (
                <>
                  <path
                    d={pathStr}
                    fill="none"
                    stroke="#E0A83A"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                  {pts.map((p, i) => {
                    const y = 4 + ((85.0 - p.temp) / (85.0 - 50.0)) * 32;
                    const isSafe = p.temp >= 60.0;
                    return (
                      <circle
                        key={i}
                        cx={p.x}
                        cy={y}
                        r="1.8"
                        fill={isSafe ? "#4E8F5A" : "#C2493D"}
                        stroke="#FFFDF7"
                        strokeWidth="0.6"
                      />
                    );
                  })}
                </>
              );
            })()}
          </svg>

          <div className="flex justify-between text-[10px] font-mono text-secondary-text pt-1 border-t border-border-warm/60">
            <span>Bếp: 85°C</span>
            <span>Ngưỡng: 60°C</span>
            <span>
              Cuối: {activeRoute.stops[activeRoute.stops.length - 1]?.estimated_temp_c}°C
            </span>
          </div>
        </div>
      </div>

      {/* Stops Sequence Table */}
      <div className="space-y-1.5">
        <span className="text-[11px] font-bold text-secondary-text uppercase tracking-wider block">
          Trình tự các chặng giao
        </span>

        <div className="overflow-x-auto rounded-warm border border-border-warm bg-surface shadow-soft">
          <table className="w-full text-left text-xs divide-y divide-border-warm">
            <thead className="bg-sunken/60 text-[10px] font-mono text-secondary-text uppercase">
              <tr>
                <th className="py-2 px-3 text-center w-8">#</th>
                <th className="py-2 px-3">Mã đơn</th>
                <th className="py-2 px-3 text-center">Giao</th>
                <th className="py-2 px-3 text-center">Tải còn</th>
                <th className="py-2 px-3 text-center">Thời gian</th>
                <th className="py-2 px-3 text-right">Nhiệt độ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-warm/60 font-sans">
              <tr className="bg-amber-50/50 text-secondary-text font-mono text-[11px]">
                <td className="py-2 px-3 text-center">0</td>
                <td className="py-2 px-3 font-bold text-brand-brown">Depot 490 ĐBP</td>
                <td className="py-2 px-3 text-center">—</td>
                <td className="py-2 px-3 text-center font-bold">{activeRoute.total_load}</td>
                <td className="py-2 px-3 text-center">00:00</td>
                <td className="py-2 px-3 text-right text-status-success font-bold">85.0°C</td>
              </tr>

              {activeRoute.stops.map((s, idx) => (
                <tr key={`stop-row-${idx}`} className="hover:bg-sunken/40 transition">
                  <td className="py-2 px-3 text-center font-mono text-secondary-text">{idx + 1}</td>
                  <td className="py-2 px-3 font-mono font-bold text-primary-text">{s.order_id}</td>
                  <td className="py-2 px-3 text-center font-mono text-brand-brown font-semibold">{s.demand}</td>
                  <td className="py-2 px-3 text-center font-mono text-secondary-text">{s.remaining_load}</td>
                  <td className="py-2 px-3 text-center font-mono text-secondary-text">+{s.elapsed_time_min} ph</td>
                  <td className="py-2 px-3 text-right font-mono font-bold">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] ${
                        s.thermal_violation
                          ? "bg-red-50 text-status-danger border border-red-200"
                          : "bg-emerald-50 text-status-success border border-emerald-200"
                      }`}
                    >
                      {s.estimated_temp_c}°C
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
