#!/usr/bin/env python3
"""Regression tests for the project-wide PredX run lock."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import run_lock


BASE_TIME = datetime(2026, 8, 26, 1, 0, tzinfo=timezone.utc)


class RunLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def acquire(self, owner: str = "scheduled-alpha") -> dict[str, object]:
        return run_lock.acquire(
            self.root,
            owner=owner,
            account="PolymarketAlpha",
            mode="scheduled",
            now=BASE_TIME,
        )

    def test_second_run_is_rejected_across_account_and_mode(self) -> None:
        first = self.acquire()
        second = run_lock.acquire(
            self.root,
            owner="manual-labs",
            account="PredX_Labs",
            mode="manual",
            now=BASE_TIME + timedelta(minutes=1),
        )
        self.assertTrue(first["ok"])
        self.assertFalse(second["ok"])
        self.assertEqual(second["code"], "SKIPPED_CONCURRENT_RUN")
        self.assertEqual(second["holder"]["owner"], "scheduled-alpha")
        self.assertNotIn("token", second["holder"])

    def test_heartbeat_extends_lease_and_release_requires_token(self) -> None:
        first = self.acquire()
        wrong = run_lock.release(self.root, token="wrong-token", now=BASE_TIME)
        self.assertEqual(wrong["code"], "LOCK_TOKEN_MISMATCH")

        beat_at = BASE_TIME + timedelta(minutes=20)
        beat = run_lock.heartbeat(self.root, token=str(first["token"]), now=beat_at)
        self.assertEqual(beat["code"], "HEARTBEAT")
        self.assertEqual(
            beat["expires_at"],
            run_lock.isoformat(beat_at + timedelta(seconds=run_lock.DEFAULT_LEASE_SECONDS)),
        )

        released = run_lock.release(
            self.root,
            token=str(first["token"]),
            now=beat_at + timedelta(minutes=1),
        )
        self.assertEqual(released["code"], "RELEASED")
        self.assertEqual(run_lock.status(self.root)["code"], "FREE")

    def test_expired_lease_is_recovered_atomically(self) -> None:
        first = self.acquire()
        after_expiry = BASE_TIME + timedelta(seconds=run_lock.DEFAULT_LEASE_SECONDS + 1)
        second = run_lock.acquire(
            self.root,
            owner="scheduled-poly",
            account="PolyPredX",
            mode="scheduled",
            now=after_expiry,
        )
        self.assertTrue(second["ok"])
        self.assertEqual(second["code"], "ACQUIRED")
        self.assertNotEqual(first["token"], second["token"])
        audit_path = self.root / run_lock.AUDIT_RELATIVE
        events = [json.loads(line)["event"] for line in audit_path.read_text().splitlines()]
        self.assertIn("acquired_after_stale_recovery", events)

    def test_status_never_exposes_token(self) -> None:
        self.acquire()
        current = run_lock.status(self.root, now=BASE_TIME)
        self.assertEqual(current["code"], "HELD")
        self.assertNotIn("token", current["holder"])

    def test_incomplete_lock_is_busy_then_recoverable_after_expiry(self) -> None:
        lock_dir = self.root / run_lock.LOCK_RELATIVE
        lock_dir.mkdir(parents=True)
        observed_at = datetime.fromtimestamp(lock_dir.stat().st_mtime, timezone.utc)

        busy = run_lock.acquire(
            self.root,
            owner="manual-labs",
            account="PredX_Labs",
            mode="manual",
            now=observed_at + timedelta(minutes=1),
        )
        self.assertEqual(busy["code"], "SKIPPED_CONCURRENT_RUN")
        self.assertEqual(busy["holder"]["metadata_state"], "incomplete")

        recovered = run_lock.acquire(
            self.root,
            owner="manual-labs",
            account="PredX_Labs",
            mode="manual",
            now=observed_at + timedelta(seconds=run_lock.DEFAULT_LEASE_SECONDS + 1),
        )
        self.assertEqual(recovered["code"], "ACQUIRED")


if __name__ == "__main__":
    unittest.main()
