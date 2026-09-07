---
name: predx-x-news-writer
description: Generate and revise verified, news-led bilingual X post packages in the user's established house style for PolymarketAlpha, PolyPredX, PredX_Labs, and PredX_News. Use for scheduled or on-demand news writing, Chinese-first mother drafts, paragraph-aligned English publication copy, reference-calibrated length and formatting, account assignment, style variation, freshness checks, and pre-publication linting. Do not use it to log into X, handle credentials or cookies, evade platform controls, publish posts, or perform engagement actions.
---

# PredX X News Writer

Produce complete X posts that feel distilled from the user's recent reference archive: concise but explained, numerically specific, visually scannable, and varied across accounts. Treat Chinese as the authoritative mother draft and English as its publication-ready semantic counterpart. Use X demand signals to choose among verified stories; never confuse popularity with proof. Keep publication outside this skill.

## Required references

Read before every drafting run:

- `references/house-style.md` for the reference-derived voice, density, and format envelope.
- `references/account-profiles.md` for account assignment and audience lens.
- `references/x-demand-signals.md` for the X-first discovery gate and heat scoring.
- `references/source-and-freshness-policy.md` for eligible news and time windows.
- `references/bilingual-output-rules.md` for Chinese-first drafting and strict alignment.
- `references/style-library.md` for structure selection and non-template variation.
- `references/verification-rules.md` for `READY`, `REVIEW`, and `HOLD` decisions.

Read both `references/scheduling-contract.md` and `references/scheduled-research-protocol.md` for scheduled batches. Read `references/performance-feedback-loop.md` for scheduled runs or whenever published-post metrics are supplied or collected. Read `references/product-context.md` only when internal relevance improves selection. Read `references/news-input-schema.md` when normalizing machine-collected material.

## Workflow

