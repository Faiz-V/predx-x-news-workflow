# Source and freshness policy

## Freshness

- Priority A: published in the last 30 minutes.
- Priority B: 31–60 minutes old.
- Fallback: 61–180 minutes only when the event remains live, has a meaningful new development, and no fresher qualified story exists for that account.
- Older than 180 minutes: normally reject for a scheduled news batch.
- Calculate freshness from the earliest credible public disclosure of the current fact or from a new material development, not necessarily from when the underlying incident occurred. Record the event time, disclosure time, and collector time separately when available.
- A recently reposted old article is old unless the repost adds a new, attributable development. A previously unknown older incident that a company, regulator, court, or reputable newsroom has only just disclosed is a fresh disclosure and may qualify.
- Treat the scheduled trigger as the beginning of a collection interval, not a publication cutoff. A qualified event first posted during the run remains eligible and must be checked in Snapshot B.
- A 61–180 minute event may use the live fallback only when at least two distinct relevant X echoes from the last 60 minutes establish current demand; otherwise reject it as stale.

## Source tiers

1. Primary: government, regulator, court, league, club, company, executive, filing, transcript, official data release.
2. High-quality reporting: established newsrooms or specialist outlets with direct sourcing and a timestamp.
3. Named reporter or subject-matter specialist with a record of original reporting.
4. Aggregators and anonymous X accounts: discovery leads only.

Prefer a primary source plus one independent report for consequential or disputed claims. A single primary source may be enough for its own decision or announcement, but describe it as that source's statement.

## X-derived material

- Treat a post from the subject's verified official account as a primary statement, not proof that every embedded claim is true.
- Treat screenshots, clipped videos, translations, and anonymous posts as leads until independently verified.
- Preserve the original post URL and timestamp when supplied.
- Do not implement account login, cookie handling, proxy rotation, CAPTCHA handling, anti-detection, rate-limit evasion, or publishing in this skill.

## X demand gate

- For scheduled batches, begin with candidates visibly active on X; do not treat publication by a news platform alone as proof of audience demand.
- Apply `x-demand-signals.md` before drafting. X heat selects the story; eligible sources verify it.
- Prefer `HOT`, then `WARM`. Treat `UNPROVEN` as `HOLD` unless the user explicitly permits a news-platform fallback.
- A viral X post never overrides weak sourcing, a stale underlying event, or failed verification.

## Selection priorities

After verification and freshness gates, rank by:

1. X heat and relative engagement velocity;
2. fit for the account's audience;
3. consequence;
4. source confidence;
5. freshness;
6. novelty relative to today's prior batches;
7. clarity of the next observable development.

For `PolyPredX`, apply one account-specific priority after all truth, freshness, and X-demand gates: choose a qualified geopolitical, conflict, diplomacy, sanctions, or international-security story before a qualified general-politics story. This is a selection preference, never permission to use a weaker source, unresolved battlefield claim, stale update, or `UNPROVEN` X signal; when the priority pool fails any gate, use the strongest qualified election, legislative, judicial, campaign, or domestic-policy candidate instead.

Do not fill a slot with a rumor, recycled story, or low-impact item merely to satisfy volume. Return `HOLD` with a short explanation when the available packet is insufficient.
