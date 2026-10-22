"use client";

import React from "react";
import { OptimoTab } from "./OptimoSidebar";
import { ListOrdered, Route, FileText, BarChart2, PlayCircle, Radio } from "lucide-react";

interface FloatingTabBarProps {
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount: number;
  routesCount: number;
}

export default function FloatingTabBar({
  activeTab,
  onChangeTab,
  ordersCount,
  routesCount,
}: FloatingTabBarProps) {
  const tabs: { id: OptimoTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: "orders", label: "Đơn hàng", icon: ListOrdered, badge: ordersCount > 0 ? String(ordersCount) : undefined },
    { id: "planning", label: "Lập kế hoạch", icon: Route, badge: routesCount > 0 ? `${routesCount} xe` : undefined },
    { id: "route", label: "Chi tiết", icon: FileText },
    { id: "strategy_lab", label: "Strategy Lab", icon: BarChart2 },
    { id: "search_replay", label: "Replay", icon: PlayCircle },
    { id: "live", label: "Live", icon: Radio, badge: "MÔ PHỎNG" },
  ];

  return (
    <nav
      aria-label="Thanh phân hệ chính"
      className="pointer-events-auto bg-surface/95 backdrop-blur-md border border-border-warm rounded-warm p-1 shadow-soft flex items-center space-x-1 overflow-x-auto max-w-full"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;

        return (
          <button
            key={tab.id}
            onClick={() => onChangeTab(tab.id)}
            className={`relative flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all duration-200 ${
              isActive
                ? "bg-brand-gold-soft text-primary-text font-bold shadow-xs"
                : "text-secondary-text hover:bg-sunken hover:text-primary-text"
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isActive ? "text-brand-brown" : "text-secondary-text"}`} />
            <span>{tab.label}</span>
            {tab.badge && (
              <span
                className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full font-bold ${
                  tab.badge === "MÔ PHỎNG"
                    ? "bg-amber-100 text-amber-800 border border-amber-300"
                    : isActive
                    ? "bg-brand-gold text-primary-text"
                    : "bg-sunken text-secondary-text"
                }`}
              >
                {tab.badge}
              </span>
            )}

            {/* Active Gold Underline Indicator */}
            {isActive && (
              <div className="absolute -bottom-1 left-3 right-3 h-0.5 bg-brand-gold rounded-full" />
            )}
          </button>
        );
      })}
    </nav>
  );
}
