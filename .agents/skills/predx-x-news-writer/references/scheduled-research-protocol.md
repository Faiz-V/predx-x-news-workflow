# Scheduled research protocol

Use this protocol for every scheduled account run. It is designed for Luna: short fixed lanes, a small watchlist, deterministic history context, and two X snapshots before `HOLD`.

## 1. Load recent project context

Before opening X, run:

```bash
python3 scripts/build_run_context.py --root <project-root> --account <account> --now <ISO-8601-with-timezone>
```

Treat `blocked_story_keys`, recent openings, evidence paths, and ending texts as hard editorial context. Check the prior seven days for the same event and the current day for style repetition. If the same event has a material new development, declare `follow_up_to` and `material_new_fact`; otherwise reject it.

## 2. Snapshot A: bounded discovery

Record `snapshot_a_at`, then run small X `Latest` queries rather than one large OR chain. Search no more than six handles or terms per query because long expressions often return noisy or incomplete results.

Every account uses:

1. two trusted-newsroom queries;
2. two official or major-entity queries;
3. separate `min_faves:20` and `min_retweets:5` high-engagement queries;
4. one broad synonym query without an engagement filter.

Account seeds:

- **PolymarketAlpha:** Reuters, Bloomberg (`@business`), CNBC, Financial Times, First Squawk, FinancialJuice; Fed, BLS, Treasury, SEC, major banks and ETFs; rates, CPI, jobs, dollar, oil, gold, Bitcoin, Ethereum, stablecoins, filings, flows, liquidations and regulation.
- **PolyPredX:** Reuters, AP, BBC, Axios and major regional newsrooms; heads of government, foreign and defence ministries, NATO, UN, courts and legislatures; Iran, Israel, Ukraine, Russia, China, Taiwan, sanctions, strike, ceasefire, talks, vote, ruling and election. Run geopolitics before domestic politics.
- **PredX_Labs:** Fabrizio Romano, David Ornstein, Sky Sports News, BBC Sport, ESPN and major league or club accounts; transfer, medical, injury, lineup, contract, suspension, score, upset and record. Run football before the wider-sports fallback.
- **PredX_News:** Reuters, AP, CNBC, The Verge, TechCrunch and major specialist outlets; OpenAI, Anthropic, Google, Meta, Microsoft, Apple, Nvidia, leading chipmakers, cybersecurity agencies and space companies; model, chip, breach, launch, ruling, investment, outage and scientific result.

Keep only visible metadata on the first pass. Build:

- a ranked pool of 15–25 distinct candidates when practical;
- a three-item watchlist containing near-threshold, very fresh or fast-accelerating events;
- the two leading candidates for truth verification.

Do not discard a credible five-minute-old post merely because it has not yet accumulated the second independent echo; place it on the watchlist for Snapshot B.

## 3. Use the observation interval actively

If Snapshot A has no qualified candidate, do not return `HOLD` immediately and do not wait idly. During the next several minutes:

1. verify the watchlist's source time and central fact;
2. inspect a compact fresh-headline, RSS, filing or official-news surface;
3. take at most five promising external headlines published in the prior 90 minutes;
4. search each seed back on X using a short exact query: named entity plus action, distinctive number, or quoted event phrase;
5. re-search the watchlist for independent echoes, translated names and common aliases.

Separate three clocks: underlying event time, first credible disclosure time, and current X diffusion time. A fresh X post carrying an old fact is stale; a newly disclosed older incident or a concrete new project step is fresh.

## 4. Snapshot B: delayed hot refresh

Do not issue a researched `HOLD` until the second snapshot is taken at least eight minutes after Snapshot A when the run remains active. Aim for an 8–15 minute observation span without extending a run that already has a qualified candidate.

Snapshot B must repeat only:

- the two high-engagement queries;
- the account's major-entity query;
- exact searches for the three-item watchlist;
- exact X searches for the strongest external seeds.

Record first and final metrics for accelerating posts. A story that first appears after the scheduled trigger remains eligible; the scheduled time is the start of observation, not the candidate cutoff.

## 5. Freshness tiers

- **Tier A:** current material fact disclosed within 60 minutes and qualified `HOT` or `WARM` X demand.
- **Tier B live fallback:** fact disclosed 61–180 minutes ago, still live or developing, and supported by at least two distinct relevant X echoes from the last 60 minutes, with `latest_fresh_echo_at` recorded. Rank below every qualified Tier A candidate.
- **Reject:** old fact merely reposted, no current development, no recent echo burst, or older than 180 minutes.

For Tier B, set `x_signal.live_event`, `fresh_echo_count`, and `latest_fresh_echo_at`; select a recent echo as the demand anchor when possible.

## 6. Rescue and stop conditions

If Luna still has only `UNPROVEN` or rejected candidates after Snapshot B, run at most one bounded Sol `xhigh` rescue when delegation is available. Pass only the account, both snapshot times, query audit, ranked pool, watchlist, external seeds and rejection reasons. Sol may revisit high-engagement, major-entity and exact-event lanes, but must not repeat the full workflow.

Return `HOLD` only after Snapshot B and the available rescue. The audit must show:

- both snapshot times and observation span;
- query lanes and visible candidate counts;
- watchlist changes between snapshots;
- external seeds searched back on X;
- rescue result;
- top rejection reasons.
