"use client";

import React, { useEffect } from "react";
import {
  ListOrdered,
  Route,
  FileText,
  BarChart2,
  PlayCircle,
  Radio,
  X,
  Pin,
  MapPin,
  Info,
} from "lucide-react";
import { OptimoTab } from "./OptimoSidebar";

interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: OptimoTab;
  onChangeTab: (tab: OptimoTab) => void;
  ordersCount: number;
  routesCount: number;
  isPinned: boolean;
  onTogglePin: () => void;
}

export default function NavigationDrawer({
  isOpen,
  onClose,
  activeTab,
  onChangeTab,
  ordersCount,
  routesCount,
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
    label: string;
    icon: React.ElementType;
    badge?: string;
    isSim?: boolean;
  }[] = [
    {
      id: "orders",
      label: "Đơn hàng",
      icon: ListOrdered,
      badge: ordersCount > 0 ? String(ordersCount) : undefined,
    },
    {
      id: "planning",
      label: "Lập kế hoạch",
      icon: Route,
      badge: routesCount > 0 ? `${routesCount} xe` : undefined,
    },
    {
      id: "route",
      label: "Chi tiết tuyến",
      icon: FileText,
    },
    {
      id: "strategy_lab",
      label: "Strategy Lab",
      icon: BarChart2,
    },
    {
      id: "search_replay",
      label: "Search Replay",
      icon: PlayCircle,
    },
    {
      id: "live",
      label: "Điều phối Live",
      icon: Radio,
      badge: "MÔ PHỎNG",
      isSim: true,
    },
  ];

  if (!isOpen && !isPinned) return null;

  return (
    <>
      {/* Dimmed Overlay (only when not pinned) */}
      {!isPinned && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-primary-text/25 backdrop-blur-xs z-40 transition-opacity duration-250 ease-out"
        />
      )}

      {/* Drawer Container */}
      <aside
        className={`fixed top-0 left-0 bottom-0 w-72 bg-surface border-r border-border-warm z-50 flex flex-col justify-between shadow-floating transition-transform duration-250 ease-out ${
          isOpen || isPinned ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div>
          {/* Top Brand Header */}
          <div className="p-4 border-b border-border-warm flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-sunken border border-border-warm flex items-center justify-center font-bold text-xs text-brand-gold">
                HG
              </div>
              <div>
                <span className="text-[10px] font-mono tracking-wider uppercase font-bold text-brand-gold block">
                  HÀNG GÒN QUÁN
                </span>
                <h1 className="text-sm font-bold text-primary-text leading-tight">
                  Điều Phối Giao Hàng
                </h1>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={onTogglePin}
                title={isPinned ? "Bỏ ghim menu" : "Ghim menu cố định"}
                className={`p-1.5 rounded-lg text-secondary-text hover:bg-sunken hover:text-primary-text transition hidden md:flex ${
                  isPinned ? "text-brand-gold bg-brand-gold-soft" : ""
                }`}
              >
                <Pin className="w-4 h-4" />
              </button>
              {!isPinned && (
                <button
                  onClick={onClose}
                  aria-label="Đóng menu"
                  className="p-1.5 rounded-lg text-secondary-text hover:bg-sunken hover:text-primary-text transition"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Navigation Item List */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onChangeTab(item.id);
                    if (!isPinned) onClose();
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-warm text-xs font-medium transition ${
                    isActive
                      ? "bg-brand-gold-soft text-primary-text font-semibold border border-brand-gold/40 shadow-soft"
                      : "text-secondary-text hover:bg-sunken hover:text-primary-text"
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon
                      className={`w-4 h-4 ${
                        isActive ? "text-brand-brown" : "text-secondary-text"
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        item.isSim
                          ? "bg-amber-100 text-amber-800 border border-amber-300"
                          : isActive
                          ? "bg-brand-gold text-primary-text"
                          : "bg-sunken text-secondary-text"
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

        {/* Clean System Info Footer */}
        <div className="p-4 border-t border-border-warm space-y-2 bg-sunken/40">
          <div className="flex items-start space-x-2 text-[11px] text-secondary-text">
            <MapPin className="w-3.5 h-3.5 text-brand-gold shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-primary-text">Bếp trung tâm:</span>
              <p className="text-[10px] leading-tight">490 Điện Biên Phủ, P. 21, Bình Thạnh</p>
            </div>
          </div>

          <div className="flex items-center justify-between text-[10px] text-secondary-text pt-1 border-t border-border-warm/60">
            <span>Bán kính mạng lưới:</span>
            <span className="font-mono font-bold text-primary-text">3.5 km</span>
          </div>

          <p className="text-[10px] text-secondary-text/80 italic text-center pt-1">
            &ldquo;Tuyến giao hàng ngắn nhất để món còn nóng.&rdquo;
          </p>
        </div>
      </aside>
    </>
  );
}
