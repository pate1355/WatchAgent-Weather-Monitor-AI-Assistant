import type { Reading } from "../types";
import { formatTemp, formatTime, formatTimeLabel, weatherIcon, weatherLabel } from "../utils/weather";

interface Props {
  reading: Reading;
}

export function ReadingCard({ reading }: Props) {
  return (
    <article className="reading-card">
      <div className="reading-card-header">
        <h3>{reading.city}</h3>
        <span className="weather-badge" title={`WMO ${reading.weather_code}`}>
          <span aria-hidden>{weatherIcon(reading.weather_code)}</span>
          {weatherLabel(reading.weather_code)}
        </span>
      </div>
      <p className="temp-main">{formatTemp(reading.temperature_2m)}</p>
      <p className="temp-feels">Feels like {formatTemp(reading.apparent_temperature)}</p>
      <dl className="reading-metrics">
        <div>
          <dt>Precipitation</dt>
          <dd>{reading.precipitation.toFixed(1)} mm</dd>
        </div>
        <div>
          <dt>Wind</dt>
          <dd>{reading.wind_speed_10m.toFixed(0)} km/h</dd>
        </div>
        <div>
          <dt>{formatTimeLabel(reading.city)}</dt>
          <dd>
            {formatTime(
              reading.observation_time,
              reading.city,
              reading.observation_time_local,
            )}
          </dd>
        </div>
      </dl>
    </article>
  );
}
