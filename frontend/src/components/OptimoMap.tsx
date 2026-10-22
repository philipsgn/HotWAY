"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { Compass, Crosshair, Home, AlertTriangle, Layers } from "lucide-react";

export const ROUTE_COLORS = [
  "#2563eb", // 1. Xanh dương
  "#d97706", // 2. Vàng hổ phách
  "#059669", // 3. Xanh ngọc lục bảo
  "#7c3aed", // 4. Tím hoa cà
  "#dc2626", // 5. Đỏ gạch
  "#0891b2", // 6. Xanh mòng két
];

export interface Point {
  id: string;
  lat: number;
  lon: number;
  demand?: number;
  name?: string;
  order_id?: string;
}

export interface RouteData {
  vehicle_id: number;
  leg_geometries: number[][][];
  customer_indices: number[];
  distance_km: number;
  duration_min: number;
  stops?: {
    node_idx: number;
    order_id: string;
    arrival_time_sec: number;
    elapsed_time_min: number;
    demand: number;
    estimated_temp_c: number;
    thermal_violation: boolean;
  }[];
}

export type LocationSource = "simulated" | "device-gps";

export interface LiveLocationUpdate {
  source: LocationSource;
  lat: number;
  lon: number;
  heading?: number;
  speed_kmh?: number;
  accuracy_m?: number;
  vehicle_id?: number;
}

interface OptimoMapProps {
  depot: { lat: number; lon: number; name: string };
  orders: Point[];
  routes?: RouteData[];
  selectedVehicleId?: number | null;
  selectedOrderId?: string | null;
  onSelectOrder?: (orderId: string | null) => void;
  simVehicle?: { lat: number; lon: number; vehicle_id: number; heading?: number } | null;
  userLocation?: { lat: number; lon: number; accuracy: number } | null;
  onLocateUser?: () => void;
  isLocating?: boolean;
}

