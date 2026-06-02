# WatchAgent

Weather monitor for three Canadian cities (Ottawa, Toronto, Vancouver). Polls [Open-Meteo](https://open-meteo.com/), deduplicates hourly readings, detects notable weather events, and exposes data via HTTP.

## Architecture

```
Open-Meteo API
      │
      ▼
┌─────────────┐     new readings      ┌──────────────┐
│   Poller    │ ────────────────────► │  PostgreSQL  │
│  (async)    │                       │  readings +  │
└─────────────┘                       │    events    │
      │                               └──────┬───────┘
      │ event detector                       │
      └──────────────────────────────────────┤
                                             ▼
                                      ┌─────────────┐
                                      │   FastAPI   │
                                      │  :8000      │
                                      └─────────────┘
```

## Quick start

```bash
git clone <your-repo>
cd Nokia_Technical_Challenge
cp .env.example .env
docker compose up --build
```

**Dashboard (React UI):** http://localhost:3000  

**API:** http://localhost:8000

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/readings?city=Ottawa&limit=10"
curl "http://localhost:8000/events?city=Ottawa&limit=10"
```

Data persists in the `pgdata` Docker volume across restarts.

## API reference

### `GET /health`

```json
{"status": "ok", "readings_stored": 12, "events_stored": 3}
```

### `GET /readings?city=Ottawa&limit=50`

Returns stored readings, newest first. `city` is optional; `limit` defaults to 50.

### `GET /events?city=Ottawa&limit=50`

Returns notable events, newest first. Cross-city events have `"city": null`.

## Event detection design

Raw readings are stored for history; **notable events** surface what matters to a human monitor.

| Event type | Trigger | Why |
| --- | --- | --- |
| `rapid_temp_change` | \|ΔT\| ≥ 4°C vs previous stored reading | Context matters: a jump between consecutive observations is unusual |
| `extreme_heat` / `extreme_cold` | Per-city absolute thresholds | 32°C in Ottawa ≠ 28°C in Vancouver; coastal vs continental climates |
| `heavy_precipitation` | ≥ 5 mm in preceding hour | Precipitation is a distinct signal from temperature |
| `high_wind` | ≥ 50 km/h | Wind alerts decoupled from temp rules |
| `conditions_shift` | WMO category change (clear/rain/snow/…) | State transitions are more meaningful than raw code integers |
| `regional_contrast` | \|Ottawa − Vancouver\| ≥ 15°C, both readings &lt; 2h old | Cross-city comparison for national-scale monitoring |

**Noise control:** 60-minute cooldown per `(city, event_type)` is measured on **observation time** (not wall clock), so back-to-back readings in the same timeline do not re-alert. The poller may see the same hourly API timestamp on multiple polls; deduplication prevents duplicate rows. `rapid_temp_change` and `conditions_shift` require a prior reading for that city.

Thresholds are configurable via environment variables (see `.env.example`).

## Technology choices

- **FastAPI** — typed routes, automatic OpenAPI, async-friendly lifespan for the poller
- **PostgreSQL** — durable storage with a named Docker volume; supports the analysis skill’s SQL aggregations
- **SQLAlchemy 2** — ORM + repository pattern for testable data access
- **httpx** — async HTTP client; easy to mock in tests
- **Single container** — API and poller share one process (simpler ops for this scope)

## Tests

```bash
pip install -e ".[dev]"
ENABLE_POLLER=false DATABASE_URL=sqlite:///:memory: pytest -v
```

Covers deduplication, event detection logic, and API response shape. Open-Meteo is never called in tests.

## Cursor setup

### Rules

- **`poller-and-api.mdc`** — Failed fetches log `city`, HTTP status, retry count at WARNING; retry with backoff; never crash the loop; no partial inserts. API must match the required contracts.
- **`events-and-storage.mdc`** — Events require `event_type`, `city`, `occurred_at`, `reason`, `metadata`; use `Repository`; respect cooldowns.

### Agent

- **`event-detection-reviewer`** — Reviews `detector.py` and `test_events.py` for cooldown gaps, per-city thresholds, README alignment, and missing edge-case tests.

### Skill

- **`analyze_weather_data.py`** — Executable data analysis against Postgres:

```bash
export DATABASE_URL=postgresql+psycopg://watchagent:watchagent@localhost:5432/watchagent
python .cursor/skills/analyze_weather_data.py summary
python .cursor/skills/analyze_weather_data.py question -q "temperature trends"
```

Returns JSON for agent consumption. See `.cursor/skills/SKILL.md`.

## Frontend (Vite + React + TypeScript)

The UI lives in [`frontend/`](frontend/). It shows health stats, latest readings per city, and notable events with auto-refresh every 30 seconds.

**With Docker:** open http://localhost:3000 (nginx proxies API routes to the backend).

**Local dev** (API on :8000):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — Vite proxies `/health`, `/readings`, and `/events` to the API.

## Development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
# Start Postgres locally and set DATABASE_URL
uvicorn watchagent.main:app --reload
```

## CI

GitHub Actions on push to `main`: **test** (pytest with mocked API) and **build** (`docker build`).
