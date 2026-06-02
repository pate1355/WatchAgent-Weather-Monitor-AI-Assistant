---
name: analyze-weather-data
description: Query WatchAgent PostgreSQL readings and events; return structured JSON summaries, city comparisons, and trends. Use when answering questions about stored weather data in this project.
---

# Analyze Weather Data

Run the data analysis script against the running WatchAgent database.

## Prerequisites

- Stack running: `docker compose up`
- `DATABASE_URL` set (defaults to local Postgres from `.env.example`)

## Usage

From the repository root:

```bash
pip install sqlalchemy psycopg[binary]
export DATABASE_URL=postgresql+psycopg://watchagent:watchagent@localhost:5432/watchagent

python .cursor/skills/analyze_weather_data.py summary
python .cursor/skills/analyze_weather_data.py compare-cities
python .cursor/skills/analyze_weather_data.py events-by-type
python .cursor/skills/analyze_weather_data.py temp-trends --hours 48
python .cursor/skills/analyze_weather_data.py question -q "compare temperatures across cities"
```

Output is JSON on stdout for agent consumption.
