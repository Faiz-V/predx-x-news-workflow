from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "predx-x-news-writer" / "scripts"
EXAMPLES = ROOT / "examples"
NOW = "2026-08-11T09:30:00+08:00"


def run_json(*args: str) -> dict:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if not result.stdout:
        raise AssertionError(f"command produced no JSON output: {result.stderr}")
    payload = json.loads(result.stdout)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed with {result.returncode}:\n{result.stdout}\n{result.stderr}"
        )
    return payload


class CliWorkflowTests(unittest.TestCase):
    def test_ranker_routes_each_account(self) -> None:
        payload = run_json(
            str(SCRIPTS / "rank_candidates.py"),
            str(EXAMPLES / "news-packet.json"),
            "--now",
            NOW,
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(
            set(payload["ranked"]),
            {"PolymarketAlpha", "PolyPredX", "PredX_Labs", "PredX_News"},
        )
        self.assertTrue(all(payload["ranked"][account] for account in payload["ranked"]))
        self.assertEqual(payload["ranked"]["PolyPredX"][0]["id"], "geopolitics-briefing")

    def test_public_output_fixture_passes_lint(self) -> None:
        payload = run_json(
            str(SCRIPTS / "lint_output.py"),
            str(EXAMPLES / "sample-output.json"),
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["results"][0]["errors"], [])

    def test_history_context_detects_prior_story(self) -> None:
        payload = run_json(
            str(SCRIPTS / "build_run_context.py"),
            "--root",
            str(EXAMPLES),
            "--account",
            "PredX_News",
            "--now",
            NOW,
        )
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["ready_or_review_count_today"], 1)
        self.assertIn(
            "examplereproduciblemodelbenchmark",
            payload["blocked_story_keys"],
        )


if __name__ == "__main__":
    unittest.main()
