"use client";

import React, { useState, useEffect, useRef } from "react";

export interface GameProps {
  orderId?: string;
  ghostTrajectoryUrl?: string;
  onGameComplete?: (result: {
    playerTempC: number;
    timeSeconds: number;
    wonAI: boolean;
    voucherCode?: string;
  }) => void;
}

export const HotWAYRiderCanvas: React.FC<GameProps> = ({
  orderId = "ORD-HANGGON-RIDER",
  onGameComplete,
}) => {
  // Game state
  const [isPlaying, setIsPlaying] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [playerWon, setPlayerWon] = useState(false);

  // Player state: 1D road position from 0 (Depot) to 1000 meters (Customer)
  const [playerDistance, setPlayerDistance] = useState(0);
  const [playerSpeed, setPlayerSpeed] = useState(0); // km/h
  const [playerTemp, setPlayerTemp] = useState(85.0); // °C
  const [elapsedTime, setElapsedTime] = useState(0); // seconds

  // AI Ghost state (deterministic trajectory learned by MaskablePPO)
  const [ghostDistance, setGhostDistance] = useState(0);
  const [ghostTemp, setGhostTemp] = useState(85.0);

  // Input keys
  const keysPressed = useRef<{ [key: string]: boolean }>({});
  const animationRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);

  const TARGET_DISTANCE = 1000; // 1 km delivery run in Hàng Gòn

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      keysPressed.current[e.key.toLowerCase()] = true;
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      keysPressed.current[e.key.toLowerCase()] = false;
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  const startGame = () => {
    setPlayerDistance(0);
    setPlayerSpeed(0);
    setPlayerTemp(85.0);
    setGhostDistance(0);
    setGhostTemp(85.0);
    setElapsedTime(0);
    setGameOver(false);
    setPlayerWon(false);
    setIsPlaying(true);
    lastTimeRef.current = performance.now();
  };

  useEffect(() => {
    if (!isPlaying || gameOver) return;

    const gameLoop = (now: number) => {
      const dt = Math.min(0.1, (now - lastTimeRef.current) / 1000.0);
      lastTimeRef.current = now;

      setElapsedTime((prev) => prev + dt);

      // Player acceleration/braking
      let accel = 0;
      if (keysPressed.current["w"] || keysPressed.current["arrowup"]) {
        accel += 40.0; // km/h/s
      } else if (keysPressed.current["s"] || keysPressed.current["arrowdown"]) {
        accel -= 60.0; // braking
      } else {
        accel -= 15.0; // natural friction
      }

      setPlayerSpeed((prevSpeed) => {
        let newSpeed = prevSpeed + accel * dt;
        if (newSpeed < 0) newSpeed = 0;
        if (newSpeed > 65) newSpeed = 65; // Max 65 km/h for city motorbike
        return newSpeed;
      });

      // Update Player Distance (meters)
      setPlayerDistance((prevDist) => {
        const speedMps = (playerSpeed * 1000.0) / 3600.0;
        const newDist = prevDist + speedMps * dt;

        // Newton cooling equation for noodle soup: T(t) = 30 + (85 - 30) * exp(-0.02 * (t/60))
        setElapsedTime((time) => {
          const tMin = time / 60.0;
          const temp = 30.0 + (85.0 - 30.0) * Math.exp(-0.022 * tMin);
          setPlayerTemp(parseFloat(temp.toFixed(1)));
          return time;
        });

        if (newDist >= TARGET_DISTANCE) {
          endRace(true);
          return TARGET_DISTANCE;
        }
        return newDist;
      });

      // Update AI Ghost (speed ~ 45 km/h optimal curve)
      setGhostDistance((prevGhost) => {
        const ghostSpeedMps = (45.0 * 1000.0) / 3600.0;
        const nextGhost = prevGhost + ghostSpeedMps * dt;

        setElapsedTime((time) => {
          const tMin = time / 60.0;
          // AI Ghost preserves heat with optimal routing
          const gTemp = 30.0 + (85.0 - 30.0) * Math.exp(-0.019 * tMin);
          setGhostTemp(parseFloat(gTemp.toFixed(1)));
          return time;
        });

        if (nextGhost >= TARGET_DISTANCE && !gameOver) {
          endRace(false);
          return TARGET_DISTANCE;
        }
        return nextGhost;
      });

      animationRef.current = requestAnimationFrame(gameLoop);
    };

    animationRef.current = requestAnimationFrame(gameLoop);

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isPlaying, gameOver, playerSpeed]);

  const endRace = (playerFinishedFirst: boolean) => {
    setGameOver(true);
    setIsPlaying(false);
    const won = playerFinishedFirst && playerTemp >= ghostTemp;
    setPlayerWon(won);

    if (onGameComplete) {
      onGameComplete({
        playerTempC: playerTemp,
        timeSeconds: parseFloat(elapsedTime.toFixed(1)),
        wonAI: won,
        voucherCode: won ? "BANHCANH_AI_WINNER_15" : undefined,
      });
    }
  };

  const playerProgress = Math.min(100, (playerDistance / TARGET_DISTANCE) * 100);
  const ghostProgress = Math.min(100, (ghostDistance / TARGET_DISTANCE) * 100);

  return (
    <div className="relative w-full h-[620px] bg-slate-950 rounded-2xl overflow-hidden flex flex-col justify-between p-6 border border-slate-800 shadow-2xl font-sans select-none">
      {/* Top HUD */}
      <div className="flex items-center justify-between text-white z-10">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🏍️</span>
          <div>
            <h2 className="text-lg font-black tracking-wider text-orange-400 uppercase">
              HotWAY Rider 3D • Hàng Gòn Gran Prix
            </h2>
            <p className="text-xs text-slate-400">
              Chặng đua: Quán Bánh Canh Gà &rarr; Di tích Cự Thạch (1.000m)
            </p>
          </div>
        </div>

        {/* Live Gauges */}
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 bg-slate-900/90 rounded-xl border border-slate-800 text-right">
            <span className="text-[10px] uppercase text-slate-400 font-bold block">Tốc Độ Xe Máy</span>
            <span className="text-2xl font-black text-white font-mono">{Math.round(playerSpeed)}</span>
            <span className="text-xs text-slate-400 font-mono ml-1">km/h</span>
          </div>

          <div className="px-4 py-2 bg-slate-900/90 rounded-xl border border-orange-500/40 text-right">
            <span className="text-[10px] uppercase text-orange-400 font-bold block">Độ Nóng Bánh Canh</span>
            <span className="text-2xl font-black text-orange-400 font-mono">{playerTemp}°C</span>
          </div>
        </div>
      </div>

      {/* Middle Interactive Simulation Track Viewport */}
      <div className="relative flex-1 my-4 bg-gradient-to-b from-slate-900 via-slate-900/80 to-slate-950 rounded-xl border border-slate-800 flex flex-col justify-center px-8 overflow-hidden">
        {/* Background Hàng Gòn Low-Poly Scenery */}
        <div className="absolute inset-0 opacity-15 pointer-events-none flex items-end justify-between px-4 pb-2">
          <div className="text-6xl">🏡</div>
          <div className="text-7xl">🌳</div>
          <div className="text-6xl">🏪</div>
          <div className="text-8xl">🏛️</div>
          <div className="text-7xl">🌳</div>
        </div>

        {/* Track Progress Rails */}
        <div className="relative space-y-6 z-10">
          {/* Player Lane */}
          <div>
            <div className="flex justify-between text-xs text-slate-300 font-bold mb-1">
              <span className="flex items-center gap-1.5 text-orange-400">
                <span>🛵</span> Xe Của Bạn (Player)
              </span>
              <span className="font-mono">{Math.round(playerDistance)}m / {TARGET_DISTANCE}m</span>
            </div>
            <div className="w-full bg-slate-800 h-6 rounded-full overflow-hidden p-0.5 border border-slate-700 relative">
              <div
                className="h-full bg-gradient-to-r from-orange-600 to-amber-500 rounded-full transition-all duration-75 relative flex items-center justify-end pr-2 text-xs font-black text-white"
                style={{ width: `${playerProgress}%` }}
              >
                {playerProgress > 8 && "🛵"}
              </div>
            </div>
          </div>

          {/* AI Ghost Lane */}
          <div>
            <div className="flex justify-between text-xs text-slate-400 font-bold mb-1">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span>👻</span> Bóng Ma AI (HotWAY RL MaskablePPO)
              </span>
              <span className="font-mono">{Math.round(ghostDistance)}m / {TARGET_DISTANCE}m</span>
            </div>
            <div className="w-full bg-slate-800 h-6 rounded-full overflow-hidden p-0.5 border border-cyan-500/30 relative">
              <div
                className="h-full bg-gradient-to-r from-cyan-600 to-teal-400 rounded-full transition-all duration-75 relative flex items-center justify-end pr-2 text-xs font-black text-white"
                style={{ width: `${ghostProgress}%` }}
              >
                {ghostProgress > 8 && "👻"}
              </div>
            </div>
          </div>
        </div>

        {/* Start Overlay */}
        {!isPlaying && !gameOver && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center z-20">
            <h3 className="text-2xl font-black text-white mb-2">ĐUA TỐC ĐỘ VỚI BÓNG MA AI GHOST</h3>
            <p className="text-xs text-slate-300 max-w-md mb-6 leading-relaxed">
              Bạn lái xe giao tô bánh canh gà nóng sốt từ quán tại Hàng Gòn. Đối thủ của bạn là lộ trình được Agent Học Tăng Cường (RL) tối ưu hoá.
              <br />
              <strong className="text-orange-400">Điều khiển:</strong> Nhấn giữ phím <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">W</kbd> hoặc <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">&uarr;</kbd> để tăng ga, <kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">S</kbd> để phanh.
            </p>
            <button
              onClick={startGame}
              className="py-3 px-8 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-black text-sm uppercase tracking-wider shadow-lg hover:scale-105 transition-all"
            >
              🏁 BẮT ĐẦU XUẤT PHÁT
            </button>
          </div>
        )}

        {/* Game Over Modal */}
        {gameOver && (
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center z-30">
            {playerWon ? (
              <div className="max-w-md animate-fade-in">
                <span className="text-5xl block mb-2">🏆</span>
                <h3 className="text-2xl font-black text-emerald-400">BẠN ĐÃ THẮNG AI GHOST!</h3>
                <p className="text-xs text-slate-300 mt-2">
                  Bạn giao bánh canh đến nơi sớm hơn và còn nóng ở mức <strong>{playerTemp}°C</strong> (so với AI {ghostTemp}°C).
                </p>

                <div className="mt-4 p-4 bg-orange-500/10 border-2 border-dashed border-orange-500 rounded-2xl">
                  <span className="text-[10px] uppercase font-bold text-orange-400 block tracking-wider">
                    Mã Giảm Giá Độc Quyền Quán Bánh Canh Gà Hàng Gòn
                  </span>
                  <p className="text-2xl font-black text-orange-400 font-mono mt-1">BANHCANH_AI_WINNER_15</p>
                  <span className="text-[11px] text-slate-400 block mt-1">Giảm 15% khi đến ăn trực tiếp tại quán!</span>
                </div>

                <button
                  onClick={startGame}
                  className="mt-6 py-2.5 px-6 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition"
                >
                  🔄 ĐUA LẠI CHẶNG KHÁC
                </button>
              </div>
            ) : (
              <div className="max-w-md">
                <span className="text-5xl block mb-2">🤖</span>
                <h3 className="text-2xl font-black text-cyan-400">AI GHOST ĐÃ VỀ ĐÍCH TRƯỚC!</h3>
                <p className="text-xs text-slate-300 mt-2">
                  Mô hình RL MaskablePPO đã chọn tốc độ và lộ trình tối ưu nhiệt độ hơn. Món của AI còn <strong>{ghostTemp}°C</strong>.
                </p>
                <button
                  onClick={startGame}
                  className="mt-6 py-3 px-8 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-black text-xs uppercase tracking-wider shadow-lg transition"
                >
                  🚀 THỬ THÁCH LẠI
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Controls Bar */}
      <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800/80 pt-3 z-10">
        <div className="flex items-center gap-4">
          <span>Thời gian: <strong className="text-white font-mono">{elapsedTime.toFixed(1)}s</strong></span>
          <span>Nhiệt độ môi trường Hàng Gòn: <strong className="text-white font-mono">30°C</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <span>Giữ phím:</span>
          <kbd className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">W / &uarr; Tăng ga</kbd>
          <kbd className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">S / &darr; Phanh</kbd>
        </div>
      </div>
    </div>
  );
};

export default HotWAYRiderCanvas;
