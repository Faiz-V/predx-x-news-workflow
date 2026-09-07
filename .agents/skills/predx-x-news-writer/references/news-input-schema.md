# News input schema

Accept a JSON object with an `items` array. Additional fields are allowed, but never discard source URLs or timestamps.

```json
{
  "collected_at": "2026-08-05T09:22:00+08:00",
  "same_day_style_history": [
    {
      "account": "PredX_News",
      "story_id": "prior-story-id",
      "opening_type": "direct fact",
      "evidence_path": "incident mechanism",
      "ending_function": "next verification",
      "chinese_blocks": 5,
      "chinese_length": 276,
      "english_length": 702
    }
  ],
  "items": [
    {
      "id": "stable-source-id",
      "story_key": "account-neutral-stable-event-key",
      "topic_key": "stable-recurring-series-key",
      "selection_mode": "strict_x_news",
      "allow_news_platform_fallback": false,
      "fallback_reason": null,
      "source_age_minutes": 14,
      "series_key": null,
      "observation_period": null,
      "material_new_fact": null,
      "follow_up_to": null,
      "published_at": "2026-08-05T09:08:00+08:00",
      "source_type": "official_statement",
      "source_name": "Organization or reporter",
      "source_url": "https://example.com/source",
      "headline": "Short factual headline",
      "content": "Material facts and attributable context",
      "media_summary": "Optional description of image or video evidence",
      "engagement": {"likes": 0, "reposts": 0, "views": 0},
      "x_signal": {
        "post_url": "https://x.com/example/status/123",
        "posted_at": "2026-08-05T09:08:00+08:00",
        "metrics_collected_at": "2026-08-05T09:22:00+08:00",
        "author": "@example",
        "author_type": "official",
        "views": 0,
        "likes": 0,
        "reposts": 0,
        "replies": 0,
        "bookmarks": 0,
        "relative_velocity": 1.0,
        "independent_post_count": 2,
        "independent_post_urls": ["https://x.com/other/status/456"],
        "live_event": false,
        "fresh_echo_count": 0,
        "latest_fresh_echo_at": null,
        "audience_fit": 8,
        "heat_score": 62,
        "trend_status": "HOT"
      },
      "categories": ["technology", "ai"],
      "account_hint": ["PredX_News"],
      "audience_region": null,
      "china_related": null,
      "audience_timezone": null,
      "verification_status": "primary",
      "supporting_sources": ["https://example.com/second-source"],
      "impact_score": 8,
      "duplicate_of": null,
      "internal_market_context": "Optional internal-only note"
    }
  ]
}
```

## Enumerations

- `source_type`: `official_statement`, `filing`, `data_release`, `news`, `x_post`, `other`.
- `verification_status`: `primary`, `multi_source`, `single_reputable`, `unverified`.
- `selection_mode`: `strict_x_news` or `verified_market_brief`. The latter is authorized only for PolymarketAlpha after the strict Snapshot B path fails.
- `allow_news_platform_fallback`: set to `true` only with `selection_mode: "verified_market_brief"`; it relaxes X heat and source freshness only.
- `fallback_reason`: required for `verified_market_brief`; state why no strict Alpha candidate survived.
- `source_age_minutes`: required numeric age from earliest credible disclosure for a fallback; must be between 0 and 720.
- `account_hint`: any subset of `PolymarketAlpha`, `PolyPredX`, `PredX_Labs`, `PredX_News`.
- `audience_region` and `china_related`: every usable PolymarketAlpha candidate, including ranker input for the fallback, must explicitly set `audience_region: "US_EU"` and `china_related: false` after the regional hard gate.
- `audience_timezone`: required as `UTC` for every usable `PolymarketAlpha` item. Its canonical `published_at`, `source_time`, `disclosure_time`, timestamp-shaped `event_time`, and item-level `x_signal` clocks must have zero UTC offset. Local scheduled-task timestamps may remain in the operational timezone outside the item.
- `impact_score`: integer from 0 to 10 assigned by the collector or editor.
- `x_signal.trend_status`: `HOT`, `WARM`, or `UNPROVEN` under `x-demand-signals.md`.
- `story_key`: a stable, account-neutral identifier for the event fact, such as `sk-hynix-y2-m17-investment-2026-08-07`; reuse it for the same fact and create a new key only for a material new development.
- `topic_key`: a broader recurring-series identifier, such as `us-spot-crypto-etf-daily-flows`; do not reuse the series within the recent project window unless a material new development justifies an explicit follow-up.
- `series_key`, `observation_period`, and `material_new_fact`: all-or-nothing metadata for recurring PolymarketAlpha official releases. A new observation period may qualify as a new event, but the same period is a duplicate and Alpha may not use one series twice in a day.
- `follow_up_to`: the prior stable story key when a follow-up is justified; it never replaces `material_new_fact`.
- `x_signal.heat_score`: integer from 0 to 100. Prefer the explicit four-part heat model; if absent, the ranker estimates from available visible metrics.
- `x_signal.relative_velocity`: current engagement velocity divided by the author's typical velocity at a similar post age; omit when a baseline is unavailable.
- `x_signal.live_event`: use only for a still-developing 61–180 minute event; it does not by itself pass the demand gate.
- `x_signal.fresh_echo_count` and `latest_fresh_echo_at`: required for a live-event fallback and must describe distinct relevant X posts from the last 60 minutes.
- `x_signal.trend_status` may remain honestly `UNPROVEN` for a `verified_market_brief`; the complete X collection and audit are still required.
- `same_day_style_history`: optional prior-output metadata used to avoid repeated topics, hooks, structures, block counts, and endings. It is context only and must not be treated as a news source.

If a timestamp lacks a timezone, mark the item for review instead of silently assuming one.
