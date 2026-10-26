"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface TopFloatingBarProps {
  onToggleDrawer: () => void;
  onLocateUser: () => void;
  isLocating?: boolean;
  onQuickPlan: () => void;
  onSelectAddressPoint?: (point: { lat: number; lon: number; name: string }) => void;
  isPlanning?: boolean;
}

// Popular locations around Bình Thạnh / HCMC for instant fallback & speedy suggestions
const PRESET_LOCATIONS = [
  { name: "490 Điện Biên Phủ, Phường 21, Bình Thạnh", lat: 10.8012, lon: 106.7145 },
  { name: "Đại học HUTECH - 475A Điện Biên Phủ", lat: 10.8021, lon: 106.7148 },
  { name: "Pearl Plaza - 561A Điện Biên Phủ", lat: 10.7995, lon: 106.7185 },
  { name: "Landmark 81 - Vinhomes Central Park", lat: 10.7951, lon: 106.7218 },
  { name: "Chợ Bà Chiểu - Bạch Đằng, Bình Thạnh", lat: 10.8016, lon: 106.6961 },
  { name: "Ngã tư Hàng Xanh - Xô Viết Nghệ Tĩnh", lat: 10.8014, lon: 106.7112 },
  { name: "Đại học Ngoại Thương CS2 - D5 Bình Thạnh", lat: 10.8055, lon: 106.7128 },
  { name: "Cầu Thị Nghè - Nguyễn Thị Minh Khai", lat: 10.7905, lon: 106.7052 },
];

export default function TopFloatingBar({
  onToggleDrawer,
  onLocateUser,
  isLocating = false,
  onQuickPlan,
  onSelectAddressPoint,
  isPlanning = false,
}: TopFloatingBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ name: string; lat: number; lon: number }[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search (300ms) with Nominatim geocoding restricted to TP.HCM + preset fallback
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      const q = query.toLowerCase();
      const localMatches = PRESET_LOCATIONS.filter((p) =>
        p.name.toLowerCase().includes(q)
      );

      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          query + ", Bình Thạnh, TP.HCM"
        )}&limit=4&countrycodes=vn`;
        const res = await fetch(url, { headers: { "Accept-Language": "vi" } });
        if (res.ok) {
          const data = await res.json();
          const remoteResults = data.map((d: any) => ({
            name: d.display_name.split(",").slice(0, 3).join(","),
            lat: parseFloat(d.lat),
            lon: parseFloat(d.lon),
          }));
          const combined = [...localMatches, ...remoteResults].slice(0, 6);
          setResults(combined);
        } else {
          setResults(localMatches);
        }
      } catch {
        setResults(localMatches);
      } finally {
        setIsSearching(false);
        setIsOpen(true);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (item: { name: string; lat: number; lon: number }) => {
    setQuery(item.name);
    setIsOpen(false);
    if (onSelectAddressPoint) {
      onSelectAddressPoint(item);
    }
  };

  return (
    <header className="absolute top-3 left-4 right-4 z-30 pointer-events-none font-sans">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Left: Return to Report & Drawer Toggle */}
        <div className="pointer-events-auto flex items-center bg-white/95 backdrop-blur-sm border border-neutral-300 p-1 space-x-1.5">
          <Link
            href="/"
            className="px-2.5 py-1 text-xs font-mono font-bold text-neutral-900 border border-neutral-300 hover:bg-neutral-100 transition"
            title="Quay về trang Báo Cáo Nghiên Cứu"
          >
            ← BÁO CÁO
          </Link>

          <button
            onClick={onToggleDrawer}
            aria-label="Mở danh mục điều phối"
            className="px-2.5 py-1 text-xs font-mono text-neutral-700 border border-neutral-300 hover:bg-neutral-100 transition"
          >
            MỤC LỤC
          </button>

          <div className="hidden sm:flex flex-col px-2 border-l border-neutral-200">
            <span className="text-[10px] font-mono tracking-widest uppercase text-neutral-500">
              HOTWAY EXPERIMENTS
            </span>
            <span className="text-xs font-bold text-neutral-900">
              Bàn Điều Phối Tuyến Đường
            </span>
          </div>
        </div>

        {/* Center: Address Search Bar */}
        <div ref={searchRef} className="pointer-events-auto flex-1 max-w-md relative">
          <div className="flex items-center bg-white/95 backdrop-blur-sm border border-neutral-300 px-3 py-1.5 focus-within:border-neutral-900 transition">
            <span className="text-xs font-mono text-neutral-400 mr-2 select-none">SEARCH:</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nhập địa chỉ tìm kiếm tại Bình Thạnh..."
              className="w-full bg-transparent text-xs text-neutral-900 placeholder-neutral-400 focus:outline-none font-mono"
            />
            {query && (
              <button
                onClick={() => {
                  setQuery("");
                  setResults([]);
                }}
                className="text-xs font-mono text-neutral-500 hover:text-neutral-900 px-1"
              >
                [x]
              </button>
            )}
            {isSearching && <span className="text-xs font-mono text-neutral-500 animate-pulse ml-1">[...]</span>}
          </div>

          {/* Autocomplete Dropdown */}
          {isOpen && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-neutral-300 p-1 z-40 max-h-60 overflow-y-auto">
              {results.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelect(item)}
                  className="w-full text-left p-2 hover:bg-neutral-100 border-b border-neutral-100 last:border-0 text-xs transition"
                >
                  <p className="text-neutral-900 font-medium truncate">{item.name}</p>
                  <p className="text-[10px] text-neutral-500 font-mono">
                    {item.lat.toFixed(4)}, {item.lon.toFixed(4)}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Quick Action Buttons */}
        <div className="pointer-events-auto flex items-center space-x-2 font-mono text-xs">
          <button
            onClick={onLocateUser}
            disabled={isLocating}
            title="Định vị thiết bị GPS"
            className="h-8 px-2.5 bg-white/95 backdrop-blur-sm border border-neutral-300 text-neutral-800 hover:bg-neutral-100 transition"
          >
            {isLocating ? "[...]" : "[GPS]"}
          </button>

          <button
            onClick={onQuickPlan}
            disabled={isPlanning}
            className="h-8 px-3 bg-neutral-900 hover:bg-black text-white font-bold transition disabled:opacity-50"
          >
            {isPlanning ? "Đang tính..." : "Lập Tuyến →"}
          </button>
        </div>
      </div>
    </header>
  );
}
