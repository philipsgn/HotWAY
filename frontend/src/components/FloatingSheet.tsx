"use client";

import React, { useState, useEffect } from "react";
import { ChevronLeft, ChevronRight, Minimize2, Maximize2, X, ChevronUp, ChevronDown } from "lucide-react";

interface FloatingSheetProps {
  title: string;
  badge?: string;
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  width?: number; // desktop width in px (380 - 520)
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
  // Desktop collapse state
  const [isCollapsed, setIsCollapsed] = useState(false);
  // Mobile snap state: 'peek' (120px) | 'half' (50vh) | 'full' (88vh) | 'closed'
  const [mobileSnap, setMobileSnap] = useState<"peek" | "half" | "full">("half");

  // Read saved collapse state from localStorage with try/catch
  useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved !== null) {
        setIsCollapsed(saved === "true");
      }
    } catch (e) {
      // Ignore localStorage errors (private browsing, etc.)
    }
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
      {/* 1. Desktop Left Floating Sheet (md and up) */}
      <section
        aria-label={title}
        style={{ width: isCollapsed ? "52px" : `${width}px` }}
        className={`hidden md:flex flex-col absolute top-20 bottom-6 left-6 z-20 bg-surface/98 backdrop-blur-md border border-border-warm rounded-warm-lg shadow-floating transition-all duration-300 ease-out overflow-hidden`}
      >
        {/* Header Bar */}
        <div className="p-3.5 border-b border-border-warm flex items-center justify-between bg-sunken/40 shrink-0">
          {!isCollapsed ? (
            <div className="flex items-center space-x-2 overflow-hidden">
              <h2 className="text-xs font-bold text-primary-text uppercase tracking-wider truncate">
                {title}
              </h2>
              {badge && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-gold-soft text-primary-text font-semibold shrink-0">
                  {badge}
                </span>
              )}
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <span className="text-[10px] font-mono font-bold text-brand-gold rotate-90 origin-center whitespace-nowrap mt-4">
                {title}
              </span>
            </div>
          )}

          <div className="flex items-center space-x-1 shrink-0">
            <button
              onClick={handleToggleCollapse}
              aria-label={isCollapsed ? "Mở rộng bảng" : "Thu gọn bảng"}
              title={isCollapsed ? "Mở rộng" : "Thu gọn"}
              className="p-1 rounded-lg text-secondary-text hover:bg-sunken hover:text-primary-text transition"
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
            {!isCollapsed && (
              <button
                onClick={onClose}
                aria-label="Đóng bảng"
                title="Đóng bảng"
                className="p-1 rounded-lg text-secondary-text hover:bg-sunken hover:text-primary-text transition"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Sheet Content Body */}
        {!isCollapsed && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {children}
          </div>
        )}
      </section>

      {/* 2. Mobile Bottom Sheet (below md) */}
      <section
        aria-label={title}
        style={{
          height:
            mobileSnap === "peek" ? "140px" : mobileSnap === "half" ? "52vh" : "88vh",
        }}
        className="md:hidden flex flex-col fixed bottom-0 left-0 right-0 z-30 bg-surface/98 backdrop-blur-md border-t border-border-warm rounded-t-warm-lg shadow-floating transition-all duration-300 ease-out overflow-hidden"
      >
        {/* Drag handle & header */}
        <div className="p-3 border-b border-border-warm flex flex-col items-center shrink-0 bg-sunken/40">
          {/* Visual swipe pill */}
          <div className="w-10 h-1 bg-border-warm rounded-full mb-2" />

          <div className="w-full flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <h2 className="text-xs font-bold text-primary-text uppercase tracking-wider">
                {title}
              </h2>
              {badge && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-brand-gold-soft text-primary-text font-semibold">
                  {badge}
                </span>
              )}
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => {
                  if (mobileSnap === "peek") setMobileSnap("half");
                  else if (mobileSnap === "half") setMobileSnap("full");
                  else setMobileSnap("peek");
                }}
                className="p-1 text-secondary-text hover:text-primary-text"
              >
                {mobileSnap === "full" ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronUp className="w-4 h-4" />
                )}
              </button>
              <button onClick={onClose} className="p-1 text-secondary-text hover:text-primary-text">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Body */}
        <div className="flex-1 overflow-y-auto p-3.5 space-y-3 pb-8">
          {children}
        </div>
      </section>
    </>
  );
}
