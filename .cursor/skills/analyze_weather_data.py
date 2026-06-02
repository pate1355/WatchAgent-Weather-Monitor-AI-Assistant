#!/usr/bin/env python3
"""Query WatchAgent PostgreSQL data and return structured JSON analysis."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from watchagent.storage.models import Event, Reading  # noqa: E402


def get_engine():
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://watchagent:watchagent@localhost:5432/watchagent",
    )
    return create_engine(url)


def cmd_summary(session) -> dict:
    reading_counts = dict(
        session.execute(
            select(Reading.city, func.count()).group_by(Reading.city)
        ).all()
    )
    event_counts = dict(
        session.execute(select(Event.event_type, func.count()).group_by(Event.event_type)).all()
    )
    return {
        "readings_total": session.scalar(select(func.count()).select_from(Reading)) or 0,
        "events_total": session.scalar(select(func.count()).select_from(Event)) or 0,
        "readings_by_city": reading_counts,
        "events_by_type": event_counts,
    }


def cmd_compare_cities(session) -> dict:
    latest: dict[str, dict] = {}
    for city in ("Ottawa", "Toronto", "Vancouver"):
        row = session.scalar(
            select(Reading)
            .where(Reading.city == city)
            .order_by(Reading.observation_time.desc())
            .limit(1)
        )
        if row:
            latest[city] = {
                "observation_time": row.observation_time.isoformat(),
                "temperature_2m": row.temperature_2m,
                "precipitation": row.precipitation,
                "wind_speed_10m": row.wind_speed_10m,
                "weather_code": row.weather_code,
            }
    temps = {c: v["temperature_2m"] for c, v in latest.items()}
    spread = max(temps.values()) - min(temps.values()) if temps else 0
    return {"latest_by_city": latest, "temperature_spread_c": spread}


def cmd_events_by_type(session) -> dict:
    rows = session.execute(
        select(Event.event_type, Event.city, func.count())
        .group_by(Event.event_type, Event.city)
        .order_by(Event.event_type)
    ).all()
    return {
        "breakdown": [
            {"event_type": et, "city": city, "count": count} for et, city, count in rows
        ]
    }


def cmd_temp_trends(session, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result: dict[str, dict] = {}
    for city in ("Ottawa", "Toronto", "Vancouver"):
        stats = session.execute(
            select(
                func.count(Reading.id),
                func.min(Reading.temperature_2m),
                func.max(Reading.temperature_2m),
                func.avg(Reading.temperature_2m),
            ).where(Reading.city == city, Reading.observation_time >= since)
        ).one()
        result[city] = {
            "count": stats[0] or 0,
            "min_c": float(stats[1]) if stats[1] is not None else None,
            "max_c": float(stats[2]) if stats[2] is not None else None,
            "avg_c": round(float(stats[3]), 2) if stats[3] is not None else None,
        }
    return {"window_hours": hours, "cities": result}


def cmd_question(session, question: str) -> dict:
    q = question.lower()
    if "compare" in q or "contrast" in q or "city" in q:
        return {"question": question, "answer": cmd_compare_cities(session)}
    if "event" in q:
        return {"question": question, "answer": cmd_events_by_type(session)}
    if "trend" in q or "temperature" in q:
        return {"question": question, "answer": cmd_temp_trends(session)}
    return {"question": question, "answer": cmd_summary(session)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze WatchAgent stored weather data")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["summary", "compare-cities", "events-by-type", "temp-trends", "question"],
        default="summary",
    )
    parser.add_argument("--question", "-q", help="Natural language question (with question command)")
    parser.add_argument("--hours", type=int, default=24, help="Hours for temp-trends")
    args = parser.parse_args()

    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.execute(text("SELECT 1"))
        if args.command == "summary":
            payload = cmd_summary(session)
        elif args.command == "compare-cities":
            payload = cmd_compare_cities(session)
        elif args.command == "events-by-type":
            payload = cmd_events_by_type(session)
        elif args.command == "temp-trends":
            payload = cmd_temp_trends(session, hours=args.hours)
        elif args.command == "question":
            if not args.question:
                print(json.dumps({"error": "--question required"}), file=sys.stderr)
                return 1
            payload = cmd_question(session, args.question)
        else:
            payload = {"error": "unknown command"}
    except Exception as exc:
        payload = {"error": str(exc)}
    finally:
        session.close()

    print(json.dumps(payload, indent=2, default=str))
    return 0 if "error" not in payload else 1


if __name__ == "__main__":
    raise SystemExit(main())
