# X demand signals

Use X popularity as a discovery and selection signal, never as factual verification.

## Candidate collection

For scheduled runs, gather 15–20 visible candidates for each requested account from the last 60 minutes when practical. Keep the first pass to visible post metadata, rank the pool, then open and verify only the leading 2–3 candidates per account. Use a read-only mix of:

- the account domain's curated X list or watchlist;
- `Top` and `Latest` searches for concrete entities and events;
- verified official accounts, major newsrooms, named reporters, and established specialists;
- independent posts discussing the same event.

Always include an account-specific major-entity lane and a high-engagement lane. For the high-engagement lane, use age-aware thresholds as discovery filters rather than truth rules: approximately `min_faves:20` or `min_retweets:5` for the prior 30 minutes, and `min_faves:50` for the prior 60 minutes. Lower thresholds for credible specialist accounts when relative velocity is clearly exceptional. Run separate searches when X does not combine engagement operators reliably.

For `PolyPredX`, make active geopolitics the first account-specific lane: search the parties, governments, officials, locations, diplomatic bodies, military actions, sanctions, negotiations, and escalation or ceasefire terms tied to current international crises. Build a separate general-politics fallback lane for elections, legislation, courts, campaigns, and domestic policy. Fully verify and select a general-politics candidate only when the geopolitical lane has no fresh `HOT` or `WARM` story that passes the truth gate.

After the initial X pass, inspect a small fresh-headline or RSS surface for entities the signed-in session may not have surfaced. Search every promising seed back on X by exact entity and event phrase; reject it if X demand remains unproven.

For scheduled runs, use the two-snapshot protocol in `scheduled-research-protocol.md`. Snapshot A builds the pool and a three-item watchlist; Snapshot B refreshes only the high-engagement, major-entity, watchlist and external-seed lanes after an active 8–15 minute observation span. The scheduled trigger is the start of observation, not a hard candidate cutoff.

An already signed-in browser session may be read when available. Never log in, request or expose credentials, inspect cookies or storage, solve CAPTCHAs, evade limits, or like, reply, repost, follow, bookmark, or publish.

For scheduled runs, an already signed-in X session with visible post metadata is the required collection surface. Search-engine results, cached snippets, and `site:x.com` queries may reveal leads but cannot establish recency, engagement velocity, or a qualified X snapshot. If the signed-in session cannot be used, return `SKIPPED_X_SESSION_UNAVAILABLE` instead of `UNPROVEN` or `HOLD`.

Before declaring that no qualified candidate exists, complete all five discovery layers, re-search the leading two or three event phrases for independent echo, and rerun the high-engagement and major-entity lanes with a fresh cutoff. Record the query lanes, candidate count, first and final snapshots, and rejection reasons in the audit note.

## Required snapshot

Record the original X URL and:

- `posted_at` and timezone;
- `metrics_collected_at` and timezone;
- `first_seen_at` and the final-refresh time when observed twice;
- visible views, likes, reposts, replies, and bookmarks when available;
- author and author type;
- count and URLs of independent relevant posts within the window;
- a relative-performance estimate when the author's normal baseline is visible;
- account-audience fit from 0–10.

Missing metrics do not make a post false, but they weaken the demand signal. Never invent hidden or unavailable counts.

## Heat model

Score each candidate from 0–100:

1. Recency: 0–25.
2. Engagement velocity relative to post age and, when available, the author's recent baseline: 0–35.
3. Independent echo from distinct relevant accounts: 0–25.
4. Fit for the target account's audience: 0–15.

Prefer relative velocity and independent echo over raw likes. A huge account can create large absolute counts without unusual audience demand; a smaller specialist account can reveal a fast-emerging story with fewer interactions.

Treat the browser session as a transport and visibility surface, not as the curator. Do not use Home or For You as the candidate pool. Use explicit `Latest` queries, fixed account-domain entity coverage, engagement-filter lanes, and external seeds searched back on X to reduce personalization blind spots.

Classify:

- `HOT`: heat score 60–100, or top-quartile relative velocity plus at least two independent relevant posts.
- `WARM`: heat score 40–59 with at least two independent relevant posts.
- `UNPROVEN`: below 40, missing a usable X snapshot, older than 60 minutes without a qualifying current echo burst, or supported only by one low-context viral post.

A 61–180 minute live event may retain `HOT` or `WARM` status only when at least two distinct relevant echoes appeared in the last 60 minutes and `live_event`, `fresh_echo_count`, and `latest_fresh_echo_at` are recorded. Rank this Tier B fallback below any qualified story whose material fact was disclosed within 60 minutes.

For scheduled production, draft `HOT` first, then `WARM`. Return `HOLD` for `UNPROVEN` unless the user explicitly permits a news-platform fallback.

## Truth gate

After the heat gate, verify the event with an eligible primary or reputable reporting source. Viral but unverified material remains `HOLD`. Attribute single-source claims accurately and preserve uncertainty.

## Manipulation checks

Downgrade apparent heat when it depends on duplicated wording, coordinated low-quality accounts, engagement bait, recycled footage, an old article reposted without a new fact, or high views with almost no independent discussion. Heat must reflect a current story, not merely a viral post.
