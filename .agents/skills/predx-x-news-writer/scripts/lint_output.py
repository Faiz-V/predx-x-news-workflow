#!/usr/bin/env python3
"""Validate structured PredX bilingual X drafts without external dependencies."""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_run_context import collect_history, derive_story_key, derive_topic_key, normalize_text, parse_time


ACCOUNTS = {"PolymarketAlpha", "PolyPredX", "PredX_Labs", "PredX_News"}
STATUSES = {"READY", "REVIEW", "HOLD"}
POST_MODES = {"reference_long", "standard_x"}
SELECTION_MODES = {"strict_x_news", "verified_market_brief"}
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
HASHTAG_RE = re.compile(r"(?<!\w)#[\w_]+", re.UNICODE)
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
DIGIT_RE = re.compile(r"\d+(?:[.,]\d+)*")
MARKET_RE = re.compile(
    r"\b(?:polymarket|prediction markets?|market probabilit(?:y|ies)|betting|bets?|wallet pnl)\b",
    re.IGNORECASE,
)
CLICHE_RE = re.compile(
    r"\b(?:share your thoughts|stay tuned|drop your thoughts|comment below)\b",
    re.IGNORECASE,
)
NEXT_ZH_RE = re.compile(r"^(?:接下来|下一步|下一个(?:信号|看点|节点))")
NEXT_EN_RE = re.compile(r"^(?:next\b|the next (?:signal|step|test|catalyst)\b|what happens next\b)", re.IGNORECASE)
BARE_QUESTION_RE = re.compile(r"^(?:what do you think|your thoughts|你怎么看|怎么看)[？?]?$", re.IGNORECASE)
ALPHA_CHINA_RE = re.compile(
    r"(?:"
    r"中国|中国人民银行|人民银行|人民币|北京|上海|深圳|香港|澳门|恒生|沪深|A股|"
    r"阿里巴巴|腾讯|百度|京东|美团|拼多多|小米|华为|比亚迪|宁德时代|"
    r"\bChina(?:'s)?\b|\bChinese\b|\bPRC\b|\bPBOC\b|People's Bank of China|"
    r"\brenminbi\b|\byuan\b|\bBeijing\b|\bShanghai\b|\bShenzhen\b|"
    r"\bHong Kong\b|\bMacau\b|\bHang Seng\b|\bCSI\s*300\b|\bA-shares?\b|"
    r"\bAlibaba\b|\bTencent\b|\bBaidu\b|\bJD\.com\b|\bMeituan\b|\bPinduoduo\b|"
    r"\bXiaomi\b|\bHuawei\b|\bBYD\b|\bCATL\b"
    r")",
    re.IGNORECASE,
)
ALPHA_FORBIDDEN_TIMEZONE_RE = re.compile(
    r"(?:"
    r"\bUTC\s*[+-]\s*\d{1,2}(?::?\d{2})?\b|"
    r"\bGMT(?:\s*[+-]\s*\d{1,2}(?::?\d{2})?)?\b|"
    r"\b(?:CST|ET|EST|EDT|CET|CEST|BST)\b|"
    r"Eastern Time|Central European Time|British Summer Time|"
    r"北京时间|中国标准时间"
    r")",
    re.IGNORECASE,
)
ALPHA_CLOCK_TIME_RE = re.compile(
    r"(?:"
    r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?:\s*(?:a\.?m\.?|p\.?m\.?))?|"
    r"(?<!\d)(?:1[0-2]|[1-9])\s*(?:a\.?m\.?|p\.?m\.?)\b|"
    r"(?<!\d)(?:[01]?\d|2[0-3])(?:时|点)(?:[0-5]?\d分)?"
    r")",
    re.IGNORECASE,
)
UTC_LABEL_RE = re.compile(r"(?<![A-Za-z])UTC(?![A-Za-z])", re.IGNORECASE)
ALPHA_INTERNAL_PROCESS_ZH_RE = re.compile(
    r"(?:截至)?(?:本轮|本次)(?:采集|抓取|核验|审计)(?:时|期间)?"
)
ALPHA_INTERNAL_PROCESS_EN_RE = re.compile(
    r"\b(?:at|as of)\s+(?:(?:this|the)\s+)?(?:collection(?:\s+time)?|run|snapshot|audit)\b",
    re.IGNORECASE,
)
ENDING_FAMILY_PATTERNS = (
    ("next-step", re.compile(r"^(?:接下来|下一步|下一个(?:信号|节点|看点)|next\b|the next\b|what happens next)", re.IGNORECASE)),
    ("test-whether", re.compile(r"^(?:真正的考验|考验在于|能否|是否|the test is|the question is whether|whether\b)", re.IGNORECASE)),
    ("key-is", re.compile(r"^(?:关键在于|问题在于|真正的变量|what matters now|the key is|the real variable)", re.IGNORECASE)),
    ("meaning", re.compile(r"^(?:这意味着|这使得|这让|this means|this leaves|that means)", re.IGNORECASE)),
    ("whether-depends", re.compile(r"(?:能否|whether).*(?:取决于|决定|depends|will decide)", re.IGNORECASE)),
    ("not-but", re.compile(r"^(?:这不是.*而是|this is not.*(?:it is|but))", re.IGNORECASE)),
)

