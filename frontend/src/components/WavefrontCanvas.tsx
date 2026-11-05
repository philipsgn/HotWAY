"use client";

import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

export interface WavefrontStep {
  i: number;
  lat: number;
  lon: number;
  cost?: number;
  f_score?: number;
  frontier?: [number, number][]; // [lat, lon]
  dir?: "fwd" | "bwd";
  jam?: boolean;
}

interface WavefrontCanvasProps {
  map: maplibregl.Map | null;
  mapLoaded: boolean;
  steps: WavefrontStep[];
  currentStepIndex: number;
  finalPath: [number, number][]; // [lat, lon]
  isPathVisible: boolean;
  algorithmId?: string;
}

export default function WavefrontCanvas({
  map,
  mapLoaded,
  steps,
  currentStepIndex,
  finalPath,
  isPathVisible,
  algorithmId = "a_star",
}: WavefrontCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!map || !mapLoaded) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Resize canvas to match map container
    const resizeCanvas = () => {
      const container = map.getContainer();
      const width = container.clientWidth;
      const height = container.clientHeight;
      const dpr = window.devicePixelRatio || 1;

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    const render = () => {
      resizeCanvas();
      const container = map.getContainer();
      const width = container.clientWidth;
      const height = container.clientHeight;

      ctx.clearRect(0, 0, width, height);

      if (currentStepIndex <= 0 || steps.length === 0) {
        // If final path is visible before steps, render it
        if (isPathVisible && finalPath.length >= 2) {
          drawFinalPath(ctx, map, finalPath);
        }
        return;
      }

      const activeSlice = steps.slice(0, currentStepIndex);
      const latestStep = activeSlice[activeSlice.length - 1];

      // 1. Draw Visited Nodes (Wavefront trails)
      activeSlice.forEach((step, idx) => {
        const pt = map.project([step.lon, step.lat]);
        const isRecent = idx >= activeSlice.length - 20;

        ctx.save();
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, isRecent ? 4.5 : 2.5, 0, Math.PI * 2);

        if (step.jam) {
          ctx.fillStyle = isRecent ? "#ef4444" : "rgba(239, 68, 68, 0.4)";
          ctx.shadowColor = "#ef4444";
          ctx.shadowBlur = isRecent ? 8 : 3;
        } else if (step.dir === "bwd") {
          ctx.fillStyle = isRecent ? "#a855f7" : "rgba(168, 85, 247, 0.45)";
          ctx.shadowColor = "#a855f7";
          ctx.shadowBlur = isRecent ? 10 : 3;
        } else {
          ctx.fillStyle = isRecent ? "#00f0ff" : "rgba(0, 240, 255, 0.45)";
          ctx.shadowColor = "#00f0ff";
          ctx.shadowBlur = isRecent ? 10 : 3;
        }
        ctx.fill();
        ctx.restore();
      });

      // 2. Draw Active Frontier Nodes (Queue Priority)
      if (latestStep && latestStep.frontier && latestStep.frontier.length > 0) {
        latestStep.frontier.forEach(([fLat, fLon]) => {
          const pt = map.project([fLon, fLat]);
          ctx.save();
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
          ctx.fillStyle = "#ec4899"; // Magenta
          ctx.shadowColor = "#ec4899";
          ctx.shadowBlur = 8;
          ctx.fill();
          ctx.restore();
        });
      }

      // 3. Draw Expanding Ripple Wave on current head
      if (latestStep) {
        const headPt = map.project([latestStep.lon, latestStep.lat]);
        ctx.save();
        ctx.beginPath();
        ctx.arc(headPt.x, headPt.y, 9, 0, Math.PI * 2);
        ctx.strokeStyle = latestStep.dir === "bwd" ? "#c084fc" : "#38bdf8";
        ctx.lineWidth = 1.5;
        ctx.shadowColor = latestStep.dir === "bwd" ? "#a855f7" : "#00f0ff";
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.restore();
      }

      // 4. Draw Final Solution Path when reached
      if (isPathVisible && finalPath.length >= 2) {
        drawFinalPath(ctx, map, finalPath);
      }
    };

    // Helper to draw golden glowing neon path
    function drawFinalPath(
      c: CanvasRenderingContext2D,
      m: maplibregl.Map,
      path: [number, number][]
    ) {
      if (path.length < 2) return;

      const screenPoints = path.map(([lat, lon]) => m.project([lon, lat]));

      c.save();
      c.beginPath();
      c.moveTo(screenPoints[0].x, screenPoints[0].y);
      for (let i = 1; i < screenPoints.length; i++) {
        c.lineTo(screenPoints[i].x, screenPoints[i].y);
      }

      // Outer glow
      c.lineWidth = 6;
      c.strokeStyle = "rgba(245, 158, 11, 0.4)";
      c.shadowColor = "#f59e0b";
      c.shadowBlur = 16;
      c.lineCap = "round";
      c.lineJoin = "round";
      c.stroke();

      // Core bright line
      c.beginPath();
      c.moveTo(screenPoints[0].x, screenPoints[0].y);
      for (let i = 1; i < screenPoints.length; i++) {
        c.lineTo(screenPoints[i].x, screenPoints[i].y);
      }
      c.lineWidth = 3;
      c.strokeStyle = "#fbbf24";
      c.shadowBlur = 4;
      c.stroke();
      c.restore();
    }

    render();

    // Re-render when map moves, zooms, or rotates
    map.on("move", render);
    map.on("zoom", render);
    map.on("resize", render);

    return () => {
      map.off("move", render);
      map.off("zoom", render);
      map.off("resize", render);
    };
  }, [map, mapLoaded, steps, currentStepIndex, finalPath, isPathVisible, algorithmId]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-none z-10"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
