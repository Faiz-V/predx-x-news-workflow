#!/usr/bin/env python3
"""Regression tests for fallback quotas and recurring-series history checks."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from lint_output import apply_history_checks, lint_item


def alpha_output(story_key: str, selection_mode: str = "strict_x_news") -> dict:
    fallback = selection_mode == "verified_market_brief"
    return {
        "account": "PolymarketAlpha",
        "status": "READY",
        "scheduled_run": True,
        "story": story_key,
        "story_key": story_key,
        "topic_key": story_key,
        "audience_region": "US_EU",
        "china_related": False,
        "audience_timezone": "UTC",
        "post_mode": "standard_x",
        "format_variant": "explained_news",
        "style_fingerprint": "fact-led / official data / limited implication / 1 block",
        "source_time": "2026-08-27T06:00:00Z",
        "as_of": "2026-08-27T07:00:00Z",
        "sources": ["https://example.com/source"],
        "chinese": f"{story_key}出现新的可核验变化。",
        "english": f"{story_key} produced a new verified change.",
        "trend_status": "UNPROVEN" if fallback else "HOT",
        "x_signal": (
            {"trend_status": "UNPROVEN"}
            if fallback
            else {
                "trend_status": "HOT",
                "post_url": "https://x.com/example/status/1",
                "posted_at": "2026-08-27T06:10:00Z",
            }
        ),
        "selection_mode": selection_mode,
        "allow_news_platform_fallback": fallback,
        "fallback_reason": "Strict pool failed Snapshot B." if fallback else None,
        "verification_status": "primary",
        "impact_score": 7,
        "source_age_minutes": 360 if fallback else 60,
    }


class HistoryControlTests(unittest.TestCase):
    def apply(self, root: Path, candidate: dict) -> dict:
        result = lint_item(candidate, 1)
        apply_history_checks(
            candidate,
            result,
            root,
            datetime.fromisoformat("2026-08-27T12:00:00+00:00"),
            None,
            7,
        )
        return result

    def test_limits_verified_market_brief_to_one_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prior = alpha_output("prior-market-brief", "verified_market_brief")
            (root / "prior-output.json").write_text(json.dumps(prior), encoding="utf-8")
            result = self.apply(
                root,
                alpha_output("different-market-brief", "verified_market_brief"),
            )
            self.assertTrue(
                any("only one verified_market_brief" in error for error in result["errors"])
            )

    def test_rejects_same_series_observation_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prior = alpha_output("weekly-claims-prior")
            prior.update(
                {
                    "series_key": "weekly-us-jobless-claims",
                    "observation_period": "2026-W34",
                    "material_new_fact": "Claims rose from the prior week.",
                }
            )
            (root / "prior-output.json").write_text(json.dumps(prior), encoding="utf-8")
            candidate = alpha_output("weekly-claims-current")
            candidate.update(
                {
                    "series_key": "weekly-us-jobless-claims",
                    "observation_period": "2026-W34",
                    "material_new_fact": "The release confirms the same observation.",
                }
            )
            result = self.apply(root, candidate)
            self.assertTrue(
                any("already used" in error and "2026-W34" in error for error in result["errors"])
            )


if __name__ == "__main__":
    unittest.main()
