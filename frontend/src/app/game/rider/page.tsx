"use client";

import React, { useState } from "react";
import HotWAYRiderCanvas from "@/game/HotWAYRiderCanvas";

export default function RiderGamePage() {
  const [raceResult, setRaceResult] = useState<any>(null);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-3xl">🎮</span>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900">
              HotWAY Rider — <span className="text-orange-600">Đua Xe Với AI Ghost</span>
            </h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Mô phỏng 3D trên bản đồ số Hàng Gòn (Long Khánh, Đồng Nai) • Đua giữ nhiệt độ với Agent Học Tăng Cường
          </p>
        </div>

        <div className="mt-4 md:mt-0 flex items-center gap-2">
          <a
            href="/"
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
          >
            ← Về Trang Đặt Món
          </a>
          <a
            href="/admin/comparison-studio"
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-orange-600 text-white hover:bg-orange-700 transition"
          >
            📊 Xem Studio Đối Chứng RL
          </a>
        </div>
      </div>

      {/* 3D Game Canvas */}
      <div className="mb-8">
        <HotWAYRiderCanvas
          orderId="ORD-HANGGON-RIDER-01"
          ghostTrajectoryUrl="/api/v1/dispatch/ghost-trajectory"
          onGameComplete={(result) => setRaceResult(result)}
        />
      </div>

      {/* Rules & Academic Meaning */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-2xl block mb-2">🎯</span>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Mục Tiêu Cuộc Đua</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Điểm số không chỉ tính theo thời gian về đích mà tính theo <strong>độ nóng của tô bánh canh gà khi đến nơi</strong>. Chạy quá nhanh có thể gây tai nạn, chạy quá chậm sẽ làm nguội thức ăn!
          </p>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-2xl block mb-2">👻</span>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Bóng Ma AI (RL Ghost)</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Xe màu cyan chạy theo đúng tọa độ từng giây mà mô hình <strong>MaskablePPO</strong> đã học được trên mạng lưới đường Hàng Gòn. AI luôn chọn đường tránh thông minh để duy trì vận tốc ổn định.
          </p>
        </div>

        <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-2xl block mb-2">🏷️</span>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Phần Thưởng Thực Tế</h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Bất kỳ ai đánh bại được AI Ghost sẽ nhận ngay mã voucher giảm giá 15% của quán bánh canh gà Hàng Gòn thật, vừa kích thích trải nghiệm vừa ứng dụng vào kinh doanh địa phương.
          </p>
        </div>
      </div>
    </div>
  );
}
