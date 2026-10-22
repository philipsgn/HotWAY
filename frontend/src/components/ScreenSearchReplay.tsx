"use client";

import React, { useEffect, useState } from "react";
import { Play, Pause, RotateCcw, Activity, Check, X as XIcon, HelpCircle } from "lucide-react";

interface SearchStepTrace {
  step: number;
  action: number;
  operator: string;
  applied: boolean;
  delta: number;
  cost: number;
  best_cost: number;
  routes?: number[][];
}

interface ScreenSearchReplayProps {
  searchTrace: SearchStepTrace[];
  strategyName: string;
}

export default function ScreenSearchReplay({
  searchTrace,
  strategyName,
}: ScreenSearchReplayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<1 | 4 | 16>(1);

  const totalSteps = searchTrace.length > 0 ? searchTrace.length - 1 : 0;

  useEffect(() => {
    if (!isPlaying || totalSteps === 0) return;

    const intervalTime = Math.max(25, 400 / playbackSpeed);
    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= totalSteps) {
          setIsPlaying(false);
          return totalSteps;
        }
        return prev + 1;
      });
    }, intervalTime);

    return () => clearInterval(timer);
  }, [isPlaying, totalSteps, playbackSpeed]);

  if (searchTrace.length === 0) {
    return (
      <div className="p-8 text-center bg-surface border border-dashed border-border-warm rounded-warm space-y-2">
        <Activity className="w-8 h-8 text-secondary-text mx-auto opacity-40" />
        <p className="text-xs text-secondary-text">Chưa có vết tìm kiếm (Search Trace).</p>
        <p className="text-[11px] text-secondary-text/80 italic">
          Chuyển sang tab &quot;Lập kế hoạch&quot; và bấm &quot;Lập tuyến&quot; để ghi lại vết quyết định.
        </p>
      </div>
    );
  }

  const activeStepData = searchTrace[currentStep] || searchTrace[0];
  const initialCost = searchTrace[0]?.cost || 1.0;
  const currentCost = activeStepData.cost;
  const improvementSoFar = Math.max(0, ((initialCost - currentCost) / initialCost) * 100);

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="p-3 bg-surface border border-border-warm rounded-warm shadow-soft flex items-center justify-between">
        <div>
          <span className="text-[10px] font-mono tracking-wider uppercase text-brand-gold font-bold block">
            TIẾN TRÌNH TỐI ƯU HÓA
          </span>
          <h3 className="text-xs font-bold text-primary-text">
            Thuật toán: {strategyName.toUpperCase()}
          </h3>
        </div>

        {/* Speed Controls */}
        <div className="flex items-center space-x-1 font-mono text-xs">
          <span className="text-[10px] text-secondary-text mr-1">Tốc độ:</span>
          {([1, 4, 16] as const).map((spd) => (
            <button
              key={spd}
              onClick={() => setPlaybackSpeed(spd)}
              className={`px-2 py-0.5 rounded-lg text-[11px] font-bold transition ${
                playbackSpeed === spd
                  ? "bg-brand-gold text-primary-text shadow-xs"
                  : "bg-sunken text-secondary-text hover:bg-border-warm"
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>

      {/* Playback Controls & Scrubber Slider */}
      <div className="p-3.5 bg-surface border border-border-warm rounded-warm shadow-soft space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-3 py-1.5 rounded-xl bg-brand-gold hover:bg-brand-gold-hover text-primary-text text-xs font-bold shadow-soft transition flex items-center space-x-1"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isPlaying ? "Tạm dừng" : "Phát lại"}</span>
            </button>
            <button
              onClick={() => {
                setIsPlaying(false);
                setCurrentStep(0);
              }}
              title="Về bước đầu tiên"
              className="p-1.5 rounded-xl border border-border-warm text-secondary-text hover:bg-sunken hover:text-primary-text transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="text-xs font-mono text-secondary-text">
            Bước: <span className="font-bold text-primary-text">{currentStep}</span> / {totalSteps}
          </div>
        </div>

        {/* Range Slider */}
        <input
          type="range"
          min="0"
          max={totalSteps}
          value={currentStep}
          onChange={(e) => {
            setIsPlaying(false);
            setCurrentStep(parseInt(e.target.value));
          }}
          className="w-full accent-[#E0A83A] cursor-pointer h-2 bg-sunken rounded-lg"
        />
      </div>

      {/* Step Highlight Cards */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2.5 bg-sunken/60 rounded-xl border border-border-warm/70">
          <span className="text-[10px] font-mono text-secondary-text uppercase block">
            Toán tử chọn
          </span>
          <span className="text-xs font-bold text-primary-text font-mono mt-0.5 block truncate">
            {activeStepData.operator}
          </span>
        </div>

        <div className="p-2.5 bg-sunken/60 rounded-xl border border-border-warm/70">
          <span className="text-[10px] font-mono text-secondary-text uppercase block">
            Trạng thái bước
          </span>
          <span
            className={`text-xs font-bold font-mono mt-0.5 flex items-center space-x-1 ${
              activeStepData.applied ? "text-status-success" : "text-secondary-text"
            }`}
          >
            {activeStepData.applied ? (
              <>
                <Check className="w-3 h-3 text-status-success" />
                <span>Chấp nhận (Δ &lt; 0)</span>
              </>
            ) : (
              <>
                <XIcon className="w-3 h-3 text-secondary-text" />
                <span>Bỏ qua (Δ &ge; 0)</span>
              </>
            )}
          </span>
        </div>

        <div className="p-2.5 bg-sunken/60 rounded-xl border border-border-warm/70">
          <span className="text-[10px] font-mono text-secondary-text uppercase block">
            Quãng đường bước
          </span>
          <span className="text-xs font-bold text-primary-text font-mono mt-0.5 block">
            {(currentCost / 1000).toFixed(2)} km
          </span>
        </div>

        <div className="p-2.5 bg-sunken/60 rounded-xl border border-border-warm/70">
          <span className="text-[10px] font-mono text-secondary-text uppercase block">
            Cải thiện tích lũy
          </span>
          <span className="text-xs font-bold text-status-success font-mono mt-0.5 block">
            +{improvementSoFar.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Convergence Chart SVG */}
      <div className="p-3.5 bg-surface border border-border-warm rounded-warm shadow-soft space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-secondary-text">
          <span className="text-[11px] font-bold text-primary-text">
            Đường cong hội tụ chi phí C(t)
          </span>
          <span className="text-[10px]">
            Tốt nhất: {(activeStepData.best_cost / 1000).toFixed(2)} km
          </span>
        </div>

        <div className="h-32 relative bg-sunken/40 rounded-xl border border-border-warm p-2">
          <svg className="w-full h-full" viewBox="0 0 100 50" preserveAspectRatio="none">
            {/* Horizontal baseline */}
            <line x1="0" y1="46" x2="100" y2="46" stroke="#E6D9BC" strokeWidth="0.5" />

            {/* Step-by-step cost path */}
            {(() => {
              if (searchTrace.length < 2) return null;
              const maxC = searchTrace[0].cost;
              const minC = searchTrace[searchTrace.length - 1].best_cost;
              const range = Math.max(maxC - minC, 1.0);

              const coords = searchTrace.map((st, i) => {
                const x = (i / totalSteps) * 100;
                const y = 6 + ((st.cost - minC) / range) * 36;
                return { x, y };
              });

              const fullPathStr = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
              const currentX = (currentStep / totalSteps) * 100;

              return (
                <>
                  <path d={fullPathStr} fill="none" stroke="#8A7355" strokeWidth="1" />
                  {/* Current progress line */}
                  <line
                    x1={currentX}
                    y1="0"
                    x2={currentX}
                    y2="50"
                    stroke="#E0A83A"
                    strokeWidth="1"
                    strokeDasharray="2"
                  />
                  {/* Current point */}
                  <circle
                    cx={coords[currentStep]?.x || 0}
                    cy={coords[currentStep]?.y || 0}
                    r="2.2"
                    fill="#E0A83A"
                    stroke="#FFFDF7"
                    strokeWidth="0.8"
                  />
                </>
              );
            })()}
          </svg>
        </div>
      </div>
    </div>
  );
}
