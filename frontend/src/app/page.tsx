"use client";

import React, { useEffect, useState } from "react";
import OptimoMap from "../components/OptimoMap";
import TopFloatingBar from "../components/TopFloatingBar";
import NavigationDrawer from "../components/NavigationDrawer";
import FloatingTabBar from "../components/FloatingTabBar";
import FloatingSheet from "../components/FloatingSheet";
import ScreenOrders, { Order } from "../components/ScreenOrders";
import ScreenPlanning from "../components/ScreenPlanning";
import ScreenRouteDetail from "../components/ScreenRouteDetail";
import ScreenStrategyLab from "../components/ScreenStrategyLab";
import ScreenSearchReplay from "../components/ScreenSearchReplay";
import ScreenLiveDispatch from "../components/ScreenLiveDispatch";
import { OptimoTab } from "../components/OptimoSidebar";
import { AlertCircle, CheckCircle2 } from "lucide-react";

const DEFAULT_DEPOT = {
  lat: 10.8012,
  lon: 106.7145,
  name: "Hàng Gòn Quán - Bếp Trung Tâm",
};

interface ToastNotification {
  id: string;
  type: "error" | "success" | "info";
  message: string;
  detail?: string;
}

export default function OptimoSchedulingPage() {
  const [activeTab, setActiveTab] = useState<OptimoTab>("orders");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isDrawerPinned, setIsDrawerPinned] = useState(false);
  const [isSheetOpen, setIsSheetOpen] = useState(true);

  // Core Data States
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [snapWarnings, setSnapWarnings] = useState<{ point_id: string; snap_dist_meters: number }[]>([]);
  const [planId, setPlanId] = useState<string | null>(null);
  const [planMetrics, setPlanMetrics] = useState<any>(null);
  const [routes, setRoutes] = useState<any[]>([]);
  const [searchTrace, setSearchTrace] = useState<any[]>([]);
  const [strategyUsed, setStrategyUsed] = useState<string>("best");
  const [isFallback, setIsFallback] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState<number | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [simVehicle, setSimVehicle] = useState<{ vehicle_id: number; lat: number; lon: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // User Geolocation State
  const [userLocation, setUserLocation] = useState<{ lat: number; lon: number; accuracy: number } | null>(null);
  const [isLocating, setIsLocating] = useState(false);

  // Toast Notification System
  const [toasts, setToasts] = useState<ToastNotification[]>([]);

  const addToast = (type: "error" | "success" | "info", message: string, detail?: string) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, type, message, detail }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  // 1. Load Initial Sample Scenario on Mount & Restore Settings
  useEffect(() => {
    try {
      const savedPin = localStorage.getItem("hotway_drawer_pinned");
      if (savedPin === "true") setIsDrawerPinned(true);
    } catch (e) {}

    handleLoadSample();
  }, []);

  const handleTogglePin = () => {
    setIsDrawerPinned((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("hotway_drawer_pinned", String(next));
      } catch (e) {}
      return next;
    });
  };

  // 2. Fetch Sample Scenario
  const handleLoadSample = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/scenarios/sample", {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setScenarioId(data.scenario_id);
        setSnapWarnings(data.snap_warnings || []);

        const detailRes = await fetch(`http://localhost:8000/api/v1/scenarios/${data.scenario_id}`);
        if (detailRes.ok) {
          const detail = await detailRes.json();
          setOrders(detail.orders || []);
        }
        addToast("success", "Đã nạp kịch bản mẫu Bình Thạnh thành công");
      } else {
        addToast("error", "Không thể nạp kịch bản mẫu", "Máy chủ phản hồi mã lỗi: " + res.status);
      }
    } catch (err: any) {
      addToast(
        "error",
        "Không thể kết nối máy chủ",
        "Backend chưa hoạt động hoặc cổng 8000 bị chặn. Vui lòng kiểm tra Docker."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Add & Clear Orders
  const handleAddOrder = (order: Order) => {
    setOrders((prev) => [...prev, order]);
    addToast("info", `Đã thêm đơn ${order.id}`);
  };

  const handleClearOrders = () => {
    setOrders([]);
    setRoutes([]);
    setPlanMetrics(null);
    setPlanId(null);
    setSelectedOrderId(null);
    setSelectedVehicleId(null);
  };

  // 4. Run CVRP Planning
  const handleRunPlan = async (params: {
    strategy: string;
    num_vehicles: number;
    capacity: number;
    min_temp: number;
  }) => {
    if (orders.length === 0) {
      addToast("error", "Chưa có đơn hàng nào", "Vui lòng nạp kịch bản hoặc thêm đơn trước khi lập tuyến.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_id: scenarioId,
          strategy: params.strategy,
          thermal: {
            t0_c: 85.0,
            tenv_c: 30.0,
            k_rate: 0.020,
            min_temp: params.min_temp,
          },
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setPlanId(data.plan_id);
        setPlanMetrics(data.metrics);
        setRoutes(data.routes || []);
        setSearchTrace(data.search_trace || []);
        setStrategyUsed(data.strategy_used);
        setIsFallback(Boolean(data.fallback));
        setSelectedVehicleId(null);

        // Auto open planning sheet to see results
        setActiveTab("planning");
        setIsSheetOpen(true);
        addToast(
          "success",
          `Đã lập kế hoạch hoàn tất (${data.strategy_used})`,
          `Quãng đường: ${data.metrics?.total_distance_km} km`
        );
      } else {
        addToast("error", "Lỗi thuật toán", "Máy chủ không thể tìm phương án khả thi.");
      }
    } catch (err) {
      addToast("error", "Lỗi kết nối", "Không thể gửi yêu cầu giải bài toán đến backend.");
    } finally {
      setIsLoading(false);
    }
  };

  // 5. User Geolocation Handler
  const handleLocateUser = () => {
    if (!navigator.geolocation) {
      addToast("error", "Trình duyệt không hỗ trợ định vị GPS");
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setIsLocating(false);
        addToast("info", "Đã xác định vị trí của bạn", `Độ chính xác ~${Math.round(pos.coords.accuracy)}m`);
      },
      (err) => {
        setIsLocating(false);
        let msg = "Không thể lấy vị trí hiện tại.";
        if (err.code === 1) msg = "Bạn đã từ chối quyền truy cập vị trí.";
        else if (err.code === 2) msg = "Mất tín hiệu định vị GPS.";
        addToast("error", "Lỗi định vị", msg);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  // 6. Address Suggestion Pick Handler
  const handleSelectAddressPoint = (pt: { lat: number; lon: number; name: string }) => {
    handleAddOrder({
      id: `ORD-${Date.now().toString().slice(-4)}`,
      address: pt.name,
      lat: pt.lat,
      lon: pt.lon,
      demand: 2,
    });
    setSelectedOrderId(null);
  };

  // Tab Title Mappings
  const getTabTitle = (tab: OptimoTab) => {
    switch (tab) {
      case "orders":
        return "Quản lý đơn hàng";
      case "planning":
        return "Lập kế hoạch tuyến CVRP";
      case "route":
        return "Chi tiết chặng & nhiệt độ";
      case "strategy_lab":
        return "Strategy Lab: Đánh giá thuật toán";
      case "search_replay":
        return "Search Replay: Vết hội tụ";
      case "live":
        return "Theo dõi điều phối";
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-app font-sans text-primary-text select-none">
      {/* 1. Full-screen Real MapLibre Background Canvas */}
      <OptimoMap
        depot={DEFAULT_DEPOT}
        orders={orders}
        routes={routes}
        selectedVehicleId={selectedVehicleId}
        selectedOrderId={selectedOrderId}
        onSelectOrder={(id) => {
          setSelectedOrderId(id);
          setIsSheetOpen(true);
        }}
        simVehicle={simVehicle}
        userLocation={userLocation}
        onLocateUser={handleLocateUser}
        isLocating={isLocating}
      />

      {/* 2. Floating Top Header Bar */}
      <TopFloatingBar
        onToggleDrawer={() => setIsDrawerOpen(true)}
        onLocateUser={handleLocateUser}
        isLocating={isLocating}
        onQuickPlan={() =>
          handleRunPlan({
            strategy: "best",
            num_vehicles: 5,
            capacity: 40,
            min_temp: 60.0,
          })
        }
        onSelectAddressPoint={handleSelectAddressPoint}
        isPlanning={isLoading}
      />

      {/* 3. Floating Horizontal Tab Bar (Top for Desktop, Bottom for Mobile) */}
      <div className="hidden md:block absolute top-20 left-1/2 -translate-x-1/2 z-20">
        <FloatingTabBar
          activeTab={activeTab}
          onChangeTab={(tab) => {
            setActiveTab(tab);
            setIsSheetOpen(true);
          }}
          ordersCount={orders.length}
          routesCount={routes.length}
        />
      </div>

      <div className="md:hidden fixed bottom-3 left-4 right-4 z-20 flex justify-center">
        <FloatingTabBar
          activeTab={activeTab}
          onChangeTab={(tab) => {
            setActiveTab(tab);
            setIsSheetOpen(true);
          }}
          ordersCount={orders.length}
          routesCount={routes.length}
        />
      </div>

      {/* 4. Left Slide Navigation Drawer */}
      <NavigationDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        activeTab={activeTab}
        onChangeTab={(tab) => {
          setActiveTab(tab);
          setIsSheetOpen(true);
        }}
        ordersCount={orders.length}
        routesCount={routes.length}
        isPinned={isDrawerPinned}
        onTogglePin={handleTogglePin}
      />

      {/* 5. Floating Active Screen Content Sheet */}
      <FloatingSheet
        title={getTabTitle(activeTab)}
        badge={activeTab === "live" ? "MÔ PHỎNG" : undefined}
        isOpen={isSheetOpen}
        onClose={() => setIsSheetOpen(false)}
        width={440}
      >
        {activeTab === "orders" && (
          <ScreenOrders
            orders={orders}
            onLoadSample={handleLoadSample}
            onAddOrder={handleAddOrder}
            onClearOrders={handleClearOrders}
            isLoading={isLoading}
            snapWarnings={snapWarnings}
            selectedOrderId={selectedOrderId}
            onSelectOrder={(id) => setSelectedOrderId(id)}
          />
        )}

        {activeTab === "planning" && (
          <ScreenPlanning
            onRunPlan={handleRunPlan}
            isLoading={isLoading}
            planMetrics={planMetrics}
            routes={routes}
            selectedVehicleId={selectedVehicleId}
            onSelectVehicle={setSelectedVehicleId}
            strategyUsed={strategyUsed}
            isFallback={isFallback}
          />
        )}

        {activeTab === "route" && (
          <ScreenRouteDetail
            routes={routes}
            selectedVehicleId={selectedVehicleId || 1}
            onSelectVehicle={setSelectedVehicleId}
          />
        )}

        {activeTab === "strategy_lab" && <ScreenStrategyLab />}

        {activeTab === "search_replay" && (
          <ScreenSearchReplay
            searchTrace={searchTrace}
            strategyName={strategyUsed}
          />
        )}

        {activeTab === "live" && (
          <ScreenLiveDispatch
            planId={planId}
            onReplanRemaining={() =>
              handleRunPlan({
                strategy: "best",
                num_vehicles: 5,
                capacity: 40,
                min_temp: 60.0,
              })
            }
            onUpdateSimVehicle={setSimVehicle}
          />
        )}
      </FloatingSheet>

      {/* 6. Toast Notification Center */}
      <div className="fixed top-20 right-6 z-50 flex flex-col space-y-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto p-3 rounded-warm border shadow-floating max-w-sm flex items-start space-x-2.5 transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
              t.type === "error"
                ? "bg-red-50 border-red-200 text-status-danger"
                : t.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-status-success"
                : "bg-surface border-border-warm text-primary-text"
            }`}
          >
            {t.type === "error" ? (
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            ) : (
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            )}
            <div className="text-xs">
              <p className="font-bold">{t.message}</p>
              {t.detail && (
                <p className="text-[11px] text-secondary-text mt-0.5 leading-snug">
                  {t.detail}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
