import type { City } from "../types";
import { CITIES } from "../types";

interface Props {
  selected: City | "all";
  onSelect: (city: City | "all") => void;
}

export function CityTabs({ selected, onSelect }: Props) {
  return (
    <nav className="city-tabs" aria-label="Filter by city">
      <button
        type="button"
        className={selected === "all" ? "active" : ""}
        onClick={() => onSelect("all")}
      >
        All cities
      </button>
      {CITIES.map((city) => (
        <button
          key={city}
          type="button"
          className={selected === city ? "active" : ""}
          onClick={() => onSelect(city)}
        >
          {city}
        </button>
      ))}
    </nav>
  );
}
