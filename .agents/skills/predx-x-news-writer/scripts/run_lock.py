#!/usr/bin/env python3
"""Project-wide lease lock for PredX editorial runs.

The lock serializes scheduled and manual runs that share project history and a
single signed-in Chrome/X session.  Each command takes a short OS file lock;
the long-lived ownership is represented by a token-protected renewable lease.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = "predx-run-lock-v1"
RESOURCE = "predx-x-news-writer:shared-editorial-run"
DEFAULT_LEASE_SECONDS = 45 * 60
MIN_LEASE_SECONDS = 60
MAX_LEASE_SECONDS = 4 * 60 * 60
LOCK_RELATIVE = Path("runtime/predx-x-news-writer/.locks/shared-run.lock")
GUARD_RELATIVE = Path("runtime/predx-x-news-writer/.locks/shared-run.guard")
AUDIT_RELATIVE = Path("runtime/predx-x-news-writer/.locks/shared-run-audit.jsonl")


class RunLockError(RuntimeError):
    """Raised for malformed or unsafe lock state."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def resolve_root(raw_root: str | Path) -> Path:
    root = Path(raw_root).expanduser().resolve()
    if not root.is_dir():
        raise RunLockError(f"project root is not a directory: {root}")
    if root == Path(root.anchor):
        raise RunLockError("refusing to use a filesystem root as the project root")
    return root


def validate_lease_seconds(value: int) -> int:
    if not MIN_LEASE_SECONDS <= value <= MAX_LEASE_SECONDS:
        raise RunLockError(
            f"lease seconds must be between {MIN_LEASE_SECONDS} and {MAX_LEASE_SECONDS}"
        )
    return value


def clean_label(value: str, field: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise RunLockError(f"{field} must not be empty")
    if len(cleaned) > 200:
        raise RunLockError(f"{field} is too long")
    return cleaned


def paths(root: Path) -> tuple[Path, Path, Path]:
    return root / LOCK_RELATIVE, root / GUARD_RELATIVE, root / AUDIT_RELATIVE


@contextmanager
def operation_guard(root: Path) -> Iterator[None]:
    _, guard_path, _ = paths(root)
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    if guard_path.exists() and guard_path.is_symlink():
        raise RunLockError(f"guard path must not be a symlink: {guard_path}")
    with guard_path.open("a+", encoding="utf-8") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(guard.fileno(), fcntl.LOCK_UN)


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)


def read_metadata(lock_dir: Path) -> dict[str, object]:
    if lock_dir.is_symlink() or not lock_dir.is_dir():
        raise RunLockError(f"lock path must be a real directory: {lock_dir}")
    metadata_path = lock_dir / "owner.json"
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunLockError(f"could not read lock metadata: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunLockError("lock metadata must be a JSON object")
    return payload


def public_metadata(payload: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"token"}
    }


def append_audit(root: Path, event: dict[str, object]) -> None:
    _, _, audit_path = paths(root)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema_version": SCHEMA_VERSION, **event}
    with audit_path.open("a", encoding="utf-8") as audit:
        audit.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def is_expired(payload: dict[str, object], now: datetime) -> bool:
    expires_at = parse_time(payload.get("expires_at"))
    return expires_at is not None and now >= expires_at


def incomplete_metadata(lock_dir: Path) -> dict[str, object]:
    observed_at = datetime.fromtimestamp(lock_dir.stat().st_mtime, timezone.utc)
    return {
        "schema_version": SCHEMA_VERSION,
        "resource": RESOURCE,
        "token_id": None,
        "owner": "UNKNOWN_INCOMPLETE_LOCK",
        "account": "UNKNOWN",
        "mode": "unknown",
        "acquired_at": isoformat(observed_at),
        "heartbeat_at": isoformat(observed_at),
        "lease_seconds": DEFAULT_LEASE_SECONDS,
        "expires_at": isoformat(observed_at + timedelta(seconds=DEFAULT_LEASE_SECONDS)),
        "metadata_state": "incomplete",
    }