FORMAT_RANGES = {
    "explained_news": {
        "zh_target": (170, 260),
        "zh_limit": (150, 320),
        "en_target": (380, 650),
        "en_limit": (320, 800),
        "blocks": (4, 6),
    },
    "fast_breaking": {
        "zh_target": (140, 220),
        "zh_limit": (120, 270),
        "en_target": (300, 520),
        "en_limit": (260, 650),
        "blocks": (4, 5),
    },
    "data_stack": {
        "zh_target": (150, 260),
        "zh_limit": (130, 300),
        "en_target": (340, 620),
        "en_limit": (280, 750),
        "blocks": (5, 8),
    },
    "claim_response": {
        "zh_target": (190, 300),
        "zh_limit": (170, 340),
        "en_target": (430, 720),
        "en_limit": (380, 850),
        "blocks": (5, 6),
    },
}


def weighted_length(text: str) -> int:
    """Approximate X weighted length: URLs=23, basic chars=1, wide chars=2."""
    total = 0
    cursor = 0
    for match in URL_RE.finditer(text):
        total += sum(1 if ord(ch) <= 0x10FF else 2 for ch in text[cursor : match.start()])
        total += 23
        cursor = match.end()
    total += sum(1 if ord(ch) <= 0x10FF else 2 for ch in text[cursor:])
    return total


