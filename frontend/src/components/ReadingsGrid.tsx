import type { City, Reading } from "../types";
import { CITIES } from "../types";
import { formatTime } from "../utils/weather";
import { ReadingCard } from "./ReadingCard";
import { TemperatureChart } from "./TemperatureChart";

interface Props {
  readings: Reading[];
  filter: City | "all";
}

export function ReadingsGrid({ readings, filter }: Props) {
  const latestByCity = CITIES.map((city) => {
    const match = readings.find((r) => r.city === city);
    return match ?? null;
  });

  const showAll = filter === "all";
  const cards = showAll
    ? latestByCity.filter((r): r is Reading => r !== null)
    : readings.filter((r) => r.city === filter).slice(0, 1);

  if (cards.length === 0) {
    return (
      <section className="panel">
        <h2>Current conditions</h2>
        <p className="empty">
          No readings yet. The poller runs every few minutes.
        </p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>{showAll ? "Latest by city" : `Latest · ${filter}`}</h2>
      <div className="readings-grid">
        {cards.map((r) => (
          <ReadingCard key={r.id} reading={r} />
        ))}
      </div>
      {!showAll && readings.length > 1 && (
        <div
          style={{ display: "flex", flexDirection: "column", gap: "2.5rem" }}
        >
          <TemperatureChart readings={readings} />
          <details className="history-details">
            <summary>Older readings ({readings.length - 1})</summary>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Temp</th>
                  <th>Precip</th>
                  <th>Wind</th>
                  <th>Code</th>
                </tr>
              </thead>
              <tbody>
                {readings.slice(1).map((r) => (
                  <tr key={r.id}>
                    <td>
                      {formatTime(
                        r.observation_time,
                        r.city,
                        r.observation_time_local,
                      )}
                    </td>
                    <td>{r.temperature_2m.toFixed(1)}°C</td>
                    <td>{r.precipitation.toFixed(1)} mm</td>
                    <td>{r.wind_speed_10m.toFixed(0)} km/h</td>
                    <td>{r.weather_code}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      )}
    </section>
  );
}
