import { useCallback, useEffect, useState } from "react";
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

  return (
    <div className="app">
      <StatsBar health={health} loading={loading} lastUpdated={lastUpdated} />
      <main className="main">
        <div className="toolbar">
          <CityTabs selected={filter} onSelect={setFilter} />
          <button type="button" className="refresh-btn" onClick={() => void load()} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh"}
          </button>
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
