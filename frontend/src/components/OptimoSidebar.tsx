"use client";

import React from "react";

export type OptimoTab =
  | "orders"
  | "planning"
  | "route"
  | "strategy_lab"
  | "search_replay"
  | "live";

interface OptimoSidebarProps {
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount: number;
  routesCount: number;
}

export default function OptimoSidebar({
  activeTab,
  onChangeTab,
  ordersCount,
  routesCount,
}: OptimoSidebarProps) {
  const navItems: { id: OptimoTab; label: string; badge?: string }[] = [
    { id: "orders", label: "Đơn hàng", badge: ordersCount > 0 ? String(ordersCount) : undefined },
    { id: "planning", label: "Lập kế hoạch", badge: routesCount > 0 ? `${routesCount} xe` : undefined },
    { id: "route", label: "Chi tiết tuyến" },
    { id: "strategy_lab", label: "Strategy Lab" },
    { id: "search_replay", label: "Search Replay" },
    { id: "live", label: "Điều phối Live", badge: "MÔ PHỎNG" },
  ];

  return (
    <aside className="w-64 bg-stone-900 border-r border-stone-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-stone-800">
          <div className="text-xs font-mono text-amber-500 uppercase tracking-widest">
            HÀNG GÒN QUÁN
          </div>
          <h1 className="text-base font-semibold text-stone-100 mt-1">
            Điều Phối Tuyến CVRP
          </h1>
          <p className="text-xs text-stone-400 mt-1 leading-snug">
            Tuyến giao hàng ngắn nhất để món còn nóng.
          </p>
        </div>

        {/* Navigation Tabs */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onChangeTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded text-sm font-medium transition ${
                  isActive
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                    : "text-stone-300 hover:bg-stone-800/80 hover:text-stone-100"
                }`}
              >
                <span>{item.label}</span>
                {item.badge && (
                  <span
                    className={`text-[11px] font-mono px-2 py-0.5 rounded ${
                      isActive
                        ? "bg-amber-500 text-stone-950 font-bold"
                        : "bg-stone-800 text-stone-400"
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Footer Info */}
      <div className="p-4 border-t border-stone-800 text-[11px] font-mono text-stone-400 space-y-1">
        <div>Depot: 490 Điện Biên Phủ</div>
        <div className="text-stone-400">Bán kính mạng lưới: 3.5 km</div>
        <div className="flex items-center space-x-2 pt-1 text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Backend :8000 sẵn sàng</span>
        </div>
      </div>
    </aside>
  );
}
