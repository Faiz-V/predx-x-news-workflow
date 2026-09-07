# Scheduled research protocol

Use this protocol for every scheduled account run. The complete workflow runs directly on `gpt-5.6-sol` at `xhigh`: short fixed lanes, a small watchlist, deterministic history context, and two X snapshots before `HOLD`.

## 0. Acquire the shared run lease

After the weekday and device-activity gates pass, acquire the project-wide lease exactly as defined in `scheduling-contract.md`. Do this before performance feedback, history context, browser setup, X navigation, or output writes. If another scheduled or manual run owns it, return `SKIPPED_CONCURRENT_RUN` with the holder metadata and stop without touching Chrome/X.

Retain the acquisition token, heartbeat after browser preflight, Snapshot A and Snapshot B and before lint, and release with the same token on every terminal path. The lease covers the whole editorial run, not only individual browser calls, so the next owner reads history only after the prior owner has saved and linted its result.

## 1. Browser preflight and bounded recovery

After the device-activity gate passes, initialize Chrome control once and retain that browser binding for the run. Always create a fresh temporary X tab; never reuse a tab handle from a prior scheduled task.

Before recording Snapshot A, open a short X `Latest` query and confirm that at least one visible result can expose its timestamp and visible metrics. If Chrome discovery or connection initially fails, use the browser capability's setup or Chrome troubleshooting guidance and retry the preflight once. If it still fails, return `SKIPPED_X_SESSION_UNAVAILABLE`.

During research:

- if a tab is stale, missing, closed, or reports `No tab with id`, discard only the tab binding, create a fresh tab from the existing browser binding, and retry that operation once;
- issue X `Latest` searches serially and allow roughly 2.5–4 seconds after each navigation for result cards to settle; do not run parallel searches or a rapid navigation burst against the same signed-in session;
- for PolymarketAlpha, keep every query to at most six positive handles or terms; use compact negative exclusions where X syntax permits and apply the complete deterministic regional filter locally;
- if a narrow Alpha search unexpectedly has no result cards, run a known-broad short baseline probe once. If the baseline works, classify the narrow result as `EMPTY_OR_QUERY_SHAPE`, retry that lane once with fewer terms, and continue without declaring the session unavailable;
- if the Alpha baseline also has no cards or the page shows a generic error, classify it as a session-level search failure, stop the query sequence, preserve prior successful results, wait 30–45 seconds, then retry once in a fresh tab with a shorter equivalent query; other accounts retain their existing bounded generic-error path;
- treat an immediate fresh-tab retry without that cooldown as the same failed recovery attempt, because a session-level X search error can persist across tabs;
- never count a failed or empty-error search as evidence;
- use a directly readable status URL only to refresh a candidate already discovered through a valid query lane;
- inspect heterogeneous tool-call results by their actual shapes rather than assuming every result has `.output`;
- record preflight and recovery attempts in the research audit.

## 2. Load recent project context

Before opening X, run:

```bash
python3 scripts/build_run_context.py --root <project-root> --account <account> --now <ISO-8601-with-timezone>
```

Treat `blocked_story_keys`, recent openings, evidence paths, and ending texts as hard editorial context. Check the prior seven days for the same event and the current day for style repetition. If the same event has a material new development, declare `follow_up_to` and `material_new_fact`; otherwise reject it.

## 3. Snapshot A: bounded discovery

Record `snapshot_a_at`, then run small X `Latest` queries rather than one large OR chain. Search no more than six handles or terms per query because long expressions often return noisy or incomplete results.

Every account uses:

1. two trusted-newsroom queries;
2. two official or major-entity queries;
3. separate `min_faves:20` and `min_retweets:5` high-engagement queries;
4. one broad synonym query without an engagement filter.

Account seeds:

- **PolymarketAlpha:** Reuters, Bloomberg (`@business`), CNBC, Financial Times, First Squawk, FinancialJuice; Fed, BLS, US Treasury, SEC, CFTC, ECB, Eurostat, Bank of England, FCA, ESMA, major US/European banks and ETFs; rates, CPI, jobs, dollar, euro, sterling, oil, gold, Bitcoin, Ethereum, stablecoins, filings, flows, liquidations and regulation. Keep each lane short. Use only a compact subset of negative China terms where X syntax permits, then independently apply the complete mainland China, Hong Kong and Macau policy, macro, currency, market and company hard filter before heat scoring; only a run-specific explicit user override may admit one.
- **PolyPredX:** Reuters, AP, BBC, Axios and major regional newsrooms; heads of government, foreign and defence ministries, NATO, UN, courts and legislatures; Iran, Israel, Ukraine, Russia, China, Taiwan, sanctions, strike, ceasefire, talks, vote, ruling and election. Run geopolitics before domestic politics.
- **PredX_Labs:** Fabrizio Romano, David Ornstein, Sky Sports News, BBC Sport, ESPN and major league or club accounts; transfer, medical, injury, lineup, contract, suspension, score, upset and record. Run football before the wider-sports fallback.
- **PredX_News:** Reuters, AP, CNBC, The Verge, TechCrunch and major specialist outlets; OpenAI, Anthropic, Google, Meta, Microsoft, Apple, Nvidia, leading chipmakers, cybersecurity agencies and space companies; model, chip, breach, launch, ruling, investment, outage and scientific result.

