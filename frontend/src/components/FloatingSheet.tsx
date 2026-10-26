"use client";

import React, { useState, useEffect } from "react";

interface FloatingSheetProps {
  title: string;
  badge?: string;
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  width?: number;
  storageKey?: string;
}

export default function FloatingSheet({
  title,
  badge,
  isOpen,
  onClose,
  children,
  width = 440,
  storageKey = "hotway_sheet_state",
}: FloatingSheetProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        setIsCollapsed(saved === "true");
      }
    } catch (e) {}
  }, [storageKey]);

  const handleToggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(storageKey, String(next));
      } catch (e) {}
      return next;
    });
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Desktop Left Flat Panel (md and up) */}
      <section
        aria-label={title}
        style={{ width: isCollapsed ? "44px" : `${width}px` }}
        className="hidden md:flex flex-col absolute top-20 bottom-6 left-6 z-20 bg-white/98 backdrop-blur-xs border border-[#e5e5e5] transition-all duration-200 ease-out overflow-hidden shadow-sm"
      >
        {/* Header Bar */}
        <div className="p-3 border-b border-[#e5e5e5] flex items-center justify-between bg-[#fcfbf9] shrink-0 font-mono">
          {!isCollapsed ? (
            <div className="flex items-center space-x-2 overflow-hidden">
              <span className="text-[11px] font-bold text-[#111111] uppercase tracking-wider truncate font-sans">
                {title}
              </span>
              {badge && (
                <span className="text-[9px] px-1.5 py-0.5 border border-[#d4d4d4] text-[#555555] font-bold shrink-0">
                  {badge}
                </span>
              )}
            </div>
          ) : (
            <div className="w-full text-center text-xs font-bold text-[#111111]">
              HW
            </div>
          )}

          <div className="flex items-center space-x-1 shrink-0 text-xs text-[#555555]">
            <button
              onClick={handleToggleCollapse}
              title={isCollapsed ? "Mở rộng" : "Thu gọn"}
              className="px-1.5 py-0.5 hover:text-[#111111] hover:bg-[#f0f0f0] transition font-mono"
            >
              {isCollapsed ? "[+]" : "[-]"}
            </button>
            <button
              onClick={onClose}
              title="Đóng bảng"
              className="px-1.5 py-0.5 hover:text-[#111111] hover:bg-[#f0f0f0] transition font-mono"
            >
              [x]
            </button>
          </div>
        </div>

        {/* Panel Body */}
        {!isCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {children}
          </div>
        )}
      </section>

      {/* Mobile Flat Bottom Sheet */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-[#e5e5e5] max-h-[70vh] flex flex-col">
        <div className="p-3 border-b border-[#e5e5e5] flex items-center justify-between bg-[#fcfbf9] font-mono text-xs">
          <span className="font-bold text-[#111111] truncate">{title}</span>
          <button onClick={onClose} className="px-2 py-0.5 text-[#555555] hover:text-[#111111]">
            [x]
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {children}
        </div>
      </div>
    </>
  );
}
