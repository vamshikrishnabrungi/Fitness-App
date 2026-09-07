export const ACTIVITY_METRICS_VERSION = 'activity-metrics-v1';
export const GPS_SAMPLE_INTERVAL_MS = 1_000;
export const MAX_GPS_ACCURACY_M = 100;
export const MAX_RUNNING_SPEED_MPS = 15;

export interface MetricPoint {
  latitude: number;
  longitude: number;
  timestamp: string;
  accuracy?: number;
  smoothed_latitude?: number;
  smoothed_longitude?: number;
}

export const haversineM = (a: Pick<MetricPoint, 'latitude' | 'longitude'>, b: Pick<MetricPoint, 'latitude' | 'longitude'>) => {
  const radiusM = 6_371_008.8;
  const toRadians = Math.PI / 180;
  const lat1 = a.latitude * toRadians;
  const lat2 = b.latitude * toRadians;
  const dLat = lat2 - lat1;
  const dLon = (b.longitude - a.longitude) * toRadians;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * radiusM * Math.asin(Math.sqrt(h));
};

const metricCoordinate = (point: MetricPoint) => ({
  latitude: point.smoothed_latitude ?? point.latitude,
  longitude: point.smoothed_longitude ?? point.longitude,
});

export const acceptAndSmoothPoint = <T extends MetricPoint>(previous: T | undefined, point: T): T | null => {
  if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) return null;
  if (point.latitude < -90 || point.latitude > 90 || point.longitude < -180 || point.longitude > 180) return null;
  if (point.accuracy != null && point.accuracy > MAX_GPS_ACCURACY_M) return null;
  const timestampMs = new Date(point.timestamp).getTime();
  if (!Number.isFinite(timestampMs)) return null;

  if (!previous) {
    return { ...point, smoothed_latitude: point.latitude, smoothed_longitude: point.longitude };
  }
  const previousMs = new Date(previous.timestamp).getTime();
  const deltaSeconds = (timestampMs - previousMs) / 1_000;
  if (deltaSeconds <= 0) return null;
  if (haversineM(previous, point) / deltaSeconds > MAX_RUNNING_SPEED_MPS) return null;

  const accuracy = Math.max(1, Math.min(MAX_GPS_ACCURACY_M, point.accuracy ?? 50));
  const alpha = Math.max(0.35, Math.min(0.85, 1 - accuracy / 140));
  const previousMetric = metricCoordinate(previous);
  return {
    ...point,
    smoothed_latitude: previousMetric.latitude + alpha * (point.latitude - previousMetric.latitude),
    smoothed_longitude: previousMetric.longitude + alpha * (point.longitude - previousMetric.longitude),
  };
};

export const calculateTrackMetrics = <T extends MetricPoint>(points: T[]) => {
  const accepted: T[] = [];
  let distanceM = 0;
  for (const rawPoint of points) {
    const point = acceptAndSmoothPoint(accepted[accepted.length - 1], rawPoint);
    if (!point) continue;
    const previous = accepted[accepted.length - 1];
    if (previous) distanceM += haversineM(metricCoordinate(previous), metricCoordinate(point));
    accepted.push(point);
  }
  return { accepted, distanceM, version: ACTIVITY_METRICS_VERSION };
};
