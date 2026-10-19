"use client";

import React, { useState, useEffect } from "react";
import Link from "next/navigation";

interface MenuItem {
  id: number;
  name: string;
  price: number;
  initialTemp: number;
  kRate: number;
  category: "SOUP" | "DRY" | "DRINK";
  desc: string;
  icon: string;
}

const MENU: MenuItem[] = [
  {
    id: 1,
    name: "Bánh Canh Gà Đặc Biệt",
    price: 45000,
    initialTemp: 88,
    kRate: 0.038,
    category: "SOUP",
    desc: "Nước lèo gà ta ngọt thanh, sợi bánh dai mềm, thịt gà xé đậm vị.",
    icon: "🍲",
  },
  {
    id: 2,
    name: "Bánh Canh Gà Đùi",
    price: 50000,
    initialTemp: 88,
    kRate: 0.038,
    category: "SOUP",
    desc: "Đùi gà ta nguyên chiếc da vàng giòn, nước dùng nóng sốt thơm lừng.",
    icon: "🍗",
  },
  {
    id: 3,
    name: "Gỏi Gà Xé Phay Rau Răm",
    price: 60000,
    initialTemp: 58,
    kRate: 0.022,
    category: "DRY",
    desc: "Thịt gà xé trộn hành tây, rau răm, nước mắm chua ngọt ăn kèm bánh tráng.",
    icon: "🥗",
  },
  {
    id: 4,
    name: "Nước Sâm Lạnh Hàng Gòn",
    price: 15000,
    initialTemp: 6,
    kRate: 0.030,
    category: "DRINK",
    desc: "Nấu từ lá dứa và mía lau tự nhiên thanh mát, giữ lạnh khi giao.",
    icon: "🥤",
  },
];

const DESTINATIONS = [
  { id: "dest_1", name: "Ngã Ba Hàng Gòn (QL56)", lat: 10.9235, lon: 107.2418, distKm: 1.2 },
  { id: "dest_2", name: "UBND Xã Hàng Gòn", lat: 10.9260, lon: 107.2435, distKm: 1.8 },
  { id: "dest_3", name: "Di Tích Cự Thạch Hàng Gòn", lat: 10.9320, lon: 107.2480, distKm: 3.2 },
  { id: "dest_4", name: "Trường Tiểu Học Hàng Gòn", lat: 10.9180, lon: 107.2350, distKm: 2.1 },
  { id: "dest_5", name: "Ấp Suối Tre (Long Khánh)", lat: 10.9400, lon: 107.2550, distKm: 4.5 },
];

