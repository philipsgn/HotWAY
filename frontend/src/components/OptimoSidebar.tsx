"use client";

import React from "react";
import { Compass, Route, Navigation } from "lucide-react";

export type OptimoTab = "t1_multicriteria" | "t2_vrptw" | "t3_live";

interface OptimoSidebarProps {
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount?: number;
  routesCount?: number;
}

export default function OptimoSidebar({
  activeTab,
  onChangeTab,
}: OptimoSidebarProps) {
  const navItems: { id: OptimoTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: "t1_multicriteria", label: "T1: Đa Tiêu Chí (A→B)", icon: Compass, badge: "PARETO" },
    { id: "t2_vrptw", label: "T2: Đội Xe (VRPTW)", icon: Route, badge: "OR-TOOLS" },
    { id: "t3_live", label: "T3: Đổi Đường (SSE)", icon: Navigation, badge: "MÔ PHỎNG" },
  ];

  return (
    <aside className="w-64 bg-stone-900 border-r border-stone-800 flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-stone-800">
          <div className="text-xs font-mono text-amber-500 uppercase tracking-widest">
            HOTWAY RESEARCH v7.0.0
          </div>
          <h1 className="text-base font-semibold text-stone-100 mt-1">
            Tối Ưu Tuyến Đường Đô Thị
          </h1>
          <p className="text-xs text-stone-400 mt-1 leading-snug">
            Điều phối và đổi đường thích nghi cho xe máy.
          </p>
        </div>

        {/* Navigation Tabs */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onChangeTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded text-sm font-medium transition ${
                  isActive
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "text-stone-400 hover:text-stone-200 hover:bg-stone-800/50"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-stone-800 text-stone-400">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-stone-800 text-[11px] text-stone-500 font-mono space-y-1">
        <div>Backend: :8000 | Frontend: :3001</div>
        <div className="text-emerald-500 font-bold">Cổng 3000: BẢO VỆ TUYỆT ĐỐI</div>
      </div>
    </aside>
  );
}
