"use client";

import React, { useEffect } from "react";
import { OptimoTab } from "./OptimoSidebar";

interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount?: number;
  routesCount?: number;
  isPinned: boolean;
  onTogglePin: () => void;
}

export default function NavigationDrawer({
  isOpen,
  onClose,
  activeTab,
  onChangeTab,
  isPinned,
  onTogglePin,
}: NavigationDrawerProps) {
  // Listen for Escape key to close drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen && !isPinned) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isPinned, onClose]);

  const navItems: {
    id: OptimoTab;
    code: string;
    label: string;
    badge: string;
    isSim?: boolean;
  }[] = [
    {
      id: "t1_multicriteria",
      code: "T1",
      label: "Đa Tiêu Chí Tuyến Đi (A→B)",
      badge: "PARETO",
    },
    {
      id: "t2_vrptw",
      code: "T2",
      label: "Lập Tuyến Đội Xe Giao Hàng",
      badge: "VRPTW",
    },
    {
      id: "t3_live",
      code: "T3",
      label: "Đổi Tuyến Thích Nghi Live",
      badge: "MÔ PHỎNG",
      isSim: true,
    },
  ];

  return (
    <>
      {/* Backdrop */}
      {isOpen && !isPinned && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-neutral-900/30 backdrop-blur-xs z-30 transition-opacity"
        />
      )}

      {/* Drawer Panel */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-80 bg-white border-r border-neutral-300 transform transition-transform duration-200 ease-in-out flex flex-col justify-between font-sans ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          {/* Header */}
          <div className="p-4 border-b border-neutral-200 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-neutral-500 font-bold">
                HOTWAY EXPERIMENTS
              </span>
              <h2 className="text-sm font-bold text-neutral-900 mt-0.5">
                Bàn Điều Phối Tuyến Đường
              </h2>
            </div>
            <div className="flex items-center space-x-1 font-mono text-xs">
              <button
                onClick={onTogglePin}
                title={isPinned ? "Bỏ ghim ngăn kéo" : "Ghim ngăn kéo cố định"}
                className={`px-2 py-1 border text-[11px] transition ${
                  isPinned
                    ? "bg-neutral-900 text-white border-neutral-900"
                    : "border-neutral-300 text-neutral-700 hover:bg-neutral-100"
                }`}
              >
                {isPinned ? "[ĐÃ GHIM]" : "[GHIM]"}
              </button>
              <button
                onClick={onClose}
                className="px-2 py-1 border border-neutral-300 text-neutral-700 hover:bg-neutral-100 transition"
              >
                [X]
              </button>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="p-3 space-y-1.5">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onChangeTab(item.id);
                    if (!isPinned) onClose();
                  }}
                  className={`w-full text-left p-3 border transition ${
                    isActive
                      ? "bg-neutral-900 text-white border-neutral-900"
                      : "bg-white border-neutral-200 text-neutral-800 hover:border-neutral-400"
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="font-bold">{item.code}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 border ${
                        isActive
                          ? "border-neutral-500 text-neutral-200"
                          : item.isSim
                          ? "border-amber-400 text-amber-800 bg-amber-50"
                          : "border-neutral-300 text-neutral-600 bg-neutral-50"
                      }`}
                    >
                      {item.badge}
                    </span>
                  </div>
                  <div className={`text-xs font-medium ${isActive ? "text-neutral-100" : "text-neutral-900"}`}>
                    {item.label}
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-200 text-[11px] font-mono text-neutral-500 space-y-1">
          <div>Backend: :8000 | Frontend: :3001</div>
          <div className="text-emerald-700 font-bold">Cổng 3000: BẢO VỆ TUYỆT ĐỐI</div>
        </div>
      </aside>
    </>
  );
}
