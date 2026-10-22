"use client";

import React from "react";
import Link from "next/link";
import ScreenStrategyLab from "../../../components/ScreenStrategyLab";
import { ArrowLeft } from "lucide-react";

export default function ComparisonStudioPage() {
  return (
    <div className="min-h-screen bg-app text-primary-text flex flex-col font-sans select-none">
      <header className="p-4 bg-surface border-b border-border-warm flex items-center justify-between shadow-soft">
        <div className="flex items-center space-x-3">
          <Link
            href="/"
            className="text-xs font-bold text-brand-brown hover:bg-sunken border border-border-warm px-3 py-1.5 rounded-xl transition flex items-center space-x-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Bàn Điều Phối</span>
          </Link>
          <span className="text-secondary-text">|</span>
          <span className="text-xs font-bold text-primary-text">
            Hàng Gòn Quán • Strategy Lab (DQN-CVRP Benchmark)
          </span>
        </div>
      </header>

      <main className="flex-1 p-6 max-w-5xl mx-auto w-full overflow-y-auto">
        <ScreenStrategyLab />
      </main>
    </div>
  );
}
