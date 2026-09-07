# Scheduling contract

Task trigger timezone: `Asia/Shanghai`.

PolymarketAlpha audience timezone: `UTC`. The trigger clock controls when the local automation starts; it must not leak into Alpha publication copy or canonical news-evidence timestamps.

Run three staggered rounds on weekdays only, Monday through Friday. Do not schedule or execute recurring Saturday or Sunday rounds. Each task produces one candidate for one account; adjacent accounts are separated by 30 minutes.

| Round | PolymarketAlpha | PolyPredX | PredX_Labs | PredX_News |
|---|---:|---:|---:|---:|
| 1 | 09:30 | 10:00 | 10:30 | 11:00 |
| 2 | 13:30 | 14:00 | 14:30 | 15:00 |
| 3 | 15:45 | 16:15 | 16:45 | 17:15 |

The 12 weekday tasks create up to three qualified candidates per account. Human editors review and publish during the 09:00–12:00 and 13:00–18:00 work windows.

## Execution topology

Use 12 independent local project scheduled tasks: three per account and four account-specific tasks per round. Never make one scheduled task generate all four accounts. Tasks do not automatically share previous task history, so every task must build project context with `scripts/build_run_context.py` before research, set `scheduled_run: true`, and save its structured output under `runtime/predx-x-news-writer/<YYYY-MM-DD>/` for later rounds.

Every task must run directly on `gpt-5.6-sol` with `xhigh` reasoning. Do not use Luna and do not delegate a second model pass. Preserve each task's current active or paused state when changing model configuration.

Every task must name its account, domain, round number, exact local time, and preferred ending family. Ending preferences are diversity guards, not mandatory templates; choose a different ending when the story demands it.

## Cross-task mutual exclusion

All four accounts, all rounds, and on-demand manual runs share one project-wide editorial lease. Acquire it after the weekday/device gates and before performance collection, `build_run_context.py`, Chrome initialization, X navigation, or artifact writes:

```bash
python3 <project-root>/.agents/skills/predx-x-news-writer/scripts/run_lock.py acquire \
  --root <project-root> \
  --owner <stable-automation-id-or-manual-run-label> \
  --account <account> \
  --mode <scheduled-or-manual> \
  --lease-seconds 2700
```

The successful JSON result contains `code: "ACQUIRED"` and a token. Keep the token private to that run and renew the lease after browser preflight, Snapshot A and Snapshot B and before lint; heartbeat at least every ten minutes during any other long step:

```bash
python3 <project-root>/.agents/skills/predx-x-news-writer/scripts/run_lock.py heartbeat \
  --root <project-root> \
  --token <acquired-token>
```

If acquisition returns `SKIPPED_CONCURRENT_RUN`, stop immediately and report the holder's owner, account, mode and expiry. Do not initialize Chrome, load history, write an output artifact, wait-loop, retry in another tab or task, delete `.locks`, or weaken the lease. This structured concurrency skip is neither `HOLD` nor `SKIPPED_X_SESSION_UNAVAILABLE`.

Release the lease with the same token in a best-effort final step on every terminal path, including `READY`, `REVIEW`, `HOLD`, browser skip, validation failure, and unexpected error:

```bash
python3 <project-root>/.agents/skills/predx-x-news-writer/scripts/run_lock.py release \
  --root <project-root> \
  --token <acquired-token>
```

Never release a lease with another run's token. A missing or mismatched token is an error, not permission to delete the lock. The script alone may atomically recover a lease whose heartbeat has expired; lock events are appended under `runtime/predx-x-news-writer/.locks/` for diagnosis.

## Round behavior

- Round 1 establishes the first distinct story for the account. Prefer a limited implication or let the consequence close naturally.
- Round 2 uses new material. Prefer a specific audience-facing question or an evidence constraint when natural; do not update the morning story without a major new development.
- Round 3 produces the third qualified candidate. Prefer a short verdict, limited implication, or competition consequence, and flag the account if fewer than three `READY` drafts are visible.

Do not force these ending families onto unsuitable stories. Never use a bare `你怎么看？`, and do not use an audience-facing question more than once across one account's three daily drafts when same-day history is available.

## X-first collection

