#!/usr/bin/env python3
"""Match visible X post metrics to PredX artifacts and build feedback context."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ACTIVE_STATUSES = {"READY", "REVIEW"}
MIN_MATCH_SCORE = 0.60
MIN_MATURE_AGE_HOURS = 24.0
MIN_GROUP_SAMPLE = 2
REPEATED_GROUP_SAMPLE = 4
REGULARIZATION_PRIOR_SAMPLE = 4.0
REGULARIZED_LIFT_UPPER = 1.12
REGULARIZED_LIFT_LOWER = 0.88
STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "been",
    "before",
    "but",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "more",
    "not",
    "now",
    "said",
    "says",
    "that",
    "the",
    "their",
    "they",
    "this",
    "was",
    "were",
    "while",
    "with",
}


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def blocks(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return parts if len(parts) > 1 else [line.strip() for line in text.splitlines() if line.strip()]


def normalize_chars(value: Any) -> str:
    text = str(value or "").casefold()
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE)


def meaningful_tokens(value: Any) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", str(value or "").casefold())
    return {token for token in tokens if len(token) >= 3 and token not in STOPWORDS}


def artifact_text(item: dict[str, Any]) -> str:
    return str(
        item.get("english")
        or item.get("english_post")
        or item.get("english_review")
        or item.get("content_en")
        or item.get("post_en")
        or ""
    ).strip()


def artifact_chinese(item: dict[str, Any]) -> str:
    return str(
        item.get("chinese")
        or item.get("chinese_post")
        or item.get("chinese_review")
        or item.get("content_zh")
        or item.get("post_zh")
        or ""
    ).strip()


def iter_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    # Historical manual and scheduled artifacts are single top-level objects,
    # while some newer batch artifacts wrap records in `items`.
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def artifact_date(path: Path, item: dict[str, Any]) -> str:
    for key in ("scheduled_at", "source_time", "published_at"):
        parsed = parse_time(item.get(key))
        if parsed:
            return parsed.date().isoformat()
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", str(path))
    return match.group(1) if match else ""


def load_artifacts(root: Path, cutoff: datetime) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    runtime_root = root / "runtime" / "predx-x-news-writer"
    for path in runtime_root.glob("**/*.json"):
        if "performance" in path.parts:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in iter_items(payload):
            account = str(item.get("account") or "")
            status = str(item.get("status") or "").upper()
            english = artifact_text(item)
            if not account or status not in ACTIVE_STATUSES or not english:
                continue
            date = artifact_date(path, item)
            if date:
                parsed_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
                if parsed_date < cutoff - timedelta(days=2):
                    continue
            english_blocks = blocks(english)
            chinese_blocks = blocks(artifact_chinese(item))
            artifacts.append(
                {
                    "account": account,
                    "status": status,
                    "artifact_file": str(path.relative_to(root)),
                    "artifact_date": date,
                    "story": str(item.get("story") or ""),
                    "story_key": str(item.get("story_key") or ""),
                    "topic_key": str(item.get("topic_key") or ""),
                    "opening_type": str(item.get("opening_type") or ""),
                    "evidence_path": str(item.get("evidence_path") or ""),
                    "ending_function": str(item.get("ending_function") or ""),
                    "style_fingerprint": str(item.get("style_fingerprint") or ""),
                    "block_count": len(chinese_blocks or english_blocks),
                    "opening_text_en": english_blocks[0] if english_blocks else "",
                    "ending_text_en": english_blocks[-1] if english_blocks else "",
                    "english": english,
                }
            )
    return artifacts


def safe_metric(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def load_snapshots(root: Path, cutoff: datetime) -> tuple[list[dict[str, Any]], int]:
    snapshots_dir = root / "runtime" / "predx-x-news-writer" / "performance" / "snapshots"
    selected_by_url: dict[str, dict[str, Any]] = {}
    snapshot_count = 0
    for path in sorted(snapshots_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        collected_at = parse_time(payload.get("collected_at"))
        if collected_at is None or collected_at < cutoff:
            continue
        snapshot_count += 1
        for account_payload in payload.get("accounts", []):
            if not isinstance(account_payload, dict):
                continue
            account = str(account_payload.get("account") or "")
            handle = str(account_payload.get("handle") or "")
            followers = safe_metric(account_payload.get("followers_visible"))
            for post in account_payload.get("posts", []):
                if not isinstance(post, dict):
                    continue
                url = str(post.get("url") or "")
                posted_at = parse_time(post.get("posted_at"))
                if not account or not url or posted_at is None or posted_at < cutoff:
                    continue
                metrics = post.get("metrics") if isinstance(post.get("metrics"), dict) else {}
                row = {
                    "account": account,
                    "handle": handle,
                    "followers_visible": followers,
                    "post_id": str(post.get("post_id") or ""),
                    "post_url": url,
                    "posted_at": posted_at.isoformat(),
                    "metrics_collected_at": collected_at.isoformat(),
                    "metrics": {
                        "views": safe_metric(metrics.get("views")),
                        "likes": safe_metric(metrics.get("likes")),
                        "reposts": safe_metric(metrics.get("reposts")),
                        "replies": safe_metric(metrics.get("replies")),
                    },
                    "visible_text": str(post.get("visible_text") or ""),
                    "is_reply": "replying to" in str(post.get("visible_text") or "").casefold(),
                    "snapshot_file": str(path.relative_to(root)),
                }
                observation_age = max((collected_at - posted_at).total_seconds() / 3600, 0.0)
                row["measurement_age_hours"] = round(observation_age, 2)
                previous = selected_by_url.get(url)
                if previous is None:
                    selected_by_url[url] = row
                    continue
                previous_age = float(previous.get("measurement_age_hours") or 0.0)
                row_is_mature = observation_age >= MIN_MATURE_AGE_HOURS
                previous_is_mature = previous_age >= MIN_MATURE_AGE_HOURS
                # Once repeated snapshots exist, compare posts using the first
                # public observation at or after 24 hours. Until then, retain
                # the newest provisional observation because it is closest to
                # the maturity boundary.
                if (row_is_mature and not previous_is_mature) or (
                    row_is_mature and previous_is_mature and observation_age < previous_age
                ) or (
                    not row_is_mature
                    and not previous_is_mature
                    and row["metrics_collected_at"] > previous["metrics_collected_at"]
                ):
                    selected_by_url[url] = row
    return list(selected_by_url.values()), snapshot_count


def match_score(post: dict[str, Any], artifact: dict[str, Any]) -> float:
    if post["account"] != artifact["account"] or post.get("is_reply"):
        return 0.0
    post_time = parse_time(post.get("posted_at"))
    if post_time and artifact.get("artifact_date"):
        artifact_day = datetime.fromisoformat(artifact["artifact_date"]).date()
        if abs((post_time.date() - artifact_day).days) > 2:
            return 0.0
    visible = str(post.get("visible_text") or "")
    english = artifact["english"]
    visible_norm = normalize_chars(visible)
    english_norm = normalize_chars(english)
    opening_norm = normalize_chars(artifact.get("opening_text_en"))
    if not visible_norm or not english_norm or not opening_norm:
        return 0.0
    opening_score = 1.0 if opening_norm in visible_norm else SequenceMatcher(None, opening_norm, visible_norm).ratio()
    artifact_tokens = meaningful_tokens(english)
    visible_tokens = meaningful_tokens(visible)
    token_coverage = len(artifact_tokens & visible_tokens) / len(artifact_tokens) if artifact_tokens else 0.0
    sequence_score = SequenceMatcher(None, english_norm[:1400], visible_norm[:1800]).ratio()
    return round((0.55 * opening_score) + (0.30 * token_coverage) + (0.15 * sequence_score), 4)


def match_posts(posts: list[dict[str, Any]], artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assignments: dict[int, tuple[int, float]] = {}
    for post_index, post in enumerate(posts):
        candidates = [
            (match_score(post, artifact), artifact_index)
            for artifact_index, artifact in enumerate(artifacts)
        ]
        score, artifact_index = max(candidates, default=(0.0, -1))
        if score >= MIN_MATCH_SCORE:
            assignments[post_index] = (artifact_index, score)

    rows: list[dict[str, Any]] = []
    for post_index, post in enumerate(posts):
        row = {key: value for key, value in post.items() if key != "visible_text"}
        assignment = assignments.get(post_index)
        if assignment is None:
            row.update(
                {
                    "match_status": "UNMATCHED",
                    "match_score": 0.0,
                    "match_reason": "EXCLUDED_REPLY" if post.get("is_reply") else "NO_ARTIFACT_ABOVE_THRESHOLD",
                }
            )
        else:
            artifact_index, score = assignment
            artifact = {key: value for key, value in artifacts[artifact_index].items() if key != "english"}
            row.update({"match_status": "MATCHED", "match_score": score, **artifact})
        rows.append(row)

    publications_by_artifact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("match_status") == "MATCHED":
            publications_by_artifact[str(row.get("artifact_file") or "")].append(row)
    for publications in publications_by_artifact.values():
        publications.sort(key=lambda row: str(row.get("posted_at") or ""))
        for index, row in enumerate(publications):
            row["artifact_publication_count"] = len(publications)
            row["analysis_eligible"] = index == 0
            if index > 0:
                row["analysis_exclusion_reason"] = "REPUBLISHED_ARTIFACT_INSTANCE"
    return rows


def has_any_term(value: str, terms: Iterable[str]) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", value) for term in terms)


def content_family(account: str, text: str) -> str:
    value = text.casefold()
    if account == "PolymarketAlpha":
        if has_any_term(value, ("bitcoin", "ethereum", "crypto", "etf", "solana", "stablecoin")):
            return "crypto_and_digital_assets"
        if has_any_term(value, ("inflation", "unemployment", "payroll", "borrowing", "cpi", "ons", "ecb survey")):
            return "macro_and_official_data"
        if has_any_term(value, ("yield", "bond", "buyback", "treasury")):
            return "rates_and_treasury"
        if has_any_term(value, ("oil", "brent", "tanker", "vlcc")):
            return "energy_and_shipping"
        if has_any_term(value, ("shares", "stake", "stock", "unicredit", "commerzbank", "ark")):
            return "public_companies_and_flows"
        return "financial_policy_and_other"
    if account == "PolyPredX":
        if has_any_term(value, ("election", "primary", "reelection", "vote", "ballot")):
            return "elections"
        if has_any_term(value, ("strike", "drone", "missile", "refinery", "killed", "injured", "attack")):
            return "conflict_operations"
        if has_any_term(value, ("peace", "diplomacy", "diplomatic", "talk", "talks", "ceasefire", "sanction", "sanctions", "dialogue")):
            return "diplomacy_and_sanctions"
        if has_any_term(value, ("court", "convicted", "ruling")):
            return "courts_and_legal_process"
        return "politics_and_security_policy"
    if account == "PredX_Labs":
        if has_any_term(value, ("signed", "signing", "signings", "transfer", "medical", "contract", "deal", "joins", "loan", "offer")):
            return "transfers_and_roster"
        if has_any_term(value, ("record", "attendance", "milestone")):
            return "records_and_milestones"
        if has_any_term(value, ("scored", "minute", "aggregate", "beat", "draw", "advance", "final")):
            return "matches_and_results"
        return "football_context_and_other"
    if account == "PredX_News":
        if has_any_term(value, ("ai", "model", "chip", "gpu")):
            return "ai_and_chips"
        if has_any_term(value, ("cyber", "breach", "security")):
            return "cybersecurity"
        return "technology_and_science"
    return "other"


def enrich_matches(rows: list[dict[str, Any]], now: datetime) -> None:
    for row in rows:
        posted_at = parse_time(row.get("posted_at"))
        measured_at = parse_time(row.get("metrics_collected_at"))
        age_hours = (
            max((measured_at - posted_at).total_seconds() / 3600, 0.0)
            if posted_at and measured_at
            else math.inf
        )
        metrics = row["metrics"]
        views = metrics["views"]
        engagement_count = metrics["likes"] + metrics["reposts"] + metrics["replies"]
        followers = row.get("followers_visible") or 0
        row["measurement_age_hours"] = round(age_hours, 2) if math.isfinite(age_hours) else None
        row["maturity"] = "MATURE" if age_hours >= MIN_MATURE_AGE_HOURS else "PROVISIONAL_UNDER_24H"
        row["engagement_count"] = engagement_count
        row["engagement_rate_per_100_views"] = round((engagement_count / views) * 100, 4) if views else 0.0
        row["views_per_follower"] = round(views / followers, 4) if followers else None
        if row.get("match_status") == "MATCHED":
            text = " ".join(
                (
                    row.get("story", ""),
                    row.get("topic_key", ""),
                    row.get("evidence_path", ""),
                    row.get("opening_text_en", ""),
                    row.get("ending_text_en", ""),
                )
            )
            row["content_family"] = content_family(row["account"], text)


def group_signal(
    rows: list[dict[str, Any]], dimension: str, baseline_views: float
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = str(row.get(dimension) or "").strip()
        if value:
            grouped[value].append(row)
    signals: list[dict[str, Any]] = []
    for value, group in grouped.items():
        if len(group) < MIN_GROUP_SAMPLE:
            continue
        group_median_views = float(median(row["metrics"]["views"] for row in group))
        group_median_er = float(median(row["engagement_rate_per_100_views"] for row in group))
        raw_lift = group_median_views / baseline_views if baseline_views else 0.0
        reliability_weight = len(group) / (len(group) + REGULARIZATION_PRIOR_SAMPLE)
        regularized_lift = 1.0 + ((raw_lift - 1.0) * reliability_weight)
        direction = (
            "ABOVE_BASELINE"
            if regularized_lift >= REGULARIZED_LIFT_UPPER
            else "BELOW_BASELINE"
            if regularized_lift <= REGULARIZED_LIFT_LOWER
            else "NEAR_BASELINE"
        )
        repeated = len(group) >= REPEATED_GROUP_SAMPLE
        soft_use = (
            "LIMITED_EXPERIMENT"
            if repeated and direction != "NEAR_BASELINE"
            else "MONITOR_ONLY"
            if not repeated
            else "CONTEXT_ONLY"
        )
        signals.append(
            {
                "dimension": dimension,
                "value": value,
                "sample_size": len(group),
                "median_views": round(group_median_views, 2),
                "median_engagement_rate_per_100_views": round(group_median_er, 4),
                "view_lift_vs_account_median": round(raw_lift, 3),
                "regularized_view_lift_vs_account_median": round(regularized_lift, 3),
                "reliability_weight": round(reliability_weight, 3),
                "direction": direction,
                "confidence": "MODERATE" if len(group) >= 4 else "DIRECTIONAL",
                "evidence_tier": "REPEATED" if repeated else "EARLY",
                "soft_use": soft_use,
                "interpretation": "associated_with_performance_not_proven_causal",
            }
        )
    return signals


def account_summary(account: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    account_rows = [row for row in rows if row["account"] == account]
    matched = [row for row in account_rows if row.get("match_status") == "MATCHED"]
    unmatched = [row for row in account_rows if row.get("match_status") == "UNMATCHED"]
    analysis_eligible = [row for row in matched if row.get("analysis_eligible", True)]
    mature = [row for row in analysis_eligible if row.get("maturity") == "MATURE"]
    provisional = [row for row in analysis_eligible if row.get("maturity") != "MATURE"]
    republished = [row for row in matched if not row.get("analysis_eligible", True)]
    unmatched_audit = [
        {
            "post_url": row.get("post_url"),
            "posted_at": row.get("posted_at"),
            "is_reply": row.get("is_reply", False),
            "match_reason": row.get("match_reason"),
            "metrics": row.get("metrics", {}),
        }
        for row in unmatched[:8]
    ]
    if not mature:
        return {
            "available": False,
            "reason": "NO_MATCHED_MATURE_POSTS",
            "visible_post_count": len(account_rows),
            "matched_post_count": len(matched),
            "unmatched_post_count": len(unmatched),
            "unmatched_posts": unmatched_audit,
            "mature_post_count": 0,
            "provisional_post_count": len(provisional),
            "republished_post_count": len(republished),
            "signals": [],
            "recent_posts": matched[:8],
        }
    baseline_views = float(median(row["metrics"]["views"] for row in mature))
    baseline_er = float(median(row["engagement_rate_per_100_views"] for row in mature))
    for row in mature:
        row["relative_view_index"] = round(row["metrics"]["views"] / baseline_views, 3) if baseline_views else 0.0
    signals: list[dict[str, Any]] = []
    for dimension in ("content_family", "opening_type", "ending_function", "block_count"):
        signals.extend(group_signal(mature, dimension, baseline_views))
    signals.sort(
        key=lambda signal: (
            signal["soft_use"] == "LIMITED_EXPERIMENT",
            abs(signal["regularized_view_lift_vs_account_median"] - 1),
            signal["sample_size"],
        ),
        reverse=True,
    )
    recommendations: list[str] = []
    experiment_signals = [signal for signal in signals if signal["soft_use"] == "LIMITED_EXPERIMENT"]
    above = next((signal for signal in experiment_signals if signal["direction"] == "ABOVE_BASELINE"), None)
    below = next((signal for signal in experiment_signals if signal["direction"] == "BELOW_BASELINE"), None)
    if above:
        recommendations.append(
            f"When two otherwise qualified candidates are close, run a limited test of {above['dimension']}={above['value']}; the regularized lift is {above['regularized_view_lift_vs_account_median']:.3f} from {above['sample_size']} mature posts, so do not favor it automatically."
        )
    if below:
        recommendations.append(
            f"Keep {below['dimension']}={below['value']} in normal rotation, but when an equally qualified alternative exists, test a variation; this is not an avoidance rule."
        )
    if not experiment_signals:
        recommendations.append(
            "No repeated regularized signal is strong enough for a limited experiment; keep the normal account profile and style rotation."
        )
    recommendations.append(
        "Performance is a soft tie-breaker after truth, freshness, account fit, duplication, sensitivity and source-quality gates."
    )
    return {
        "available": True,
        "visible_post_count": len(account_rows),
        "matched_post_count": len(matched),
        "unmatched_post_count": len(unmatched),
        "unmatched_posts": unmatched_audit,
        "mature_post_count": len(mature),
        "provisional_post_count": len(provisional),
        "republished_post_count": len(republished),
        "baseline": {
            "median_views": round(baseline_views, 2),
            "median_engagement_rate_per_100_views": round(baseline_er, 4),
            "maturity_threshold_hours": MIN_MATURE_AGE_HOURS,
        },
        "overfit_protection": {
            "decision_mode": "SOFT_EXPERIMENT_ONLY",
            "observational_signal_min_sample": MIN_GROUP_SAMPLE,
            "limited_experiment_min_sample": REPEATED_GROUP_SAMPLE,
            "regularization_prior_sample": REGULARIZATION_PRIOR_SAMPLE,
            "regularized_near_baseline_band": [REGULARIZED_LIFT_LOWER, REGULARIZED_LIFT_UPPER],
            "editorial_effect": "never_select_or_reject_a_candidate",
            "monitor_only_signal_count": sum(signal["soft_use"] == "MONITOR_ONLY" for signal in signals),
            "limited_experiment_signal_count": len(experiment_signals),
        },
        "signals": signals[:12],
        "recommendations": recommendations,
        "top_mature_posts": sorted(mature, key=lambda row: row["metrics"]["views"], reverse=True)[:6],
        "recent_posts": sorted(matched, key=lambda row: row["posted_at"], reverse=True)[:8],
    }


def build_feedback(root: Path, now: datetime, window_days: int) -> dict[str, Any]:
    cutoff = now - timedelta(days=window_days)
    posts, snapshot_count = load_snapshots(root, cutoff)
    artifacts = load_artifacts(root, cutoff)
    rows = match_posts(posts, artifacts)
    enrich_matches(rows, now)
    accounts = sorted({row["account"] for row in posts} | {artifact["account"] for artifact in artifacts})
    return {
        "schema_version": "predx-performance-feedback-v1",
        "generated_at": now.isoformat(),
        "window_days": window_days,
        "source_snapshot_count": snapshot_count,
        "visible_post_count": len(posts),
        "matched_post_count": sum(row.get("match_status") == "MATCHED" for row in rows),
        "unmatched_post_count": sum(row.get("match_status") == "UNMATCHED" for row in rows),
        "accounts": {account: account_summary(account, rows) for account in accounts},
        "guardrails": [
            "Visible public metrics are observational and do not prove why a post performed.",
            "Posts observed before 24 hours remain provisional and do not enter baselines or grouped signals.",
            "With repeated snapshots, the first public observation at or after 24 hours is used; a first-ever observation may be older and is labeled with its measurement age.",
            "A grouped observation needs at least two mature matched posts; groups with fewer than four remain monitor-only.",
            "View lift is shrunk toward the same-account baseline before any signal can support a limited experiment.",
            "A performance signal can propose only a reversible experiment; it never creates a candidate allowlist, denylist or quota.",
            "Multiple X posts matched to one artifact are retained for audit, but only the earliest publication instance enters grouped analysis.",
            "Performance never overrides truth, freshness, account fit, duplication, sensitivity or source-quality gates.",
            "Private analytics fields that were not visible are not inferred.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--now", required=True, help="ISO-8601 time with timezone")
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument(
        "--output",
        default="runtime/predx-x-news-writer/performance/feedback-latest.json",
    )
    args = parser.parse_args()
    now = parse_time(args.now)
    if now is None:
        print(json.dumps({"ok": False, "error": "--now requires an ISO-8601 timezone"}))
        return 2
    root = Path(args.root).resolve()
    payload = build_feedback(root, now, args.window_days)
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    write_json(output, payload)
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(output),
                "source_snapshot_count": payload["source_snapshot_count"],
                "visible_post_count": payload["visible_post_count"],
                "matched_post_count": payload["matched_post_count"],
                "unmatched_post_count": payload["unmatched_post_count"],
                "accounts": {
                    account: {
                        "available": summary["available"],
                        "matched_post_count": summary["matched_post_count"],
                        "mature_post_count": summary["mature_post_count"],
                    }
                    for account, summary in payload["accounts"].items()
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
