"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check, ArrowLeft, Clock, MapPin } from "lucide-react";

interface DeliveryStop {
  id: string;
  orderId: string;
  address: string;
  demand: number;
  eta: string;
  status: "PENDING" | "DELIVERED";
}

const INITIAL_STOPS: DeliveryStop[] = [
  { id: "s1", orderId: "ORD-01", address: "475A Điện Biên Phủ, HUTECH", demand: 4, eta: "11:15", status: "PENDING" },
  { id: "s2", orderId: "ORD-02", address: "Pearl Plaza, D2", demand: 5, eta: "11:28", status: "PENDING" },
  { id: "s3", orderId: "ORD-03", address: "Sảnh Landmark 81, Vinhomes", demand: 6, eta: "11:42", status: "PENDING" },
  { id: "s4", orderId: "ORD-04", address: "Chợ Bà Chiểu, Bạch Đằng", demand: 3, eta: "11:58", status: "PENDING" },
];

export default function ShipperPWAPage() {
  const [stops, setStops] = useState<DeliveryStop[]>(INITIAL_STOPS);

  const toggleDelivered = (id: string) => {
    setStops((prev) =>
      prev.map((s) => (s.id === id ? { ...s, status: s.status === "PENDING" ? "DELIVERED" : "PENDING" } : s))
    );
  };

  const completedCount = stops.filter((s) => s.status === "DELIVERED").length;

  return (
    <div className="min-h-screen bg-app text-primary-text flex flex-col font-sans select-none">
      {/* Mobile App Header */}
      <header className="p-4 bg-surface border-b border-border-warm flex items-center justify-between sticky top-0 z-10 shadow-soft">
        <div>
          <span className="text-[10px] font-mono text-brand-gold uppercase tracking-widest font-bold block">
            HÀNG GÒN QUÁN • TÀI XẾ SỐ 1
          </span>
          <h1 className="text-base font-bold text-primary-text">Lộ Trình Giao Hàng</h1>
        </div>
        <Link
          href="/"
          className="text-xs font-bold text-brand-brown hover:bg-sunken border border-border-warm px-3 py-1.5 rounded-xl transition flex items-center space-x-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Điều phối</span>
        </Link>
      </header>

      {/* Progress Card */}
      <main className="p-4 max-w-lg mx-auto w-full space-y-4">
        <div className="p-4 bg-surface border border-border-warm rounded-warm shadow-soft space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-secondary-text uppercase tracking-wider">
              Tiến độ giao hàng
            </span>
            <span className="text-xs font-mono font-bold text-status-success">
              {completedCount} / {stops.length} đơn
            </span>
          </div>

          <div className="w-full bg-sunken h-2.5 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-gold rounded-full transition-all duration-300"
              style={{ width: `${(completedCount / stops.length) * 100}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-secondary-text pt-1 border-t border-border-warm/60">
            <span>Thùng giữ nhiệt: 82.5°C</span>
            <span className="text-status-success font-bold">Món đạt chuẩn</span>
          </div>
        </div>

        {/* Stops List */}
        <div className="space-y-2">
          {stops.map((stop, idx) => {
            const isDone = stop.status === "DELIVERED";
            return (
              <div
                key={stop.id}
                className={`p-3.5 rounded-warm border transition flex items-center justify-between ${
                  isDone
                    ? "bg-sunken/40 border-border-warm opacity-60"
                    : "bg-surface border-border-warm shadow-soft"
                }`}
              >
                <div className="flex items-start space-x-3 overflow-hidden">
                  <span className="w-6 h-6 rounded-full bg-sunken border border-border-warm flex items-center justify-center font-mono text-xs font-bold text-secondary-text shrink-0 mt-0.5">
                    {idx + 1}
                  </span>

                  <div className="overflow-hidden">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-brand-gold">
                        {stop.orderId}
                      </span>
                      <span className="text-xs font-bold text-primary-text truncate">
                        {stop.address}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3 text-[11px] text-secondary-text font-mono mt-1">
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-secondary-text" />
                        <span>ETA: {stop.eta}</span>
                      </span>
                      <span>•</span>
                      <span>{stop.demand} tô bánh canh</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => toggleDelivered(stop.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center space-x-1 shrink-0 ml-2 ${
                    isDone
                      ? "bg-emerald-100 text-status-success border border-emerald-300"
                      : "bg-brand-gold hover:bg-brand-gold-hover text-primary-text shadow-soft"
                  }`}
                >
                  {isDone ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Đã giao</span>
                    </>
                  ) : (
                    <span>Xác nhận</span>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
