# Performance feedback loop

Use published-post performance as a conservative editorial prior, never as factual evidence or a quota mechanism.

## Account surfaces

| Account | X handle |
|---|---|
| PolymarketAlpha | `@Polymarketalpha` |
| PolyPredX | `@PolyPredX` |
| PredX_Labs | `@PredX_Labs` |
| PredX_News | `@Predx_News` |

## Read-only collection

- At the first scheduled run for an account on a UTC date, check whether that account has a public-metric snapshot from the prior 24 hours. Refresh only when missing or stale; later same-day rounds reuse it.
- Use the already signed-in Chrome session in read-only mode. Open the account profile and an X `Latest` query such as `from:<handle> since:<date> until:<date>` in a fresh temporary tab.
- Collect original posts from the previous 14–30 days when visible. Do not like, reply, repost, follow, bookmark, edit, publish, open messages, inspect cookies or storage, or change account settings.
- Record only public, visibly rendered fields: post URL and ID, exact post timestamp, visible text, views, likes, reposts, replies, collection time, handle, and visible follower count.
- Do not infer bookmarks, clicks, profile visits, media views, unique viewers, watch time, revenue, or private analytics fields.
- Store append-only raw snapshots under `runtime/predx-x-news-writer/performance/snapshots/<UTC timestamp>.json`. A snapshot can contain one account or several accounts.
- Use schema version `predx-performance-snapshot-v1` with top-level `collected_at`, `timezone`, `window`, `accounts`, and `limitations`. Each `accounts[]` record contains `account`, `handle`, `followers_visible`, `posts`, and an optional `note`; each post contains `post_id`, `url`, `posted_at`, `metrics`, and `visible_text`.

If performance collection fails, record the reason and continue the news-writing run without performance feedback. This auxiliary collection never replaces the required X news preflight and is not grounds for `SKIPPED_X_SESSION_UNAVAILABLE` when the separate news research surface remains usable.

## Deterministic attribution and analysis

After a new snapshot, run:

```bash
python3 scripts/build_performance_feedback.py \
  --root <project-root> \
  --now <ISO-8601 time with timezone> \
  --window-days 30
```

The builder:

- matches original X posts to local `READY` or `REVIEW` artifacts by account, date, opening, token overlap, and sequence similarity;
- retains unmatched posts for audit and excludes replies from attribution;
- retains multiple posts matched to one artifact, but lets only the earliest publication instance enter grouped analysis;
- treats a post as mature only when the visible metric observation was collected at least 24 hours after publication;
- with repeated snapshots, uses the first observation at or after 24 hours, keeping measurement ages comparable over time;
- computes same-account medians, engagement per 100 views, relative view index, and grouped associations for content family, opening type, ending function, and block count;
- records a grouped observation after two mature eligible posts, but keeps two- or three-post groups `MONITOR_ONLY` so they cannot become an editorial preference;
- shrinks raw view lift toward the same-account median with a four-post prior, reducing the influence of isolated spikes;
- labels a repeated, regularized association `LIMITED_EXPERIMENT` only from four or more mature posts; this label proposes a reversible test, not a selection or rejection rule;
- writes `runtime/predx-x-news-writer/performance/feedback-latest.json`.

Never compare raw views across accounts as if their audience sizes or distribution conditions were equal. A first-ever observation may be substantially older than 24 hours; retain its explicit `measurement_age_hours` and treat the initial baseline as provisional until repeated daily snapshots create more comparable observations.

## Editorial use

`scripts/build_run_context.py` exposes the current account's compact `performance_feedback` block. Apply it only after a candidate has passed:

1. truth and source quality;
2. freshness and qualified X demand;
3. account and region fit;
4. duplication and follow-up checks;
5. sensitivity and publication-safety checks.

Treat `MONITOR_ONLY` observations as background, not preferences. Use `LIMITED_EXPERIMENT` associations only to break a close tie between otherwise qualified candidates or to vary an opening/ending when the factual structure permits. Change one editorial variable at a time, retain normal style rotation, and reassess after later snapshots rather than accumulating a permanent rule. These associations do not prove causality. Never:

- select a weaker or more sensitive story to chase views;
- override PolymarketAlpha's China exclusion, UTC rule, or US/EU focus;
- override PolyPredX's geopolitics-first priority or PredX_Labs' football-first focus;
- imitate unsupported certainty, engagement bait, or a misleading numeric hook;
- convert one high-performing post into a universal template;
- turn an underperforming group into a topic, opening, ending, or length blacklist;
- infer a preference for PredX_News when no mature matched posts exist.

When feedback is missing, stale, unmatched, or under-sampled, follow the normal account profile and style-diversity rules without inventing a performance preference.