def visible_zh_length(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def content_blocks(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    blocks = [part.strip() for part in re.split(r"\n\s*\n", stripped) if part.strip()]
    if len(blocks) == 1 and "\n" in stripped:
        lines = [line.strip() for line in stripped.splitlines() if line.strip()]
        if len(lines) > 1:
            return lines
    return blocks


def sentence_count(text: str) -> int:
    if not text.strip():
        return 0
    if CHINESE_RE.search(text):
        endings = re.findall(r"[。！？!?]+", text)
        return max(1, len(endings))
    cleaned = re.sub(r"\b(?:U\.S|U\.K|e\.g|i\.e)\.", "abbr", text, flags=re.IGNORECASE)
    endings = re.findall(r"[.!?]+(?:[\"'”’)]*)?(?=\s|$)", cleaned)
    return max(1, len(endings))


def in_range(value: int, bounds: tuple[int, int]) -> bool:
    return bounds[0] <= value <= bounds[1]


def numeric_alignment_warnings(chinese: str, english: str) -> list[str]:
    warnings: list[str] = []
    zh_blocks = content_blocks(chinese)
    en_blocks = content_blocks(english)
    if len(zh_blocks) != len(en_blocks):
        return warnings
    for index, (zh_block, en_block) in enumerate(zip(zh_blocks, en_blocks), 1):
        zh_count = len(DIGIT_RE.findall(zh_block))
        en_count = len(DIGIT_RE.findall(en_block))
        if zh_count != en_count:
            warnings.append(
                f"block {index} has {zh_count} Chinese numeric token(s) and {en_count} English numeric token(s); verify alignment"
            )
    return warnings


def alpha_timezone_errors(item: dict[str, Any], chinese: str, english: str) -> list[str]:
    errors: list[str] = []
    if item.get("audience_timezone") != "UTC":
        errors.append('PolymarketAlpha READY/REVIEW items require audience_timezone: "UTC"')

    for language, body in (("Chinese", chinese), ("English", english)):
        forbidden = ALPHA_FORBIDDEN_TIMEZONE_RE.search(body)
        if forbidden:
            errors.append(
                f"PolymarketAlpha {language} copy uses forbidden non-UTC timezone '{forbidden.group(0)}'"
            )
        for block_index, block in enumerate(content_blocks(body), 1):
            if ALPHA_CLOCK_TIME_RE.search(block) and not UTC_LABEL_RE.search(block):
                errors.append(
                    f"PolymarketAlpha {language} block {block_index} has a clock time without an explicit UTC label"
                )

    internal_zh = ALPHA_INTERNAL_PROCESS_ZH_RE.search(chinese)
    if internal_zh:
        errors.append(
            f"PolymarketAlpha Chinese copy exposes internal collection/audit language '{internal_zh.group(0)}'; use natural reader-facing wording such as '截至目前'"
        )
    internal_en = ALPHA_INTERNAL_PROCESS_EN_RE.search(english)
    if internal_en:
        errors.append(
            f"PolymarketAlpha English copy exposes internal collection/audit language '{internal_en.group(0)}'; use natural reader-facing wording such as 'currently'"
        )

    timestamp_fields: list[tuple[str, Any]] = [
        ("source_time", item.get("source_time")),
        ("source_published_at", item.get("source_published_at")),
        ("published_at", item.get("published_at")),
        ("disclosure_time", item.get("disclosure_time")),
    ]
    event_time = item.get("event_time")
    if event_time and parse_time(event_time) is not None:
        timestamp_fields.append(("event_time", event_time))

    signal = item.get("x_signal") if isinstance(item.get("x_signal"), dict) else {}
    for key in (
        "posted_at",
        "first_seen_at",
        "metrics_collected_at",
        "final_refresh_at",
        "latest_fresh_echo_at",
    ):
        timestamp_fields.append((f"x_signal.{key}", signal.get(key)))

    first_snapshot = signal.get("first_snapshot")
    if isinstance(first_snapshot, dict):
        timestamp_fields.append(
            ("x_signal.first_snapshot.collected_at", first_snapshot.get("collected_at"))
        )
    measurement_history = signal.get("measurement_history")
    if isinstance(measurement_history, list):
        for history_index, measurement in enumerate(measurement_history, 1):
            if isinstance(measurement, dict):
                timestamp_fields.append(
                    (
                        f"x_signal.measurement_history[{history_index}].collected_at",
                        measurement.get("collected_at"),
                    )
                )

    for field, value in timestamp_fields:
        if value in (None, ""):
            continue
        parsed = parse_time(value)
        if parsed is None:
            errors.append(f"PolymarketAlpha {field} must be an ISO-8601 timestamp with timezone")
        elif parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            errors.append(f"PolymarketAlpha {field} must be normalized to UTC")
    return errors


def load_payload(path: str | None) -> Any:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    return json.loads(raw)


def as_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Expected a JSON object, array, or object containing an items array")


def get_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if item.get(key) is not None:
            return str(item[key]).strip()
    return ""


def fingerprint_parts(item: dict[str, Any]) -> tuple[str, str, str]:
    opening = str(item.get("opening_type", "")).strip().lower()
    evidence = str(item.get("evidence_path", "")).strip().lower()
    ending = str(item.get("ending_function", "")).strip().lower()
    fingerprint = str(item.get("style_fingerprint", item.get("style", ""))).strip()
    if fingerprint:
        parts = [part.strip().lower() for part in fingerprint.split("/")]
        opening = opening or (parts[0] if len(parts) > 0 else "")
        evidence = evidence or (parts[1] if len(parts) > 1 else "")
        ending = ending or (parts[2] if len(parts) > 2 else "")
    return opening, evidence, ending


def actual_ending(item: dict[str, Any]) -> tuple[str, str]:
    chinese = get_text(item, "chinese", "chinese_post", "chinese_review")
    english = get_text(item, "english", "english_post")
    zh_blocks = content_blocks(chinese)
    en_blocks = content_blocks(english)
    zh_last = zh_blocks[-1].strip() if zh_blocks else ""
    en_last = en_blocks[-1].strip() if en_blocks else ""
    if NEXT_ZH_RE.search(zh_last) or NEXT_EN_RE.search(en_last):
        return "next-step", zh_last or en_last
    if zh_last.endswith(("？", "?")) or en_last.endswith("?"):
        return "question", zh_last or en_last
    return "other", zh_last or en_last


def text_units(value: str) -> set[str]:
    normalized = normalize_text(value)
    if not normalized:
        return set()
    if CHINESE_RE.search(value):
        if len(normalized) == 1:
            return {normalized}
        return {normalized[index : index + 2] for index in range(len(normalized) - 1)}
    words = re.findall(r"[a-z0-9]+", value.casefold())
    if len(words) <= 1:
        return set(words)
    return {" ".join(words[index : index + 2]) for index in range(len(words) - 1)}


def text_similarity(left: str, right: str) -> float:
    left_units = text_units(left)
    right_units = text_units(right)
    if not left_units or not right_units:
        return 0.0
    return 2 * len(left_units & right_units) / (len(left_units) + len(right_units))


def ending_phrase_family(value: str) -> str:
    stripped = value.strip()
    for name, pattern in ENDING_FAMILY_PATTERNS:
        if pattern.search(stripped):
            return name
    return ""


def apply_history_checks(
    item: dict[str, Any],
    result: dict[str, Any],
    history_root: Path,
    as_of: datetime,
    candidate_path: Path | None,
    lookback_days: int,
) -> None:
    if result["status"] == "HOLD" or result["account"] not in ACCOUNTS:
        result["history_compared"] = 0
        return

    history = collect_history(
        history_root,
        result["account"],
        as_of,
        lookback_days=lookback_days,
        exclude_path=candidate_path,
    )
    active = [row for row in history if row["status"] in {"READY", "REVIEW"}]
    same_day = [row for row in active if row["run_date"] == as_of.date().isoformat()]
    result["history_compared"] = len(active)

    candidate_story_key = derive_story_key(item)
    candidate_topic_key = derive_topic_key(item)
    candidate_story = str(item.get("story") or "")
    candidate_sources = {str(url) for url in item.get("sources", []) if isinstance(url, str)}
    chinese_blocks = content_blocks(get_text(item, "chinese", "chinese_post", "chinese_review"))
    opening = chinese_blocks[0] if chinese_blocks else ""
    ending = chinese_blocks[-1] if chinese_blocks else ""
    candidate_series_key = (
        normalize_text(item.get("series_key"))
        if result["account"] == "PolymarketAlpha"
        else ""
    )
    candidate_observation_period = str(item.get("observation_period") or "").strip()
    series_update = bool(
        candidate_series_key
        and candidate_observation_period
        and get_text(item, "material_new_fact")
    )
    follow_up = bool(item.get("follow_up_to") and item.get("material_new_fact")) or series_update

    if str(item.get("selection_mode") or "strict_x_news") == "verified_market_brief":
        prior_fallback = next(
            (row for row in same_day if row.get("selection_mode") == "verified_market_brief"),
            None,
        )
        if prior_fallback:
            result["errors"].append(
                f"only one verified_market_brief is allowed per account per day; already used in {prior_fallback['file']}"
            )

    if candidate_series_key:
        for row in active:
            if candidate_series_key != row.get("series_key"):
                continue
            if candidate_observation_period == row.get("observation_period"):
                result["errors"].append(
                    f"series observation '{candidate_series_key}' for period '{candidate_observation_period}' already used in {row['file']}"
                )
                break
            if row in same_day:
                result["errors"].append(
                    f"series '{candidate_series_key}' already used today in {row['file']}; limit recurring series to one item per day"
                )
                break

    for row in active:
        same_story_key = bool(candidate_story_key and candidate_story_key == row["story_key"])
        story_similarity = text_similarity(candidate_story, row["story"])
        shared_sources = candidate_sources & set(row["sources"])
        if same_story_key or story_similarity >= 0.82 or (shared_sources and story_similarity >= 0.50):
            message = f"probable repeated story versus {row['file']}: {row['story']}"
            if follow_up:
                result["warnings"].append(message + "; verify the declared material_new_fact")
            else:
                result["errors"].append(message)
            break

    if candidate_topic_key and not follow_up:
        for row in active:
            if candidate_topic_key == row.get("topic_key"):
                result["errors"].append(
                    f"topic series '{candidate_topic_key}' already used recently in {row['file']}; require a material new development"
                )
                break

    for row in active:
        opening_similarity = text_similarity(opening, row["opening_text"])
        if opening_similarity >= 0.88:
            result["errors"].append(
                f"opening wording is too similar to {row['file']} ({opening_similarity:.2f})"
            )
            break

    candidate_family = ending_phrase_family(ending)
    for row in same_day:
        ending_similarity = text_similarity(ending, row["ending_text"])
        prior_family = ending_phrase_family(row["ending_text"])
        if ending_similarity >= 0.62:
            result["errors"].append(
                f"ending wording is too similar to same-day draft {row['file']} ({ending_similarity:.2f})"
            )
            break
        if candidate_family and candidate_family == prior_family:
            result["errors"].append(
                f"ending phrase family '{candidate_family}' repeats same-day draft {row['file']}"
            )
            break


def lint_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    account = str(item.get("account", ""))
    status = str(item.get("status", ""))
    mode = str(item.get("post_mode", "reference_long"))
    variant = str(item.get("format_variant", "explained_news"))
    english = get_text(item, "english", "english_post")
    chinese = get_text(item, "chinese", "chinese_post", "chinese_review")
    sources = item.get("sources", [])
    source_time = get_text(item, "source_time", "published_at")
    x_signal = item.get("x_signal") if isinstance(item.get("x_signal"), dict) else {}
    trend_status = str(item.get("trend_status") or x_signal.get("trend_status") or "").upper()
    selection_mode = str(item.get("selection_mode") or "strict_x_news")
    allow_fallback = item.get("allow_news_platform_fallback") is True
    zh_blocks = content_blocks(chinese)
    en_blocks = content_blocks(english)
    zh_length = visible_zh_length(chinese)
    en_length = len(english)
    zh_sentence_counts = [sentence_count(block) for block in zh_blocks]
    en_sentence_counts = [sentence_count(block) for block in en_blocks]

    if account not in ACCOUNTS:
        errors.append(f"unknown account: {account or '<missing>'}")
    if status not in STATUSES:
        errors.append(f"invalid status: {status or '<missing>'}")
    if mode not in POST_MODES:
        errors.append(f"invalid post_mode: {mode or '<missing>'}")
    if selection_mode not in SELECTION_MODES:
        errors.append(f"invalid selection_mode: {selection_mode or '<missing>'}")
    if not isinstance(sources, list) or not sources:
        errors.append("at least one source URL is required")
    elif any(not isinstance(source, str) or not URL_RE.fullmatch(source.strip()) for source in sources):
        errors.append("every source must be a direct HTTP(S) URL")
    if not source_time:
        errors.append("source_time or published_at is required")

    fallback_requested = allow_fallback or selection_mode == "verified_market_brief"
    if fallback_requested:
        if account != "PolymarketAlpha":
            errors.append("verified market brief fallback is currently authorized only for PolymarketAlpha")
        if not (allow_fallback and selection_mode == "verified_market_brief"):
            errors.append(
                'verified market brief requires allow_news_platform_fallback: true and selection_mode: "verified_market_brief"'
            )
        if not get_text(item, "fallback_reason"):
            errors.append("verified_market_brief requires a fallback_reason")
        if trend_status not in {"HOT", "WARM", "UNPROVEN"}:
            errors.append("verified_market_brief requires an explicit HOT, WARM, or UNPROVEN X signal")
        verification_status = str(item.get("verification_status") or "")
        if verification_status not in {"primary", "multi_source", "single_reputable"}:
            errors.append(
                "verified_market_brief requires verification_status primary, multi_source, or single_reputable"
            )
        if status == "READY" and verification_status == "single_reputable":
            errors.append("single_reputable verified_market_brief must remain REVIEW")
        try:
            impact_score = float(item.get("impact_score"))
        except (TypeError, ValueError):
            errors.append("verified_market_brief requires numeric impact_score")
        else:
            if impact_score < 6 or impact_score > 10:
                errors.append("verified_market_brief impact_score must be between 6 and 10")
        try:
            source_age_minutes = float(item.get("source_age_minutes"))
        except (TypeError, ValueError):
            errors.append("verified_market_brief requires numeric source_age_minutes")
        else:
            if source_age_minutes < 0 or source_age_minutes > 720:
                errors.append("verified_market_brief source_age_minutes must be between 0 and 720")

    if item.get("scheduled_run") and status != "HOLD":
        if not get_text(item, "story_key"):
            errors.append("scheduled READY/REVIEW items require a stable story_key for duplicate checks")
        if not get_text(item, "topic_key"):
            errors.append("scheduled READY/REVIEW items require a stable topic_key for recent-series checks")
        if not fallback_requested:
            if selection_mode != "strict_x_news":
                errors.append('strict scheduled items require selection_mode: "strict_x_news"')
            if trend_status not in {"HOT", "WARM"}:
                errors.append("scheduled READY/REVIEW items require a HOT or WARM X signal")
            if not x_signal.get("post_url") or not x_signal.get("posted_at"):
                errors.append("scheduled READY/REVIEW items require X post URL and timestamp")

    if status != "HOLD" and account == "PolymarketAlpha":
        series_values = {
            "series_key": get_text(item, "series_key"),
            "observation_period": get_text(item, "observation_period"),
            "material_new_fact": get_text(item, "material_new_fact"),
        }
        if any(series_values.values()) and not all(series_values.values()):
            errors.append(
                "series updates require series_key, observation_period, and material_new_fact together"
            )

    if status == "REVIEW" and not get_text(item, "review_item", "editorial_caveat"):
        errors.append("REVIEW items require an exact review_item")
    if status == "HOLD" and not get_text(item, "hold_reason", "editorial_caveat"):
        errors.append("HOLD items require a hold_reason")

    if status == "HOLD":
        if chinese or english:
            errors.append("HOLD items must omit both Chinese and English post bodies")
    else:
        if account == "PolymarketAlpha":
            if item.get("audience_region") != "US_EU":
                errors.append('PolymarketAlpha READY/REVIEW items require audience_region: "US_EU"')
            if item.get("china_related") is not False:
                errors.append("PolymarketAlpha READY/REVIEW items require china_related: false")
            alpha_selection_text = "\n".join(
                [get_text(item, "story", "subject"), chinese, english]
            )
            if ALPHA_CHINA_RE.search(alpha_selection_text):
                errors.append(
                    "PolymarketAlpha China hard gate failed: selected story or post body is China-related"
                )
            errors.extend(alpha_timezone_errors(item, chinese, english))
        if not chinese:
            errors.append("READY/REVIEW items require a Chinese mother draft")
        if not english:
            errors.append("READY/REVIEW items require English publication copy")
        if chinese and english:
            if len(zh_blocks) != len(en_blocks):
                errors.append(
                    f"bilingual block mismatch: Chinese has {len(zh_blocks)}, English has {len(en_blocks)}"
                )
            warnings.extend(numeric_alignment_warnings(chinese, english))
            zh_multi = [i for i, count in enumerate(zh_sentence_counts, 1) if count > 1]
            en_multi = [i for i, count in enumerate(en_sentence_counts, 1) if count > 1]
            if any(count > 2 for count in zh_sentence_counts + en_sentence_counts):
                errors.append("a content block contains more than two sentences")
            if len(zh_multi) > 1 or len(en_multi) > 1:
                warnings.append(
                    "multiple multi-sentence blocks detected; default to one sentence per block"
                )
            if zh_blocks and visible_zh_length(zh_blocks[0]) > 36:
                warnings.append("Chinese opening exceeds the preferred 36-character title length")
            if en_blocks and len(en_blocks[0]) > 90:
                warnings.append("English opening exceeds the preferred 90-character title length")
            long_zh = [i for i, block in enumerate(zh_blocks[1:], 2) if visible_zh_length(block) > 75]
            long_en = [i for i, block in enumerate(en_blocks[1:], 2) if len(block) > 160]
            if long_zh:
                warnings.append("long Chinese block(s): " + ", ".join(map(str, long_zh)))
            if long_en:
                warnings.append("long English block(s): " + ", ".join(map(str, long_en)))

            just_in = zh_blocks[0].upper().startswith("JUST IN:") or en_blocks[0].upper().startswith("JUST IN:")
            if fallback_requested and just_in:
                errors.append("verified_market_brief must not use a JUST IN opening")
            source_age = item.get("source_age_minutes")
            if just_in and source_age is not None:
                try:
                    if float(source_age) > 60:
                        errors.append("JUST IN opening requires a source no more than 60 minutes old")
                except (TypeError, ValueError):
                    warnings.append("source_age_minutes is not numeric; verify JUST IN freshness manually")

        if mode == "standard_x" and english:
            length = weighted_length(english)
            if length > 280:
                errors.append(f"standard_x English weighted length is {length}, above 280")

        if mode == "reference_long" and chinese and english:
            rules = FORMAT_RANGES.get(variant)
            if rules is None:
                warnings.append(f"unknown format_variant '{variant}'; using explained_news ranges")
                rules = FORMAT_RANGES["explained_news"]
            if not in_range(zh_length, rules["zh_limit"]):
                errors.append(
                    f"Chinese length {zh_length} is outside acceptable {rules['zh_limit'][0]}–{rules['zh_limit'][1]} for {variant}"
                )
            elif not in_range(zh_length, rules["zh_target"]):
                warnings.append(
                    f"Chinese length {zh_length} is outside target {rules['zh_target'][0]}–{rules['zh_target'][1]} for {variant}"
                )
            if not in_range(en_length, rules["en_limit"]):
                errors.append(
                    f"English length {en_length} is outside acceptable {rules['en_limit'][0]}–{rules['en_limit'][1]} for {variant}"
                )
            elif not in_range(en_length, rules["en_target"]):
                warnings.append(
                    f"English length {en_length} is outside target {rules['en_target'][0]}–{rules['en_target'][1]} for {variant}"
                )
            if not in_range(len(zh_blocks), rules["blocks"]):
                errors.append(
                    f"Chinese block count {len(zh_blocks)} is outside {rules['blocks'][0]}–{rules['blocks'][1]} for {variant}"
                )

        if english:
            hashtag_count = len(HASHTAG_RE.findall(english))
            if hashtag_count > 1:
                errors.append(f"English copy has {hashtag_count} hashtags; maximum is 1")
            if CHINESE_RE.search(english):
                errors.append("English publication copy contains Chinese characters")
            if URL_RE.search(english) and not item.get("allow_in_post_url", False):
                errors.append("English publication copy contains a URL; keep sources outside the body")
            if MARKET_RE.search(english) and not item.get("allow_prediction_market_reference", False):
                warnings.append("public copy directly references prediction-market or betting language")
            if CLICHE_RE.search(english):
                warnings.append("generic engagement CTA detected; remove unless editorially necessary")
            if en_blocks and BARE_QUESTION_RE.fullmatch(en_blocks[-1].strip()):
                warnings.append("bare engagement question detected; name the real subject or tradeoff")
        if chinese and URL_RE.search(chinese) and not item.get("allow_in_post_url", False):
            errors.append("Chinese mother draft contains a URL; keep sources outside the body")
        if zh_blocks and BARE_QUESTION_RE.fullmatch(zh_blocks[-1].strip()):
            warnings.append("bare engagement question detected; name the real subject or tradeoff")

        if not item.get("style_fingerprint") and not item.get("style"):
            warnings.append("missing style fingerprint; non-template batch checks will be limited")

    return {
        "index": index,
        "account": account,
        "status": status,
        "post_mode": mode,
        "format_variant": variant,
        "source_time": source_time,
        "trend_status": trend_status or None,
        "selection_mode": selection_mode,
        "audience_timezone": item.get("audience_timezone"),
        "chinese_length": zh_length,
        "english_length": en_length,
        "weighted_english_length": weighted_length(english) if english else 0,
        "chinese_blocks": len(zh_blocks),
        "english_blocks": len(en_blocks),
        "chinese_sentence_counts": zh_sentence_counts,
        "english_sentence_counts": en_sentence_counts,
        "hashtag_count": len(HASHTAG_RE.findall(english)) if english else 0,
        "errors": errors,
        "warnings": warnings,
    }


def lint_batch(items: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    active = [item for item in items if str(item.get("status", "")) != "HOLD"]
    accounts = [str(item.get("account", "")) for item in items]

    duplicates = [name for name, count in collections.Counter(accounts).items() if name and count > 1]
    if duplicates:
        errors.append("duplicate account entries: " + ", ".join(sorted(duplicates)))
    if len(items) == 4 and set(accounts) != ACCOUNTS:
        errors.append("a four-item batch must contain each account exactly once")

    fingerprints = [fingerprint_parts(item) for item in active]
    openings = [parts[0] for parts in fingerprints if parts[0]]
    evidence_paths = [parts[1] for parts in fingerprints if parts[1]]
    endings = [parts[2] for parts in fingerprints if parts[2]]
    actual_endings = [actual_ending(item) for item in active]

    for label, values in (("opening type", openings), ("evidence path", evidence_paths)):
        overused = [value for value, count in collections.Counter(values).items() if count > 2]
        if overused:
            errors.append(f"{label} used more than twice: " + ", ".join(sorted(overused)))

    if len(active) >= 4:
        if len(set(evidence_paths)) < 3 and len(evidence_paths) == len(active):
            warnings.append("four-account batch uses fewer than three evidence paths")
        if len(set(endings)) < 2 and len(endings) == len(active):
            warnings.append("four-account batch uses only one ending function")
        block_counts = [result["chinese_blocks"] for result in results if result["status"] != "HOLD"]
        if block_counts and len(set(block_counts)) < 2:
            warnings.append("all active drafts use the same block count; verify this is news-driven")

    if len(active) >= 3:
        next_step_count = sum(1 for family, _ in actual_endings if family == "next-step")
        question_count = sum(1 for family, _ in actual_endings if family == "question")
        if next_step_count == len(active):
            errors.append("all active drafts use next-step closing language; vary the actual ending function")
        elif next_step_count > len(active) / 2:
            warnings.append("more than half of active drafts use next-step closing language")
        if len(active) == 4 and question_count > 1:
            warnings.append("more than one draft uses a closing question; verify each is specific and necessary")

    return {"errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="JSON file; omit to read stdin")
    parser.add_argument("--history-root", help="Project root containing prior output JSON files")
    parser.add_argument("--as-of", help="ISO-8601 comparison time with timezone; defaults to now")
    parser.add_argument("--history-days", type=int, default=7)
    args = parser.parse_args()
    try:
        items = as_items(load_payload(args.path))
        results = [lint_item(item, i) for i, item in enumerate(items, 1)]
        if args.history_root:
            as_of = parse_time(args.as_of) if args.as_of else datetime.now(timezone.utc)
            if as_of is None:
                raise ValueError("--as-of requires an ISO-8601 timezone")
            candidate_path = Path(args.path).resolve() if args.path else None
            for item, result in zip(items, results):
                apply_history_checks(
                    item,
                    result,
                    Path(args.history_root).resolve(),
                    as_of,
                    candidate_path,
                    args.history_days,
                )
        batch = lint_batch(items, results)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    ok = not batch["errors"] and not any(result["errors"] for result in results)
    print(json.dumps({"ok": ok, "results": results, "batch": batch}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
