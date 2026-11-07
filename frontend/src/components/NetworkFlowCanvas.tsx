"use client";

import React, { useEffect, useRef, useState } from "react";

interface Node {
  id: string;
  name: string;
  region: string;
  x: number; // percentage 0-100
  y: number; // percentage 0-100
  size: number;
  type: "hub" | "depot" | "cluster";
  packetsCount: number;
}

interface Edge {
  source: string;
  target: string;
  distanceKm: number;
  activeCost: string;
  color: string;
}

interface Packet {
  sourceId: string;
  targetId: string;
  progress: number; // 0 to 1
  speed: number;
  color: string;
  size: number;
}

const NODES: Node[] = [
  { id: "HN", name: "Hà Nội Hub", region: "Miền Bắc (40 POI)", x: 28, y: 18, size: 7, type: "hub", packetsCount: 42 },
  { id: "HN_DEPOT", name: "Trạm Ba Đình", region: "Hà Nội Cục Bộ", x: 20, y: 26, size: 4.5, type: "depot", packetsCount: 18 },
  { id: "HN_SUB", name: "Trạm Hoàng Mai", region: "Hà Nội Vành Đai", x: 34, y: 28, size: 4, type: "cluster", packetsCount: 14 },
  
  { id: "DN", name: "Đà Nẵng Hub", region: "Miền Trung (20 POI)", x: 58, y: 46, size: 6.5, type: "hub", packetsCount: 26 },
  { id: "DN_SUB", name: "Trạm Hải Châu", region: "Đà Nẵng Nội Đô", x: 68, y: 40, size: 4, type: "depot", packetsCount: 12 },

  { id: "HCM", name: "TP.HCM Hub", region: "Miền Nam (40 POI)", x: 74, y: 78, size: 7.5, type: "hub", packetsCount: 58 },
  { id: "HCM_BT", name: "Bình Thạnh Hub", region: "TP.HCM Trọng Điểm", x: 66, y: 68, size: 5, type: "depot", packetsCount: 22 },
  { id: "HCM_TD", name: "Thủ Đức Tech Hub", region: "TP.HCM Vệ Tinh", x: 84, y: 68, size: 4.5, type: "cluster", packetsCount: 19 },
];

const EDGES: Edge[] = [
  // Inter-hub trunk lines
  { source: "HN", target: "DN", distanceKm: 760, activeCost: "C(t)=1.08", color: "#005691" },
  { source: "DN", target: "HCM", distanceKm: 850, activeCost: "C(t)=1.12", color: "#005691" },
  { source: "HN", target: "HCM", distanceKm: 1610, activeCost: "C(t)=1.15", color: "rgba(0, 86, 145, 0.45)" },

  // Hanoi local mesh
  { source: "HN", target: "HN_DEPOT", distanceKm: 8.4, activeCost: "C(t)=1.45 (Mưa)", color: "rgba(0, 255, 255, 0.6)" },
  { source: "HN", target: "HN_SUB", distanceKm: 11.2, activeCost: "C(t)=1.20", color: "rgba(0, 255, 255, 0.4)" },
  { source: "HN_DEPOT", target: "HN_SUB", distanceKm: 9.8, activeCost: "C(t)=1.10", color: "rgba(204, 204, 204, 0.3)" },

  // Da Nang local
  { source: "DN", target: "DN_SUB", distanceKm: 6.2, activeCost: "C(t)=1.02", color: "rgba(0, 255, 255, 0.5)" },

  // HCMC local mesh
  { source: "HCM", target: "HCM_BT", distanceKm: 7.1, activeCost: "C(t)=1.62 (Cao điểm)", color: "#FFA500" },
  { source: "HCM", target: "HCM_TD", distanceKm: 13.5, activeCost: "C(t)=1.18", color: "rgba(0, 255, 255, 0.6)" },
  { source: "HCM_BT", target: "HCM_TD", distanceKm: 9.3, activeCost: "C(t)=1.25", color: "rgba(204, 204, 204, 0.35)" },
  { source: "DN", target: "HCM_BT", distanceKm: 845, activeCost: "C(t)=1.14", color: "rgba(0, 86, 145, 0.3)" },
];

