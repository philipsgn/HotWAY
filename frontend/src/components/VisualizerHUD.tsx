"use client";

import React from "react";

export interface AlgorithmOption {
  id: string;
  name: string;
  tag: string;
  description: string;
  badgeColor: string;
}

export const ALGORITHM_OPTIONS: AlgorithmOption[] = [
  {
    id: "a_star",
    name: "A* Search",
    tag: "HEURISTIC",
    description: "Sóng búp elip có định hướng bám sát mục tiêu với Heuristic Haversine h(n)",
    badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
  },
  {
    id: "dijkstra",
    name: "Dijkstra",
    tag: "UNINFORMED",
    description: "Sóng lan truyền tròn 360 độ đẳng hướng duyệt toàn bộ không gian trạng thái",
    badgeColor: "bg-blue-500/20 text-blue-300 border-blue-500/40",
  },
  {
    id: "bidirectional",
    name: "Bidirectional",
    tag: "DUAL FRONT",
    description: "Hai đầu sóng xuất phát đồng thời từ A và B gặp nhau ở điểm hội tụ trung gian",
    badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
  },
  {
    id: "dynamic_c_t",
    name: "HotWAY Dynamic C(t)",
    tag: "TRAFFIC ADAPTIVE",
    description: "Sóng uốn lượn thích nghi né tránh điểm nghẽn kẹt xe đô thị theo thời gian thực",
    badgeColor: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
  },
];

interface VisualizerHUDProps {
  currentAlgorithm: string;
  onSelectAlgorithm: (id: string) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onStepForward: () => void;
  onReset: () => void;
  speed: number;
  onChangeSpeed: (s: number) => void;
  currentStep: number;
  totalSteps: number;
  metrics: {
    compute_time_ms: number;
    distance_km: number;
    estimated_time_min: number;
    nodes_visited_count: number;
  };
  isLoading: boolean;
  onRunSolve: () => void;
  startSelected: boolean;
  destSelected: boolean;
}

