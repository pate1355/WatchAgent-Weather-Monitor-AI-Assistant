import { useCallback, useEffect, useRef, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import { getEvents, getHealth, getReadings } from "./api/client";
import { CityTabs } from "./components/CityTabs";
import { EventsList } from "./components/EventsList";
import { ReadingsGrid } from "./components/ReadingsGrid";
import { StatsBar } from "./components/StatsBar";
import type { City, Health, Reading, WeatherEvent } from "./types";

const REFRESH_MS = 30_000;

export default function App() {
  const [filter, setFilter] = useState<City | "all">("all");
  const [health, setHealth] = useState<Health | null>(null);
  const [readings, setReadings] = useState<Reading[]>([]);
  const [events, setEvents] = useState<WeatherEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const maxEventId = useRef<number>(-1);

  const load = useCallback(async () => {
    try {
      setError(null);
      const cityParam = filter === "all" ? undefined : filter;
      const [h, r, e] = await Promise.all([
        getHealth(),
        getReadings(cityParam, 50),
        getEvents(cityParam, 50),
      ]);
      setHealth(h);
      setReadings(r);

      if (maxEventId.current !== -1) {
        const newEvents = e.filter((ev) => ev.id > maxEventId.current);
        [...newEvents].reverse().forEach((ev) => {
          toast(ev.title, {
            icon: "⚠️",
            style: {
              borderRadius: "8px",
              background: "var(--bg-elevated)",
              color: "var(--text-primary)",
              border: "1px solid var(--border)",
            },
          });
        });
      }
      if (e.length > 0) {
        maxEventId.current = Math.max(maxEventId.current, ...e.map((ev) => ev.id));
      }

      setEvents(e);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    void load();
  }, [load]);

  useEffect(() => {
    const id = window.setInterval(() => void load(), REFRESH_MS);
    return () => window.clearInterval(id);
  }, [load]);

  const exportCsv = useCallback(() => {
    if (readings.length === 0) return;
    const header = "city,time,temperature_c,precipitation_mm,wind_kmh,weather_code\n";
    const rows = readings.map(r => `${r.city},${r.observation_time},${r.temperature_2m},${r.precipitation},${r.wind_speed_10m},${r.weather_code}`).join("\n");
    const blob = new Blob([header + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `watchagent_readings_${filter}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [readings, filter]);

  return (
    <div className="app">
      <Toaster position="top-right" />
      <StatsBar health={health} loading={loading} lastUpdated={lastUpdated} />
      <main className="main">
        <div className="toolbar">
          <CityTabs selected={filter} onSelect={setFilter} />
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="button" className="refresh-btn" onClick={exportCsv} disabled={readings.length === 0}>
              Export CSV
            </button>
            <button type="button" className="refresh-btn" onClick={() => void load()} disabled={loading}>
              {loading ? "Refreshing…" : "Refresh"}
            </button>
          </div>
        </div>
        {error && (
          <div className="error-banner" role="alert">
            {error}
            <span className="error-hint"> Is the API running on port 8000?</span>
          </div>
        )}
        <ReadingsGrid readings={readings} filter={filter} />
        <EventsList events={events} />
      </main>
    </div>
  );
}
