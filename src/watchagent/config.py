from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://watchagent:watchagent@localhost:5432/watchagent"
    poll_interval_seconds: int = 300
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Event detection thresholds
    rapid_temp_delta_c: float = 4.0
    heavy_precipitation_mm: float = 5.0
    high_wind_kmh: float = 50.0
    regional_contrast_delta_c: float = 15.0
    regional_contrast_max_age_hours: float = 2.0
    event_cooldown_minutes: int = 60

    # Per-city heat thresholds (°C)
    heat_threshold_ottawa: float = 32.0
    heat_threshold_toronto: float = 31.0
    heat_threshold_vancouver: float = 28.0

    # Per-city cold thresholds (°C)
    cold_threshold_ottawa: float = -25.0
    cold_threshold_toronto: float = -20.0
    cold_threshold_vancouver: float = -5.0

    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    poller_max_retries: int = 3
    poller_retry_base_seconds: float = 2.0
    enable_poller: bool = True


def get_heat_threshold(city: str, settings: Settings) -> float:
    mapping = {
        "Ottawa": settings.heat_threshold_ottawa,
        "Toronto": settings.heat_threshold_toronto,
        "Vancouver": settings.heat_threshold_vancouver,
    }
    return mapping[city]


def get_cold_threshold(city: str, settings: Settings) -> float:
    mapping = {
        "Ottawa": settings.cold_threshold_ottawa,
        "Toronto": settings.cold_threshold_toronto,
        "Vancouver": settings.cold_threshold_vancouver,
    }
    return mapping[city]
