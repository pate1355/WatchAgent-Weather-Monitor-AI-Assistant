export type City = "Ottawa" | "Toronto" | "Vancouver";

export const CITIES: City[] = ["Ottawa", "Toronto", "Vancouver"];

/** IANA zones returned by Open-Meteo with timezone=auto */
export const CITY_TIMEZONES: Record<City, string> = {
  Ottawa: "America/Toronto",
  Toronto: "America/Toronto",
  Vancouver: "America/Vancouver",
};

export interface Health {
  status: string;
  readings_stored: number;
  events_stored: number;
}

export interface Reading {
  id: number;
  city: string;
  observation_time: string;
  /** Open-Meteo local clock for the city (e.g. 2026-06-01T18:30) — use for display */
  observation_time_local: string;
  temperature_2m: number;
  apparent_temperature: number;
  precipitation: number;
  wind_speed_10m: number;
  weather_code: number;
  created_at: string;
}

export interface WeatherEvent {
  id: number;
  city: string | null;
  occurred_at: string;
  occurred_at_local?: string | null;
  event_type: string;
  title: string;
  description: string;
  reason: string;
  metadata: Record<string, unknown>;
  reading_id: number | null;
  created_at: string;
}