export default function CustomerOrderPage() {
  const [selectedItem, setSelectedItem] = useState<MenuItem>(MENU[0]);
  const [containerType, setContainerType] = useState<"INSULATED_BAG" | "FOAM_BOX" | "STANDARD_BAG">("INSULATED_BAG");
  const [selectedDest, setSelectedDest] = useState(DESTINATIONS[2]);
  const [isOrdered, setIsOrdered] = useState(false);
  const [currentTemp, setCurrentTemp] = useState<number>(MENU[0].initialTemp);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isTrafficRush, setIsTrafficRush] = useState(true);

  // Compute thermal decay dynamically: T(t) = T_env + (T_0 - T_env) * exp(-k * t)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isOrdered) {
      interval = setInterval(() => {
        setElapsedSeconds((prev) => {
          const nextSec = prev + 1;
          const tEnv = 30.0;
          let k = selectedItem.kRate;
          if (containerType === "INSULATED_BAG") k *= 0.50;
          if (containerType === "FOAM_BOX") k *= 0.70;

          const tMin = (nextSec * 15) / 60.0; // 15x accelerated for demo
          const temp = tEnv + (selectedItem.initialTemp - tEnv) * Math.exp(-k * tMin);
          setCurrentTemp(parseFloat(temp.toFixed(1)));
          return nextSec;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isOrdered, selectedItem, containerType]);

  const handlePlaceOrder = () => {
    setCurrentTemp(selectedItem.initialTemp);
    setElapsedSeconds(0);
    setIsOrdered(true);
  };

  const getThermalStatus = (temp: number) => {
    if (temp >= 75) return { label: "NÓNG HỔI VỪA THỔI VỪA ĂN", color: "bg-red-500 text-white" };
    if (temp >= 60) return { label: "NÓNG NGON CHUẨN VỊ (ĐẠT CHUẨN)", color: "bg-orange-500 text-white" };
    return { label: "CẢNH BÁO: MÓN ĐANG NGUỘI", color: "bg-slate-500 text-white" };
  };

  const thermalStatus = getThermalStatus(currentTemp);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-8 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl">🍲</span>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              HotWAY <span className="text-orange-600">Hàng Gòn</span>
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
              Đang mở cửa • Long Khánh, Đồng Nai
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Hệ thống giao đồ ăn tối ưu nhiệt độ bằng Học Tăng Cường (Reinforcement Learning) đầu tiên tại Hàng Gòn
          </p>
        </div>

        {/* Quick Nav Links */}
        <div className="flex items-center gap-3 mt-4 md:mt-0">
          <a
            href="/shipper"
            className="px-3.5 py-2 text-sm font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-800 transition shadow-sm"
          >
            📱 Shipper PWA
          </a>
          <a
            href="/admin/comparison-studio"
            className="px-3.5 py-2 text-sm font-semibold rounded-lg bg-orange-600 text-white hover:bg-orange-700 transition shadow-sm"
          >
            📊 So sánh RL vs Baseline
          </a>
          <a
            href="/game/rider"
            className="px-3.5 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition shadow-sm"
          >
            🎮 Đua 3D với AI Ghost
          </a>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Menu & Packaging */}
        <div className="lg:col-span-7 space-y-6">
          <section className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span>📋</span> Menu Quán Bánh Canh Gà Hàng Gòn
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {MENU.map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    setSelectedItem(item);
                    if (!isOrdered) setCurrentTemp(item.initialTemp);
                  }}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedItem.id === item.id
                      ? "border-orange-500 bg-orange-50/50 shadow-sm"
                      : "border-slate-100 bg-white hover:border-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className="text-3xl">{item.icon}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-800">
                      T₀: {item.initialTemp}°C
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 mt-2">{item.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">{item.desc}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="font-extrabold text-orange-600">
                      {item.price.toLocaleString("vi-VN")} đ
                    </span>
                    <span className="text-[11px] text-slate-400">k = {item.kRate}/phút</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Packaging Box Selection */}
          <section className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
              <span>🎒</span> Loại Thùng / Túi Giữ Nhiệt
            </h2>
            <div className="grid grid-cols-3 gap-3">
              {[
                { type: "INSULATED_BAG", label: "Túi Bạc Giữ Nhiệt", eff: "Giảm nguội 50%", icon: "🛡️" },
                { type: "FOAM_BOX", label: "Thùng Xốp Chuẩn", eff: "Giảm nguội 30%", icon: "📦" },
                { type: "STANDARD_BAG", label: "Túi Ni-lông Thường", eff: "Không cách nhiệt", icon: "🛍️" },
              ].map((box) => (
                <div
                  key={box.type}
                  onClick={() => setContainerType(box.type as any)}
                  className={`p-3 rounded-xl border text-center cursor-pointer transition ${
                    containerType === box.type
                      ? "border-orange-500 bg-orange-50/60 font-semibold text-slate-900"
                      : "border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <span className="text-xl block">{box.icon}</span>
                  <p className="text-xs mt-1">{box.label}</p>
                  <span className="text-[10px] text-emerald-600 block font-medium mt-0.5">{box.eff}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Destination Selector */}
          <section className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <span>📍</span> Địa Điểm Giao Hàng tại Hàng Gòn
              </h2>
              <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isTrafficRush}
                  onChange={(e) => setIsTrafficRush(e.target.checked)}
                  className="rounded text-orange-600"
                />
                Mô phỏng kẹt xe QL56 (Giờ cao điểm)
              </label>
            </div>
            <div className="space-y-2">
              {DESTINATIONS.map((dest) => (
                <div
                  key={dest.id}
                  onClick={() => setSelectedDest(dest)}
                  className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition ${
                    selectedDest.id === dest.id
                      ? "border-orange-500 bg-orange-50/40 font-medium"
                      : "border-slate-100 hover:border-slate-200"
                  }`}
                >
                  <div>
                    <p className="text-sm text-slate-900">{dest.name}</p>
                    <p className="text-xs text-slate-400">Khoảng cách từ Quán: ~{dest.distKm} km</p>
                  </div>
                  <span className="text-xs font-bold text-slate-600">
                    {Math.round((dest.distKm / 30) * 60 + (isTrafficRush ? 6 : 0))} phút
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column: Thermal Meter & Live Dispatching */}
        <div className="lg:col-span-5 space-y-6">
          <section className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 sticky top-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
              <span>🌡️</span> Đồng Hồ Nhiệt Độ Món Ăn Thời Gian Thực
            </h2>

            {/* Thermal Dial Display */}
            <div className="flex flex-col items-center justify-center p-6 bg-slate-900 rounded-2xl text-white relative overflow-hidden">
              <div className="absolute top-2 right-3 text-xs text-slate-400 font-mono">
                T_env: 30°C • Newton Decay
              </div>
              <div className="text-6xl font-black tracking-tight text-orange-400 mt-3">
                {currentTemp}°C
              </div>
              <p className="text-xs text-slate-400 mt-1">Nhiệt độ ước tính của {selectedItem.name}</p>

              <div className="mt-4 w-full">
                <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      currentTemp >= 75 ? "bg-red-500" : currentTemp >= 60 ? "bg-orange-500" : "bg-slate-500"
                    }`}
                    style={{ width: `${Math.min(100, Math.max(0, (currentTemp / 90) * 100))}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                  <span>20°C (Nguội lạnh)</span>
                  <span className="text-orange-400 font-bold">60°C (Ngưỡng ngon)</span>
                  <span>90°C (Mới nấu)</span>
                </div>
              </div>

              <div className={`mt-4 px-3 py-1.5 rounded-lg text-xs font-bold ${thermalStatus.color}`}>
                {thermalStatus.label}
              </div>
            </div>

            {/* Dispatch Route Card */}
            <div className="mt-6 p-4 rounded-xl bg-slate-50 border border-slate-200">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                Lộ Trình Đề Xuất Bởi RL Policy Runner
              </h3>
              <div className="text-xs space-y-2 text-slate-700">
                <div className="flex justify-between">
                  <span className="text-slate-500">Điểm xuất phát:</span>
                  <span className="font-semibold">Quán Bánh Canh Gà Hàng Gòn (Depot)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Điểm giao:</span>
                  <span className="font-semibold">{selectedDest.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Thuật toán định tuyến:</span>
                  <span className="font-bold text-orange-600">
                    HotWAY MaskablePPO (Tránh tắc QL56)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Dự kiến nhiệt độ lúc đến:</span>
                  <span className="font-extrabold text-emerald-600">
                    {Math.max(62, Math.round(selectedItem.initialTemp - selectedDest.distKm * 4.2))}°C
                  </span>
                </div>
              </div>
            </div>

            {/* Action CTA */}
            <div className="mt-6">
              {!isOrdered ? (
                <button
                  onClick={handlePlaceOrder}
                  className="w-full py-3.5 px-4 rounded-xl bg-orange-600 hover:bg-orange-700 text-white font-bold text-base shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  <span>🚀</span> Đặt Món & Kích Hoạt Điều Phối RL
                </button>
              ) : (
                <div className="space-y-3">
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
                    <span className="text-base animate-spin">🔄</span>
                    <div>
                      <p className="font-bold">Đơn hàng đang được vận chuyển!</p>
                      <p className="text-[11px] text-emerald-700">Shipper đang di chuyển về {selectedDest.name}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsOrdered(false)}
                    className="w-full py-2.5 px-4 rounded-xl border border-slate-300 text-slate-600 text-xs font-semibold hover:bg-slate-100 transition"
                  >
                    Hủy / Đặt đơn khác
                  </button>
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
