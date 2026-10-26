"use client";

import React from "react";
import { OptimoTab } from "./OptimoSidebar";

interface FloatingTabBarProps {
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount?: number;
  routesCount?: number;
}

export default function FloatingTabBar({
  activeTab,
  onChangeTab,
}: FloatingTabBarProps) {
  const tabs: { id: OptimoTab; label: string; num: string }[] = [
    { id: "t1_multicriteria", label: "T1: Đa Tiêu Chí (A→B)", num: "01" },
    { id: "t2_vrptw", label: "T2: Lập Tuyến Đội Xe (VRPTW)", num: "02" },
    { id: "t3_live", label: "T3: Đổi Đường Thích Nghi (SSE)", num: "03" },
  ];

  return (
    <nav
      aria-label="Thanh phân hệ chính"
      className="pointer-events-auto bg-white/95 backdrop-blur-xs border border-[#e5e5e5] p-1 flex items-center space-x-1 font-mono text-xs shadow-xs"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            onClick={() => onChangeTab(tab.id)}
            className={`px-3 py-1.5 transition text-left whitespace-nowrap ${
              isActive
                ? "bg-[#111111] text-white font-bold"
                : "text-[#555555] hover:text-[#111111] hover:bg-[#f5f4f0]"
            }`}
          >
            <span className="text-[10px] text-[#888888] mr-1.5">{tab.num}</span>
            <span className="font-sans font-medium">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
