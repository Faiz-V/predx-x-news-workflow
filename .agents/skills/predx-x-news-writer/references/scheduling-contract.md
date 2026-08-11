# Scheduling contract

Timezone: `Asia/Shanghai`.

Run three staggered rounds on weekdays only, Monday through Friday. Do not schedule or execute recurring Saturday or Sunday rounds. Each task produces one candidate for one account; adjacent accounts are separated by 30 minutes.

| Round | PolymarketAlpha | PolyPredX | PredX_Labs | PredX_News |
|---|---:|---:|---:|---:|
| 1 | 09:30 | 10:00 | 10:30 | 11:00 |
| 2 | 13:30 | 14:00 | 14:30 | 15:00 |
| 3 | 15:45 | 16:15 | 16:45 | 17:15 |

The 12 weekday tasks create up to three qualified candidates per account. Human editors review and publish during the 09:00–12:00 and 13:00–18:00 work windows.

## Execution topology

Use 12 independent local project scheduled tasks: three per account and four account-specific tasks per round. Never make one scheduled task generate all four accounts. Tasks do not automatically share previous task history, so every task must build project context with `scripts/build_run_context.py` before research, set `scheduled_run: true`, and save its structured output under `runtime/predx-x-news-writer/<YYYY-MM-DD>/` for later rounds.

Every task must name its account, domain, round number, exact local time, and preferred ending family. Ending preferences are diversity guards, not mandatory templates; choose a different ending when the story demands it.

## Round behavior

- Round 1 establishes the first distinct story for the account. Prefer a limited implication or let the consequence close naturally.
- Round 2 uses new material. Prefer a specific audience-facing question or an evidence constraint when natural; do not update the morning story without a major new development.
- Round 3 produces the third qualified candidate. Prefer a short verdict, limited implication, or competition consequence, and flag the account if fewer than three `READY` drafts are visible.

Do not force these ending families onto unsuitable stories. Never use a bare `你怎么看？`, and do not use an audience-facing question more than once across one account's three daily drafts when same-day history is available.

## X-first collection

- Before each task, collect 15–20 visible X candidates for that account's domain from the prior 60 minutes when practical; rank visible metadata first and fully verify only the leading 2–3.
- Follow `scheduled-research-protocol.md`: take Snapshot A, keep a three-item watchlist, use the interval for verification and external seed discovery, then take Snapshot B at least eight minutes after Snapshot A before returning a researched `HOLD`.
- For each `PolyPredX` task, search active geopolitical and conflict developments before the general-politics fallback lane; select the fallback only when no geopolitical candidate passes the freshness, X-demand, and truth gates.
- Rank candidates with `x-demand-signals.md`, then verify the leading `HOT` or `WARM` story with eligible sources before writing.
- Do not substitute a news-platform-only story when X demand is `UNPROVEN`; return `HOLD` unless the user explicitly permits the fallback.
- Use only a read-only visible browser session. Never log in, handle credentials or cookies, or interact with X content.
- After confirming the device is active, use Chrome/browser control with the already signed-in X session. Search-engine `site:x.com` results do not satisfy the collection requirement.
- If the device is asleep or inactive, report `SKIPPED_DISPLAY_INACTIVE`; if browser control, the signed-in X session, timestamps, or visible metrics are unavailable, report `SKIPPED_X_SESSION_UNAVAILABLE`. Neither condition is a researched `HOLD`.
- Before a researched `HOLD`, complete both snapshots, gather 15–25 candidates when practical, re-search the leading two or three events for independent echo, and perform a final high-engagement plus major-entity refresh.
- On Luna scheduled runs, trigger at most one bounded Sol `xhigh` rescue only after a provisional `HOLD` or an all-`UNPROVEN` pool. Pass the compact research audit rather than repeating the full task. If rescue delegation is unavailable, record that fact; do not create a fixed extra daily round.

## Daily controls

- Never count a `HOLD` as a usable candidate.
- Clearly identify follow-up stories and explain the new fact; do not repackage an earlier post.
- Record stable `story_key` and `topic_key` values, the named entity, style fingerprint, Chinese and English lengths, block count, ending function, opening text and full final block in every usable output.
- Avoid repeating the same opening type plus evidence path or the same ending family in consecutive drafts for one account unless the news itself requires it.
- If the context script fails, record `HISTORY_CONTEXT_UNAVAILABLE`, use the round preference, and do not claim duplicate checking was exhaustive.
- Do not schedule or perform publication. End with the complete editor-facing Markdown package. For every `READY` or `REVIEW` result, paste both full post bodies directly into the final response; an output-file link is audit backup only.
