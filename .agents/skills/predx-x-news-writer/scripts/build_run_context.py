#!/usr/bin/env python3
"""Build compact recent-output context for a scheduled PredX writing run."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ACTIVE_STATUSES = {"READY", "REVIEW"}
OUTPUT_GLOBS = ("*output.json", "runtime/predx-x-news-writer/**/*.json")


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def as_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    return [payload] if isinstance(payload, dict) else []


def blocks(text: Any) -> list[str]:
    value = str(text or "").strip()
    if not value:
        return []
    parts = [part.strip() for part in re.split(r"\n\s*\n", value) if part.strip()]
    return parts if len(parts) > 1 else [line.strip() for line in value.splitlines() if line.strip()]


def normalize_text(value: Any) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\u3400-\u9fff]+", "", text, flags=re.UNICODE)
    return text


def derive_story_key(item: dict[str, Any]) -> str:
    explicit = normalize_text(item.get("story_key"))
    if explicit:
        return explicit
    story = normalize_text(item.get("story"))
    if story:
        return story[:120]
    chinese = blocks(item.get("chinese") or item.get("chinese_post") or item.get("chinese_review"))
    return normalize_text(chinese[0] if chinese else "")[:120]


def derive_topic_key(item: dict[str, Any]) -> str:
    explicit = normalize_text(item.get("topic_key"))
    if explicit:
        return explicit
    story = str(item.get("story") or "")
    chinese = str(item.get("chinese") or item.get("chinese_post") or item.get("chinese_review") or "")
    text = f"{story} {chinese}".casefold()
    patterns = (
        ("crypto-etf-flows", ("etf",), ("流入", "流出", "inflow", "outflow")),
        ("central-bank-gold-reserves", ("黄金", "gold"), ("储备", "reserve")),
        ("china-crude-imports", ("中国", "china"), ("原油进口", "crude import")),
    )
    for key, entity_terms, event_terms in patterns:
        if any(term in text for term in entity_terms) and any(term in text for term in event_terms):
            return key
    return ""


def item_time(item: dict[str, Any], path: Path) -> datetime:
    signal = item.get("x_signal") if isinstance(item.get("x_signal"), dict) else {}
    for value in (
        item.get("source_time"),
        item.get("published_at"),
        signal.get("posted_at"),
        signal.get("metrics_collected_at"),
    ):
        parsed = parse_time(value)
        if parsed:
            return parsed
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def iter_output_paths(root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in OUTPUT_GLOBS:
        for path in root.glob(pattern):
            resolved = path.resolve()
            if resolved in seen or ".agents" in path.parts:
                continue
            seen.add(resolved)
            yield path


def collect_history(
    root: Path,
    account: str,
    now: datetime,
    lookback_days: int = 7,
    exclude_path: Path | None = None,
) -> list[dict[str, Any]]:
    cutoff = now - timedelta(days=lookback_days)
    excluded = exclude_path.resolve() if exclude_path else None
    rows: list[dict[str, Any]] = []
    seen_records: set[tuple[str, str, str]] = set()

    for path in iter_output_paths(root):
        if excluded and path.resolve() == excluded:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in as_items(payload):
            if str(item.get("account", "")) != account:
                continue
            timestamp = item_time(item, path)
            if timestamp.astimezone(timezone.utc) < cutoff.astimezone(timezone.utc):
                continue
            chinese = str(item.get("chinese") or item.get("chinese_post") or item.get("chinese_review") or "")
            chinese_blocks = blocks(chinese)
            story = str(item.get("story") or "").strip()
            status = str(item.get("status") or "").upper()
            story_key = derive_story_key(item)
            dedupe_key = (status, story_key, timestamp.isoformat())
            if dedupe_key in seen_records:
                continue
            seen_records.add(dedupe_key)
            sources = [str(url) for url in item.get("sources", []) if isinstance(url, str)]
            rows.append(
                {
                    "status": status,
                    "story": story,
                    "story_key": story_key,
                    "topic_key": derive_topic_key(item),
                    "source_time": timestamp.isoformat(),
                    "date": timestamp.astimezone(now.tzinfo).date().isoformat(),
                    "opening_type": str(item.get("opening_type") or ""),
                    "evidence_path": str(item.get("evidence_path") or ""),
                    "ending_function": str(item.get("ending_function") or ""),
                    "opening_text": chinese_blocks[0] if chinese_blocks else "",
                    "ending_text": chinese_blocks[-1] if chinese_blocks else "",
                    "block_count": len(chinese_blocks),
                    "sources": sources,
                    "file": str(path),
                }
            )

    rows.sort(key=lambda row: row["source_time"], reverse=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Project root containing prior output JSON files")
    parser.add_argument("--account", required=True)
    parser.add_argument("--now", required=True, help="ISO-8601 time with timezone")
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--exclude", help="Candidate file to exclude from history")
    args = parser.parse_args()

    now = parse_time(args.now)
    if now is None:
        print(json.dumps({"ok": False, "error": "--now requires an ISO-8601 timezone"}, ensure_ascii=False))
        return 2

    root = Path(args.root).resolve()
    exclude = Path(args.exclude).resolve() if args.exclude else None
    history = collect_history(root, args.account, now, args.lookback_days, exclude)
    today = now.date().isoformat()
    active = [row for row in history if row["status"] in ACTIVE_STATUSES]
    same_day = [row for row in active if row["date"] == today]
    holds = [row for row in history if row["status"] == "HOLD"]
    payload = {
        "ok": True,
        "account": args.account,
        "as_of": now.isoformat(),
        "ready_or_review_count_today": len(same_day),
        "blocked_story_keys": [row["story_key"] for row in active if row["story_key"]],
        "blocked_topic_keys": sorted({row["topic_key"] for row in active if row["topic_key"]}),
        "same_day_style_history": same_day[:8],
        "recent_story_history": active[:16],
        "recent_holds": holds[:8],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