def remove_exact_lock_directory(lock_dir: Path) -> None:
    """Remove a renamed stale/released lock without traversing subdirectories."""
    if lock_dir.is_symlink() or not lock_dir.is_dir():
        raise RunLockError(f"refusing to clean unsafe lock directory: {lock_dir}")
    for child in lock_dir.iterdir():
        if child.is_symlink() or not child.is_file():
            raise RunLockError(f"refusing to clean unexpected lock entry: {child}")
        child.unlink()
    lock_dir.rmdir()


def retire_lock(lock_dir: Path, reason: str) -> None:
    retired = lock_dir.parent / f".{lock_dir.name}.{reason}.{uuid.uuid4().hex}"
    os.replace(lock_dir, retired)
    remove_exact_lock_directory(retired)


def acquire(
    raw_root: str | Path,
    *,
    owner: str,
    account: str,
    mode: str,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    now: datetime | None = None,
) -> dict[str, object]:
    root = resolve_root(raw_root)
    owner = clean_label(owner, "owner")
    account = clean_label(account, "account")
    if mode not in {"manual", "scheduled"}:
        raise RunLockError("mode must be manual or scheduled")
    lease_seconds = validate_lease_seconds(lease_seconds)
    now = (now or utc_now()).astimezone(timezone.utc)
    lock_dir, _, _ = paths(root)

    with operation_guard(root):
        reclaimed: dict[str, object] | None = None
        if lock_dir.exists() or lock_dir.is_symlink():
            try:
                current = read_metadata(lock_dir)
            except RunLockError:
                current = incomplete_metadata(lock_dir)
            if not is_expired(current, now):
                expires_at = parse_time(current.get("expires_at"))
                retry_after = None
                if expires_at is not None:
                    retry_after = max(0, int((expires_at - now).total_seconds()))
                result = {
                    "ok": False,
                    "code": "SKIPPED_CONCURRENT_RUN",
                    "resource": RESOURCE,
                    "holder": public_metadata(current),
                    "retry_after_seconds": retry_after,
                }
                append_audit(
                    root,
                    {
                        "event": "acquire_busy",
                        "at": isoformat(now),
                        "request_owner": owner,
                        "request_account": account,
                        "request_mode": mode,
                        "holder_token_id": str(current.get("token", ""))[:8],
                    },
                )
                return result
            reclaimed = public_metadata(current)
            retire_lock(lock_dir, "stale")

        lock_dir.mkdir()
        token = uuid.uuid4().hex
        expires_at = now + timedelta(seconds=lease_seconds)
        payload: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "resource": RESOURCE,
            "token": token,
            "token_id": token[:8],
            "owner": owner,
            "account": account,
            "mode": mode,
            "acquired_at": isoformat(now),
            "heartbeat_at": isoformat(now),
            "lease_seconds": lease_seconds,
            "expires_at": isoformat(expires_at),
        }
        write_json_atomic(lock_dir / "owner.json", payload)
        append_audit(
            root,
            {
                "event": "acquired_after_stale_recovery" if reclaimed else "acquired",
                "at": isoformat(now),
                "owner": owner,
                "account": account,
                "mode": mode,
                "token_id": token[:8],
                "reclaimed_holder": reclaimed,
            },
        )
        return {"ok": True, "code": "ACQUIRED", **payload}


