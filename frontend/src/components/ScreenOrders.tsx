"use client";

import React, { useState } from "react";
import { Plus, Trash2, RefreshCw, AlertTriangle, PackageOpen, MapPin } from "lucide-react";

export interface Order {
  id: string;
  address: string;
  lat: number;
  lon: number;
  demand: number;
  window_start?: string;
  window_end?: string;
}

interface ScreenOrdersProps {
  orders: Order[];
  onLoadSample: () => void;
  onAddOrder: (order: Order) => void;
  onClearOrders: () => void;
  isLoading: boolean;
  snapWarnings?: { point_id: string; snap_dist_meters: number }[];
  selectedOrderId?: string | null;
  onSelectOrder?: (orderId: string) => void;
}

export default function ScreenOrders({
  orders,
  onLoadSample,
  onAddOrder,
  onClearOrders,
  isLoading,
  snapWarnings = [],
  selectedOrderId,
  onSelectOrder,
}: ScreenOrdersProps) {
  const [newAddress, setNewAddress] = useState("");
  const [newLat, setNewLat] = useState("10.8015");
  const [newLon, setNewLon] = useState("106.7135");
  const [newDemand, setNewDemand] = useState("3");

  const totalBowls = orders.reduce((sum, o) => sum + o.demand, 0);

  const handleManualAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAddress.trim()) return;

    const lat = parseFloat(newLat);
    const lon = parseFloat(newLon);
    const demand = parseInt(newDemand) || 3;

    onAddOrder({
      id: `ORD-${Date.now().toString().slice(-4)}`,
      address: newAddress.trim(),
      lat,
      lon,
      demand,
      window_start: "11:00",
      window_end: "12:00",
    });

    setNewAddress("");
  };

  return (
    <div className="space-y-4">
      {/* Top Stats & Action Bar */}
      <div className="flex items-center justify-between bg-sunken/60 p-3 rounded-warm border border-border-warm">
        <div>
          <span className="text-[10px] font-mono tracking-wider uppercase text-secondary-text font-bold block">
            TỔNG SỐ LƯỢNG
          </span>
          <div className="flex items-baseline space-x-1.5 mt-0.5">
            <span className="text-lg font-bold font-mono text-primary-text">
              {orders.length}
            </span>
            <span className="text-xs text-secondary-text">đơn</span>
            <span className="text-secondary-text">•</span>
            <span className="text-sm font-bold font-mono text-brand-brown">
              {totalBowls}
            </span>
            <span className="text-xs text-secondary-text">tô bánh canh</span>
          </div>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            onClick={onLoadSample}
            disabled={isLoading}
            className="px-3 py-1.5 rounded-xl bg-brand-gold hover:bg-brand-gold-hover active:bg-brand-gold-pressed text-primary-text font-bold text-xs shadow-soft transition disabled:opacity-50 flex items-center space-x-1"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
            <span>Nạp mẫu</span>
          </button>
          {orders.length > 0 && (
            <button
              onClick={onClearOrders}
              title="Xóa danh sách đơn"
              className="p-1.5 rounded-xl border border-border-warm text-secondary-text hover:bg-sunken hover:text-status-danger transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Snap Distance Warnings */}
      {snapWarnings.length > 0 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-warm text-xs text-amber-900 space-y-1">
          <div className="flex items-center space-x-1.5 font-bold text-amber-800">
            <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
            <span>Cảnh báo khoảng cách snap đường (&gt; 60m):</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-800/90 pl-1">
            {snapWarnings.slice(0, 3).map((w, idx) => (
              <li key={idx}>
                Điểm {w.point_id}: cách nút đường {w.snap_dist_meters}m
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Add Form */}
      <form
        onSubmit={handleManualAdd}
        className="p-3 bg-surface border border-border-warm rounded-warm shadow-soft space-y-2.5"
      >
        <span className="text-[11px] font-bold text-primary-text block">
          Thêm đơn nhanh
        </span>
        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="Địa chỉ giao (vd: 561A Điện Biên Phủ)"
            value={newAddress}
            onChange={(e) => setNewAddress(e.target.value)}
            className="flex-1 bg-sunken border border-border-warm rounded-xl px-3 py-1.5 text-xs text-primary-text placeholder-secondary-text/70 focus:outline-none focus:border-brand-gold"
          />
          <input
            type="number"
            placeholder="Số tô"
            value={newDemand}
            onChange={(e) => setNewDemand(e.target.value)}
            min="1"
            max="20"
            className="w-16 bg-sunken border border-border-warm rounded-xl px-2 py-1.5 text-xs text-primary-text text-center font-mono focus:outline-none focus:border-brand-gold"
          />
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl border border-brand-gold text-brand-brown hover:bg-brand-gold-soft font-bold text-xs transition flex items-center space-x-1"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm</span>
          </button>
        </div>
      </form>

      {/* Orders List / Cards */}
      <div className="space-y-2">
        <span className="text-[11px] font-bold text-secondary-text uppercase tracking-wider block">
          Danh sách chặng giao ({orders.length})
        </span>

        {orders.length === 0 ? (
          <div className="p-8 text-center bg-surface border border-dashed border-border-warm rounded-warm space-y-2">
            <PackageOpen className="w-8 h-8 text-secondary-text mx-auto opacity-40" />
            <p className="text-xs text-secondary-text">Chưa có đơn hàng nào.</p>
            <p className="text-[11px] text-secondary-text/80 italic">
              Tuyến giao hàng ngắn nhất để món còn nóng.
            </p>
            <button
              onClick={onLoadSample}
              className="mt-2 px-3 py-1.5 rounded-xl bg-brand-gold hover:bg-brand-gold-hover text-primary-text font-bold text-xs transition"
            >
              Nạp mẫu Bình Thạnh
            </button>
          </div>
        ) : (
          <div className="space-y-1.5 max-h-[380px] overflow-y-auto pr-0.5">
            {orders.map((o, idx) => {
              const isSelected = selectedOrderId === o.id;
              return (
                <div
                  key={o.id}
                  onClick={() => onSelectOrder && onSelectOrder(o.id)}
                  className={`p-2.5 rounded-warm border transition cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? "bg-brand-gold-soft border-brand-gold shadow-soft"
                      : "bg-surface border-border-warm hover:bg-sunken/60"
                  }`}
                >
                  <div className="flex items-center space-x-2.5 overflow-hidden">
                    <span className="w-6 h-6 rounded-full bg-sunken border border-border-warm flex items-center justify-center font-mono text-[11px] font-bold text-secondary-text shrink-0">
                      {idx + 1}
                    </span>
                    <div className="overflow-hidden">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-brand-gold">
                          {o.id}
                        </span>
                        <span className="text-xs font-medium text-primary-text truncate">
                          {o.address}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-[10px] text-secondary-text font-mono mt-0.5">
                        <MapPin className="w-3 h-3 text-secondary-text" />
                        <span>
                          {o.lat.toFixed(4)}, {o.lon.toFixed(4)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="shrink-0 pl-2">
                    <span className="px-2 py-0.5 rounded-full bg-sunken border border-border-warm font-mono text-xs font-bold text-primary-text">
                      {o.demand} tô
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
