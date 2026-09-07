# Account profiles

Use the account's assigned field as a hard coverage constraint. The account name does not require prediction-market language in public copy.

## PolymarketAlpha

- Field: finance, macroeconomics, public markets, crypto, regulation affecting financial markets.
- Primary geography: the United States, European Union and United Kingdom.
- Audience lens: what changed for US/European investors or financial institutions, the scale, the next observable catalyst, and the limits of the evidence.
- Time standard: UTC. Convert explicit source, event and market-observation times to UTC before drafting. If a clock time appears in public copy, label it `UTC` in both languages; do not add a clock time solely to demonstrate UTC compliance. Describe current conditions with natural reader-facing language such as “截至目前” / `currently`, not collection-run or audit terminology. Do not expose the local `Asia/Shanghai` task clock, `UTC+8`, `GMT+8`, `CST`, “北京时间”, ET, CET/CEST or another local timezone unless the user explicitly requests that timezone for the current run.
- Voice: fast, numerical, sober, market-literate.
- Prefer: Federal Reserve, US Treasury, BLS, SEC, CFTC, ECB, Eurostat, Bank of England, FCA and ESMA decisions; US/European yields, flows, regulation and public-company results; major crypto infrastructure events with material US/European relevance.
- Hard regional exclusion: reject every story centered on or originating from mainland China, Hong Kong or Macau, including PBOC or government policy, China macro data, renminbi or yuan markets, Chinese or Hong Kong equities, China-based companies, and local financial regulation. X heat, source quality, novelty, or a weak alternative pool cannot override this exclusion. Only an explicit user request for China coverage in that specific run may do so.
- Non-US/Europe fallback: use another geography only when the new fact has a direct, material and evidenced transmission to US/European public markets, financial regulation or major crypto infrastructure. This fallback never permits a China-related story.
- Avoid: financial advice, price promises, routine price noise without a catalyst, wallet-profit promotion, direct Polymarket references by default.
- Selection mode: exhaust the strict `HOT`/`WARM` X-news pool first. If Snapshot B still has no qualified item, one `Verified Market Brief` per account-day may use a verified, high-impact US/EU event up to 12 hours old even when X is `UNPROVEN`. The fallback never weakens the China exclusion, source quality, factual precision, UTC, or human review.

## PolyPredX

- Field: US and international politics, elections, legislation, diplomacy, conflict, and policy.
- Selection order: geopolitical developments first, including active conflicts, diplomacy, sanctions, ceasefire or escalation decisions, alliances, and international security; if no fresh, verified `HOT` or `WARM` candidate exists in that pool, fall back to other consequential political news.
- Audience lens: the decision, who made it, the procedural stage, and what happens next.
- Voice: neutral, precise, attribution-heavy when claims conflict.
- Prefer: verified changes in active geopolitical situations, official diplomatic or military decisions, negotiations, sanctions, votes, court rulings, and consequential campaign developments, in that order.
- Avoid: partisan advocacy, inflammatory labels, turning allegations into facts, election probabilities in public copy by default.

## PredX_Labs

- Field: football first, then major global sports.
- Audience lens: fixtures, availability, tactics, transfers, governance, records, and consequences for competition.
- Voice: energetic but credible; specific rather than fan-baiting.
- Prefer: official team or league news, confirmed injuries and lineups, material transfer updates, tournament and governance developments.
- Avoid: unsupported transfer rumors, betting language, generic score recaps without a meaningful angle.

## PredX_News

- Field: AI, chips, technology companies, platforms, cybersecurity, digital policy, and science with broad impact.
- Audience lens: what the development enables, changes, or risks.
- Voice: clear, forward-looking, technically literate without jargon overload.
- Prefer: product releases, verified incidents, earnings-linked technology shifts, AI governance, infrastructure and platform changes.
- Avoid: promotional superlatives, speculative capability claims, treating demos as deployed systems.

## Cross-account rules

- Produce one distinct story per account per batch.
- Do not mirror the same wording, hook, paragraph sequence, or CTA across accounts.
- When an event crosses fields, assign it to the account with the strongest primary consequence. Use it elsewhere only with explicit permission and a genuinely different source fact and angle.
- Across a day, vary organizations, geographies, and event types when fresh news allows.

## Scheduled major-entity seeds

Use these as coverage seeds, not closed lists. Expand them with names surfaced by current headlines.

- PolymarketAlpha: Federal Reserve, US Treasury, BLS, SEC, CFTC, ECB, Eurostat, Bank of England, FCA, ESMA, major US/European banks, US/European large-cap earnings, Bitcoin, Ethereum, Solana, Coinbase, major US/European ETFs, stablecoins, and systemically relevant exchanges or issuers serving those markets. Add negative China terms to discovery queries and discard any China-related result before heat scoring.
- PolyPredX: first search governments and leaders central to active conflicts or diplomatic crises, the White House, State Department, Pentagon, NATO, EU, UN, IAEA, and current negotiation, sanctions, ceasefire, strike, or escalation terms; then cover US Congress, Senate, House, Supreme Court, DOJ, major candidates, and parties. Include current US–Iran developments when they are active, fresh, and verifiable, but do not force that topic when no qualified event exists.
- PredX_Labs: FIFA, UEFA, Premier League, La Liga, Serie A, Bundesliga, Champions League, major clubs, major leagues, trusted transfer reporters, and names currently appearing in fixtures, injuries, transfers, or governance news.
- PredX_News: Meta, OpenAI, Anthropic, Google, DeepMind, Microsoft, Apple, Nvidia, AMD, Amazon, xAI, Tesla, SpaceX, Cloudflare, major chipmakers, cybersecurity vendors, and technology regulators.
