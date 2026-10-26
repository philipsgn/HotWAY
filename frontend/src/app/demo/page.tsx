"use client";

import React, { useEffect, useState } from "react";
import OptimoMap, { RouteData, Point } from "../../components/OptimoMap";
import TopFloatingBar from "../../components/TopFloatingBar";
import NavigationDrawer from "../../components/NavigationDrawer";
import FloatingTabBar from "../../components/FloatingTabBar";
import FloatingSheet from "../../components/FloatingSheet";
import ScreenT1MultiCriteria, { T1RouteInfo } from "../../components/ScreenT1MultiCriteria";
import ScreenT2VRPTW from "../../components/ScreenT2VRPTW";
import ScreenT3AdaptiveReroute from "../../components/ScreenT3AdaptiveReroute";
import { OptimoTab } from "../../components/OptimoSidebar";

const DEFAULT_DEPOT = {
  lat: 10.8016,
  lon: 106.7115,
  name: "Bưu Cục Tập Kết Hàng Bình Thạnh (Node #1497276525)",
};

interface ToastNotification {
  id: string;
  type: "error" | "success" | "info";
  message: string;
  detail?: string;
}

export default function OptimoSchedulingPage() {
  const [activeTab, setActiveTab] = useState<OptimoTab>("t1_multicriteria");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isDrawerPinned, setIsDrawerPinned] = useState(false);
  const [isSheetOpen, setIsSheetOpen] = useState(true);

  // Map visualization states
  const [orders, setOrders] = useState<Point[]>([]);
  const [routes, setRoutes] = useState<RouteData[]>([]);
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

  // Restore drawer pin setting
  useEffect(() => {
    try {
      const savedPin = localStorage.getItem("hotway_drawer_pinned");
      if (savedPin === "true") setIsDrawerPinned(true);
    } catch (e) {}
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

  // Handle T1 Route Selection & Rendering on Map
  const handleSelectT1Route = (selectedRoute: T1RouteInfo | null, allRoutes: T1RouteInfo[]) => {
    if (!selectedRoute) return;

    // Convert 4 Pareto routes into MapLibre RouteData layers
    // Vehicle IDs: 1 (Blue), 2 (Amber), 3 (Emerald), 4 (Purple)
    const mapRoutes: RouteData[] = allRoutes.map((r, idx) => ({
      vehicle_id: idx + 1,
      leg_geometries: [r.coordinates],
      customer_indices: [],
      distance_km: r.distance_m / 1000,
      duration_min: r.expected_time_min,
    }));

    setRoutes(mapRoutes);

    // Find vehicle id for currently selected route
    const selIdx = allRoutes.findIndex((r) => r.key === selectedRoute.key);
    if (selIdx >= 0) {
      setSelectedVehicleId(selIdx + 1);
    }
  };

  const handleUpdateT1Points = (origin: [number, number], dest: [number, number]) => {
    setOrders([
      {
        id: "ORIGIN",
        lat: origin[0],
        lon: origin[1],
        name: "Điểm đi (Origin Node #1497276525)",
      },
      {
        id: "DEST",
        lat: dest[0],
        lon: dest[1],
        name: "Điểm đến (Destination Node #5337055581)",
      },
    ]);
  };

  // Handle T3 Live Simulation Geometry Updates
  const handleUpdateT3Geometry = (traversedCoords: [number, number][]) => {
    if (traversedCoords.length >= 2) {
      setRoutes([
        {
          vehicle_id: 1,
          leg_geometries: [traversedCoords],
          customer_indices: [],
          distance_km: 2.3,
          duration_min: 1.2,
        },
      ]);
    }
  };

  // User Geolocation Handler
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
        addToast("info", "Đã xác định vị trí thiết bị", `Độ chính xác ~${Math.round(pos.coords.accuracy)}m`);
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

  // Address Suggestion Pick Handler
  const handleSelectAddressPoint = (pt: { lat: number; lon: number; name: string }) => {
    addToast("info", "Đã chọn địa chỉ", pt.name);
  };

  // Tab Title Mappings
  const getTabTitle = (tab: OptimoTab) => {
    switch (tab) {
      case "t1_multicriteria":
        return "T1: Tuyến Pareto Đa Tiêu Chí (A → B)";
      case "t2_vrptw":
        return "T2: Lập Tuyến Đội Xe VRPTW";
      case "t3_live":
        return "T3: Đổi Tuyến Thích Nghi (Live SSE)";
    }
  };

  const getTabBadge = (tab: OptimoTab) => {
    switch (tab) {
      case "t1_multicriteria":
        return "PARETO";
      case "t2_vrptw":
        return "VRPTW";
      case "t3_live":
        return "MÔ PHỎNG";
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-white font-sans text-neutral-900 select-none">
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
        onQuickPlan={() => addToast("info", "Tính toán Pareto", "Đang phân tích 4 tuyến Pareto đặc trưng.")}
        onSelectAddressPoint={handleSelectAddressPoint}
        isPlanning={isLoading}
      />

      {/* 3. Floating Horizontal Tab Bar (Top for Desktop, Bottom for Mobile) */}
      <div className="hidden md:block absolute top-16 left-1/2 -translate-x-1/2 z-20">
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
        badge={getTabBadge(activeTab)}
        isOpen={isSheetOpen}
        onClose={() => setIsSheetOpen(false)}
        width={440}
      >
        {activeTab === "t1_multicriteria" && (
          <ScreenT1MultiCriteria
            onSelectRoute={handleSelectT1Route}
            onUpdateMapPoints={handleUpdateT1Points}
          />
        )}

        {activeTab === "t2_vrptw" && <ScreenT2VRPTW />}

        {activeTab === "t3_live" && (
          <ScreenT3AdaptiveReroute
            onUpdateSimVehicle={setSimVehicle}
            onUpdateRouteGeometry={handleUpdateT3Geometry}
          />
        )}
      </FloatingSheet>

      {/* 6. Toast Notification Center */}
      <div className="fixed top-16 right-6 z-50 flex flex-col space-y-2 pointer-events-none font-sans">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto p-3 border max-w-sm transition-all duration-200 ${
              t.type === "error"
                ? "bg-red-50 border-red-300 text-red-900"
                : t.type === "success"
                ? "bg-emerald-50 border-emerald-300 text-emerald-900"
                : "bg-white border-neutral-300 text-neutral-900"
            }`}
          >
            <div className="flex items-baseline space-x-2">
              <span className="font-mono text-[10px] font-bold tracking-wider">
                [{t.type.toUpperCase()}]
              </span>
              <p className="text-xs font-semibold">{t.message}</p>
            </div>
            {t.detail && (
              <p className="text-[11px] text-neutral-600 mt-1 font-mono">
                {t.detail}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
