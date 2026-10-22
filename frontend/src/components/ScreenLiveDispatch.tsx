"use client";

import React, { useEffect, useState } from "react";
import { ROUTE_COLORS } from "./OptimoMap";
import { Radio, RotateCcw, AlertTriangle, Check, RefreshCw, Smartphone } from "lucide-react";

interface VehicleSimState {
  vehicle_id: number;
  status: string;
  lat: number;
  lon: number;
  progress_percent: number;
  elapsed_time_sec: number;
  estimated_temp_c: number;
  is_thermal_warning: boolean;
  label: string;
}

interface ScreenLiveDispatchProps {
  planId: string | null;
  onReplanRemaining: () => void;
  onUpdateSimVehicle: (sim: { vehicle_id: number; lat: number; lon: number } | null) => void;
}

export default function ScreenLiveDispatch({
  planId,
  onReplanRemaining,
  onUpdateSimVehicle,
}: ScreenLiveDispatchProps) {
  const [simTimeSec, setSimTimeSec] = useState(0);
  const [isSimulating, setIsSimulating] = useState(true);
  const [vehicles, setVehicles] = useState<VehicleSimState[]>([]);
  const [activeDriverTab, setActiveDriverTab] = useState<"dispatcher" | "driver_pwa">("dispatcher");
  const [deliveredStops, setDeliveredStops] = useState<{ [stopId: string]: boolean }>({});

  useEffect(() => {
    if (!planId) return;

    const fetchSim = () => {
      fetch(`http://localhost:8000/api/v1/sim/${planId}?time_offset_sec=${simTimeSec}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.vehicles) {
            setVehicles(data.vehicles);
            if (data.vehicles.length > 0) {
              onUpdateSimVehicle({
                vehicle_id: data.vehicles[0].vehicle_id,
                lat: data.vehicles[0].lat,
                lon: data.vehicles[0].lon,
              });
            }
          }
        })
        .catch(() => {});
    };

    fetchSim();

    if (!isSimulating) return;
    const interval = setInterval(() => {
      setSimTimeSec((prev) => prev + 15);
    }, 1500);

    return () => clearInterval(interval);
  }, [planId, simTimeSec, isSimulating, onUpdateSimVehicle]);

  if (!planId) {
    return (
      <div className="p-8 text-center bg-surface border border-dashed border-border-warm rounded-warm space-y-2">
        <Radio className="w-8 h-8 text-secondary-text mx-auto opacity-40" />
        <p className="text-xs text-secondary-text">Chưa có kế hoạch tuyến để theo dõi.</p>
        <p className="text-[11px] text-secondary-text/80 italic">
          Vui lòng chuyển sang tab &quot;Lập kế hoạch&quot; và bấm &quot;Lập tuyến&quot;.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Simulation Banner with Honest "MÔ PHỎNG" Badge */}
      <div className="p-3 bg-amber-50 border border-amber-200 rounded-warm flex items-center justify-between text-xs text-amber-950">
        <div className="flex items-center space-x-2">
          <span className="px-2 py-0.5 rounded-full bg-brand-gold text-primary-text font-mono font-bold text-[10px] shrink-0">
            MÔ PHỎNG
          </span>
          <span className="text-[11px] leading-tight">
            Mô phỏng di chuyển theo tốc độ đường bộ thật. Không phải GPS phần cứng.
          </span>
        </div>

        <div className="flex items-center space-x-1 shrink-0 ml-2">
          <button
            onClick={() => setIsSimulating(!isSimulating)}
            className="px-2.5 py-1 rounded-lg bg-surface border border-border-warm text-primary-text text-[11px] font-bold hover:bg-sunken transition"
          >
            {isSimulating ? "Tạm dừng" : "Tiếp tục"}
          </button>
          <button
            onClick={() => setSimTimeSec(0)}
            title="Mô phỏng lại từ đầu"
            className="p-1 rounded-lg border border-border-warm text-secondary-text hover:bg-sunken transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Mode Switcher */}
      <div className="flex items-center justify-between border-b border-border-warm/80 pb-2">
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setActiveDriverTab("dispatcher")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition ${
              activeDriverTab === "dispatcher"
                ? "bg-brand-gold-soft text-primary-text shadow-xs"
                : "text-secondary-text hover:bg-sunken"
            }`}
          >
            Điều phối trung tâm
          </button>
          <button
            onClick={() => setActiveDriverTab("driver_pwa")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 ${
              activeDriverTab === "driver_pwa"
                ? "bg-brand-gold-soft text-primary-text shadow-xs"
                : "text-secondary-text hover:bg-sunken"
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>Tài xế (PWA)</span>
          </button>
        </div>

        <button
          onClick={onReplanRemaining}
          className="px-3 py-1.5 rounded-xl border border-border-warm bg-surface text-brand-brown hover:bg-sunken text-xs font-bold transition"
        >
          Lập lại tuyến
        </button>
      </div>

      {/* View 1: Dispatcher Live Overview */}
      {activeDriverTab === "dispatcher" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-[11px] font-mono text-secondary-text">
            <span>Thời gian đã trôi: {(simTimeSec / 60).toFixed(1)} phút</span>
            <span>{vehicles.length} xe đang chạy</span>
          </div>

          <div className="space-y-2">
            {vehicles.map((v) => {
              const color = ROUTE_COLORS[(v.vehicle_id - 1) % ROUTE_COLORS.length];
              const isCompleted = v.status === "COMPLETED";

              return (
                <div
                  key={`sim-veh-${v.vehicle_id}`}
                  className="p-3 rounded-warm bg-surface border border-border-warm shadow-soft space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="w-3 h-3 rounded-full border border-white" style={{ backgroundColor: color }} />
                      <h4 className="text-xs font-bold text-primary-text">Tài xế Xe {v.vehicle_id}</h4>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                        isCompleted
                          ? "bg-emerald-50 text-status-success border border-emerald-200"
                          : "bg-amber-50 text-status-warning border border-amber-200"
                      }`}
                    >
                      {isCompleted ? "ĐÃ HOÀN THÀNH" : "ĐANG GIAO HÀNG"}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono text-secondary-text">
                      <span>Tiến độ tuyến</span>
                      <span className="font-bold text-primary-text">{v.progress_percent}%</span>
                    </div>
                    <div className="w-full bg-sunken h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-gold rounded-full transition-all duration-300"
                        style={{ width: `${v.progress_percent}%` }}
                      />
                    </div>
                  </div>

                  {/* Temperature & Coords */}
                  <div className="flex items-center justify-between text-[11px] pt-1 border-t border-border-warm/60 font-mono">
                    <span className="text-secondary-text">
                      Tọa độ: {v.lat.toFixed(4)}, {v.lon.toFixed(4)}
                    </span>
                    <span
                      className={`font-bold ${
                        v.is_thermal_warning ? "text-status-danger" : "text-status-success"
                      }`}
                    >
                      {v.estimated_temp_c}°C
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* View 2: Driver Mobile PWA (Checklist) */}
      {activeDriverTab === "driver_pwa" && (
        <div className="bg-surface border border-border-warm rounded-warm p-3.5 space-y-3 shadow-soft">
          <div className="border-b border-border-warm pb-2 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono text-brand-gold uppercase font-bold block">
                TÀI XẾ SỐ 1
              </span>
              <h3 className="text-xs font-bold text-primary-text">Nhiệm vụ giao hàng</h3>
            </div>
            <span className="text-[10px] font-mono text-status-success bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-bold">
              Món ăn: 81.4°C
            </span>
          </div>

          <div className="space-y-2">
            {[
              { id: "STOP-01", address: "475A Điện Biên Phủ, HUTECH", demand: 4, eta: "11:15" },
              { id: "STOP-02", address: "Pearl Plaza, D2", demand: 5, eta: "11:28" },
              { id: "STOP-03", address: "Sảnh Landmark 81, Vinhomes", demand: 6, eta: "11:42" },
            ].map((st) => {
              const isDone = deliveredStops[st.id];
              return (
                <div
                  key={st.id}
                  className={`p-2.5 rounded-xl border transition flex items-center justify-between ${
                    isDone
                      ? "bg-sunken/40 border-border-warm opacity-60"
                      : "bg-surface border-border-warm shadow-xs"
                  }`}
                >
                  <div className="overflow-hidden">
                    <div className="flex items-center space-x-1.5">
                      <span className="text-xs font-bold text-primary-text truncate">{st.address}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-brand-gold-soft text-brand-brown font-bold shrink-0">
                        {st.demand} tô
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-secondary-text mt-0.5 block">
                      Dự kiến đến: {st.eta}
                    </span>
                  </div>

                  <button
                    onClick={() =>
                      setDeliveredStops((prev) => ({ ...prev, [st.id]: !prev[st.id] }))
                    }
                    className={`px-2.5 py-1 rounded-xl text-xs font-bold transition flex items-center space-x-1 shrink-0 ml-2 ${
                      isDone
                        ? "bg-emerald-100 text-status-success border border-emerald-300"
                        : "bg-brand-gold hover:bg-brand-gold-hover text-primary-text"
                    }`}
                  >
                    {isDone ? (
                      <>
                        <Check className="w-3 h-3" />
                        <span>Đã giao</span>
                      </>
                    ) : (
                      <span>Xác nhận</span>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