export default function NetworkFlowCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null);
  const [telemetry, setTelemetry] = useState({
    activePackets: 24,
    throughput: "148 pkt/s",
    avgLatency: "24.6 ms",
    networkEfficiency: "98.7%",
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio);
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio);
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    window.addEventListener("resize", handleResize);

    // Initial packet pool
    const packets: Packet[] = [];
    const colors = ["#00FFFF", "#00FF00", "#FFA500", "#00FFFF"];

    for (let i = 0; i < 30; i++) {
      const edge = EDGES[Math.floor(Math.random() * EDGES.length)];
      packets.push({
        sourceId: edge.source,
        targetId: edge.target,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.004,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: 2.2 + Math.random() * 1.5,
      });
    }

    const nodeMap = new Map<string, Node>();
    NODES.forEach((n) => nodeMap.set(n.id, n));

    let time = 0;

    const render = () => {
      time += 0.02;
      const displayW = canvas.offsetWidth;
      const displayH = canvas.offsetHeight;

      ctx.clearRect(0, 0, displayW, displayH);

      // Draw subtle background grid lines (Data center rack grid)
      ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
      ctx.lineWidth = 1;
      const gridSize = 32;
      for (let x = 0; x < displayW; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, displayH);
        ctx.stroke();
      }
      for (let y = 0; y < displayH; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(displayW, y);
        ctx.stroke();
      }

      // Draw Edges (Network Links)
      EDGES.forEach((edge) => {
        const s = nodeMap.get(edge.source);
        const t = nodeMap.get(edge.target);
        if (!s || !t) return;

        const sx = (s.x / 100) * displayW;
        const sy = (s.y / 100) * displayH;
        const tx = (t.x / 100) * displayW;
        const ty = (t.y / 100) * displayH;

        const isConnectedToHover =
          hoveredNode &&
          (hoveredNode.id === edge.source || hoveredNode.id === edge.target);

        ctx.beginPath();
        ctx.moveTo(sx, sy);
        ctx.lineTo(tx, ty);

        if (isConnectedToHover) {
          ctx.strokeStyle = "#00FFFF";
          ctx.lineWidth = 2.5;
          ctx.shadowColor = "#00FFFF";
          ctx.shadowBlur = 8;
        } else {
          ctx.strokeStyle = edge.color;
          ctx.lineWidth = edge.source === "HN" && edge.target === "HCM" ? 1.2 : 1.6;
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0; // Reset
      });

      // Draw Animated Packets (Moving pulses along edges)
      packets.forEach((pkt) => {
        pkt.progress += pkt.speed;
        if (pkt.progress >= 1) {
          pkt.progress = 0;
          const nextEdge = EDGES[Math.floor(Math.random() * EDGES.length)];
          pkt.sourceId = nextEdge.source;
          pkt.targetId = nextEdge.target;
        }

        const s = nodeMap.get(pkt.sourceId);
        const t = nodeMap.get(pkt.targetId);
        if (!s || !t) return;

        const sx = (s.x / 100) * displayW;
        const sy = (s.y / 100) * displayH;
        const tx = (t.x / 100) * displayW;
        const ty = (t.y / 100) * displayH;

        const px = sx + (tx - sx) * pkt.progress;
        const py = sy + (ty - sy) * pkt.progress;

        // Packet glow
        ctx.beginPath();
        ctx.arc(px, py, pkt.size, 0, Math.PI * 2);
        ctx.fillStyle = pkt.color;
        ctx.shadowColor = pkt.color;
        ctx.shadowBlur = 6;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Draw Nodes
      NODES.forEach((node) => {
        const nx = (node.x / 100) * displayW;
        const ny = (node.y / 100) * displayH;
        const isHovered = hoveredNode?.id === node.id;

        // Outer halo / pulse
        if (node.type === "hub" || isHovered) {
          const pulseR = node.size * (1.8 + 0.3 * Math.sin(time * 3 + node.x));
          ctx.beginPath();
          ctx.arc(nx, ny, pulseR, 0, Math.PI * 2);
          ctx.fillStyle = isHovered
            ? "rgba(0, 255, 255, 0.22)"
            : "rgba(0, 86, 145, 0.18)";
          ctx.fill();
        }

        // Base node ring
        ctx.beginPath();
        ctx.arc(nx, ny, isHovered ? node.size * 1.3 : node.size, 0, Math.PI * 2);
        ctx.fillStyle =
          node.type === "hub"
            ? "#005691"
            : node.type === "depot"
            ? "#333333"
            : "#242428";
        ctx.strokeStyle = isHovered
          ? "#00FFFF"
          : node.type === "hub"
          ? "#00FFFF"
          : "#CCCCCC";
        ctx.lineWidth = isHovered ? 2 : 1.2;
        ctx.fill();
        ctx.stroke();

        // Node center pip
        ctx.beginPath();
        ctx.arc(nx, ny, node.size * 0.4, 0, Math.PI * 2);
        ctx.fillStyle =
          node.type === "hub" ? "#00FF00" : isHovered ? "#00FFFF" : "#FFFFFF";
        ctx.fill();

        // Node Label
        ctx.font = `${isHovered ? "bold 12px" : "10px"} 'Open Sans', sans-serif`;
        ctx.fillStyle = isHovered ? "#FFFFFF" : "#CCCCCC";
        ctx.fillText(node.name, nx + node.size + 6, ny + 3);

        if (node.type === "hub") {
          ctx.font = "9px 'JetBrains Mono', monospace";
          ctx.fillStyle = "rgba(0, 255, 255, 0.75)";
          ctx.fillText(node.region, nx + node.size + 6, ny + 14);
        }
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Mouse movement handler for node hover
    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const displayW = canvas.offsetWidth;
      const displayH = canvas.offsetHeight;

      let found: Node | null = null;
      for (const node of NODES) {
        const nx = (node.x / 100) * displayW;
        const ny = (node.y / 100) * displayH;
        const dist = Math.hypot(mx - nx, my - ny);
        if (dist <= node.size * 2.5 + 8) {
          found = node;
          break;
        }
      }
      setHoveredNode(found);
    };

    const handleMouseLeave = () => {
      setHoveredNode(null);
    };

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      window.removeEventListener("resize", handleResize);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, [hoveredNode]);

  // Periodic telemetry fluctuation
  useEffect(() => {
    const timer = setInterval(() => {
      setTelemetry({
        activePackets: 22 + Math.floor(Math.random() * 8),
        throughput: `${140 + Math.floor(Math.random() * 20)} pkt/s`,
        avgLatency: `${(24.1 + Math.random() * 1.2).toFixed(1)} ms`,
        networkEfficiency: "98.9%",
      });
    }, 2400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-[380px] sm:h-[440px] md:h-[480px] rounded-lg border border-[#333333] bg-[#1a1a1e] overflow-hidden select-none"
    >
      {/* Topology Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full block cursor-crosshair"
      />

      {/* Top Left Header Badge */}
      <div className="absolute top-3 left-3 flex items-center space-x-2 bg-[#242428]/90 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-[#444444] text-[11px] font-mono text-[#CCCCCC]">
        <span className="w-2 h-2 rounded-full bg-[#00FF00] animate-pulse"></span>
        <span className="font-semibold text-white tracking-wider">TOPOLOGY: NATIONWIDE MESH</span>
        <span className="text-neutral-500">|</span>
        <span className="text-[#00FFFF]">100 POI</span>
      </div>

      {/* Bottom Telemetry HUD Bar */}
      <div className="absolute bottom-3 left-3 right-3 bg-[#242428]/95 backdrop-blur-md px-3.5 py-2.5 rounded-lg border border-[#444444] flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-4">
          <div>
            <span className="text-[#888888] block text-[10px] uppercase">Node Trọng Tâm</span>
            <span className="font-semibold text-white">
              {hoveredNode ? hoveredNode.name : "Toàn Mạng Lưới (3 Vùng)"}
            </span>
          </div>
          <div className="hidden sm:block">
            <span className="text-[#888888] block text-[10px] uppercase">Throughput</span>
            <span className="text-[#00FFFF] font-bold">{telemetry.throughput}</span>
          </div>
          <div>
            <span className="text-[#888888] block text-[10px] uppercase">Độ Trễ CPU</span>
            <span className="text-[#00FF00] font-bold">{telemetry.avgLatency}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-[11px] text-[#CCCCCC]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#FFA500]"></span>
          <span>Dòng C(t) Dynamic Isotropic</span>
        </div>
      </div>
    </div>
  );
}
