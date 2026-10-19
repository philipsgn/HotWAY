"use client";

import React, { useState, useEffect } from "react";

export default function ShipperPWAPage() {
  const [isSimulatingGPS, setIsSimulatingGPS] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [currentLat, setCurrentLat] = useState(10.9212); // Quán Bánh Canh Gà
  const [currentLon, setCurrentLon] = useState(107.2401);
  const [currentTemp, setCurrentTemp] = useState(85.0);
  const [speedKmh, setSpeedKmh] = useState(32.5);
  const [isDelivered, setIsDelivered] = useState(false);

  // Pre-calculated route coordinates along Hàng Gòn from Quán to Di tích Cự Thạch
  const ROUTE_STEPS = [
    { lat: 10.9212, lon: 107.2401, name: "Quán Bánh Canh Gà Hàng Gòn (Xuất phát)", speed: 0.0, temp: 85.0 },
    { lat: 10.9235, lon: 107.2418, name: "Ngã Ba Hàng Gòn (QL56)", speed: 35.0, temp: 82.4 },
    { lat: 10.9260, lon: 107.2435, name: "Đoạn đường tránh Hàng Gòn (RL chọn)", speed: 38.0, temp: 79.8 },
    { lat: 10.9285, lon: 107.2452, name: "Ấp Hàng Gòn 1", speed: 30.0, temp: 77.2 },
    { lat: 10.9305, lon: 107.2468, name: "Gần ngã tư liên ấp", speed: 28.0, temp: 75.1 },
    { lat: 10.9320, lon: 107.2480, name: "Nhà khách hàng (Di tích Cự Thạch)", speed: 0.0, temp: 74.5 },
  ];

  // GPS Simulation Loop
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSimulatingGPS && !isDelivered) {
      interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= ROUTE_STEPS.length - 1) {
            setIsDelivered(true);
            return prev;
          }
          const next = prev + 1;
          const stepData = ROUTE_STEPS[next];
          setCurrentLat(stepData.lat);
          setCurrentLon(stepData.lon);
          setCurrentTemp(stepData.temp);
          setSpeedKmh(stepData.speed);
          return next;
        });
      }, 2500); // Step every 2.5 seconds
    }
    return () => clearInterval(interval);
  }, [isSimulatingGPS, isDelivered]);

  const handleResetTrip = () => {
    setCurrentStep(0);
    const start = ROUTE_STEPS[0];
    setCurrentLat(start.lat);
    setCurrentLon(start.lon);
    setCurrentTemp(start.temp);
    setSpeedKmh(start.speed);
    setIsDelivered(false);
  };

  return (
    <div className="max-w-md mx-auto min-h-screen bg-slate-900 text-white flex flex-col justify-between p-4 font-sans">
      {/* Top Mobile Bar */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🛵</span>
            <div>
              <h1 className="font-bold text-sm tracking-tight">HotWAY Shipper PWA</h1>
              <p className="text-[11px] text-slate-400">Tài xế: Nguyễn Văn Hùng • Xe 60B2-882.19</p>
            </div>
          </div>
          <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            ONLINE
          </span>
        </div>

        {/* GPS Control Card */}
        <div className="mt-4 p-3 bg-slate-800/80 rounded-xl border border-slate-700/60">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-300 font-medium">Chế độ Định Vị GPS:</span>
            <button
              onClick={() => setIsSimulatingGPS(!isSimulatingGPS)}
              className={`px-2.5 py-1 rounded text-xs font-bold transition ${
                isSimulatingGPS
                  ? "bg-orange-500 text-white"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {isSimulatingGPS ? "⚡ Giả Lập GPS Ảo (BẬT)" : "🛰️ GPS Thật (Thiết bị)"}
            </button>
          </div>
          <div className="mt-2 text-[11px] font-mono text-slate-400 flex justify-between">
            <span>Lat: {currentLat.toFixed(6)}</span>
            <span>Lon: {currentLon.toFixed(6)}</span>
            <span>{speedKmh} km/h</span>
          </div>
        </div>

        {/* Active Order Card */}
        <div className="mt-4 p-4 bg-slate-800 rounded-2xl border border-slate-700 shadow-lg">
          <div className="flex items-center justify-between text-xs pb-3 border-b border-slate-700">
            <span className="font-bold text-orange-400">ĐƠN HÀNG #ORD-HG-088</span>
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px]">
              TÚI BẠC GIỮ NHIỆT
            </span>
          </div>

          <div className="mt-3 space-y-2">
            <div className="flex items-start gap-2">
              <span className="text-base">🍲</span>
              <div>
                <p className="font-bold text-sm">2x Bánh Canh Gà Đặc Biệt</p>
                <p className="text-xs text-slate-400">1x Nước Sâm Lạnh Hàng Gòn</p>
              </div>
            </div>

            <div className="flex items-start gap-2 pt-2 border-t border-slate-700/60">
              <span className="text-base">📍</span>
              <div>
                <p className="text-xs text-slate-300 font-medium">Giao đến: Di tích Cự Thạch Hàng Gòn</p>
                <p className="text-[11px] text-slate-400">Khách: Chị Lan • 0918.423.xxx</p>
              </div>
            </div>
          </div>
        </div>

        {/* Live Thermal Monitor Meter */}
        <div className="mt-4 p-4 bg-gradient-to-br from-slate-800 to-slate-850 rounded-2xl border border-slate-700">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>CẢM BIẾN NHIỆT MÓN ĂN</span>
            <span className="text-emerald-400 font-bold">MÔ HÌNH NEWTON</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-orange-400">{currentTemp}°C</span>
            <span className="text-xs text-slate-400">
              (Chuẩn ngon: &ge; 60°C)
            </span>
          </div>
          <div className="mt-2 w-full bg-slate-700 h-2 rounded-full overflow-hidden">
            <div
              className="bg-orange-500 h-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, (currentTemp / 90) * 100))}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-2">
            {currentTemp >= 75
              ? "🔥 Rất nóng: Bánh canh vừa ra lò, chất lượng tuyệt hảo."
              : "🍲 Nóng ngon: Hương vị thơm ngon, mỡ gà không bị đông."}
          </p>
        </div>

        {/* Step-by-Step Waypoint Progress */}
        <div className="mt-4 p-3 bg-slate-800/60 rounded-xl border border-slate-700/60">
          <p className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">
            Lộ trình RL dẫn đường ({currentStep + 1}/{ROUTE_STEPS.length}):
          </p>
          <p className="text-xs text-emerald-400 font-semibold">
            👉 {ROUTE_STEPS[currentStep].name}
          </p>
        </div>
      </div>

      {/* Bottom Action Button */}
      <div className="pt-4 mt-4 border-t border-slate-800">
        {!isDelivered ? (
          <button
            onClick={() => setIsDelivered(true)}
            className="w-full py-3.5 px-4 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-bold text-sm shadow-lg transition"
          >
            ✅ Xác Nhận Đã Giao Tới Khách Hàng
          </button>
        ) : (
          <div className="space-y-2">
            <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-center">
              <p className="text-sm font-bold text-emerald-400">🎉 GIAO HÀNG THÀNH CÔNG!</p>
              <p className="text-xs text-slate-300">Nhiệt độ lúc đến: {currentTemp}°C (Đạt chuẩn nóng sốt)</p>
            </div>
            <button
              onClick={handleResetTrip}
              className="w-full py-2.5 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700 transition"
            >
              🔄 Nhận Chuyến Mới / Chạy Lại Demo
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
