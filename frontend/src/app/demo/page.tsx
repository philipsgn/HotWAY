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

const REGIONAL_DEPOTS = {
  hanoi: {
    lat: 21.0285,
    lon: 105.8542,
    name: "Hub Bưu Chính Hà Nội (Hoàn Kiếm)",
  },
  danang: {
    lat: 16.0544,
    lon: 108.2022,
    name: "Hub Bưu Chính Đà Nẵng (Hải Châu)",
  },
  hcmc: {
    lat: 10.8016,
    lon: 106.7115,
    name: "Hub Bưu Chính TP.HCM (Bình Thạnh / Q1)",
  },
};

const DEFAULT_DEPOT = REGIONAL_DEPOTS.hcmc;

interface ToastNotification {
  id: string;
  type: "error" | "success" | "info";
  message: string;
  detail?: string;
}

export default function OptimoSchedulingPage() {
  const [activeTab, setActiveTab] = useState<OptimoTab>("t1_multicriteria");
  const [currentDepot, setCurrentDepot] = useState(DEFAULT_DEPOT);
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

  // Dynamic Interactive Picking States (Zero-Hardcode Rule)
  const [pinningMode, setPinningMode] = useState<"origin" | "destination" | "stop" | null>(null);
  const [originPoint, setOriginPoint] = useState<{ lat: number; lon: number; name?: string }>({
    lat: 10.8016,
    lon: 106.7115,
    name: "Hub Bình Thạnh (#1497276525)",
  });
  const [destinationPoint, setDestinationPoint] = useState<{ lat: number; lon: number; name?: string }>({
    lat: 10.7951,
    lon: 106.7218,
    name: "Landmark 81 (#5337055581)",
  });
  const [customStops, setCustomStops] = useState<Point[]>([]);
  const [originalBenchmarkInstance, setOriginalBenchmarkInstance] = useState<any>(null);
  const [originalBenchmarkRoutes, setOriginalBenchmarkRoutes] = useState<any[]>([]);

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
    const mapRoutes: RouteData[] = allRoutes.map((r, idx) => {
      const coords = (r as any).coordinates || (r as any).coords || [];
      const validCoords: [number, number][] = Array.isArray(coords) ? coords : [];
      return {
        vehicle_id: idx + 1,
        leg_geometries: validCoords.length > 0 ? [validCoords] : [],
        customer_indices: [],
        distance_km: (r.distance_m || 0) / 1000,
        duration_min: r.expected_time_min || 0,
      };
    });

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

  // Handler for Region Switching & Instance Inspection in T2
  const handleSelectRegion = (regionId: "hanoi" | "danang" | "hcmc") => {
    const targetDepot = REGIONAL_DEPOTS[regionId];
    if (targetDepot) {
      setCurrentDepot(targetDepot);
      addToast(
        "info",
        `Chuyển trọng tâm bản đồ: ${targetDepot.name}`,
        `Tọa độ: ${targetDepot.lat.toFixed(4)}, ${targetDepot.lon.toFixed(4)}`
      );
    }
  };

  const handleSelectT2Instance = (instance: any, modelRoutes: any[] = []) => {
    if (!instance) return;
    setOriginalBenchmarkInstance(instance);
    setOriginalBenchmarkRoutes(modelRoutes);
    if (instance.depot) {
      setCurrentDepot({
        lat: instance.depot.lat,
        lon: instance.depot.lon,
        name: instance.depot.name || `Hub Bưu Chính (${instance.region})`,
      });
    }
    if (instance.stops && Array.isArray(instance.stops)) {
      const pts: Point[] = instance.stops.map((s: any, idx: number) => ({
        id: s.node_id || `STOP_${idx + 1}`,
        lat: s.lat,
        lon: s.lon,
        name: s.name || `Điểm giao #${idx + 1}`,
        order_id: `ORD-${idx + 1}`,
        demand: 1,
      }));
      setOrders(pts);

      const chosenRoute = modelRoutes.find((result) => result.model.includes("Attention Model") && result.valid)
        || modelRoutes.find((result) => result.valid);
      if (!chosenRoute) {
        setRoutes([]);
        addToast("error", "Không có tour solver hợp lệ", "Benchmark không cung cấp route hợp lệ cho instance này.");
        return;
      }
      const allNodes = [instance.depot, ...instance.stops];
      const routeNodeIndices: number[] = chosenRoute.route;
      const routeCoords: [number, number][] = routeNodeIndices.map((nodeIdx) => [allNodes[nodeIdx].lat, allNodes[nodeIdx].lon]);

      setRoutes([
        {
          vehicle_id: 1,
          leg_geometries: [routeCoords],
          customer_indices: routeNodeIndices.slice(1, -1),
          distance_km: chosenRoute.total_dist_km,
          duration_min: chosenRoute.total_duration_min,
        },
      ]);

      addToast(
        "success",
        `Nạp hành trình: ${instance.instance_id}`,
        `${instance.region} • ${instance.num_stops} điểm dừng • Giờ xuất phát: ${instance.departure_hour || 8}h00`
      );
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

  // Interactive Map Click Handler for Dynamic Address Selection
  const handleMapClick = (coords: { lat: number; lon: number }) => {
    if (!pinningMode) return;

    if (pinningMode === "origin") {
      const pt = {
        lat: coords.lat,
        lon: coords.lon,
        name: `Mốc A [${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}]`,
      };
      setOriginPoint(pt);
      setPinningMode(null);
      setOrders((prev) => {
        const rest = prev.filter((p) => p.id !== "ORIGIN");
        return [{ id: "ORIGIN", lat: pt.lat, lon: pt.lon, name: pt.name }, ...rest];
      });
      addToast("success", "Đã chọn Điểm Xuất Phát (A)", `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`);
    } else if (pinningMode === "destination") {
      const pt = {
        lat: coords.lat,
        lon: coords.lon,
        name: `Mốc B [${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}]`,
      };
      setDestinationPoint(pt);
      setPinningMode(null);
      setOrders((prev) => {
        const rest = prev.filter((p) => p.id !== "DEST");
        return [...rest, { id: "DEST", lat: pt.lat, lon: pt.lon, name: pt.name }];
      });
      addToast("success", "Đã chọn Điểm Đến (B)", `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`);
    } else if (pinningMode === "stop") {
      const newStop: Point = {
        id: `STOP_CUSTOM_${Date.now()}`,
        lat: coords.lat,
        lon: coords.lon,
        name: `Điểm giao tự chọn (${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)})`,
        order_id: `ORD-CUST-${customStops.length + 1}`,
        demand: 1,
      };
      setCustomStops((prev) => [...prev, newStop]);
      setOrders((prev) => [...prev, newStop]);
      setPinningMode(null);
      addToast("success", "Đã cắm điểm giao mới vào tour", `Tọa độ: ${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`);
    }
  };

  const handleSwapPoints = () => {
    const oldA = originPoint;
    const oldB = destinationPoint;
    setOriginPoint(oldB);
    setDestinationPoint(oldA);
    setOrders([
      { id: "ORIGIN", lat: oldB.lat, lon: oldB.lon, name: oldB.name },
      { id: "DEST", lat: oldA.lat, lon: oldA.lon, name: oldA.name },
    ]);
    addToast("info", "Đã đảo chiều hành trình", "Điểm đi và điểm đến đã hoán đổi (A ⇄ B).");
  };

  const handleUseGPSAsOrigin = () => {
    if (userLocation) {
      const pt = {
        lat: userLocation.lat,
        lon: userLocation.lon,
        name: `GPS thiết bị (~${Math.round(userLocation.accuracy)}m)`,
      };
      setOriginPoint(pt);
      setOrders((prev) => {
        const rest = prev.filter((p) => p.id !== "ORIGIN");
        return [{ id: "ORIGIN", lat: pt.lat, lon: pt.lon, name: pt.name }, ...rest];
      });
      addToast("success", "Đã đặt GPS làm Điểm Đi (A)", `${pt.lat.toFixed(4)}, ${pt.lon.toFixed(4)}`);
    } else {
      handleLocateUser();
    }
  };

  // Address Suggestion Pick Handler
  const handleSelectAddressPoint = (pt: { lat: number; lon: number; name: string }) => {
    if (activeTab === "t1_multicriteria") {
      setDestinationPoint(pt);
      setOrders((prev) => {
        const rest = prev.filter((p) => p.id !== "DEST");
        return [...rest, { id: "DEST", lat: pt.lat, lon: pt.lon, name: pt.name }];
      });
      addToast("success", "Đã cập nhật Điểm Đến (B)", pt.name);
    } else {
      const newStop: Point = {
        id: `STOP_SEARCH_${Date.now()}`,
        lat: pt.lat,
        lon: pt.lon,
        name: pt.name,
        order_id: `ORD-SRCH-${customStops.length + 1}`,
        demand: 1,
      };
      setCustomStops((prev) => [...prev, newStop]);
      setOrders((prev) => [...prev, newStop]);
      addToast("success", "Đã thêm điểm giao vào hành trình", pt.name);
    }
  };

  const handleStartPinningStop = () => {
    setPinningMode("stop");
    addToast("info", "Chế độ cắm điểm dừng", "Nhấp chuột vào bất kỳ vị trí nào trên bản đồ để thêm điểm giao.");
  };

  const handleClearCustomStops = () => {
    setOrders((prev) => prev.filter((p) => !p.id.startsWith("STOP_CUSTOM_") && !p.id.startsWith("STOP_SEARCH_")));
    setCustomStops([]);
    addToast("info", "Đã xóa các điểm tự chọn", "Khôi phục danh sách điểm gốc.");
  };

  const handleResetBenchmark = () => {
    if (originalBenchmarkInstance) {
      handleSelectT2Instance(originalBenchmarkInstance, originalBenchmarkRoutes);
      setCustomStops([]);
    }
  };

  // Tab Title Mappings
  const getTabTitle = (tab: OptimoTab) => {
    switch (tab) {
      case "t1_multicriteria":
        return "T1: Tuyến Pareto Đa Tiêu Chí (A → B)";
      case "t2_vrptw":
        return "T2: Lập Tuyến NCO & VRPTW (100 POI Toàn Quốc)";
      case "t3_live":
        return "T3: Đổi Tuyến Thích Nghi (Live SSE)";
    }
  };

  const getTabBadge = (tab: OptimoTab) => {
    switch (tab) {
      case "t1_multicriteria":
        return "PARETO";
      case "t2_vrptw":
        return "NCO / VRPTW";
      case "t3_live":
        return "ADAPTIVE REROUTE";
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-white font-sans text-neutral-900 select-none">
      {/* 1. Full-screen Real MapLibre Background Canvas */}
      <OptimoMap
        depot={currentDepot}
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
        onMapClick={handleMapClick}
        isPinningMode={pinningMode}
        pinningPrompt={
          pinningMode === "origin"
            ? "ĐANG CHỌN ĐIỂM ĐI (A) — Nhấp vào vị trí bất kỳ trên bản đồ"
            : pinningMode === "destination"
            ? "ĐANG CHỌN ĐIỂM ĐẾN (B) — Nhấp vào vị trí bất kỳ trên bản đồ"
            : pinningMode === "stop"
            ? "ĐANG THÊM ĐIỂM DỪNG GIAO HÀNG — Nhấp vào vị trí bất kỳ trên bản đồ"
            : undefined
        }
        onCancelPinning={() => setPinningMode(null)}
      />

      {/* 2. Floating Top Header Bar */}
      <TopFloatingBar
        onToggleDrawer={() => setIsDrawerOpen(true)}
        onLocateUser={handleLocateUser}
        isLocating={isLocating}
        onQuickPlan={() => addToast("info", "Tính toán Pareto", "Đang phân tích 4 tuyến Pareto đặc trưng.")}
        onSelectAddressPoint={handleSelectAddressPoint}
        onStartPinning={(mode) => setPinningMode(mode)}
        pinningMode={pinningMode}
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
            originPoint={originPoint}
            destinationPoint={destinationPoint}
            onStartPinning={(mode) => setPinningMode(mode)}
            onSwapPoints={handleSwapPoints}
            onUseCurrentLocationAsOrigin={handleUseGPSAsOrigin}
          />
        )}

        {activeTab === "t2_vrptw" && (
          <ScreenT2VRPTW
            onSelectRouteInstance={handleSelectT2Instance}
            onSelectRegion={handleSelectRegion}
            onStartPinningStop={handleStartPinningStop}
            customStopsCount={customStops.length}
            onClearCustomStops={handleClearCustomStops}
            onResetBenchmark={handleResetBenchmark}
          />
        )}

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
            className={`pointer-events-auto p-3 border max-w-sm transition-[opacity,transform] duration-200 ${
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
