#!/usr/bin/env python3
"""Regression tests for manual-run cooldown after a recent HOLD."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("check_manual_cooldown.py")


class ManualCooldownTests(unittest.TestCase):
    def run_check(self, root: Path, now: str, *extra: str) -> tuple[int, dict]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(root),
                "--account",
                "PolymarketAlpha",
                "--now",
                now,
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode, json.loads(result.stdout)

    def make_hold(self, root: Path) -> None:
        payload = {
            "account": "PolymarketAlpha",
            "status": "HOLD",
            "story_key": "no-qualified-candidate",
            "source_time": "2026-08-27T01:10:00Z",
            "as_of": "2026-08-27T01:30:00Z",
        }
        (root / "alpha-output.json").write_text(json.dumps(payload), encoding="utf-8")

    def test_blocks_retry_inside_sixty_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_hold(root)
            code, payload = self.run_check(root, "2026-08-27T02:00:00Z")
            self.assertEqual(code, 3)
            self.assertEqual(payload["code"], "SKIPPED_MANUAL_COOLDOWN")
            self.assertEqual(payload["eligible_at"], "2026-08-27T02:30:00+00:00")

    def test_allows_retry_after_sixty_minutes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_hold(root)
            code, payload = self.run_check(root, "2026-08-27T02:30:00Z")
            self.assertEqual(code, 0)
            self.assertEqual(payload["code"], "MANUAL_COOLDOWN_CLEAR")

    def test_fresh_seed_can_override_cooldown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_hold(root)
            code, payload = self.run_check(
                root,
                "2026-08-27T02:00:00Z",
                "--override-reason",
                "fresh user seed",
            )
            self.assertEqual(code, 0)
            self.assertEqual(payload["code"], "MANUAL_COOLDOWN_OVERRIDDEN")


if __name__ == "__main__":
    unittest.main()
