import type { Health } from "../types";

interface Props {
  health: Health | null;
  loading: boolean;
  lastUpdated: Date | null;
}

export function StatsBar({ health, loading, lastUpdated }: Props) {
  return (
    <header className="stats-bar">
      <div className="brand">
        <span className="brand-icon" aria-hidden>
          ◉
        </span>
        <div>
          <h1>WatchAgent</h1>
          <p className="subtitle">
            Canadian weather monitor · Ottawa · Toronto · Vancouver ·{" "}
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={{color: "var(--text-primary)", textDecoration: "underline"}}>
              API Docs
            </a>
          </p>
        </div>
      </div>
      <div className="stats-row">
        <div className="stat">
          <span className="stat-label">Status</span>
          <span className={`stat-value ${health?.status === "ok" ? "ok" : ""}`}>
            {loading && !health ? "…" : (health?.status ?? "—")}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Readings</span>
          <span className="stat-value mono">{health?.readings_stored ?? "—"}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Events</span>
          <span className="stat-value mono">{health?.events_stored ?? "—"}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Updated</span>
          <span className="stat-value small">
            {lastUpdated ? lastUpdated.toLocaleTimeString() : "—"}
          </span>
        </div>
      </div>
    </header>
  );
}
