#!/usr/bin/env python3
"""Check whether a manual PredX research run should start after a recent HOLD."""

from __future__ import annotations

import argparse
import json
from datetime import timedelta, timezone
from pathlib import Path

from build_run_context import collect_history, parse_time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--account", required=True)
    parser.add_argument("--now", required=True, help="ISO-8601 time with timezone")
    parser.add_argument("--cooldown-minutes", type=int, default=60)
    parser.add_argument("--override-reason", default="")
    args = parser.parse_args()

    now = parse_time(args.now)
    if now is None:
        print(json.dumps({"ok": False, "error": "--now requires an ISO-8601 timezone"}))
        return 2
    if args.cooldown_minutes < 0:
        print(json.dumps({"ok": False, "error": "--cooldown-minutes must be non-negative"}))
        return 2

    history = collect_history(Path(args.root).resolve(), args.account, now)
    holds = [row for row in history if row["status"] == "HOLD"]
    latest = max(
        holds,
        key=lambda row: parse_time(row["run_time"]).astimezone(timezone.utc),
        default=None,
    )
    override = args.override_reason.strip()
    if override:
        print(
            json.dumps(
                {
                    "ok": True,
                    "code": "MANUAL_COOLDOWN_OVERRIDDEN",
                    "account": args.account,
                    "override_reason": override,
                    "latest_hold_at": latest["run_time"] if latest else None,
                },
                ensure_ascii=False,
            )
        )
        return 0
    if latest is None:
        print(json.dumps({"ok": True, "code": "MANUAL_COOLDOWN_CLEAR", "account": args.account}))
        return 0

    latest_at = parse_time(latest["run_time"])
    if latest_at is None:
        print(json.dumps({"ok": False, "error": "latest HOLD has no usable run timestamp"}))
        return 2
    elapsed = max((now - latest_at).total_seconds() / 60, 0.0)
    if elapsed < args.cooldown_minutes:
        print(
            json.dumps(
                {
                    "ok": False,
                    "code": "SKIPPED_MANUAL_COOLDOWN",
                    "account": args.account,
                    "latest_hold_at": latest_at.isoformat(),
                    "elapsed_minutes": round(elapsed, 1),
                    "cooldown_minutes": args.cooldown_minutes,
                    "eligible_at": (latest_at + timedelta(minutes=args.cooldown_minutes)).isoformat(),
                },
                ensure_ascii=False,
            )
        )
        return 3

    print(
        json.dumps(
            {
                "ok": True,
                "code": "MANUAL_COOLDOWN_CLEAR",
                "account": args.account,
                "latest_hold_at": latest_at.isoformat(),
                "elapsed_minutes": round(elapsed, 1),
                "cooldown_minutes": args.cooldown_minutes,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
