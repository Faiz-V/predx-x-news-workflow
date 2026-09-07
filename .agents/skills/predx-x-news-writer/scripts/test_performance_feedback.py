#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


feedback = load_module("build_performance_feedback", "build_performance_feedback.py")
run_context = load_module("build_run_context", "build_run_context.py")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def artifact(story_key: str, opening: str, views_marker: str) -> dict[str, object]:
    return {
        "account": "PolymarketAlpha",
        "status": "READY",
        "story": f"US inflation {views_marker}",
        "story_key": story_key,
        "topic_key": "us-inflation",
        "source_time": "2026-08-22T10:00:00+00:00",
        "opening_type": "direct fact",
        "evidence_path": "release → detail → implication",
        "ending_function": "short verdict",
        "style_fingerprint": "direct fact / release / short verdict / 4 blocks",
        "chinese": "第一段\n\n第二段\n\n第三段\n\n第四段",
        "english": f"{opening}\n\nOfficial US data showed {views_marker}.\n\nMarkets repriced the path.\n\nThe release matters more than forecasts.",
    }


def post(post_id: str, posted_at: str, text: str, views: int) -> dict[str, object]:
    return {
        "post_id": post_id,
        "url": f"https://x.com/Polymarketalpha/status/{post_id}",
        "posted_at": posted_at,
        "metrics": {"views": views, "likes": 2, "reposts": 1, "replies": 0},
        "visible_text": text,
    }


class PerformanceFeedbackTests(unittest.TestCase):
    def test_small_groups_are_monitor_only_and_repeated_groups_are_regularized(self) -> None:
        early_rows = [
            {"metrics": {"views": 400}, "engagement_rate_per_100_views": 1.0},
            {"metrics": {"views": 400}, "engagement_rate_per_100_views": 1.0},
        ]
        for row in early_rows:
            row["opening_type"] = "number-led"
        early = feedback.group_signal(early_rows, "opening_type", 100.0)[0]
        self.assertEqual(early["view_lift_vs_account_median"], 4.0)
        self.assertEqual(early["regularized_view_lift_vs_account_median"], 2.0)
        self.assertEqual(early["soft_use"], "MONITOR_ONLY")

        repeated_rows = [
            {"opening_type": "direct fact", "metrics": {"views": 150}, "engagement_rate_per_100_views": 1.0}
            for _ in range(4)
        ]
        repeated = feedback.group_signal(repeated_rows, "opening_type", 100.0)[0]
        self.assertEqual(repeated["regularized_view_lift_vs_account_median"], 1.25)
        self.assertEqual(repeated["soft_use"], "LIMITED_EXPERIMENT")

    def test_top_level_artifacts_reply_and_republication_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = artifact("us-inflation-a", "US inflation slowed in July.", "release A")
            second = artifact("us-inflation-b", "US payroll growth weakened in July.", "release B")
            write_json(root / "runtime/predx-x-news-writer/2026-08-22/a.json", first)
            write_json(root / "runtime/predx-x-news-writer/2026-08-22/b.json", second)
            snapshot = {
                "schema_version": "predx-performance-snapshot-v1",
                "collected_at": "2026-08-24T03:00:00+00:00",
                "accounts": [
                    {
                        "account": "PolymarketAlpha",
                        "handle": "@Polymarketalpha",
                        "followers_visible": 50,
                        "posts": [
                            post("1", "2026-08-22T11:00:00+00:00", first["english"], 120),
                            post("2", "2026-08-22T12:00:00+00:00", first["english"], 80),
                            post("3", "2026-08-22T13:00:00+00:00", second["english"], 100),
                            post("4", "2026-08-22T14:00:00+00:00", f"Replying to @someone {second['english']}", 500),
                        ],
                    }
                ],
            }
            write_json(
                root / "runtime/predx-x-news-writer/performance/snapshots/2026-08-24T03-00-00Z.json",
                snapshot,
            )

            payload = feedback.build_feedback(
                root,
                datetime.fromisoformat("2026-08-24T12:00:00+08:00"),
                30,
            )
            summary = payload["accounts"]["PolymarketAlpha"]
            self.assertEqual(payload["matched_post_count"], 3)
            self.assertEqual(payload["unmatched_post_count"], 1)
            self.assertEqual(summary["republished_post_count"], 1)
            self.assertEqual(summary["mature_post_count"], 2)
            self.assertEqual(summary["unmatched_posts"][0]["match_reason"], "EXCLUDED_REPLY")
            macro = next(
                signal
                for signal in summary["signals"]
                if signal["dimension"] == "content_family"
                and signal["value"] == "macro_and_official_data"
            )
            self.assertEqual(macro["sample_size"], 2)
            self.assertEqual(macro["soft_use"], "MONITOR_ONLY")

    def test_repeated_snapshots_select_first_mature_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshots = root / "runtime/predx-x-news-writer/performance/snapshots"
            published_at = "2026-08-22T00:00:00+00:00"
            for hour, views in ((20, 20), (30, 30), (50, 99)):
                payload = {
                    "collected_at": f"2026-08-{22 if hour < 24 else 23 if hour < 48 else 24}T{hour % 24:02d}:00:00+00:00",
                    "accounts": [
                        {
                            "account": "PolymarketAlpha",
                            "handle": "@Polymarketalpha",
                            "followers_visible": 50,
                            "posts": [post("repeat", published_at, "US inflation slowed in July.", views)],
                        }
                    ],
                }
                write_json(snapshots / f"snapshot-{hour}.json", payload)

            rows, count = feedback.load_snapshots(
                root,
                datetime.fromisoformat("2026-08-20T00:00:00+00:00"),
            )
            self.assertEqual(count, 3)
            self.assertEqual(rows[0]["metrics"]["views"], 30)
            self.assertEqual(rows[0]["measurement_age_hours"], 30.0)

    def test_run_context_exposes_compact_account_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(
                root / run_context.PERFORMANCE_FEEDBACK_PATH,
                {
                    "generated_at": "2026-08-24T03:00:00+00:00",
                    "source_snapshot_count": 2,
                    "accounts": {
                        "PolymarketAlpha": {
                            "available": True,
                            "visible_post_count": 4,
                            "matched_post_count": 3,
                            "mature_post_count": 2,
                            "provisional_post_count": 1,
                            "republished_post_count": 1,
                            "baseline": {"median_views": 100},
                            "signals": [
                                {"dimension": "opening_type", "value": "direct fact", "direction": "ABOVE_BASELINE"}
                            ],
                            "recommendations": ["soft only"],
                            "top_mature_posts": [
                                {
                                    "story_key": "story-a",
                                    "metrics": {"views": 120},
                                    "relative_view_index": 1.2,
                                    "post_url": "https://x.com/example/status/1",
                                }
                            ],
                        }
                    },
                },
            )
            context = run_context.load_performance_feedback(
                root,
                "PolymarketAlpha",
                datetime.fromisoformat("2026-08-24T12:00:00+08:00"),
            )
            self.assertTrue(context["available"])
            self.assertEqual(context["republished_post_count"], 1)
            self.assertEqual(context["top_mature_posts"][0]["story_key"], "story-a")
            self.assertEqual(context["interpretation"], "observational_association_soft_tiebreaker_only")


if __name__ == "__main__":
    unittest.main()
