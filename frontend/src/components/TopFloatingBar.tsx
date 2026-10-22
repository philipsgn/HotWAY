"use client";

import React, { useState, useEffect, useRef } from "react";
import { Menu, Search, Crosshair, ArrowRight, MapPin, X, Loader2 } from "lucide-react";

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
  { name: "Hàng Gòn Quán - 490 Điện Biên Phủ", lat: 10.8012, lon: 106.7145 },
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
      // Filter presets first
      const q = query.toLowerCase();
      const localMatches = PRESET_LOCATIONS.filter((p) =>
        p.name.toLowerCase().includes(q)
      );

      try {
        // Query OpenStreetMap Nominatim limited to Ho Chi Minh City
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
    <header className="absolute top-4 left-4 right-4 z-30 pointer-events-none">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-3">
        {/* Left: Drawer Toggle & Brand Badge */}
        <div className="pointer-events-auto flex items-center bg-surface/95 backdrop-blur-md border border-border-warm rounded-warm p-1.5 shadow-soft">
          <button
            onClick={onToggleDrawer}
            aria-label="Mở menu quản trị"
            className="w-9 h-9 rounded-xl flex items-center justify-center text-primary-text hover:bg-sunken active:bg-subtle transition"
          >
            <Menu className="w-5 h-5 text-brand-brown" />
          </button>
          <div className="hidden sm:flex flex-col pr-3 pl-2 border-l border-border-warm ml-1.5">
            <span className="text-[10px] font-mono tracking-widest uppercase font-bold text-brand-gold">
              HÀNG GÒN QUÁN
            </span>
            <span className="text-xs font-semibold text-primary-text leading-tight">
              Điều Phối Tuyến
            </span>
          </div>
        </div>

        {/* Center: Address Search Bar */}
        <div ref={searchRef} className="pointer-events-auto flex-1 max-w-md relative">
          <div className="flex items-center bg-surface/95 backdrop-blur-md border border-border-warm rounded-warm px-3.5 py-2 shadow-soft focus-within:border-brand-gold focus-within:shadow-elevated transition">
            <Search className="w-4 h-4 text-secondary-text shrink-0 mr-2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tìm địa chỉ tại Bình Thạnh..."
              className="w-full bg-transparent text-xs text-primary-text placeholder-secondary-text/70 focus:outline-none"
            />
            {query && (
              <button
                onClick={() => {
                  setQuery("");
                  setResults([]);
                }}
                className="text-secondary-text hover:text-primary-text"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            {isSearching && <Loader2 className="w-3.5 h-3.5 text-brand-gold animate-spin ml-2" />}
          </div>

          {/* Autocomplete Dropdown */}
          {isOpen && results.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-surface border border-border-warm rounded-warm shadow-floating p-1 z-40 max-h-64 overflow-y-auto">
              {results.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelect(item)}
                  className="w-full text-left p-2.5 rounded-xl hover:bg-sunken flex items-start space-x-2 text-xs transition"
                >
                  <MapPin className="w-3.5 h-3.5 text-brand-gold shrink-0 mt-0.5" />
                  <div className="flex-1 overflow-hidden">
                    <p className="text-primary-text font-medium truncate">{item.name}</p>
                    <p className="text-[10px] text-secondary-text font-mono">
                      {item.lat.toFixed(4)}, {item.lon.toFixed(4)}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Quick Action Buttons */}
        <div className="pointer-events-auto flex items-center space-x-2">
          <button
            onClick={onLocateUser}
            disabled={isLocating}
            title="Định vị của tôi"
            aria-label="Vị trí của tôi"
            className={`w-9 h-9 rounded-warm bg-surface/95 backdrop-blur-md border border-border-warm shadow-soft flex items-center justify-center text-brand-brown hover:bg-sunken active:bg-subtle transition ${
              isLocating ? "animate-spin text-brand-gold" : ""
            }`}
          >
            <Crosshair className="w-4 h-4" />
          </button>

          <button
            onClick={onQuickPlan}
            disabled={isPlanning}
            className="h-9 px-4 rounded-warm bg-brand-gold hover:bg-brand-gold-hover active:bg-brand-gold-pressed text-primary-text font-bold text-xs shadow-soft flex items-center space-x-1.5 transition disabled:opacity-60"
          >
            {isPlanning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Đang tính...</span>
              </>
            ) : (
              <>
                <span>Lập tuyến</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