1. For every scheduled or on-demand production run, acquire the project-wide lease with `scripts/run_lock.py` before building history context, collecting performance, opening Chrome, or writing an output artifact. Scheduled and manual runs for all four accounts share this one lock because they share both project history and the signed-in Chrome/X session. If acquisition returns `SKIPPED_CONCURRENT_RUN`, stop immediately and report the visible holder metadata; do not open or navigate X, write a replacement output, wait-loop, delete the lock, or bypass it. For an on-demand PolymarketAlpha run only, then call `scripts/check_manual_cooldown.py`; after an Alpha `HOLD`, return `SKIPPED_MANUAL_COOLDOWN` until 60 minutes have elapsed. A fresh event seed supplied by the user or an explicit user override may be recorded with `--override-reason`; ordinary “retry” language is not an override. Retain the returned lease token, heartbeat after browser preflight, Snapshot A and Snapshot B and before lint (at least once every 10 minutes during other long work), and release it with the same token in a best-effort final step after success, `HOLD`, skip, or error. Only the lock script may recover an expired lease. Follow the exact command contract in `references/scheduling-contract.md`.
2. Establish both the operational trigger timezone and the audience timezone. Scheduled tasks may continue to trigger in `Asia/Shanghai`, but that local clock is operational metadata only. For `PolymarketAlpha`, normalize source, disclosure, event and X-signal timestamps to UTC and set `audience_timezone: "UTC"`; any explicit clock time in either public-copy language must be labeled and expressed in UTC. UTC is an internal normalization standard, not wording that must appear in the post: omit clock times and timezone labels when they do not help the story. When a current-state qualifier is useful, write natural public language such as “截至目前” and `currently`, never process language such as “本轮采集时”, “截至本次核验”, `at collection time`, or `as of this run`. Never publish `UTC+8`, `GMT+8`, `CST`, “北京时间”, or another local-market timezone in Alpha copy unless the user explicitly overrides the timezone for that specific run.
3. Start from an X-first news packet whenever available. For scheduled research, use the X collection chain below. Read only visible public pages or an already available signed-in browser session; never log in, expose credentials or cookies, manage proxies, solve CAPTCHAs, evade controls, or interact with posts.
4. Collect or accept several candidates per requested account, then apply the X demand gate in `references/x-demand-signals.md`. A news-platform article alone does not prove audience demand.
5. Normalize X timestamps and metric snapshots alongside source publication times, names, figures, attribution, uncertainty, and supporting links.
6. For scheduled runs, build recent project context with `scripts/build_run_context.py` before selection. Treat recent `story_key` values, openings and actual ending texts as comparison input, not optional memory. If its `performance_feedback` block is available, treat `MONITOR_ONLY` signals as background and use only same-account `LIMITED_EXPERIMENT` associations as a soft, reversible tie-breaker after every truth, freshness, account-fit, duplication, sensitivity and source-quality gate; never treat performance as causal evidence, convert it into a standing editorial rule, or let it select a weaker story. Run the normal X-news path first: prefer X posts and supporting material from the last 30 minutes and normally require 60 minutes or less. If a complete PolymarketAlpha Snapshot B still yields no strict candidate, use the standing `Verified Market Brief` fallback defined below; do not apply that fallback to another account.
7. Apply account and regional hard gates before ranking by X heat. For `PolymarketAlpha`, serve a US/Europe audience: prioritize US, EU and UK finance, macro, public markets, crypto and financial regulation; reject every China-related or China-centered candidate regardless of X heat, including mainland China, Hong Kong or Macau macro data, policy, regulators, currencies, markets and companies. Do not use a China story because the non-China pool is weak; only an explicit user request for that specific run can override this gate. Among candidates that remain, rank by X heat, account fit, consequence, source confidence, novelty, and the clarity of the next observable development. For `PolyPredX`, first select from qualified geopolitical, conflict, diplomacy, sanctions, or international-security developments; use elections, legislation, courts, campaigns, and other political news only when that priority pool has no qualified story.
8. Assign one distinct story to each requested account. Do not reuse a story without explicit permission and a materially different verified angle. For PolymarketAlpha, recurring official series such as ETF flows, employment, inflation, Treasury auctions and inventories may qualify as a new observation only when `series_key`, a new `observation_period`, and `material_new_fact` are all recorded. Never use the same Alpha series twice in one account-day.
9. Build a fact spine before writing: `event`, `driver or context`, `scale or evidence`, `consequence`, and an optional closing purpose. The closing purpose may be a checkpoint, constraint, limited implication, specific audience question, short verdict, or no separate ending. If a cause is unknown, state that rather than inventing one.
10. Select a style fingerprint from `references/style-library.md`: opening type, evidence path, ending function, and block count. Compare both the declared ending function and the actual final wording with available same-day outputs; do not disguise repeated `接下来`, `下一步`, or `Next` endings with different labels.
11. Write the complete Chinese mother draft first. Make the opening a short, title-like single sentence: use `JUST IN:` only for a genuinely fresh development, otherwise use an objective direct fact, number, named actor, or contrast.
12. Default to one sentence per block. Keep 4–6 visible blocks, but shorten each block before removing event, mechanism, or consequence. Use a second sentence only when it is essential to the same block's job. Let the consequence close the post when it already lands cleanly instead of appending a compulsory forecast paragraph.
13. Calibrate the Chinese draft against `references/house-style.md`. Remove padding, repeated conclusions, secondary examples, and background that does not change interpretation.
14. Lock the Chinese draft, then write English block by block. Preserve paragraph count, information order, figures, attribution, causal limits, and conclusion. Use idiomatic English without adding or dropping meaning.
15. Run the alignment, verification, format, hashtag, sentence-density, X-signal, public-content, duplicate-story, opening-similarity and actual-ending checks. For scheduled output and every manual `Verified Market Brief`, use `scripts/lint_output.py <output> --history-root <project-root> --as-of <time>` so the daily fallback and series quotas are enforceable. Revise every error and treat warnings as editorial prompts.
16. Return the complete batch for human review in Markdown. For every `READY` or `REVIEW` result, paste both complete post bodies into the final response; a file link, status summary, notification card, or audit note must never replace the bodies. Never publish, schedule publication, like, reply, repost, follow, or send external messages.

