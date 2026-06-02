import { CITY_TIMEZONES } from "../types";

export function weatherLabel(code: number): string {
  if (code === 0) return "Clear";
  if (code <= 3) return "Partly cloudy";
  if (code <= 48) return "Fog";
  if (code <= 67 || (code >= 80 && code <= 82)) return "Rain";
  if (code <= 77 || (code >= 85 && code <= 86)) return "Snow";
  if (code >= 95) return "Thunderstorm";
  return "Other";
}

export function weatherIcon(code: number): string {
  if (code === 0) return "☀️";
  if (code <= 3) return "⛅";
  if (code <= 48) return "🌫️";
  if (code <= 67 || (code >= 80 && code <= 82)) return "🌧️";
  if (code <= 77 || (code >= 85 && code <= 86)) return "❄️";
  if (code >= 95) return "⛈️";
  return "🌡️";
}

export function eventTypeLabel(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const LOCAL_ISO = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/;

/** Format Open-Meteo local time without JS timezone conversion (matches API clock). */
export function formatLocalObservationTime(localIso: string): string {
  const match = LOCAL_ISO.exec(localIso);
  if (!match) return localIso;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const hour = Number(match[4]);
  const minute = match[5];
  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  const h12 = hour % 12 || 12;
  const ampm = hour >= 12 ? "PM" : "AM";
  return `${months[month - 1]} ${day}, ${year} at ${h12}:${minute} ${ampm}`;
}

/** Prefer observation_time_local; fall back to UTC ISO + city zone. */
export function formatTime(
  utcIso: string,
  city?: string,
  localIso?: string | null,
): string {
  if (localIso) return formatLocalObservationTime(localIso);
  const timeZone =
    city && city in CITY_TIMEZONES
      ? CITY_TIMEZONES[city as keyof typeof CITY_TIMEZONES]
      : undefined;
  return new Date(utcIso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  });
}

export function formatTimeLabel(city: string): string {
  const tz = CITY_TIMEZONES[city as keyof typeof CITY_TIMEZONES];
  if (!tz) return "Observed";
  const abbr = new Date().toLocaleString("en-US", { timeZone: tz, timeZoneName: "short" })
    .split(" ")
    .pop();
  return `Observed (${city} · ${abbr ?? tz})`;
}

export function formatTemp(c: number): string {
  return `${c.toFixed(1)}°C`;
}
