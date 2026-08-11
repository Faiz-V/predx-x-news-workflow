#!/usr/bin/env python3
"""Rank news candidates for each PredX X account."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACCOUNT_CATEGORIES = {
    "PolymarketAlpha": {"finance", "macro", "markets", "crypto", "regulation"},
    "PolyPredX": {
        "politics",
        "elections",
        "policy",
        "geopolitics",
        "courts",
        "conflict",
        "diplomacy",
        "sanctions",
        "international_security",
        "war",
    },
    "PredX_Labs": {"sports", "football", "soccer"},
    "PredX_News": {"technology", "tech", "ai", "chips", "cybersecurity", "science"},
}
POLYPREDX_GEOPOLITICAL_CATEGORIES = {
    "geopolitics",
    "conflict",
    "diplomacy",
    "sanctions",
    "international_security",
    "war",
}
VERIFY_SCORE = {
    "primary": 35,
    "multi_source": 30,
    "single_reputable": 20,
    "unverified": -50,
}


def clamp_number(value: Any, lower: float, upper: float, default: float = 0) -> float:
    try:
        return max(lower, min(upper, float(value)))
    except (TypeError, ValueError):
        return default


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp lacks timezone: {value}")
    return parsed


def freshness_score(age_minutes: float) -> float:
    if age_minutes < -2:
        return -50
    if age_minutes <= 30:
        return 45
    if age_minutes <= 60:
        return 35
    if age_minutes <= 180:
        return 15
    return -35


def x_heat(item: dict[str, Any], now: datetime) -> tuple[float, str, float | None, list[str]]:
    signal = item.get("x_signal")
    if not isinstance(signal, dict) or not signal.get("post_url") or not signal.get("posted_at"):
        return 0, "UNPROVEN", None, ["no usable X demand signal"]

    posted = parse_time(str(signal["posted_at"]))
    age_minutes = (now.astimezone(timezone.utc) - posted.astimezone(timezone.utc)).total_seconds() / 60
    notes: list[str] = []
    fresh_echo_count = int(clamp_number(signal.get("fresh_echo_count"), 0, 20))
    latest_echo = None
    if signal.get("latest_fresh_echo_at"):
        latest_echo = parse_time(str(signal["latest_fresh_echo_at"]))
    latest_echo_age = (
        (now.astimezone(timezone.utc) - latest_echo.astimezone(timezone.utc)).total_seconds() / 60
        if latest_echo
        else None
    )
    live_fallback = bool(
        signal.get("live_event")
        and 60 < age_minutes <= 180
        and fresh_echo_count >= 2
        and latest_echo_age is not None
        and -2 <= latest_echo_age <= 60
    )

    explicit = signal.get("heat_score")
    if explicit is not None:
        heat = clamp_number(explicit, 0, 100)
        notes.append("collector heat score")
    else:
        if age_minutes <= 15:
            recency = 25
        elif age_minutes <= 30:
            recency = 20
        elif age_minutes <= 60:
            recency = 14
        elif age_minutes <= 180:
            recency = 4
        else:
            recency = 0

        relative_velocity = clamp_number(signal.get("relative_velocity"), 0, 20)
        if relative_velocity >= 3:
            velocity = 35
        elif relative_velocity >= 2:
            velocity = 30
        elif relative_velocity >= 1.5:
            velocity = 24
        elif relative_velocity >= 1:
            velocity = 18
        elif relative_velocity > 0:
            velocity = 10
        else:
            effective_age = max(age_minutes, 5)
            weighted_engagement = (
                clamp_number(signal.get("likes"), 0, 10**12)
                + 2 * clamp_number(signal.get("reposts"), 0, 10**12)
                + 1.5 * clamp_number(signal.get("replies"), 0, 10**12)
                + 0.5 * clamp_number(signal.get("bookmarks"), 0, 10**12)
            )
            per_minute = weighted_engagement / effective_age
            if per_minute >= 20:
                velocity = 28
            elif per_minute >= 8:
                velocity = 23
            elif per_minute >= 3:
                velocity = 18
            elif per_minute >= 1:
                velocity = 12
            elif per_minute >= 0.2:
                velocity = 6
            else:
                velocity = 0
            notes.append("absolute velocity used; author baseline unavailable")

        independent = int(clamp_number(signal.get("independent_post_count"), 0, 20))
        echo = (0, 5, 12, 18, 22, 25)[min(independent, 5)]
        fit = clamp_number(signal.get("audience_fit"), 0, 10) * 1.5
        heat = min(100, recency + velocity + echo + fit)

    independent = int(clamp_number(signal.get("independent_post_count"), 0, 20))
    relative_velocity = clamp_number(signal.get("relative_velocity"), 0, 20)
    if age_minutes < -2:
        status = "UNPROVEN"
        notes.append("X post timestamp is in the future")
    elif age_minutes > 60 and not live_fallback:
        status = "UNPROVEN"
        notes.append("X post outside normal 60-minute demand window without a qualified live-event echo burst")
    elif heat >= 60 or (relative_velocity >= 1.5 and independent >= 2):
        status = "HOT"
    elif heat >= 40 and independent >= 2:
        status = "WARM"
    else:
        status = "UNPROVEN"

    if live_fallback:
        notes.append(
            f"live-event fallback supported by {fresh_echo_count} fresh echo(es); latest echo age {latest_echo_age:.1f} minutes"
        )

    notes.append(f"X trend {status}")
    return round(heat, 1), status, round(age_minutes, 1), notes


def score(
    item: dict[str, Any], account: str, now: datetime
) -> tuple[float, float, list[str], float, str, float | None]:
    published = parse_time(str(item["published_at"]))
    age_minutes = (now.astimezone(timezone.utc) - published.astimezone(timezone.utc)).total_seconds() / 60
    reasons: list[str] = []
    total = freshness_score(age_minutes)
    total += VERIFY_SCORE.get(str(item.get("verification_status", "unverified")), -50)
    total += max(0, min(10, int(item.get("impact_score", 0)))) * 2

    heat, trend_status, x_age, x_notes = x_heat(item, now)
    total += heat * 0.45
    if trend_status == "UNPROVEN":
        total -= 20
    reasons.extend(x_notes)

    hints = set(item.get("account_hint", []))
    categories = {str(value).lower() for value in item.get("categories", [])}
    if account in hints:
        total += 20
        reasons.append("explicit account hint")
    overlap = categories & ACCOUNT_CATEGORIES[account]
    if overlap:
        total += 15
        reasons.append("category match: " + ", ".join(sorted(overlap)))
    if item.get("duplicate_of"):
        total -= 60
        reasons.append("duplicate penalty")
    if age_minutes > 180:
        reasons.append("outside normal freshness window")
    if str(item.get("verification_status", "unverified")) == "unverified":
        reasons.append("unverified")
    return round(total, 2), round(age_minutes, 1), reasons, heat, trend_status, x_age


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="News packet JSON file")
    parser.add_argument("--now", help="ISO-8601 time with timezone; defaults to current time")
    parser.add_argument("--limit", type=int, default=5, help="Candidates per account")
    parser.add_argument(
        "--include-unproven",
        action="store_true",
        help="Include candidates that do not pass the normal X demand gate",
    )
    args = parser.parse_args()

    try:
        payload = load(args.path)
        items = payload["items"]
        now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
        ranked: dict[str, list[dict[str, Any]]] = {}
        for account in ACCOUNT_CATEGORIES:
            rows = []
            for item in items:
                hints = set(item.get("account_hint", []))
                categories = {str(value).lower() for value in item.get("categories", [])}
                if (hints or categories) and account not in hints and not (
                    categories & ACCOUNT_CATEGORIES[account]
                ):
                    continue
                value, age, reasons, heat, trend_status, x_age = score(item, account, now)
                if trend_status == "UNPROVEN" and not args.include_unproven:
                    continue
                rows.append(
                    {
                        "id": item.get("id"),
                        "headline": item.get("headline"),
                        "source_url": item.get("source_url"),
                        "score": value,
                        "age_minutes": age,
                        "x_heat_score": heat,
                        "trend_status": trend_status,
                        "x_age_minutes": x_age,
                        "selection_priority": (
                            "geopolitics_first"
                            if account == "PolyPredX"
                            and categories & POLYPREDX_GEOPOLITICAL_CATEGORIES
                            else "general_politics_fallback"
                            if account == "PolyPredX"
                            else "standard"
                        ),
                        "selection_tier": (
                            0
                            if account != "PolyPredX"
                            or categories & POLYPREDX_GEOPOLITICAL_CATEGORIES
                            else 1
                        ),
                        "notes": reasons,
                    }
                )
            ranked[account] = sorted(
                rows,
                key=lambda row: (
                    row["selection_tier"],
                    -row["score"],
                    row["age_minutes"],
                ),
            )[: args.limit]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps({"ok": True, "ranked": ranked}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
