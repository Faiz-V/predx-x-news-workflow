#!/usr/bin/env python3
"""Regression tests for PolymarketAlpha fallback candidate gates."""

from __future__ import annotations

import unittest

from rank_candidates import alpha_fallback_eligible


def candidate(**overrides: object) -> dict:
    item = {
        "headline": "Federal Reserve releases updated balance-sheet data",
        "summary": "US liquidity conditions changed materially.",
        "verification_status": "primary",
        "impact_score": 7,
        "audience_region": "US_EU",
        "china_related": False,
    }
    item.update(overrides)
    return item


class AlphaFallbackCandidateTests(unittest.TestCase):
    def test_accepts_verified_six_hour_market_brief(self) -> None:
        eligible, reasons = alpha_fallback_eligible(candidate(), 360)
        self.assertTrue(eligible)
        self.assertEqual(reasons, [])

    def test_rejects_candidate_older_than_twelve_hours(self) -> None:
        eligible, reasons = alpha_fallback_eligible(candidate(), 721)
        self.assertFalse(eligible)
        self.assertTrue(any("12-hour" in reason for reason in reasons))

    def test_rejects_low_impact_candidate(self) -> None:
        eligible, reasons = alpha_fallback_eligible(candidate(impact_score=5), 120)
        self.assertFalse(eligible)
        self.assertTrue(any("impact score" in reason for reason in reasons))

    def test_rejects_china_related_candidate(self) -> None:
        eligible, reasons = alpha_fallback_eligible(
            candidate(headline="PBOC changes yuan liquidity settings"), 120
        )
        self.assertFalse(eligible)
        self.assertTrue(any("China-related" in reason for reason in reasons))

    def test_requires_explicit_us_eu_relevance(self) -> None:
        eligible, reasons = alpha_fallback_eligible(candidate(audience_region=None), 120)
        self.assertFalse(eligible)
        self.assertTrue(any("US_EU" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