Keep only visible metadata on the first pass. Build:

- a ranked pool of 15–25 distinct candidates when practical;
- a three-item watchlist containing near-threshold, very fresh or fast-accelerating events;
- the two leading candidates for truth verification.

For PolymarketAlpha, record the regional-gate result before ranking. A China-related candidate is `REJECTED_CHINA_HARD_GATE`, never watchlisted, selected, or retained as a fallback. A usable Alpha item must record `audience_region: "US_EU"`, `china_related: false`, and `audience_timezone: "UTC"`. Normalize its source, disclosure and X-evidence clocks to UTC before writing; the local `Asia/Shanghai` task time belongs only to scheduling and operational audit fields.

Do not discard a credible five-minute-old post merely because it has not yet accumulated the second independent echo; place it on the watchlist for Snapshot B.

## 4. Use the observation interval actively

If Snapshot A has no qualified candidate, do not return `HOLD` immediately and do not wait idly. During the next several minutes:

1. verify the watchlist's source time and central fact;
2. inspect a compact fresh-headline, RSS, filing or official-news surface;
3. take at most five promising external headlines published in the prior 90 minutes;
4. search each seed back on X using a short exact query: named entity plus action, distinctive number, or quoted event phrase;
5. re-search the watchlist for independent echoes, translated names and common aliases.

Separate three clocks: underlying event time, first credible disclosure time, and current X diffusion time. A fresh X post carrying an old fact is stale; a newly disclosed older incident or a concrete new project step is fresh.

## 5. Snapshot B: delayed hot refresh

Do not issue a researched `HOLD` until the second snapshot is taken at least eight minutes after Snapshot A when the run remains active. Aim for an 8–15 minute observation span without extending a run that already has a qualified candidate.

Snapshot B must repeat only:

- the two high-engagement queries;
- the account's major-entity query;
- exact searches for the three-item watchlist;
- exact X searches for the strongest external seeds.

Record first and final metrics for accelerating posts. A story that first appears after the scheduled trigger remains eligible; the scheduled time is the start of observation, not the candidate cutoff.

## 6. Freshness tiers

- **Tier A:** current material fact disclosed within 60 minutes and qualified `HOT` or `WARM` X demand.
- **Tier B live fallback:** fact disclosed 61–180 minutes ago, still live or developing, and supported by at least two distinct relevant X echoes from the last 60 minutes, with `latest_fresh_echo_at` recorded. Rank below every qualified Tier A candidate.
- **Tier C PolymarketAlpha Verified Market Brief:** evaluate only after Snapshot B proves that Tier A/B has no qualified Alpha item. The current fact may be 0–720 minutes old and X may be `UNPROVEN`, but the item must have `impact_score >= 6`, pass the US/EU and China gates, be non-duplicate, and use `primary`, `multi_source`, or `single_reputable` verification. A single reputable source stays `REVIEW`; `JUST IN` is forbidden; limit the mode to one Alpha item per account-day.
- **Reject:** old fact merely reposted, no current development, no recent echo burst, or older than 180 minutes outside the authorized Alpha Tier C fallback.

For Tier B, set `x_signal.live_event`, `fresh_echo_count`, and `latest_fresh_echo_at`; select a recent echo as the demand anchor when possible.

## 7. Recovery and stop conditions

The scheduled task itself is already the Sol `xhigh` pass. Do not delegate or spawn a Luna, Sol, or other-model rescue. After Snapshot B, evaluate the Alpha Tier C fallback when the target account is PolymarketAlpha. Return `HOLD` only when both the strict pool and the authorized Alpha fallback have no qualified candidate; other accounts retain the strict stop rule.

The audit must show:

- the shared-run lock owner, token id (never the full token), acquisition time, heartbeat checkpoints, release result, and any stale-lease recovery;
- both snapshot times and observation span;
- query lanes and visible candidate counts;
- watchlist changes between snapshots;
- external seeds searched back on X;
- browser preflight result and any bounded recovery attempts;
- top rejection reasons.