## Scheduled X collection chain

Treat this sequence as a hard gate for scheduled runs:

1. After the device-activity check passes, initialize the available Chrome/browser-control capability once and inspect X through the existing signed-in session in read-only mode. Keep the browser binding for the run, but create a fresh temporary X tab instead of reusing a tab handle saved by another run. Do not enter, request, reveal, or modify credentials, cookies, storage, proxies, or account settings.
2. Before Snapshot A, confirm that the fresh tab can open an X `Latest` query and expose a post timestamp plus visible metrics. If initial Chrome discovery or connection fails, perform one bounded same-run recovery using the browser capability's setup or Chrome troubleshooting guidance, then retry the preflight once. If browser control is still unavailable, X is signed out, the session is blocked by a CAPTCHA or verification screen, or visible metadata remains unavailable, stop with `SKIPPED_X_SESSION_UNAVAILABLE`. Do not call this `HOLD`, and do not substitute search-engine `site:x.com` results as an X heat snapshot.
3. Treat the browser binding and tab binding separately. If a tab is missing, stale, closed, or reports `No tab with id`, discard only that tab binding, create a fresh tab from the existing browser binding, reload the same short `Latest` query, and retry that operation once. Reconnect the browser only after an explicit browser-disconnected error.
4. Follow `scheduled-research-protocol.md`. Search X's `Latest` results through small fixed queries across trusted accounts, major entities, broad terms, separate high-engagement lanes, and exact X searches seeded by fresh external headlines.
5. Take Snapshot A, gather 15–25 visible candidates when practical, and keep a three-item watchlist for very fresh or near-threshold events. Record URL, post age, visible metrics, author type, fit and first snapshot time before opening articles.
6. Re-search the leading two or three stories by exact entity and event phrase to identify independent X echoes. A single newsroom post with no independent discussion is normally `UNPROVEN`.
7. Use web search, news sites, filings, RSS, and official pages only after the initial X pass, for factual verification, source-time checks, and fresh event seeds. Search every promising external seed back on X and require a qualified X signal before drafting.
8. If Snapshot A has no qualified story, use the interval for watchlist verification, compact external headline discovery and exact X back-searches. Take Snapshot B at least eight minutes after Snapshot A while the run remains active; repeat only high-engagement, major-entity, watchlist and external-seed lanes.
9. Every scheduled task runs the complete workflow directly on `gpt-5.6-sol` at `xhigh`. Do not delegate a rescue pass to Luna, Sol, or another model. For PolymarketAlpha, evaluate the authorized `Verified Market Brief` fallback after Snapshot B and before `HOLD`; for every other account, return `HOLD` after the normal gates and bounded browser/query recovery. Set `scheduled_run: true` and save the structured result under `runtime/predx-x-news-writer/<YYYY-MM-DD>/`, including stable `story_key` and `topic_key` values for every `READY` or `REVIEW` item and the complete research audit.

Never end a scheduled run after only generic web searches. Distinguish three outcomes: `SKIPPED_DISPLAY_INACTIVE`, `SKIPPED_X_SESSION_UNAVAILABLE`, and a fully researched `HOLD`.

## Performance feedback loop

- Follow `references/performance-feedback-loop.md`. At the first scheduled run for an account on a UTC date, refresh its visible public post metrics only when the latest account snapshot is missing or older than 24 hours; later rounds reuse the daily snapshot.
- Keep performance collection read-only and separate from the required X news preflight. If it fails, record `PERFORMANCE_FEEDBACK_UNAVAILABLE` and continue normal news research when the news surface itself remains usable.
- Preserve raw append-only snapshots, then run `scripts/build_performance_feedback.py` before `scripts/build_run_context.py` so current associations enter the account context.
- Exclude replies and repeated publication instances from grouped analysis. Posts observed before 24 hours are provisional. Never infer unavailable private metrics.
- Performance can break a close tie between otherwise qualified candidates or guide a compatible style variant. It never overrides the core editorial gates, account priorities, regional exclusions, UTC rules, or human review.