- Before each task, collect 15–20 visible X candidates for that account's domain from the prior 60 minutes when practical; rank visible metadata first and fully verify only the leading 2–3.
- Follow `scheduled-research-protocol.md`: take Snapshot A, keep a three-item watchlist, use the interval for verification and external seed discovery, then take Snapshot B at least eight minutes after Snapshot A before returning a researched `HOLD`.
- For each `PolyPredX` task, search active geopolitical and conflict developments before the general-politics fallback lane; select the fallback only when no geopolitical candidate passes the freshness, X-demand, and truth gates.
- For each `PolymarketAlpha` task, search US, EU and UK finance lanes first and apply negative China terms where X syntax permits. Reject mainland China, Hong Kong and Macau policy, macro, currency, market and company stories before heat scoring; never use one because it is hotter than a US/Europe candidate or because the eligible pool would otherwise be empty. A run-specific explicit user request is the only override.
- Rank candidates with `x-demand-signals.md`, then verify the leading `HOT` or `WARM` story with eligible sources before writing.
- After Snapshot B, if and only if the strict PolymarketAlpha pool has no qualified story, evaluate the standing `Verified Market Brief` fallback in `x-demand-signals.md`. It may admit a verified, high-impact, non-China US/EU item no more than 720 minutes old with `UNPROVEN` X demand. Limit this mode to one Alpha item per account-day and record the required fallback fields. Other accounts still return `HOLD` for `UNPROVEN`.
- Use only a read-only visible browser session. Never log in, handle credentials or cookies, or interact with X content.
- After confirming the device is active, use Chrome/browser control with the already signed-in X session. Search-engine `site:x.com` results do not satisfy the collection requirement.
- Initialize the Chrome browser binding once per run and create a fresh temporary X tab before Snapshot A. Never reuse a tab handle from another scheduled task.
- If initial Chrome connection fails, perform one troubleshooting-guided preflight retry. If a tab becomes stale or reports `No tab with id`, keep the browser binding, replace only the tab, and retry that operation once. Keep each X query to at most six positive handles or terms. If a narrow query returns zero cards, run a short known-broad baseline probe: a successful baseline means the narrow query is genuinely empty or malformed and may be retried once with fewer terms; a failed baseline or generic error is session-level and requires a 30–45 second cooldown before one fresh-tab shorter-query retry. Failed searches are not evidence.
- If the device is asleep or inactive, report `SKIPPED_DISPLAY_INACTIVE`; if browser control, the signed-in X session, timestamps, or visible metrics are unavailable, report `SKIPPED_X_SESSION_UNAVAILABLE`. Neither condition is a researched `HOLD`.
- Before a researched `HOLD`, complete both snapshots, gather 15–25 candidates when practical, re-search the leading two or three events for independent echo, and perform a final high-engagement plus major-entity refresh.
- Keep all browser and query recovery bounded and record it in the audit. The Sol `xhigh` scheduled run is the only model pass; after Snapshot B and the allowed retries, return a researched `HOLD` rather than delegating another model or creating an extra round.

## Daily controls

- Never count a `HOLD` as a usable candidate.
- Clearly identify follow-up stories and explain the new fact; do not repackage an earlier post.
- For recurring PolymarketAlpha releases such as ETF flows, employment, inflation, Treasury auctions or inventories, set `series_key`, a new `observation_period`, and `material_new_fact` together. Reject the same observation period and never use the same Alpha series twice on the same day.
- Record stable `story_key` and `topic_key` values, the named entity, style fingerprint, Chinese and English lengths, block count, ending function, opening text and full final block in every usable output.
- Record `audience_region: "US_EU"`, `china_related: false`, and `audience_timezone: "UTC"` in every usable PolymarketAlpha output. Keep `scheduled_at` and device/activity timestamps in the operational timezone when needed, but normalize `source_time`, `published_at`, `disclosure_time`, `event_time` when timestamp-shaped, and item-level X-signal measurement times to UTC. Any clock time in Alpha public copy must be UTC-labeled in both languages.
- Avoid repeating the same opening type plus evidence path or the same ending family in consecutive drafts for one account unless the news itself requires it.
- If the context script fails, record `HISTORY_CONTEXT_UNAVAILABLE`, use the round preference, and do not claim duplicate checking was exhaustive.
- Do not schedule or perform publication. End with the complete editor-facing Markdown package. For every `READY` or `REVIEW` result, paste both full post bodies directly into the final response; an output-file link is audit backup only.

## Daily performance feedback

- During the first scheduled run for each account on a UTC date, refresh that account's visible public post metrics only if no account snapshot exists from the prior 24 hours. Do not repeat the sweep in rounds 2 and 3.
- Store the append-only raw snapshot under `runtime/predx-x-news-writer/performance/snapshots/`, then run `scripts/build_performance_feedback.py` before `scripts/build_run_context.py`.
- Read `references/performance-feedback-loop.md` for the snapshot schema, attribution rules, 24-hour maturity gate, repeated-publication handling, and editorial guardrails.
- Performance collection is auxiliary and read-only. A collection failure becomes `PERFORMANCE_FEEDBACK_UNAVAILABLE`; it does not by itself fail or skip the scheduled news task.
- The generated `performance_feedback` context may break a close tie only after every normal editorial gate. It must not cause quota filling, weaken verification, override account scope, or turn one strong post into a fixed template.
