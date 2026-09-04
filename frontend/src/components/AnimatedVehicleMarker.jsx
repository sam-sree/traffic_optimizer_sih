import React, { useEffect, useState, useRef } from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Helper to calculate bearing (angle in degrees) between two lat/lng coordinates
function calculateBearing(lat1, lng1, lat2, lng2) {
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const lat1Rad = (lat1 * Math.PI) / 180;
  const lat2Rad = (lat2 * Math.PI) / 180;

  const y = Math.sin(dLng) * Math.cos(lat2Rad);
  const x =
    Math.cos(lat1Rad) * Math.sin(lat2Rad) -
    Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);

  const bearing = (Math.atan2(y, x) * 180) / Math.PI;
  return (bearing + 360) % 360;
}

// Create custom HTML/SVG div icon for the vehicle
function createTruckIcon(color, vehicleId, bearing) {
  const svgMarkup = `
    <div class="animated-truck-wrapper" style="transform: rotate(${bearing}deg);">
      <div class="truck-pulse-ring" style="background-color: ${color}33;"></div>
      <div class="truck-badge" style="background-color: ${color};">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/>
          <path d="M15 18H9"/>
          <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/>
          <circle cx="17" cy="18" r="2"/>
          <circle cx="7" cy="18" r="2"/>
        </svg>
      </div>
      <span class="truck-num-label" style="border-color: ${color}; color: ${color};">V${vehicleId}</span>
    </div>
  `;

  return L.divIcon({
    className: 'custom-truck-icon-container',
    html: svgMarkup,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18]
  });
}

export default function AnimatedVehicleMarker({
  pathCoords = [],
  color = '#3020ad',
  vehicleId = 1,
  isPlaying = true,
  speedMultiplier = 1
}) {
  const [currentPos, setCurrentPos] = useState(null);
  const [bearing, setBearing] = useState(0);
  const animRef = useRef(null);
  const stateRef = useRef({ segmentIndex: 0, progress: 0 });

  useEffect(() => {
    if (!pathCoords || pathCoords.length < 2) {
      setCurrentPos(pathCoords?.[0] || null);
      return;
    }

    // Reset position to start when pathCoords changes
    stateRef.current = { segmentIndex: 0, progress: 0 };
    const p1 = pathCoords[0];
    const p2 = pathCoords[1];
    setCurrentPos(p1);
    setBearing(calculateBearing(p1[0], p1[1], p2[0], p2[1]));

    let lastTime = performance.now();

    const animate = (time) => {
      const delta = (time - lastTime) / 1000;
      lastTime = time;

      if (isPlaying) {
        // Speed of movement along segment
        const speed = 0.4 * speedMultiplier;
        stateRef.current.progress += delta * speed;

        if (stateRef.current.progress >= 1) {
          stateRef.current.progress = 0;
          stateRef.current.segmentIndex =
            (stateRef.current.segmentIndex + 1) % (pathCoords.length - 1);
        }

        const idx = stateRef.current.segmentIndex;
        const pt1 = pathCoords[idx];
        const pt2 = pathCoords[idx + 1];

        if (pt1 && pt2) {
          const lat = pt1[0] + (pt2[0] - pt1[0]) * stateRef.current.progress;
          const lng = pt1[1] + (pt2[1] - pt1[1]) * stateRef.current.progress;
          setCurrentPos([lat, lng]);

          const newBearing = calculateBearing(pt1[0], pt1[1], pt2[0], pt2[1]);
          setBearing(newBearing);
        }
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [pathCoords, isPlaying, speedMultiplier]);

  if (!currentPos) return null;

  const truckIcon = createTruckIcon(color, vehicleId, bearing);

  return (
    <Marker position={currentPos} icon={truckIcon}>
      <Popup>
        <div className="truck-popup-card">
          <strong style={{ color }}>Vehicle #{vehicleId} (Live Dispatch)</strong>
          <p className="text-xs text-slate-500 mt-1">
            Traversing active polyline sub-tour.
          </p>
        </div>
      </Popup>
    </Marker>
  );
}
