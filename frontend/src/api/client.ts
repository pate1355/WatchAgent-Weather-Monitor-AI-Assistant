import type { Health, Reading, WeatherEvent } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function getHealth(): Promise<Health> {
  return fetchJson<Health>("/health");
}

export function getReadings(city?: string, limit = 50): Promise<Reading[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (city) params.set("city", city);
  return fetchJson<{ readings: Reading[] }>(`/readings?${params}`).then(
    (d) => d.readings,
  );
}

export function getEvents(city?: string, limit = 50): Promise<WeatherEvent[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (city) params.set("city", city);
  return fetchJson<{ events: WeatherEvent[] }>(`/events?${params}`).then(
    (d) => d.events,
  );
}