export default function VisualizerHUD({
  currentAlgorithm,
  onSelectAlgorithm,
  isPlaying,
  onTogglePlay,
  onStepForward,
  onReset,
  speed,
  onChangeSpeed,
  currentStep,
  totalSteps,
  metrics,
  isLoading,
  onRunSolve,
  startSelected,
  destSelected,
}: VisualizerHUDProps) {
  const activeAlgo = ALGORITHM_OPTIONS.find((a) => a.id === currentAlgorithm) || ALGORITHM_OPTIONS[0];
  const progressPct = totalSteps > 0 ? Math.min(100, Math.round((currentStep / totalSteps) * 100)) : 0;

  return (
    <div className="space-y-3 font-sans">
      {/* 1. Algorithm Selection Segmented Control */}
      <div className="bg-[#09090b]/90 backdrop-blur-md border border-neutral-800 p-2.5">
        <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-neutral-800 font-mono text-[10px] text-neutral-400">
          <span className="uppercase tracking-widest font-bold text-neutral-300">THUẬT TOÁN ĐỊNH TUYẾN</span>
          <span className="text-emerald-400 font-bold">REAL-TIME GRAPH SOLVER</span>
        </div>

        <div className="grid grid-cols-2 gap-1.5 font-mono text-xs">
          {ALGORITHM_OPTIONS.map((algo) => {
            const isSelected = algo.id === currentAlgorithm;
            return (
              <button
                key={algo.id}
                onClick={() => onSelectAlgorithm(algo.id)}
                className={`p-2 text-left border transition flex flex-col justify-between ${
                  isSelected
                    ? "border-cyan-500 bg-cyan-950/30 text-white shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                    : "border-neutral-800 bg-neutral-900/60 text-neutral-400 hover:border-neutral-700 hover:text-neutral-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold">{algo.name}</span>
                  <span className={`text-[8px] px-1 py-0.2 border ${algo.badgeColor}`}>
                    {algo.tag}
                  </span>
                </div>
                <div className="text-[10px] text-neutral-500 mt-1 line-clamp-1 font-sans">
                  {algo.description}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Playback Timeline Controls */}
      <div className="bg-[#09090b]/90 backdrop-blur-md border border-neutral-800 p-3 space-y-3">
        <div className="flex items-center justify-between font-mono text-xs">
          <div className="flex items-center space-x-2">
            <button
              onClick={onTogglePlay}
              disabled={totalSteps === 0 || isLoading}
              className={`px-3 py-1.5 font-bold border transition flex items-center space-x-1.5 ${
                isPlaying
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
                  : "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 hover:bg-cyan-500/30 disabled:opacity-40"
              }`}
            >
              <span>{isPlaying ? "TẠM DỪNG [⏸]" : "PHÁT SÓNG [▶]"}</span>
            </button>

            <button
              onClick={onStepForward}
              disabled={isPlaying || totalSteps === 0 || currentStep >= totalSteps}
              className="px-2.5 py-1.5 border border-neutral-700 hover:border-neutral-500 text-neutral-300 hover:text-white transition disabled:opacity-40"
              title="Tua 1 bước"
            >
              TIẾN [⏭]
            </button>

            <button
              onClick={onReset}
              disabled={totalSteps === 0}
              className="px-2.5 py-1.5 border border-neutral-700 hover:border-neutral-500 text-neutral-400 hover:text-neutral-200 transition disabled:opacity-40"
              title="Khởi tạo lại"
            >
              RESET [↺]
            </button>
          </div>

          {/* Speed Selector Buttons */}
          <div className="flex items-center space-x-1 border border-neutral-800 p-0.5">
            {[1, 5, 15, 30, 50].map((s) => (
              <button
                key={s}
                onClick={() => onChangeSpeed(s)}
                className={`px-1.5 py-0.5 text-[10px] transition ${
                  speed === s
                    ? "bg-neutral-200 text-neutral-900 font-bold"
                    : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Progress Timeline Bar */}
        <div className="space-y-1">
          <div className="flex items-center justify-between font-mono text-[10px] text-neutral-400">
            <span>TIẾN ĐỘ DUYỆT ĐỒ THỊ</span>
            <span>
              {currentStep} / {totalSteps} BƯỚC ({progressPct}%)
            </span>
          </div>
          <div className="w-full h-1.5 bg-neutral-900 border border-neutral-800 overflow-hidden">
            <div
              className="h-full bg-cyan-400 transition-[width] duration-75 shadow-[0_0_8px_rgba(6,182,212,0.8)]"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* 3. Live Analytics HUD Matrix */}
      <div className="bg-[#09090b]/90 backdrop-blur-md border border-neutral-800 p-3 space-y-2 font-mono">
        <div className="flex items-center justify-between text-[10px] text-neutral-400 uppercase tracking-widest pb-1 border-b border-neutral-800">
          <span>CHỈ SỐ THỰC THI (ANALYTICS HUD)</span>
          <span className="text-cyan-400">FPS: ~60 (CANVAS ACCEL)</span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="p-2 border border-neutral-800/80 bg-neutral-950/40">
            <span className="text-[10px] text-neutral-500 block">NÚT ĐÃ DUYỆT</span>
            <span className="text-base font-bold text-cyan-400">
              {currentStep} / {metrics.nodes_visited_count || totalSteps}
            </span>
          </div>

          <div className="p-2 border border-neutral-800/80 bg-neutral-950/40">
            <span className="text-[10px] text-neutral-500 block">ĐỘ TRỄ THUẬT TOÁN</span>
            <span className="text-base font-bold text-emerald-400">
              {metrics.compute_time_ms} ms
            </span>
          </div>

          <div className="p-2 border border-neutral-800/80 bg-neutral-950/40">
            <span className="text-[10px] text-neutral-500 block">CỰ LY LỘ TRÌNH</span>
            <span className="text-base font-bold text-amber-400">
              {metrics.distance_km} km
            </span>
          </div>

          <div className="p-2 border border-neutral-800/80 bg-neutral-950/40">
            <span className="text-[10px] text-neutral-500 block">DỰ TÍNH XE MÁY</span>
            <span className="text-base font-bold text-purple-400">
              {metrics.estimated_time_min} phút
            </span>
          </div>
        </div>

        {/* Visualizer Legend */}
        <div className="pt-2 border-t border-neutral-800 flex items-center justify-between text-[10px] text-neutral-400">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_6px_#00f0ff]"></span>
            <span>Wavefront (Cyan)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-pink-500 shadow-[0_0_6px_#ec4899]"></span>
            <span>Queue (Magenta)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_#f59e0b]"></span>
            <span>Final Path (Gold)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
