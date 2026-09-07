#!/usr/bin/env python3
"""Focused regression tests for PolymarketAlpha UTC enforcement."""

from __future__ import annotations

import copy
import unittest

from lint_output import lint_item


def alpha_item() -> dict:
    return {
        "account": "PolymarketAlpha",
        "status": "READY",
        "audience_region": "US_EU",
        "china_related": False,
        "audience_timezone": "UTC",
        "post_mode": "standard_x",
        "format_variant": "explained_news",
        "style_fingerprint": "number-led / data release / measured implication / 1 block",
        "story": "Federal Reserve market update",
        "source_time": "2026-08-20T01:23:39Z",
        "disclosure_time": "2026-08-20T01:23:39Z",
        "sources": ["https://example.com/source"],
        "chinese": "美联储数据于01:23 UTC公布，市场波动随后上升。",
        "english": "The Federal Reserve data arrived at 01:23 UTC, followed by higher market volatility.",
        "x_signal": {
            "posted_at": "2026-08-20T01:23:39Z",
            "metrics_collected_at": "2026-08-20T01:42:51Z",
            "measurement_history": [
                {"collected_at": "2026-08-20T01:41:24Z", "views": 100}
            ],
        },
    }


class PolymarketAlphaTimezoneTests(unittest.TestCase):
    def timezone_errors(self, item: dict) -> list[str]:
        return [
            message
            for message in lint_item(item, 1)["errors"]
            if "PolymarketAlpha" in message and ("timezone" in message or "UTC" in message)
        ]

    def test_accepts_utc_copy_and_timestamps(self) -> None:
        self.assertEqual(self.timezone_errors(alpha_item()), [])

    def test_requires_audience_timezone(self) -> None:
        item = alpha_item()
        item.pop("audience_timezone")
        self.assertIn(
            'PolymarketAlpha READY/REVIEW items require audience_timezone: "UTC"',
            self.timezone_errors(item),
        )

    def test_rejects_utc_plus_eight_in_copy(self) -> None:
        item = alpha_item()
        item["chinese"] = "市场数据于09:23 UTC+8公布，波动随后上升。"
        item["english"] = "Market data arrived at 09:23 UTC+8, followed by higher volatility."
        errors = self.timezone_errors(item)
        self.assertTrue(any("forbidden non-UTC timezone" in message for message in errors))

    def test_rejects_clock_time_without_utc_label(self) -> None:
        item = alpha_item()
        item["chinese"] = "美联储数据于01:23公布，市场波动随后上升。"
        item["english"] = "The Federal Reserve data arrived at 01:23, followed by higher market volatility."
        errors = self.timezone_errors(item)
        self.assertTrue(any("clock time without an explicit UTC label" in message for message in errors))

    def test_rejects_non_utc_structured_timestamp(self) -> None:
        item = copy.deepcopy(alpha_item())
        item["source_time"] = "2026-08-20T09:23:39+08:00"
        item["x_signal"]["measurement_history"][0]["collected_at"] = (
            "2026-08-20T09:41:24+08:00"
        )
        errors = self.timezone_errors(item)
        self.assertTrue(any("source_time must be normalized to UTC" in message for message in errors))
        self.assertTrue(
            any("measurement_history[1].collected_at must be normalized to UTC" in message for message in errors)
        )

    def test_rejects_internal_collection_language_in_public_copy(self) -> None:
        item = alpha_item()
        item["chinese"] = "本轮采集时，美联储数据已公布，市场波动随后上升。"
        item["english"] = "At collection time, the Federal Reserve data was out and market volatility had risen."
        errors = lint_item(item, 1)["errors"]
        self.assertTrue(any("Chinese copy exposes internal collection/audit language" in message for message in errors))
        self.assertTrue(any("English copy exposes internal collection/audit language" in message for message in errors))

    def test_accepts_natural_current_state_language(self) -> None:
        item = alpha_item()
        item["chinese"] = "截至目前，美联储数据已公布，市场波动随后上升。"
        item["english"] = "The Federal Reserve data is now out, and market volatility has risen."
        errors = lint_item(item, 1)["errors"]
        self.assertFalse(any("internal collection/audit language" in message for message in errors))


class PolymarketAlphaFallbackTests(unittest.TestCase):
    def fallback_item(self) -> dict:
        item = alpha_item()
        item.update(
            {
                "scheduled_run": True,
                "story_key": "fed-market-update-2026-08-20",
                "topic_key": "fed-market-update",
                "selection_mode": "verified_market_brief",
                "allow_news_platform_fallback": True,
                "fallback_reason": "No strict HOT/WARM candidate survived Snapshot B.",
                "verification_status": "primary",
                "impact_score": 7,
                "source_age_minutes": 360,
                "trend_status": "UNPROVEN",
            }
        )
        return item

    def fallback_errors(self, item: dict) -> list[str]:
        return lint_item(item, 1)["errors"]

    def test_accepts_scheduled_verified_market_brief(self) -> None:
        self.assertEqual(self.fallback_errors(self.fallback_item()), [])

    def test_accepts_manual_verified_market_brief(self) -> None:
        item = self.fallback_item()
        item.pop("scheduled_run")
        self.assertEqual(self.fallback_errors(item), [])

    def test_rejects_fallback_older_than_twelve_hours(self) -> None:
        item = self.fallback_item()
        item["source_age_minutes"] = 721
        self.assertTrue(
            any("between 0 and 720" in message for message in self.fallback_errors(item))
        )

    def test_rejects_low_impact_fallback(self) -> None:
        item = self.fallback_item()
        item["impact_score"] = 5
        self.assertIn(
            "verified_market_brief impact_score must be between 6 and 10",
            self.fallback_errors(item),
        )

    def test_single_reputable_fallback_must_remain_review(self) -> None:
        item = self.fallback_item()
        item["verification_status"] = "single_reputable"
        self.assertIn(
            "single_reputable verified_market_brief must remain REVIEW",
            self.fallback_errors(item),
        )

    def test_rejects_just_in_fallback(self) -> None:
        item = self.fallback_item()
        item["chinese"] = "JUST IN: 美联储数据已公布，市场波动随后上升。"
        item["english"] = "JUST IN: Federal Reserve data is out, followed by higher market volatility."
        self.assertIn(
            "verified_market_brief must not use a JUST IN opening",
            self.fallback_errors(item),
        )

    def test_series_metadata_is_all_or_nothing(self) -> None:
        item = self.fallback_item()
        item["series_key"] = "weekly-us-jobless-claims"
        self.assertIn(
            "series updates require series_key, observation_period, and material_new_fact together",
            self.fallback_errors(item),
        )

    def test_alpha_series_rule_does_not_change_other_accounts(self) -> None:
        item = alpha_item()
        item["account"] = "PolyPredX"
        item["series_key"] = "general-politics-series"
        errors = lint_item(item, 1)["errors"]
        self.assertNotIn(
            "series updates require series_key, observation_period, and material_new_fact together",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
