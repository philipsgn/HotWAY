"use client";

import React, { useState, useEffect } from "react";

export interface T1RouteInfo {
  key: string;
  label: string;
  tag: string;
  distance_m: number;
  expected_time_min: number;
  p90_time_min: number;
  num_turns: number;
  num_left_turns: number;
  alley_ratio_pct: number;
  num_signals: number;
  ease_penalty_score: number;
  coordinates: [number, number][]; // [lat, lon]
}

interface ScreenT1MultiCriteriaProps {
  onSelectRoute?: (route: T1RouteInfo | null, allRoutes: T1RouteInfo[]) => void;
  onUpdateMapPoints?: (origin: [number, number], dest: [number, number]) => void;
}

const ARCHETYPE_ACCENTS: Record<string, { tag: string; label: string; num: string; hex: string }> = {
  fastest: { tag: "FASTEST", label: "Nhanh nhất kỳ vọng", num: "01", hex: "#059669" },
  shortest: { tag: "SHORTEST", label: "Ngắn nhất cự ly", num: "02", hex: "#2563eb" },
  stable: { tag: "STABLE", label: "Ổn định nhất p90", num: "03", hex: "#d97706" },
  easiest: { tag: "EASIEST", label: "Dễ đi nhất (0 rẽ trái)", num: "04", hex: "#7c3aed" },
};

