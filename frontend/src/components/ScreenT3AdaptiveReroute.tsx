"use client";

import React, { useState, useEffect, useRef } from "react";

interface TelemetryEvent {
  event_type: "INIT" | "PROGRESS" | "REROUTE" | "COMPLETE";
  step?: number;
  current_node?: number;
  coordinates?: [number, number]; // [lat, lon]
  congestion_state?: number; // 0: Clear, 1: Slow, 2: Congested
  step_duration_sec?: number;
  cumulative_time_min?: number;
  is_reroute?: boolean;
  total_travel_time_min?: number;
  steps_taken?: number;
  policy?: string;
  attribution?: string;
}

interface ScreenT3AdaptiveRerouteProps {
  onUpdateSimVehicle?: (vehicle: { lat: number; lon: number; vehicle_id: number; heading?: number } | null) => void;
  onUpdateRouteGeometry?: (coords: [number, number][]) => void;
}

const CONGESTION_LABELS: Record<number, string> = {
  0: "Thông thoáng",
  1: "Di chuyển chậm",
  2: "Kẹt xe",
};

export default function ScreenT3AdaptiveReroute({
  onUpdateSimVehicle,
  onUpdateRouteGeometry,
}: ScreenT3AdaptiveRerouteProps) {
  const [policy, setPolicy] = useState<string>("dynamic_dijkstra");
  const [isRain, setIsRain] = useState<boolean>(false);
  const [isIncident, setIsIncident] = useState<boolean>(false);
  const [speedMult, setSpeedMult] = useState<number>(10.0);
  const [seed, setSeed] = useState<number>(2026);

  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isComplete, setIsComplete] = useState<boolean>(false);
  const [eventsFeed, setEventsFeed] = useState<TelemetryEvent[]>([]);
  const [latestEvent, setLatestEvent] = useState<TelemetryEvent | null>(null);
  const [rerouteCount, setRerouteCount] = useState<number>(0);
  const [cumulativeTimeMin, setCumulativeTimeMin] = useState<number>(0.0);

  const eventSourceRef = useRef<EventSource | null>(null);

  const stopStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsPlaying(false);
  };

  const startStream = () => {
    stopStream();
    setIsPlaying(true);
    setIsComplete(false);
    setEventsFeed([]);
    setRerouteCount(0);
    setCumulativeTimeMin(0.0);

    const url = `http://localhost:8000/api/v1/sim/stream?policy=${policy}&rain=${isRain}&incident=${isIncident}&speed_mult=${speedMult}&seed=${seed}`;
    const es = new EventSource(url);
    eventSourceRef.current = es;

    const collectedCoords: [number, number][] = [];

    es.addEventListener("init", (e: MessageEvent) => {
      try {
        const payload: TelemetryEvent = JSON.parse(e.data);
        setLatestEvent(payload);
        setEventsFeed((prev) => [payload, ...prev.slice(0, 30)]);
      } catch (err) {
        console.error("Init parse error:", err);
      }
    });

    es.addEventListener("step", (e: MessageEvent) => {
      try {
        const payload: TelemetryEvent = JSON.parse(e.data);
        setLatestEvent(payload);
        if (payload.cumulative_time_min !== undefined) {
          setCumulativeTimeMin(payload.cumulative_time_min);
        }
        setEventsFeed((prev) => [payload, ...prev.slice(0, 30)]);

        if (payload.coordinates && onUpdateSimVehicle) {
          collectedCoords.push(payload.coordinates);
          onUpdateSimVehicle({
            lat: payload.coordinates[0],
            lon: payload.coordinates[1],
            vehicle_id: 1,
          });
          if (onUpdateRouteGeometry) {
            onUpdateRouteGeometry([...collectedCoords]);
          }
        }
      } catch (err) {
        console.error("Step parse error:", err);
      }
    });

    es.addEventListener("reroute", (e: MessageEvent) => {
      try {
        const payload: TelemetryEvent = JSON.parse(e.data);
        payload.is_reroute = true;
        setLatestEvent(payload);
        setRerouteCount((c) => c + 1);
        if (payload.cumulative_time_min !== undefined) {
          setCumulativeTimeMin(payload.cumulative_time_min);
        }
        setEventsFeed((prev) => [payload, ...prev.slice(0, 30)]);

        if (payload.coordinates && onUpdateSimVehicle) {
          collectedCoords.push(payload.coordinates);
          onUpdateSimVehicle({
            lat: payload.coordinates[0],
            lon: payload.coordinates[1],
            vehicle_id: 1,
          });
          if (onUpdateRouteGeometry) {
            onUpdateRouteGeometry([...collectedCoords]);
          }
        }
      } catch (err) {
        console.error("Reroute parse error:", err);
      }
    });

    es.addEventListener("complete", (e: MessageEvent) => {
      try {
        const payload: TelemetryEvent = JSON.parse(e.data);
        setLatestEvent(payload);
        setIsComplete(true);
        setIsPlaying(false);
        setEventsFeed((prev) => [payload, ...prev.slice(0, 30)]);
        es.close();
      } catch (err) {
        console.error("Complete parse error:", err);
      }
    });

    es.onerror = () => {
      stopStream();
    };
  };

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, []);

  return (
    <div className="space-y-4 text-xs text-[#111111] font-sans">
      {/* Header Info */}
      <div className="pb-3 border-b border-[#e5e5e5]">
        <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase tracking-wider">
          <span>TẦNG T3 — ĐỔI ĐƯỜNG THÍCH NGHI (SSE STREAM)</span>
          <span className="font-bold text-[#111111]">MÔ PHỎNG</span>
        </div>
        <h2 className="text-sm font-bold text-[#111111] mt-1">
          Mô Phỏng Từng Bước Di Chuyển Thời Gian Thực
        </h2>
        <p className="text-[11px] text-[#555555] mt-0.5 leading-snug">
          Truyền phát Server-Sent Events qua cổng 8000. So sánh khả năng tránh điểm nghẽn của Dynamic Dijkstra và DQN.
        </p>
      </div>

      {/* Policy Selector & Toggles */}
      <div className="space-y-2.5 pb-3 border-b border-[#e5e5e5]">
        <div>
          <label className="text-[11px] font-bold text-[#111111] block mb-1">
            Chính sách định tuyến:
          </label>
          <div className="grid grid-cols-3 gap-1.5 font-mono text-[10px]">
            <button
              onClick={() => {
                setPolicy("dynamic_dijkstra");
                if (isPlaying) stopStream();
              }}
              className={`p-1.5 text-left border transition ${
                policy === "dynamic_dijkstra"
                  ? "border-[#111111] bg-[#f5f4f0] font-bold text-[#111111]"
                  : "border-[#e5e5e5] text-[#555555] hover:border-[#111111]"
              }`}
            >
              [1] Dynamic Dijkstra
              <span className="block text-[9px] text-[#777777] font-normal">Khuyên dùng</span>
            </button>

            <button
              onClick={() => {
                setPolicy("static_dijkstra");
                if (isPlaying) stopStream();
              }}
              className={`p-1.5 text-left border transition ${
                policy === "static_dijkstra"
                  ? "border-[#111111] bg-[#f5f4f0] font-bold text-[#111111]"
                  : "border-[#e5e5e5] text-[#555555] hover:border-[#111111]"
              }`}
            >
              [2] Static Dijkstra
              <span className="block text-[9px] text-[#777777] font-normal">Cố định</span>
            </button>

            <button
              onClick={() => {
                setPolicy("edge_dqn");
                if (isPlaying) stopStream();
              }}
              className={`p-1.5 text-left border transition ${
                policy === "edge_dqn"
                  ? "border-[#111111] bg-[#f5f4f0] font-bold text-[#111111]"
                  : "border-[#e5e5e5] text-[#555555] hover:border-[#111111]"
              }`}
            >
              [3] Edge-Scoring DQN
              <span className="block text-[9px] text-[#777777] font-normal">Kết quả âm tính</span>
            </button>
          </div>
        </div>

        {/* Toggles */}
        <div className="flex items-center space-x-3 text-[10px] font-mono">
          <button
            onClick={() => setIsRain(!isRain)}
            className={`px-2 py-0.5 border transition ${
              isRain ? "bg-[#111111] text-white font-bold" : "border-[#d4d4d4] text-[#555555]"
            }`}
          >
            MƯA (1.40x): {isRain ? "ON" : "OFF"}
          </button>

          <button
            onClick={() => setIsIncident(!isIncident)}
            className={`px-2 py-0.5 border transition ${
              isIncident ? "bg-[#111111] text-white font-bold" : "border-[#d4d4d4] text-[#555555]"
            }`}
          >
            SỰ CỐ NGHẼN: {isIncident ? "ON" : "OFF"}
          </button>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between pt-2 border-t border-[#f0f0f0]">
          <div className="flex items-center space-x-2">
            {!isPlaying ? (
              <button
                onClick={startStream}
                className="px-3 py-1 bg-[#111111] hover:bg-[#333333] text-white font-bold text-xs transition"
              >
                {isComplete ? "Chạy Lại →" : "Bắt Đầu Mô Phỏng →"}
              </button>
            ) : (
              <button
                onClick={stopStream}
                className="px-3 py-1 bg-red-800 text-white font-bold text-xs transition"
              >
                Tạm Dừng [||]
              </button>
            )}

            <button
              onClick={() => {
                stopStream();
                startStream();
              }}
              className="px-2 py-1 border border-[#d4d4d4] text-[#555555] hover:border-[#111111] text-xs font-mono"
            >
              Reset
            </button>
          </div>

          <div className="flex items-center space-x-1 font-mono text-[10px] text-[#777777]">
            <span>Tốc độ:</span>
            {[5, 10, 20].map((s) => (
              <button
                key={s}
                onClick={() => setSpeedMult(s)}
                className={`px-1.5 py-0.5 font-bold transition ${
                  speedMult === s ? "bg-[#111111] text-white" : "border border-[#e5e5e5] text-[#555555]"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Live Telemetry Stats (3-column open text stats) */}
      <div className="grid grid-cols-3 gap-2 py-2 border-b border-[#e5e5e5] font-mono text-[11px]">
        <div>
          <span className="text-[10px] text-[#777777] block">Tích lũy:</span>
          <span className="text-sm font-bold text-[#111111]">{cumulativeTimeMin.toFixed(2)}m</span>
        </div>
        <div>
          <span className="text-[10px] text-[#777777] block">Bước rẽ:</span>
          <span className="text-sm font-bold text-[#111111]">{latestEvent?.step || 0}</span>
        </div>
        <div>
          <span className="text-[10px] text-[#777777] block">Đổi đường:</span>
          <span className="text-sm font-bold text-[#111111]">{rerouteCount} lần</span>
        </div>
      </div>

      {/* Event Stream Log */}
      <div className="space-y-1">
        <div className="flex items-center justify-between font-mono text-[10px] text-[#777777] uppercase font-bold">
          <span>NHẬT KÝ SỰ KIỆN VIỄN TRẮC (SSE)</span>
          <span>{isPlaying ? "Đang truyền phát..." : isComplete ? "Hoàn tất" : "Sẵn sàng"}</span>
        </div>

        <div className="max-h-40 overflow-y-auto font-mono text-[10px] border border-[#e5e5e5] p-2 space-y-1">
          {eventsFeed.length === 0 ? (
            <div className="text-[#888888] py-4 text-center font-sans text-xs">
              Bấm &ldquo;Bắt Đầu Mô Phỏng&rdquo; để khởi động luồng viễn trắc.
            </div>
          ) : (
            eventsFeed.map((ev, idx) => (
              <div
                key={idx}
                className={`py-0.5 border-b border-[#f5f5f5] ${
                  ev.event_type === "REROUTE"
                    ? "font-bold text-amber-900 bg-amber-50"
                    : ev.event_type === "COMPLETE"
                    ? "font-bold text-emerald-900 bg-emerald-50"
                    : "text-[#333333]"
                }`}
              >
                <span>
                  {ev.event_type === "INIT" && "▶ KHỞI TẠO HÀNH TRÌNH"}
                  {ev.event_type === "PROGRESS" && `[BƯỚC ${ev.step}] Nút ${ev.current_node}`}
                  {ev.event_type === "REROUTE" && `⚡ ĐỔI ĐƯỜNG TẠI BƯỚC ${ev.step}`}
                  {ev.event_type === "COMPLETE" && `✔ HOÀN TẤT: ${ev.total_travel_time_min} phút`}
                </span>
                {ev.congestion_state !== undefined && (
                  <span className="text-[#777777] ml-2">
                    ({CONGESTION_LABELS[ev.congestion_state]})
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Insight */}
      <div className="border-l-2 border-[#111111] pl-3 py-1.5 bg-[#f5f4f0] text-[10px] text-[#333333] leading-relaxed">
        <strong>Dynamic Dijkstra</strong> giải lại đường đi trong &lt; 1 ms trên 2 nhân CPU. Tác tử DQN bị tích lũy sai số xấp xỉ giá trị qua chuỗi 20 - 30 bước rẽ, gặp số lần tắc đường cao gấp 3 - 5 lần.
      </div>
    </div>
  );
}