def heartbeat(
    raw_root: str | Path,
    *,
    token: str,
    lease_seconds: int | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    root = resolve_root(raw_root)
    token = clean_label(token, "token")
    now = (now or utc_now()).astimezone(timezone.utc)
    lock_dir, _, _ = paths(root)

    with operation_guard(root):
        if not lock_dir.exists():
            return {"ok": False, "code": "LOCK_NOT_FOUND", "resource": RESOURCE}
        payload = read_metadata(lock_dir)
        if payload.get("token") != token:
            return {
                "ok": False,
                "code": "LOCK_TOKEN_MISMATCH",
                "resource": RESOURCE,
                "holder": public_metadata(payload),
            }
        effective_lease = validate_lease_seconds(
            lease_seconds if lease_seconds is not None else int(payload.get("lease_seconds", 0))
        )
        payload["heartbeat_at"] = isoformat(now)
        payload["lease_seconds"] = effective_lease
        payload["expires_at"] = isoformat(now + timedelta(seconds=effective_lease))
        write_json_atomic(lock_dir / "owner.json", payload)
        append_audit(
            root,
            {
                "event": "heartbeat",
                "at": isoformat(now),
                "owner": payload.get("owner"),
                "account": payload.get("account"),
                "token_id": str(payload.get("token_id", "")),
            },
        )
        return {"ok": True, "code": "HEARTBEAT", **public_metadata(payload)}


def release(
    raw_root: str | Path,
    *,
    token: str,
    now: datetime | None = None,
) -> dict[str, object]:
    root = resolve_root(raw_root)
    token = clean_label(token, "token")
    now = (now or utc_now()).astimezone(timezone.utc)
    lock_dir, _, _ = paths(root)

    with operation_guard(root):
        if not lock_dir.exists():
            return {"ok": False, "code": "LOCK_NOT_FOUND", "resource": RESOURCE}
        payload = read_metadata(lock_dir)
        if payload.get("token") != token:
            return {
                "ok": False,
                "code": "LOCK_TOKEN_MISMATCH",
                "resource": RESOURCE,
                "holder": public_metadata(payload),
            }
        retire_lock(lock_dir, "released")
        append_audit(
            root,
            {
                "event": "released",
                "at": isoformat(now),
                "owner": payload.get("owner"),
                "account": payload.get("account"),
                "mode": payload.get("mode"),
                "token_id": str(payload.get("token_id", "")),
            },
        )
        return {
            "ok": True,
            "code": "RELEASED",
            "resource": RESOURCE,
            "owner": payload.get("owner"),
            "account": payload.get("account"),
        }


def status(raw_root: str | Path, *, now: datetime | None = None) -> dict[str, object]:
    root = resolve_root(raw_root)
    now = (now or utc_now()).astimezone(timezone.utc)
    lock_dir, _, _ = paths(root)
    with operation_guard(root):
        if not lock_dir.exists():
            return {"ok": True, "code": "FREE", "resource": RESOURCE}
        try:
            payload = read_metadata(lock_dir)
        except RunLockError:
            payload = incomplete_metadata(lock_dir)
        return {
            "ok": True,
            "code": (
                "STALE"
                if is_expired(payload, now)
                else "INCOMPLETE"
                if payload.get("metadata_state") == "incomplete"
                else "HELD"
            ),
            "resource": RESOURCE,
            "holder": public_metadata(payload),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire_parser = subparsers.add_parser("acquire")
    acquire_parser.add_argument("--root", required=True)
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--account", required=True)
    acquire_parser.add_argument("--mode", required=True, choices=("manual", "scheduled"))
    acquire_parser.add_argument("--lease-seconds", type=int, default=DEFAULT_LEASE_SECONDS)

    heartbeat_parser = subparsers.add_parser("heartbeat")
    heartbeat_parser.add_argument("--root", required=True)
    heartbeat_parser.add_argument("--token", required=True)
    heartbeat_parser.add_argument("--lease-seconds", type=int)

    release_parser = subparsers.add_parser("release")
    release_parser.add_argument("--root", required=True)
    release_parser.add_argument("--token", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--root", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "acquire":
            result = acquire(
                args.root,
                owner=args.owner,
                account=args.account,
                mode=args.mode,
                lease_seconds=args.lease_seconds,
            )
        elif args.command == "heartbeat":
            result = heartbeat(
                args.root,
                token=args.token,
                lease_seconds=args.lease_seconds,
            )
        elif args.command == "release":
            result = release(args.root, token=args.token)
        else:
            result = status(args.root)
    except (OSError, RunLockError, ValueError) as exc:
        result = {"ok": False, "code": "LOCK_ERROR", "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        return 4

    print(json.dumps(result, ensure_ascii=False))
    if result.get("ok"):
        return 0
    if result.get("code") == "SKIPPED_CONCURRENT_RUN":
        return 2
    return 3


if __name__ == "__main__":
    sys.exit(main())