export default function ScreenT1MultiCriteria({
  onSelectRoute,
  onUpdateMapPoints,
}: ScreenT1MultiCriteriaProps) {
  const [routesData, setRoutesData] = useState<Record<string, T1RouteInfo> | null>(null);
  const [selectedKey, setSelectedKey] = useState<string>("fastest");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRain, setIsRain] = useState<boolean>(false);

  const fetchT1Routes = async (rainActive: boolean = false) => {
    setIsLoading(true);
    try {
      const url = `http://localhost:8000/api/v1/routes/t1?rain=${rainActive}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setRoutesData(data.routes);
        if (data.metadata?.origin && data.metadata?.destination && onUpdateMapPoints) {
          onUpdateMapPoints(
            [data.metadata.origin.lat, data.metadata.origin.lon],
            [data.metadata.destination.lat, data.metadata.destination.lon]
          );
        }
        if (onSelectRoute && data.routes) {
          const list = Object.values(data.routes) as T1RouteInfo[];
          onSelectRoute(data.routes[selectedKey] || list[0], list);
        }
      } else {
        const fb = await fetch("/data/t1_routes_sample.json");
        if (fb.ok) {
          const fbData = await fb.json();
          setRoutesData(fbData.routes);
          if (onSelectRoute && fbData.routes) {
            const list = Object.values(fbData.routes) as T1RouteInfo[];
            onSelectRoute(fbData.routes[selectedKey] || list[0], list);
          }
        }
      }
    } catch (err) {
      try {
        const fb = await fetch("/data/t1_routes_sample.json");
        if (fb.ok) {
          const fbData = await fb.json();
          setRoutesData(fbData.routes);
          if (onSelectRoute && fbData.routes) {
            const list = Object.values(fbData.routes) as T1RouteInfo[];
            onSelectRoute(fbData.routes[selectedKey] || list[0], list);
          }
        }
      } catch (e) {
        console.error("Failed to load T1 routes:", e);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchT1Routes(isRain);
  }, [isRain]);

  const handleSelect = (key: string) => {
    setSelectedKey(key);
    if (routesData && onSelectRoute) {
      const list = Object.values(routesData);
      onSelectRoute(routesData[key], list);
    }
  };

  if (isLoading || !routesData) {
    return (
      <div className="py-12 text-center font-mono text-xs text-[#777777]">
        Đang nạp 4 tuyến Pareto từ đồ thị Bình Thạnh...
      </div>
    );
  }

  const selectedRoute = routesData[selectedKey];
  const keys = ["fastest", "shortest", "stable", "easiest"];

  return (
    <div className="space-y-5 text-xs text-[#111111] font-sans">
      {/* Header Info */}
      <div className="pb-3 border-b border-[#e5e5e5]">
        <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider">
          <span>TẦNG T1 — ĐỊNH TUYẾN ĐA TIÊU CHÍ (A → B)</span>
          <span>PARETO SET</span>
        </div>
        <h2 className="text-sm font-bold text-[#111111] mt-1">
          4 Tuyến Đường Đặc Trưng Cho Xe Máy
        </h2>
        <p className="text-[11px] text-[#555555] mt-0.5 leading-snug">
          Lọc tập Pareto không bị lấn át trên cự ly mét, thời gian kỳ vọng, phân vị p90 và độ an toàn rẽ trái cắt dòng xe.
        </p>

        {/* Rain Filter Toggle */}
        <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#f0f0f0]">
          <span className="text-[11px] text-[#666666]">Hệ số cản mưa bão (1.40x):</span>
          <button
            onClick={() => setIsRain(!isRain)}
            className={`px-2 py-0.5 font-mono text-[10px] transition ${
              isRain
                ? "bg-[#111111] text-white font-bold"
                : "border border-[#d4d4d4] text-[#555555] hover:border-[#111111]"
            }`}
          >
            {isRain ? "ĐANG BẬT MƯA [1.4x]" : "ĐƯỜNG KHÔ [1.0x]"}
          </button>
        </div>
      </div>

      {/* 4 Flat Archetype Options (Minimalist list with borders, NO boxy cards) */}
      <div className="space-y-1.5 font-mono">
        {keys.map((k) => {
          const r = routesData[k];
          if (!r) return null;
          const isSel = selectedKey === k;
          const meta = ARCHETYPE_ACCENTS[k];

          return (
            <button
              key={k}
              onClick={() => handleSelect(k)}
              className={`w-full p-2.5 text-left border transition flex items-center justify-between ${
                isSel
                  ? "border-[#111111] bg-[#f5f4f0]"
                  : "border-[#e5e5e5] bg-transparent hover:border-[#a3a3a3]"
              }`}
            >
              <div className="flex items-center space-x-2">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: meta.hex }}
                ></span>
                <div>
                  <div className="text-[10px] text-[#777777] uppercase font-bold">
                    {meta.num} / {meta.tag}
                  </div>
                  <div className="text-xs font-sans font-bold text-[#111111]">
                    {r.label}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-xs font-bold text-[#111111]">
                  {r.expected_time_min.toFixed(1)} phút
                </div>
                <div className="text-[10px] text-[#777777]">
                  {(r.distance_m / 1000).toFixed(2)} km
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Detailed Selected Route Metrics (Hairline table format) */}
      {selectedRoute && (
        <div className="pt-3 border-t border-[#e5e5e5] space-y-3">
          <div className="font-mono text-[10px] text-[#777777] uppercase tracking-wider font-bold">
            CHI TIẾT CHỈ SỐ: {selectedRoute.label.toUpperCase()}
          </div>

          <table className="text-[11px] font-mono border-t border-b border-[#e5e5e5]">
            <tbody className="divide-y divide-[#f0f0f0]">
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Cự ly tuyến:</td>
                <td className="py-1.5 text-right font-bold text-[#111111]">{selectedRoute.distance_m.toFixed(1)} mét</td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Thời gian kỳ vọng:</td>
                <td className="py-1.5 text-right font-bold text-[#111111]">{selectedRoute.expected_time_min.toFixed(2)} phút</td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Phân vị 90 (p90):</td>
                <td className="py-1.5 text-right text-[#111111]">{selectedRoute.p90_time_min.toFixed(2)} phút</td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Khúc cua rẽ trái cắt dòng:</td>
                <td className="py-1.5 text-right font-bold text-[#111111]">
                  {selectedRoute.num_left_turns === 0 ? "0 (Không rẽ trái)" : `${selectedRoute.num_left_turns} khúc`}
                </td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Tổng số lần rẽ:</td>
                <td className="py-1.5 text-right text-[#111111]">{selectedRoute.num_turns} lần rẽ</td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Tỷ lệ đoạn hẻm:</td>
                <td className="py-1.5 text-right text-[#111111]">{selectedRoute.alley_ratio_pct.toFixed(1)}%</td>
              </tr>
              <tr>
                <td className="py-1.5 text-left font-sans text-[#555555]">Nút giao có đèn:</td>
                <td className="py-1.5 text-right text-[#111111]">{selectedRoute.num_signals} nút đèn</td>
              </tr>
            </tbody>
          </table>

          {selectedKey === "easiest" && (
            <div className="p-2 border-l-2 border-[#111111] bg-[#f5f4f0] text-[11px] text-[#333333] leading-relaxed">
              <strong>Ưu điểm:</strong> Tuyến này tăng +25.3% cự ly nhưng triệt tiêu hoàn toàn 100% các khúc cua rẽ trái cắt dòng giao thông đối diện, đem lại sự an toàn cao nhất cho tài xế xe máy chặng cuối.
            </div>
          )}
        </div>
      )}

      {/* Traceability */}
      <div className="pt-2 font-mono text-[10px] text-[#888888] border-t border-[#f0f0f0]">
        Dữ liệu đối soát: results/t1_routes_sample.json • Đồ thị SCC 568 nút
      </div>
    </div>
  );
}
