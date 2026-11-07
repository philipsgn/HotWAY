"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import WavefrontCanvas, { WavefrontStep } from "../../components/WavefrontCanvas";
import VisualizerHUD from "../../components/VisualizerHUD";

// Preset landmarks for instant testing
const PRESET_PAIRS = [
  {
    name: "Landmark 81 → Hàng Xanh",
    start: [10.7951, 106.7218],
    end: [10.8014, 106.7112],
  },
  {
    name: "Nhà Thờ Đức Bà → Chợ Bà Chiểu",
    start: [10.7798, 106.6990],
    end: [10.8016, 106.6961],
  },
  {
    name: "Cầu Thị Nghè → ĐH Ngoại Thương",
    start: [10.7905, 106.7052],
    end: [10.8055, 106.7128],
  },
];

export default function AlgorithmVisualizerPage() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Markers
  const startMarkerRef = useRef<maplibregl.Marker | null>(null);
  const endMarkerRef = useRef<maplibregl.Marker | null>(null);

  // Selection states
  const [startPoint, setStartPoint] = useState<[number, number]>(PRESET_PAIRS[0].start as [number, number]);
  const [endPoint, setEndPoint] = useState<[number, number]>(PRESET_PAIRS[0].end as [number, number]);
  const [pinTarget, setPinTarget] = useState<"start" | "end" | "none">("none");

  // Algorithm & Animation states
  const [algorithm, setAlgorithm] = useState<string>("a_star");
  const [steps, setSteps] = useState<WavefrontStep[]>([]);
  const [finalPath, setFinalPath] = useState<[number, number][]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(15);
  const [isPathVisible, setIsPathVisible] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Live Metrics
  const [metrics, setMetrics] = useState({
    compute_time_ms: 0,
    distance_km: 0,
    estimated_time_min: 0,
    nodes_visited_count: 0,
  });

  // 1. Initialize MapLibre with Dark Tone Styling
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Dark styled map configuration
    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [106.712, 10.798], // Center HCMC Binh Thanh
      zoom: 14.2,
      pitch: 20,
      bearing: 0,
      attributionControl: false,
    });

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "HotWAY Research Algorithm Visualizer • OpenStreetMap",
      }),
      "bottom-right"
    );

    map.on("load", () => {
      mapRef.current = map;
      setMapLoaded(true);

      // Apply dark styling to liberty tiles
      const container = map.getCanvasContainer();
      if (container) {
        container.style.filter = "invert(92%) hue-rotate(180deg) brightness(85%) contrast(120%)";
      }
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 2. Fetch and Solve Path from Backend API
  const runPathfinding = useCallback(
    async (s: [number, number], e: [number, number], algo: string) => {
      setIsLoading(true);
      setIsPlaying(false);
      setCurrentStepIndex(0);
      setIsPathVisible(false);

      try {
        const payload = {
          start_coords: s,
          end_coords: e,
          algorithm: algo,
          max_steps: 1200,
        };

        const res = await fetch("http://localhost:8000/api/solve-path", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (res.ok) {
          const json = await res.json();
          const d = json.data;
          setSteps(d.steps || []);
          setFinalPath(d.final_path || []);
          setMetrics(d.metrics || {
            compute_time_ms: 0,
            distance_km: 0,
            estimated_time_min: 0,
            nodes_visited_count: 0,
          });

          // Auto-start playback
          setTimeout(() => setIsPlaying(true), 300);
        } else {
          console.warn("Backend solve-path returned error, using fallback simulated wavefront.");
          simulateFallbackWavefront(s, e, algo);
        }
      } catch (err) {
        console.warn("Could not reach backend :8000, running client simulated wavefront.", err);
        simulateFallbackWavefront(s, e, algo);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Client-side fallback generator for offline demo resilience
  const simulateFallbackWavefront = (s: [number, number], e: [number, number], algo: string) => {
    const generatedSteps: WavefrontStep[] = [];
    const numSteps = algo === "a_star" ? 180 : algo === "dijkstra" ? 420 : 280;
    const path: [number, number][] = [];

    // Interpolate path
    const pathPoints = 25;
    for (let p = 0; p <= pathPoints; p++) {
      const frac = p / pathPoints;
      path.push([s[0] + (e[0] - s[0]) * frac, s[1] + (e[1] - s[1]) * frac]);
    }

    for (let i = 1; i <= numSteps; i++) {
      const prog = i / numSteps;
      const centerLat = s[0] + (e[0] - s[0]) * prog;
      const centerLon = s[1] + (e[1] - s[1]) * prog;
      const radius = (algo === "dijkstra" ? 0.008 : 0.003) * Math.sin(prog * Math.PI);

      const angle = (i * 137.5 * Math.PI) / 180;
      const lat = centerLat + Math.sin(angle) * radius;
      const lon = centerLon + Math.cos(angle) * radius;

      generatedSteps.push({
        i,
        lat,
        lon,
        cost: Math.round(prog * 2500),
        frontier: [
          [lat + 0.0005, lon + 0.0005],
          [lat - 0.0005, lon - 0.0005],
        ],
        dir: algo === "bidirectional" && i % 2 === 0 ? "bwd" : "fwd",
        jam: algo === "dynamic_c_t" && prog > 0.4 && prog < 0.6,
      });
    }

    setSteps(generatedSteps);
    setFinalPath(path);
    setMetrics({
      compute_time_ms: algo === "a_star" ? 8.4 : algo === "dijkstra" ? 45.2 : 12.1,
      distance_km: 2.45,
      estimated_time_min: 5.8,
      nodes_visited_count: generatedSteps.length,
    });
    setTimeout(() => setIsPlaying(true), 300);
  };

  // 3. Update Markers on Map
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Start Marker (Green Glow Pin)
    if (!startMarkerRef.current) {
      const el = document.createElement("div");
      el.className = "cursor-pointer";
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <div class="absolute w-8 h-8 rounded-full bg-emerald-500/30 animate-ping"></div>
          <div class="w-6 h-6 rounded-full bg-emerald-500 border-2 border-white shadow-[0_0_12px_#10b981] flex items-center justify-center text-white font-mono font-bold text-xs">
            A
          </div>
        </div>
      `;
      startMarkerRef.current = new maplibregl.Marker({ element: el })
        .setLngLat([startPoint[1], startPoint[0]])
        .addTo(map);
    } else {
      startMarkerRef.current.setLngLat([startPoint[1], startPoint[0]]);
    }

    // End Marker (Red Glow Pin)
    if (!endMarkerRef.current) {
      const el = document.createElement("div");
      el.className = "cursor-pointer";
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <div class="absolute w-8 h-8 rounded-full bg-rose-500/30 animate-ping"></div>
          <div class="w-6 h-6 rounded-full bg-rose-500 border-2 border-white shadow-[0_0_12px_#f43f5e] flex items-center justify-center text-white font-mono font-bold text-xs">
            B
          </div>
        </div>
      `;
      endMarkerRef.current = new maplibregl.Marker({ element: el })
        .setLngLat([endPoint[1], endPoint[0]])
        .addTo(map);
    } else {
      endMarkerRef.current.setLngLat([endPoint[1], endPoint[0]]);
    }
  }, [mapLoaded, startPoint, endPoint]);

  // 4. Map Click Handler for Setting Start/End
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const handleClick = (e: maplibregl.MapMouseEvent) => {
      const lat = e.lngLat.lat;
      const lon = e.lngLat.lng;

      if (pinTarget === "start") {
        setStartPoint([lat, lon]);
        setPinTarget("none");
        runPathfinding([lat, lon], endPoint, algorithm);
      } else if (pinTarget === "end") {
        setEndPoint([lat, lon]);
        setPinTarget("none");
        runPathfinding(startPoint, [lat, lon], algorithm);
      }
    };

    map.on("click", handleClick);
    return () => {
      map.off("click", handleClick);
    };
  }, [mapLoaded, pinTarget, startPoint, endPoint, algorithm, runPathfinding]);

  // 5. Initial Solve on Load
  useEffect(() => {
    if (mapLoaded) {
      runPathfinding(startPoint, endPoint, algorithm);
      if (mapRef.current) {
        const safeLat = Math.max(-85, Math.min(85, (startPoint[0] + endPoint[0]) / 2));
        const safeLon = Math.max(-180, Math.min(180, (startPoint[1] + endPoint[1]) / 2));
        mapRef.current.flyTo({
          center: [safeLon, safeLat],
          zoom: 14.5,
          essential: true,
        });
      }
    }
  }, [mapLoaded]);

  // 6. Animation Playback Loop using requestAnimationFrame
  useEffect(() => {
    if (!isPlaying) return;

    let animId: number;

    const stepLoop = () => {
      setCurrentStepIndex((prev) => {
        const next = prev + speed;
        if (next >= steps.length) {
          setIsPlaying(false);
          setIsPathVisible(true);
          return steps.length;
        }
        return next;
      });
      animId = requestAnimationFrame(stepLoop);
    };

    animId = requestAnimationFrame(stepLoop);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying, speed, steps.length]);

  const handleSelectAlgorithm = (algo: string) => {
    setAlgorithm(algo);
    runPathfinding(startPoint, endPoint, algo);
  };

  const handleSelectPreset = (p: typeof PRESET_PAIRS[0]) => {
    setStartPoint(p.start as [number, number]);
    setEndPoint(p.end as [number, number]);
    if (mapRef.current) {
      const safeLat = Math.max(-85, Math.min(85, (p.start[0] + p.end[0]) / 2));
      const safeLon = Math.max(-180, Math.min(180, (p.start[1] + p.end[1]) / 2));
      mapRef.current.flyTo({
        center: [safeLon, safeLat],
        zoom: 14.5,
      });
    }
    runPathfinding(p.start as [number, number], p.end as [number, number], algorithm);
  };

  return (
    <div className="relative w-screen h-[100dvh] overflow-hidden bg-black text-white select-none">
      {/* 1. Fullscreen Map Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* 2. Canvas Wavefront Layer */}
      <WavefrontCanvas
        map={mapRef.current}
        mapLoaded={mapLoaded}
        steps={steps}
        currentStepIndex={currentStepIndex}
        finalPath={finalPath}
        isPathVisible={isPathVisible}
        algorithmId={algorithm}
      />

      {/* 3. Top Floating Sci-Fi Header */}
      <header className="absolute top-3 left-4 right-4 z-20 pointer-events-none">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
          {/* Brand & Mode */}
          <div className="pointer-events-auto flex items-center bg-[#09090b]/90 backdrop-blur-md border border-neutral-800 px-3 py-2 space-x-3">
            <Link
              href="/"
              className="text-xs font-mono font-bold text-neutral-300 hover:text-white transition flex items-center space-x-1"
            >
              <span>← BÁO CÁO</span>
            </Link>
            <span className="text-neutral-700">|</span>
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#00f0ff] animate-pulse"></span>
              <span className="font-mono text-xs font-bold tracking-wider uppercase text-white">
                PATHFINDING WAVEFRONT VISUALIZER
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 bg-neutral-800 text-neutral-400 border border-neutral-700">
                v7.3.2
              </span>
            </div>
          </div>

          {/* Preset Buttons & Pinning Action */}
          <div className="pointer-events-auto flex items-center space-x-2 font-mono text-xs">
            {/* Pin Start Button */}
            <button
              onClick={() => setPinTarget(pinTarget === "start" ? "none" : "start")}
              className={`px-3 py-1.5 border transition flex items-center space-x-1.5 ${
                pinTarget === "start"
                  ? "bg-emerald-500 text-black font-bold border-white"
                  : "bg-[#09090b]/90 backdrop-blur-md border-emerald-600/60 text-emerald-300 hover:bg-emerald-950/40"
              }`}
            >
              <span>{pinTarget === "start" ? "NHẤP BẢN ĐỒ ĐẶT A..." : "📍 CẮM ĐIỂM A"}</span>
            </button>

            {/* Pin End Button */}
            <button
              onClick={() => setPinTarget(pinTarget === "end" ? "none" : "end")}
              className={`px-3 py-1.5 border transition flex items-center space-x-1.5 ${
                pinTarget === "end"
                  ? "bg-rose-500 text-black font-bold border-white"
                  : "bg-[#09090b]/90 backdrop-blur-md border-rose-600/60 text-rose-300 hover:bg-rose-950/40"
              }`}
            >
              <span>{pinTarget === "end" ? "NHẤP BẢN ĐỒ ĐẶT B..." : "🎯 CẮM ĐIỂM B"}</span>
            </button>

            {/* Switch to WebGIS Demo */}
            <Link
              href="/demo"
              className="px-3 py-1.5 bg-neutral-900/90 backdrop-blur-md border border-neutral-700 hover:border-neutral-500 text-neutral-300 hover:text-white transition"
            >
              MỞ DEMO TOÀN QUỐC →
            </Link>
          </div>
        </div>
      </header>

      {/* 4. Floating HUD Control Panel on Left */}
      <div className="absolute top-18 bottom-6 left-4 z-20 w-80 sm:w-96 pointer-events-auto overflow-y-auto no-scrollbar">
        <VisualizerHUD
          currentAlgorithm={algorithm}
          onSelectAlgorithm={handleSelectAlgorithm}
          isPlaying={isPlaying}
          onTogglePlay={() => setIsPlaying(!isPlaying)}
          onStepForward={() => {
            setCurrentStepIndex((prev) => Math.min(steps.length, prev + speed));
            if (currentStepIndex + speed >= steps.length) setIsPathVisible(true);
          }}
          onReset={() => {
            setIsPlaying(false);
            setCurrentStepIndex(0);
            setIsPathVisible(false);
          }}
          speed={speed}
          onChangeSpeed={setSpeed}
          currentStep={currentStepIndex}
          totalSteps={steps.length}
          metrics={metrics}
          isLoading={isLoading}
          onRunSolve={() => runPathfinding(startPoint, endPoint, algorithm)}
          startSelected={true}
          destSelected={true}
        />

        {/* Preset Pairs Drawer Pill */}
        <div className="mt-3 bg-[#09090b]/90 backdrop-blur-md border border-neutral-800 p-2.5 font-mono text-xs">
          <div className="text-[10px] text-neutral-400 uppercase tracking-widest mb-1.5 font-bold">
            CẶP ĐIỂM MẪU (BENCHMARK PRESETS)
          </div>
          <div className="space-y-1">
            {PRESET_PAIRS.map((p, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPreset(p)}
                className="w-full text-left px-2 py-1.5 border border-neutral-800 hover:border-cyan-500/50 hover:bg-neutral-900 text-neutral-300 hover:text-white transition text-[11px]"
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
