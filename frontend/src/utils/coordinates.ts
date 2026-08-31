export function isValidLatitude(lat: number): boolean {
  return Number.isFinite(lat) && lat >= -90 && lat <= 90;
}

export function isValidLongitude(lon: number): boolean {
  return Number.isFinite(lon) && lon >= -180 && lon <= 180;
}

export function isFiniteCoord(v: number): boolean {
  return Number.isFinite(v) && !Number.isNaN(v);
}

export function displacementKm(dx: number, dy: number): number {
  return Math.sqrt(dx * dx + dy * dy) / 1000;
}

export function formatCoord(v: number, decimals = 4): string {
  return v.toFixed(decimals);
}
