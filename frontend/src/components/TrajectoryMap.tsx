import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useEffect, useState } from 'react';
import type { Prediction } from '../types/trajectory';
import { HORIZON_COLORS, HORIZON_LABELS } from '../types/trajectory';
import { displacementKm, formatCoord } from '../utils/coordinates';

import 'leaflet/dist/leaflet.css';

// Fix Leaflet default marker icon
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

interface TrajectoryMapProps {
  currentLat: number | null;
  currentLon: number | null;
  predictions: Prediction[] | null;
  activeHorizon: number | null;
}

const CURRENT_ICON = new L.DivIcon({
  className: '',
  html: `<div style="width:16px;height:16px;background:#fff;border:3px solid #0ea5e9;border-radius:50%;box-shadow:0 0 8px rgba(14,165,233,0.5)"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

function predictionIcon(color: string) {
  return new L.DivIcon({
    className: '',
    html: `<div style="width:12px;height:12px;background:${color};border:2px solid #fff;border-radius:50%;box-shadow:0 0 6px ${color}80"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
}

function FitBounds({ currentLat, currentLon, predictions }: { currentLat: number | null; currentLon: number | null; predictions: Prediction[] | null }) {
  const map = useMap();
  useEffect(() => {
    const points: [number, number][] = [];
    if (currentLat != null && currentLon != null) points.push([currentLat, currentLon]);
    if (predictions) {
      for (const p of predictions) {
        points.push([p.predicted_latitude, p.predicted_longitude]);
      }
    }
    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });
    }
  }, [map, currentLat, currentLon, predictions]);
  return null;
}

export default function TrajectoryMap({ currentLat, currentLon, predictions, activeHorizon }: TrajectoryMapProps) {
  const [visibleHorizons, setVisibleHorizons] = useState<Set<number>>(new Set([24, 72, 168, 240, 720]));

  const toggleHorizon = (h: number) => {
    setVisibleHorizons(prev => {
      const next = new Set(prev);
      next.has(h) ? next.delete(h) : next.add(h);
      return next;
    });
  };

  const center: [number, number] = currentLat != null && currentLon != null
    ? [currentLat, currentLon]
    : [-72, 0];

  return (
    <div className="relative h-full rounded-xl overflow-hidden border border-slate-700/50">
      <MapContainer center={center} zoom={4} className="h-full w-full" style={{ background: '#0f172a' }}>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        <FitBounds currentLat={currentLat} currentLon={currentLon} predictions={predictions} />

        {/* Current position */}
        {currentLat != null && currentLon != null && (
          <Marker position={[currentLat, currentLon]} icon={CURRENT_ICON}>
            <Popup>
              <div className="text-xs font-mono">
                <strong>Current Iceberg Position</strong><br />
                Lat: {formatCoord(currentLat)}°<br />
                Lon: {formatCoord(currentLon)}°
              </div>
            </Popup>
          </Marker>
        )}

        {/* Prediction lines + markers */}
        {predictions && currentLat != null && currentLon != null && predictions.map(p => {
          const h = p.horizon_hours;
          if (!visibleHorizons.has(h) && activeHorizon !== h) return null;
          const color = HORIZON_COLORS[h] || '#888';
          const isActive = activeHorizon === h;
          return (
            <div key={h}>
              <Polyline
                positions={[[currentLat, currentLon], [p.predicted_latitude, p.predicted_longitude]]}
                pathOptions={{ color, weight: isActive ? 4 : 2, dashArray: isActive ? undefined : '6 4', opacity: isActive ? 1 : 0.7 }}
              />
              <Marker position={[p.predicted_latitude, p.predicted_longitude]} icon={predictionIcon(color)}>
                <Popup>
                  <div className="text-xs font-mono space-y-0.5">
                    <strong>{HORIZON_LABELS[h] || `${h}h`}</strong><br />
                    Lat: {formatCoord(p.predicted_latitude)}°<br />
                    Lon: {formatCoord(p.predicted_longitude)}°<br />
                    Δ: {displacementKm(p.predicted_dx_m, p.predicted_dy_m).toFixed(2)} km<br />
                    Model: {p.selected_model}<br />
                    Quality: {p.prediction_quality}
                    {p.fallback_used && <><br /><span className="text-amber-600 font-bold">⚠ Fallback Active</span></>}
                  </div>
                </Popup>
              </Marker>
            </div>
          );
        })}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-slate-900/90 backdrop-blur border border-slate-700/50 rounded-lg p-3 text-xs space-y-1.5">
        <p className="font-semibold text-slate-300 mb-1">Forecast Horizons</p>
        <div className="flex items-center gap-2 text-white">
          <span className="w-3 h-3 rounded-full bg-white border-2 border-cyan-400" /> Current
        </div>
        {[24, 72, 168, 240, 720].map(h => (
          <button key={h} onClick={() => toggleHorizon(h)}
            className={`flex items-center gap-2 w-full text-left transition-opacity ${visibleHorizons.has(h) ? 'opacity-100' : 'opacity-40'}`}>
            <span className="w-3 h-3 rounded-full" style={{ background: HORIZON_COLORS[h] }} />
            <span className="text-slate-300">{HORIZON_LABELS[h]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
