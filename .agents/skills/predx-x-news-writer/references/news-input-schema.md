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
- `account_hint`: any subset of `PolymarketAlpha`, `PolyPredX`, `PredX_Labs`, `PredX_News`.
- `impact_score`: integer from 0 to 10 assigned by the collector or editor.
- `x_signal.trend_status`: `HOT`, `WARM`, or `UNPROVEN` under `x-demand-signals.md`.
- `story_key`: a stable, account-neutral identifier for the event fact, such as `chipmaker-y2-m17-investment-2026-08-07`; reuse it for the same fact and create a new key only for a material new development.
- `topic_key`: a broader recurring-series identifier, such as `us-spot-crypto-etf-daily-flows`; do not reuse the series within the recent project window unless a material new development justifies an explicit follow-up.
- `x_signal.heat_score`: integer from 0 to 100. Prefer the explicit four-part heat model; if absent, the ranker estimates from available visible metrics.
- `x_signal.relative_velocity`: current engagement velocity divided by the author's typical velocity at a similar post age; omit when a baseline is unavailable.
- `x_signal.live_event`: use only for a still-developing 61–180 minute event; it does not by itself pass the demand gate.
- `x_signal.fresh_echo_count` and `latest_fresh_echo_at`: required for a live-event fallback and must describe distinct relevant X posts from the last 60 minutes.
- `same_day_style_history`: optional prior-output metadata used to avoid repeated topics, hooks, structures, block counts, and endings. It is context only and must not be treated as a news source.

If a timestamp lacks a timezone, mark the item for review instead of silently assuming one.
