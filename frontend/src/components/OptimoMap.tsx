"use client";

import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export const ROUTE_COLORS = [
  "#1d4ed8", // 1. Xanh dương
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
    estimated_temp_c?: number;
    thermal_violation?: boolean;
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
          customAttribution: "Dữ liệu OpenStreetMap (ODbL) | HotWAY",
        }),
        "bottom-right"
      );

      // Handle style load error -> Fallback to standard raster tiles
      map.on("error", (e) => {
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
      el.className = "cursor-pointer";
      el.innerHTML = `
        <div class="flex flex-col items-center">
          <div class="px-1.5 py-0.5 bg-neutral-900 text-white text-[9px] font-mono font-bold tracking-widest uppercase border border-white">
            DEPOT
          </div>
          <div class="w-3 h-3 bg-neutral-900 border-2 border-white -mt-1 rotate-45"></div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 15 }).setHTML(`
        <div class="p-2 space-y-1 font-sans text-xs">
          <div class="text-[10px] font-mono uppercase tracking-wider text-neutral-500 font-bold">BƯU CỤC TẬP KẾT HÀNG</div>
          <div class="font-bold text-neutral-900">${depot.name}</div>
          <div class="text-[11px] text-neutral-600 font-mono">Tọa độ: ${depot.lat.toFixed(4)}, ${depot.lon.toFixed(4)}</div>
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
    const orderRouteMap = new Map<string, { color: string; seq: number; eta?: string }>();
    routes.forEach((r) => {
      const color = ROUTE_COLORS[(r.vehicle_id - 1) % ROUTE_COLORS.length];
      if (r.stops) {
        r.stops.forEach((st, idx) => {
          orderRouteMap.set(st.order_id, {
            color,
            seq: idx + 1,
            eta: `${Math.round(st.elapsed_time_min)} phút`,
          });
        });
      }
    });

    orders.forEach((ord, index) => {
      const routeInfo = orderRouteMap.get(ord.id);
      const isSelected = selectedOrderId === ord.id;
      const markerColor = routeInfo ? routeInfo.color : "#171717";
      const seqNumber = routeInfo ? routeInfo.seq : index + 1;

      const el = document.createElement("div");
      el.className = "cursor-pointer transition-transform duration-150 hover:scale-110";
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          ${isSelected ? '<div class="absolute w-7 h-7 bg-neutral-900/20 animate-ping"></div>' : ''}
          <div style="background-color: ${markerColor};" class="w-5 h-5 border border-white flex items-center justify-center text-white text-[10px] font-mono font-bold">
            ${seqNumber}
          </div>
        </div>
      `;

      el.addEventListener("click", () => {
        if (onSelectOrder) onSelectOrder(ord.id);
      });

      const popupHTML = `
        <div class="p-2 space-y-1 font-sans text-xs">
          <div class="flex items-center justify-between border-b border-neutral-200 pb-1 font-mono">
            <span class="font-bold text-neutral-900">${ord.id}</span>
            <span class="text-[10px] text-neutral-600">
              ${ord.demand || 1} kiện
            </span>
          </div>
          <div class="text-[11px] text-neutral-800 font-medium">${ord.name || "Điểm giao hàng"}</div>
          <div class="text-[10px] text-neutral-500 font-mono">Tọa độ: ${ord.lat.toFixed(4)}, ${ord.lon.toFixed(4)}</div>
          ${routeInfo && routeInfo.eta ? `
            <div class="flex items-center justify-between text-[11px] pt-1 border-t border-neutral-100 font-mono">
              <span class="text-neutral-500">Dự kiến đến:</span>
              <span class="font-bold text-neutral-900">${routeInfo.eta}</span>
            </div>
          ` : ''}
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 12 }).setHTML(popupHTML);

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

        // 1. Casing line (white border for high contrast)
        map.addLayer({
          id: casingLayerId,
          type: "line",
          source: sourceId,
          layout: {
            "line-join": "miter",
            "line-cap": "butt",
          },
          paint: {
            "line-color": "#FFFFFF",
            "line-width": 5,
            "line-opacity": 0.95,
          },
        });

        // 2. Main route line
        map.addLayer({
          id: lineLayerId,
          type: "line",
          source: sourceId,
          layout: {
            "line-join": "miter",
            "line-cap": "butt",
          },
          paint: {
            "line-color": color,
            "line-width": 3,
            "line-opacity": 0.95,
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
        el.className = "flex items-center justify-center";
        el.innerHTML = `
          <div class="w-3 h-3 bg-neutral-900 border-2 border-white"></div>
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
        el.className = "flex flex-col items-center cursor-pointer font-mono";
        el.innerHTML = `
          <div class="bg-neutral-900 text-white text-[9px] px-1 py-0.5 border border-white tracking-wider">
            XE ${simVehicle.vehicle_id} [MÔ PHỎNG]
          </div>
          <div style="background-color: ${vColor};" class="w-3 h-3 border border-white mt-0.5"></div>
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
    <div className="relative w-full h-full overflow-hidden select-none font-sans">
      {/* 1. MapLibre Canvas Container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* 2. Map Error Banner if any */}
      {mapError && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-20 bg-white border border-red-300 text-red-900 px-4 py-2 font-mono text-xs">
          <span>[LỖI]: {mapError} Vui lòng kiểm tra kết nối mạng.</span>
        </div>
      )}

      {/* 3. Floating Quick Action Controls (Bottom Right) */}
      <div className="absolute bottom-6 right-5 z-10 flex flex-col space-y-1 font-mono text-xs">
        <button
          onClick={handleResetToDepot}
          title="Về bưu cục trung tâm"
          aria-label="Về bưu cục trung tâm"
          className="h-8 px-2.5 bg-white border border-neutral-300 text-neutral-800 hover:bg-neutral-100 active:bg-neutral-200 transition"
        >
          [Kho]
        </button>

        {onLocateUser && (
          <button
            onClick={onLocateUser}
            disabled={isLocating}
            title="Vị trí thiết bị GPS"
            aria-label="Định vị vị trí của tôi"
            className="h-8 px-2.5 bg-white border border-neutral-300 text-neutral-800 hover:bg-neutral-100 active:bg-neutral-200 transition"
          >
            {isLocating ? "[...]" : "[GPS]"}
          </button>
        )}

        <div className="flex border border-neutral-300 bg-white">
          <button
            onClick={handleZoomIn}
            title="Phóng to"
            aria-label="Phóng to bản đồ"
            className="w-7 h-8 flex items-center justify-center font-bold text-neutral-800 hover:bg-neutral-100 border-r border-neutral-300 transition"
          >
            +
          </button>
          <button
            onClick={handleZoomOut}
            title="Thu nhỏ"
            aria-label="Thu nhỏ bản đồ"
            className="w-7 h-8 flex items-center justify-center font-bold text-neutral-800 hover:bg-neutral-100 transition"
          >
            -
          </button>
        </div>
      </div>

      {/* 4. Small Map Legend Overlay (Top Right) */}
      <div className="hidden sm:flex absolute top-20 right-5 z-10 bg-white/95 backdrop-blur-sm border border-neutral-300 px-3 py-1.5 text-[11px] font-mono items-center space-x-3 text-neutral-600">
        <div className="flex items-center space-x-1.5">
          <span className="inline-block w-2 h-2 bg-neutral-900"></span>
          <span className="text-neutral-900 font-semibold uppercase">DEPOT</span>
        </div>
        <span>|</span>
        <div>
          <span>{orders.length} ĐIỂM GIAO</span>
        </div>
        {routes.length > 0 && (
          <>
            <span>|</span>
            <span className="text-neutral-900 font-bold">{routes.length} TUYẾN XE</span>
          </>
        )}
      </div>
    </div>
  );
}