## Automated-run reliability

- The project-wide run lease is the outer reliability boundary. Per-tab recovery is allowed only after this run owns the lease. A second scheduled or manual run must return `SKIPPED_CONCURRENT_RUN` instead of touching the shared Chrome/X session or shared history concurrently.
- Use one browser runtime and browser binding per run. Tab bindings are disposable and must not be carried across scheduled runs.
- Pace X `Latest` queries serially: after every navigation, allow roughly 2.5–4 seconds for result cards to settle before reading them. Never issue parallel X searches or a rapid navigation burst against the same signed-in session.
- For PolymarketAlpha, keep each X query to at most six positive handles or terms. If a syntactically valid narrow Alpha query unexpectedly exposes no result cards, run one short known-broad baseline probe. When the baseline works, treat the narrow zero as a genuine empty result or query-shape problem and retry that lane once with fewer terms; do not call the session unavailable. When the baseline also fails or a generic error appears, stop issuing queries, preserve prior results, allow a 30–45 second cooldown, then retry once in a fresh tab with a shorter equivalent query. Other accounts retain their existing bounded generic-error recovery. Replacing the tab without the cooldown is not a useful recovery for a session-level X search failure. A failed search is never evidence. A directly readable selected-status URL may refresh an already discovered candidate, but it cannot replace the required query lanes.
- Keep recovery bounded: one Chrome preflight retry, one fresh-tab retry per failed browser operation, and one shorter-query retry per failed search. Record each retry and its result in the research audit; do not loop indefinitely.
- Inspect each tool result according to its actual result shape. Do not batch heterogeneous tool results through code that assumes every result has an `.output` field. If a grouped read fails, preserve completed results and retry only the failed operation once.
- Validate small page-evaluation snippets before using them across multiple tabs or queries. Prefer simple serial loops over a large combined expression for Snapshot B.
- Write the structured artifact before final presentation and run the history-aware linter after every material edit until it reports `0 errors / 0 warnings`.

## Hard defaults

- Use `reference_long` mode unless the user explicitly requests a standard 280-character post or a thread.
- In `reference_long` mode, target 4–6 content blocks, roughly 170–260 non-whitespace Chinese characters and 380–650 English characters. These are calibration bands, not a five-paragraph template; use the variant ranges in `references/house-style.md`.
- Make the first block title-like and brief. Prefer one sentence per block; never let every block become a multi-sentence mini-paragraph.
- Include a verified event, its driver or material context, and its consequence. Choose the ending that best fits the story; a next checkpoint is optional, not a required fifth block.
- Treat Chinese as authoritative. English must have the same content-block count and the same factual sequence. Never compress the English into a summary or expand it with new analysis.
- Preserve exact numbers, names, times, offices, teams, procedural stages, and uncertainty across both languages.
- Use zero hashtags by default and no more than one relevant hashtag.
- Keep direct references to Polymarket, prediction markets, probabilities, betting, wallet performance, and PredX out of public copy unless explicitly requested for a specific post.
- Avoid advice, guarantees, unsupported causality, partisan persuasion, fabricated quotes, generic engagement bait, and false certainty. A specific audience-facing question is allowed when it names the real decision, tradeoff, or uncertainty in the story.
- Keep sources, timestamps, status labels, and editorial notes outside both post bodies.
- Do not recycle the same hook, paragraph logic, ending, or sentence rhythm across all four accounts. Variation must come from the news structure, not slang or decoration.
- Mark weak, stale, or materially unresolved items `HOLD` rather than filling the quota.
- For scheduled batches, mark news-only candidates without a qualified X signal `HOLD`, except for the standing PolymarketAlpha `Verified Market Brief` fallback below.
- Search-engine snippets and `site:x.com` results are discovery hints only; they cannot supply the visible-metric snapshot required for a scheduled `HOT` or `WARM` classification.
- For `PolymarketAlpha`, the China exclusion is a hard pre-ranking gate, not a preference. A China-centered candidate must be rejected even when it is fresher or hotter than every US/Europe candidate. Every `READY` or `REVIEW` Alpha artifact must set `audience_region: "US_EU"` and `china_related: false`.
- For `PolymarketAlpha`, separate task scheduling from audience time. `scheduled_at`, device checks and other operational fields may retain `Asia/Shanghai`; the usable item must set `audience_timezone: "UTC"`, normalize its canonical news and X-evidence timestamps to UTC, and express every public-copy clock time in UTC in both languages.
- For `PolymarketAlpha`, strict X-news selection always runs first. After a complete Snapshot B with no qualified strict story, one `Verified Market Brief` may be used per account-day when the current fact is no more than 720 minutes old, materially consequential, US/EU relevant, non-China, non-duplicate, and supported by a primary source or multiple reputable sources. X may be `UNPROVEN`, but the X lanes and audit remain mandatory. Set `selection_mode: "verified_market_brief"`, `allow_news_platform_fallback: true`, `fallback_reason`, `verification_status`, `impact_score` of at least 6, and `source_age_minutes`; never use `JUST IN`. A single reputable source must remain `REVIEW`. This relaxes only heat and freshness, never truth, legal-role precision, regional scope, UTC, safety, or human review.

