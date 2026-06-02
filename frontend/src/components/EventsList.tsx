import type { WeatherEvent } from "../types";
import { eventTypeLabel, formatTime } from "../utils/weather";

interface Props {
  events: WeatherEvent[];
}

const EVENT_COLORS: Record<string, string> = {
  rapid_temp_change: "var(--accent-amber)",
  extreme_heat: "var(--accent-red)",
  extreme_cold: "var(--accent-blue)",
  heavy_precipitation: "var(--accent-teal)",
  high_wind: "var(--accent-purple)",
  conditions_shift: "var(--accent-green)",
  regional_contrast: "var(--accent-orange)",
  blizzard_warning: "var(--accent-blue)",
};

export function EventsList({ events }: Props) {
  if (events.length === 0) {
    return (
      <section className="panel">
        <h2>Notable events</h2>
        <p className="empty">
          No events recorded yet. Events appear when detection rules fire on new readings.
        </p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Notable events</h2>
      <ul className="events-list">
        {events.map((ev) => (
          <li key={ev.id} className="event-item">
            <div
              className="event-type-pill"
              style={{
                borderColor: EVENT_COLORS[ev.event_type] ?? "var(--border)",
                color: EVENT_COLORS[ev.event_type] ?? "var(--text-muted)",
              }}
            >
              {eventTypeLabel(ev.event_type)}
            </div>
            <div className="event-body">
              <h3>{ev.title}</h3>
              <p className="event-desc">{ev.description}</p>
              <p className="event-reason">
                <strong>Why:</strong> {ev.reason}
              </p>
              <footer className="event-meta">
                <span>{ev.city ?? "All cities"}</span>
                <span>
                  {formatTime(
                    ev.occurred_at,
                    ev.city ?? undefined,
                    ev.occurred_at_local,
                  )}
                </span>
              </footer>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