// OpenFreeMap Liberty style (free for commercial use, OSM vector tiles)
const MAP_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";
// Raster fallback if vector styles fail to load
const RASTER_FALLBACK_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    "osm-raster": {
      type: "raster",
      tiles: [
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
  },
  layers: [
    {
      id: "osm-raster-layer",
      type: "raster",
      source: "osm-raster",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

export default function OptimoMap({
  depot,
  orders,
  routes = [],
  selectedVehicleId = null,
  selectedOrderId = null,
  onSelectOrder,
  simVehicle = null,
  userLocation = null,
  onLocateUser,
  isLocating = false,
}: OptimoMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<{ [key: string]: maplibregl.Marker }>({});
  const depotMarkerRef = useRef<maplibregl.Marker | null>(null);
  const simMarkerRef = useRef<maplibregl.Marker | null>(null);
  const userMarkerRef = useRef<maplibregl.Marker | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // 1. Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    try {
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: MAP_STYLE_URL,
        center: [depot.lon, depot.lat],
        zoom: 14.5,
        pitch: 15,
        bearing: 0,
        attributionControl: false,
      });

      // Add standard attribution on bottom-right
      map.addControl(
        new maplibregl.AttributionControl({
          compact: true,
          customAttribution: "Dữ liệu OpenStreetMap © HotWAY",
        }),
        "bottom-right"
      );

      // Handle style load error -> Fallback to standard raster tiles
      map.on("error", (e) => {
        // If vector style failed to load, fall back gracefully
        if (!mapLoaded && e.error && e.error.message?.includes("style")) {
          console.warn("Chuyển sang bản đồ dự phòng OSM Raster...");
          map.setStyle(RASTER_FALLBACK_STYLE);
        }
      });

      map.on("load", () => {
        mapRef.current = map;
        setMapLoaded(true);
      });

      // Cleanup
      return () => {
        map.remove();
        mapRef.current = null;
      };
    } catch (err: any) {
      console.error("Lỗi khởi tạo bản đồ:", err);
      setMapError("Không thể tải bản đồ WebGL.");
    }
  }, [depot.lat, depot.lon]);

  // 2. Render Depot Marker
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    if (!depotMarkerRef.current) {
      const el = document.createElement("div");
      el.className = "group cursor-pointer";
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <div class="absolute w-9 h-9 bg-amber-500/30 rounded-full animate-ping"></div>
          <div class="relative w-8 h-8 bg-[#3B2A1A] border-2 border-[#E0A83A] rounded-xl shadow-lg flex items-center justify-center text-amber-300 font-bold text-xs">
            HG
          </div>
          <div class="absolute -bottom-1 w-2 h-2 bg-[#3B2A1A] rotate-45 border-r border-b border-[#E0A83A]"></div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 20 }).setHTML(`
        <div class="p-1 space-y-1">
          <div class="text-[10px] font-mono uppercase tracking-wider text-amber-700 font-bold">Bếp Trung Tâm</div>
          <div class="text-xs font-bold text-[#3B2A1A]">${depot.name}</div>
          <div class="text-[11px] text-[#8A7355]">490 Điện Biên Phủ, P. 21, Bình Thạnh</div>
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([depot.lon, depot.lat])
        .setPopup(popup)
        .addTo(mapRef.current);

      depotMarkerRef.current = marker;
    }
  }, [mapLoaded, depot]);

  // 3. Render Order Stop Markers with Vehicle Color & Numbering
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    // Clear old markers
    Object.values(markersRef.current).forEach((m) => m.remove());
    markersRef.current = {};

    // Map order_id to route color & sequence index
    const orderRouteMap = new Map<string, { color: string; seq: number; temp?: number; eta?: string }>();
    routes.forEach((r) => {
      const color = ROUTE_COLORS[(r.vehicle_id - 1) % ROUTE_COLORS.length];
      if (r.stops) {
        r.stops.forEach((st, idx) => {
          orderRouteMap.set(st.order_id, {
            color,
            seq: idx + 1,
            temp: st.estimated_temp_c,
            eta: `${Math.round(st.elapsed_time_min)} phút`,
          });
        });
      }
    });

    orders.forEach((ord, index) => {
      const routeInfo = orderRouteMap.get(ord.id);
      const isSelected = selectedOrderId === ord.id;
      const markerColor = routeInfo ? routeInfo.color : "#8B5E34";
      const seqNumber = routeInfo ? routeInfo.seq : index + 1;

      const el = document.createElement("div");
      el.className = "cursor-pointer transition-transform duration-200 hover:scale-125";
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          ${isSelected ? '<div class="absolute w-8 h-8 rounded-full bg-amber-400/40 animate-ping"></div>' : ''}
          <div style="background-color: ${markerColor};" class="w-6 h-6 rounded-full border-2 border-white shadow-md flex items-center justify-center text-white text-[11px] font-bold font-mono">
            ${seqNumber}
          </div>
          <div style="border-top-color: ${markerColor};" class="absolute -bottom-1 border-solid border-t-4 border-x-transparent border-x-4 border-b-0"></div>
        </div>
      `;

      el.addEventListener("click", () => {
        if (onSelectOrder) onSelectOrder(ord.id);
      });

      const popupHTML = `
        <div class="p-1 space-y-1 text-xs">
          <div class="flex items-center justify-between border-b border-[#E6D9BC] pb-1">
            <span class="font-mono font-bold text-[#3B2A1A]">${ord.id}</span>
            <span class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#FBE9B7] text-[#8B5E34] font-semibold">
              ${ord.demand || 1} tô
            </span>
          </div>
          <div class="text-[11px] text-[#3B2A1A] font-medium">${ord.name || "Điểm giao hàng"}</div>
          <div class="text-[10px] text-[#8A7355] font-mono">Tọa độ: ${ord.lat.toFixed(4)}, ${ord.lon.toFixed(4)}</div>
          ${routeInfo && routeInfo.temp ? `
            <div class="flex items-center justify-between text-[11px] pt-1">
              <span class="text-[#8A7355]">Nhiệt độ dự kiến:</span>
              <span class="font-mono font-bold ${routeInfo.temp >= 60 ? 'text-[#4E8F5A]' : 'text-[#C2493D]'}">
                ${routeInfo.temp.toFixed(1)}°C
              </span>
            </div>
          ` : ''}
          ${routeInfo && routeInfo.eta ? `
            <div class="flex items-center justify-between text-[11px]">
              <span class="text-[#8A7355]">Thời gian tới:</span>
              <span class="font-mono text-[#3B2A1A]">${routeInfo.eta}</span>
            </div>
          ` : ''}
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 16 }).setHTML(popupHTML);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([ord.lon, ord.lat])
        .setPopup(popup)
        .addTo(mapRef.current!);

      if (isSelected) {
        marker.togglePopup();
      }

      markersRef.current[ord.id] = marker;
    });
  }, [mapLoaded, orders, routes, selectedOrderId, onSelectOrder]);

  // 4. Render Real Route Polylines from `leg_geometries` (OSMnx directed path)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    const map = mapRef.current;

    // Filter routes if a vehicle is selected
    const activeRoutes = selectedVehicleId === null
      ? routes
      : routes.filter((r) => r.vehicle_id === selectedVehicleId);

    // Remove existing route layers & sources
    for (let i = 1; i <= 10; i++) {
      if (map.getLayer(`route-casing-${i}`)) map.removeLayer(`route-casing-${i}`);
      if (map.getLayer(`route-line-${i}`)) map.removeLayer(`route-line-${i}`);
      if (map.getSource(`route-source-${i}`)) map.removeSource(`route-source-${i}`);
    }

    activeRoutes.forEach((route) => {
      const color = ROUTE_COLORS[(route.vehicle_id - 1) % ROUTE_COLORS.length];
      const sourceId = `route-source-${route.vehicle_id}`;
      const casingLayerId = `route-casing-${route.vehicle_id}`;
      const lineLayerId = `route-line-${route.vehicle_id}`;

      // Flatten leg_geometries into GeoJSON LineString coordinates: [lon, lat]
      const coordinates: [number, number][] = [];
      if (route.leg_geometries && route.leg_geometries.length > 0) {
        route.leg_geometries.forEach((leg) => {
          leg.forEach((pt) => {
            if (pt.length >= 2) {
              coordinates.push([pt[1], pt[0]]); // pt is [lat, lon] -> GeoJSON is [lon, lat]
            }
          });
        });
      }

      if (coordinates.length >= 2) {
        map.addSource(sourceId, {
          type: "geojson",
          data: {
            type: "Feature",
            properties: { vehicle_id: route.vehicle_id },
            geometry: {
              type: "LineString",
              coordinates,
            },
          },
        });

        // 1. Casing line (2px white border for high contrast)
        map.addLayer({
          id: casingLayerId,
          type: "line",
          source: sourceId,
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": "#FFFFFF",
            "line-width": 6,
            "line-opacity": 0.95,
          },
        });

        // 2. Main route line
        map.addLayer({
          id: lineLayerId,
          type: "line",
          source: sourceId,
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": color,
            "line-width": 3.8,
            "line-opacity": 0.92,
          },
        });
      }
    });
  }, [mapLoaded, routes, selectedVehicleId]);

  // 5. Render Real User Location Marker (navigator.geolocation)
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    if (userLocation) {
      if (!userMarkerRef.current) {
        const el = document.createElement("div");
        el.className = "relative flex items-center justify-center";
        el.innerHTML = `
          <div class="absolute w-8 h-8 rounded-full bg-blue-500/30 animate-ping"></div>
          <div class="w-4 h-4 rounded-full bg-blue-600 border-2 border-white shadow-md"></div>
        `;
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([userLocation.lon, userLocation.lat])
          .addTo(mapRef.current);
        userMarkerRef.current = marker;
      } else {
        userMarkerRef.current.setLngLat([userLocation.lon, userLocation.lat]);
      }
    } else if (userMarkerRef.current) {
      userMarkerRef.current.remove();
      userMarkerRef.current = null;
    }
  }, [mapLoaded, userLocation]);

  // 6. Render Live Simulated Vehicle Marker with "MÔ PHỎNG" Badge
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    if (simVehicle) {
      const vColor = ROUTE_COLORS[(simVehicle.vehicle_id - 1) % ROUTE_COLORS.length];
      if (!simMarkerRef.current) {
        const el = document.createElement("div");
        el.className = "flex flex-col items-center cursor-pointer";
        el.innerHTML = `
          <div class="bg-amber-600 text-white text-[9px] font-mono px-1.5 py-0.2 rounded font-bold shadow mb-0.5 tracking-wider">
            MÔ PHỎNG
          </div>
          <div class="relative flex items-center justify-center">
            <div style="background-color: ${vColor};" class="w-7 h-7 rounded-full border-2 border-white shadow-lg flex items-center justify-center text-white text-xs font-bold">
              🚚
            </div>
          </div>
        `;
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([simVehicle.lon, simVehicle.lat])
          .addTo(mapRef.current);
        simMarkerRef.current = marker;
      } else {
        simMarkerRef.current.setLngLat([simVehicle.lon, simVehicle.lat]);
      }
    } else if (simMarkerRef.current) {
      simMarkerRef.current.remove();
      simMarkerRef.current = null;
    }
  }, [mapLoaded, simVehicle]);

  // 7. Pan / Zoom controls
  const handleResetToDepot = () => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center: [depot.lon, depot.lat],
        zoom: 14.5,
        pitch: 15,
        bearing: 0,
        essential: true,
      });
    }
  };

  const handleZoomIn = () => mapRef.current?.zoomIn();
  const handleZoomOut = () => mapRef.current?.zoomOut();

  return (
    <div className="relative w-full h-full overflow-hidden select-none">
      {/* 1. MapLibre Canvas Container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* 2. Map Error Banner if any */}
      {mapError && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-20 bg-surface border border-status-danger/40 text-primary-text px-4 py-2.5 rounded-warm shadow-elevated flex items-center space-x-2 text-xs">
          <AlertTriangle className="w-4 h-4 text-status-danger" />
          <span>{mapError} Vui lòng kiểm tra kết nối mạng.</span>
        </div>
      )}

      {/* 3. Floating Quick Action Controls (Bottom Right) */}
      <div className="absolute bottom-6 right-5 z-10 flex flex-col space-y-2">
        <button
          onClick={handleResetToDepot}
          title="Về bếp Hàng Gòn Quán"
          aria-label="Về bếp trung tâm"
          className="w-10 h-10 rounded-xl bg-surface border border-border-warm shadow-soft flex items-center justify-center text-primary-text hover:bg-sunken hover:border-brand-gold active:scale-95 transition"
        >
          <Home className="w-4 h-4 text-brand-brown" />
        </button>

        {onLocateUser && (
          <button
            onClick={onLocateUser}
            disabled={isLocating}
            title="Vị trí của tôi"
            aria-label="Định vị vị trí của tôi"
            className={`w-10 h-10 rounded-xl bg-surface border border-border-warm shadow-soft flex items-center justify-center text-primary-text hover:bg-sunken hover:border-brand-gold active:scale-95 transition ${
              isLocating ? "animate-spin text-brand-gold" : ""
            }`}
          >
            <Crosshair className="w-4 h-4 text-brand-brown" />
          </button>
        )}

        <div className="flex flex-col rounded-xl bg-surface border border-border-warm shadow-soft overflow-hidden">
          <button
            onClick={handleZoomIn}
            title="Phóng to"
            aria-label="Phóng to bản đồ"
            className="w-10 h-9 flex items-center justify-center text-sm font-bold text-primary-text hover:bg-sunken border-b border-border-warm active:bg-subtle transition"
          >
            +
          </button>
          <button
            onClick={handleZoomOut}
            title="Thu nhỏ"
            aria-label="Thu nhỏ bản đồ"
            className="w-10 h-9 flex items-center justify-center text-sm font-bold text-primary-text hover:bg-sunken active:bg-subtle transition"
          >
            -
          </button>
        </div>
      </div>

      {/* 4. Small Map Legend Overlay (Top Right) */}
      <div className="hidden sm:flex absolute top-20 right-5 z-10 bg-surface/90 backdrop-blur-md border border-border-warm rounded-warm px-3 py-2 text-[11px] shadow-soft items-center space-x-3 text-secondary-text">
        <div className="flex items-center space-x-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#E0A83A] border border-[#3B2A1A]"></span>
          <span className="text-primary-text font-medium">Bếp 490 Điện Biên Phủ</span>
        </div>
        <span>•</span>
        <div className="flex items-center space-x-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-route-1 border border-white"></span>
          <span>{orders.length} điểm giao</span>
        </div>
        {routes.length > 0 && (
          <>
            <span>•</span>
            <span className="font-mono text-primary-text font-semibold">{routes.length} xe</span>
          </>
        )}
      </div>
    </div>
  );
}