## Output contract

Return accounts in this order: `PolymarketAlpha`, `PolyPredX`, `PredX_Labs`, `PredX_News`.

For each account provide:

````markdown
## <account>
**Status:** READY | REVIEW | HOLD
**Story:** <short factual label>
**Story key:** <stable event identifier>
**Topic key:** <stable recurring-series identifier>
**Style fingerprint:** <opening / evidence path / ending / block count>
**Source time:** <timestamp and timezone>
**X signal:** HOT | WARM | UNPROVEN — <post time, snapshot time, relative heat evidence>
**Sources:** <direct Markdown links>
**Audience region:** <required for PolymarketAlpha: US_EU>
**China related:** <required for PolymarketAlpha: false>
**Audience timezone:** <required for PolymarketAlpha: UTC>

### 中文母稿

```text
<complete reference-style Chinese post>
```

### English publication copy

```text
<the same content blocks and meaning in idiomatic English>
```

**Editorial checks:** <Chinese length and blocks; English length and blocks; multi-sentence blocks; hashtag count; exact caveat>
````

The outer response is ordinary Markdown; the two `text` fences are copy surfaces and are not part of either post. If status is `HOLD`, omit both post bodies and state what evidence is missing. For `SKIPPED_*`, return the skip code and concrete reason. Do not present a `REVIEW` item as ready to publish. Always include the audit-file link when one exists, but never use it as a substitute for a `READY` or `REVIEW` body.

## Scheduled batches

Follow `references/scheduling-contract.md`. Each scheduled run covers exactly one account. Three staggered weekday rounds create up to three candidates per account for human review. Do not schedule weekend runs, and do not lower verification or style standards to fill a missing slot.

## Utility scripts

```bash
python3 scripts/rank_candidates.py packet.json --now 2026-08-05T09:30:00+08:00
python3 scripts/rank_candidates.py packet.json --now 2026-08-05T09:30:00+08:00 --alpha-market-brief
python3 scripts/build_performance_feedback.py --root <project-root> --now <ISO-8601 time with timezone> --window-days 30
python3 scripts/check_manual_cooldown.py --root <project-root> --account PolymarketAlpha --now <ISO-8601 time with timezone>
python3 scripts/lint_output.py output.json
```

Both scripts use only the Python standard library. `lint_output.py` defaults to `reference_long`; set an item's `post_mode` to `standard_x` only when a 280-character post was explicitly requested.
