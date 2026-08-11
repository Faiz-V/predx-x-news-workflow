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

Read both `references/scheduling-contract.md` and `references/scheduled-research-protocol.md` for scheduled batches. Read `references/product-context.md` only when internal relevance improves selection. Read `references/news-input-schema.md` when normalizing machine-collected material.

## Workflow

1. Establish the current time and timezone. Use `Asia/Shanghai` for scheduled runs unless instructed otherwise.
2. Start from an X-first news packet whenever available. For scheduled research, use the X collection chain below. Read only visible public pages or an already available signed-in browser session; never log in, expose credentials or cookies, manage proxies, solve CAPTCHAs, evade controls, or interact with posts.
3. Collect or accept several candidates per requested account, then apply the X demand gate in `references/x-demand-signals.md`. A news-platform article alone does not prove audience demand.
4. Normalize X timestamps and metric snapshots alongside source publication times, names, figures, attribution, uncertainty, and supporting links.
5. For scheduled runs, build recent project context with `scripts/build_run_context.py` before selection. Treat recent `story_key` values, openings and actual ending texts as comparison input, not optional memory. Reject stale, duplicate, unverifiable, account-incompatible, or trend-unproven items. Prefer X posts and supporting material from the last 30 minutes and normally require 60 minutes or less.
6. Among candidates that pass verification and freshness, rank by X heat, account fit, consequence, source confidence, novelty, and the clarity of the next observable development. For `PolyPredX`, first select from qualified geopolitical, conflict, diplomacy, sanctions, or international-security developments; use elections, legislation, courts, campaigns, and other political news only when that priority pool has no qualified story.
7. Assign one distinct story to each requested account. Do not reuse a story without explicit permission and a materially different verified angle.
8. Build a fact spine before writing: `event`, `driver or context`, `scale or evidence`, `consequence`, and an optional closing purpose. The closing purpose may be a checkpoint, constraint, limited implication, specific audience question, short verdict, or no separate ending. If a cause is unknown, state that rather than inventing one.
9. Select a style fingerprint from `references/style-library.md`: opening type, evidence path, ending function, and block count. Compare both the declared ending function and the actual final wording with available same-day outputs; do not disguise repeated `接下来`, `下一步`, or `Next` endings with different labels.
10. Write the complete Chinese mother draft first. Make the opening a short, title-like single sentence: use `JUST IN:` only for a genuinely fresh development, otherwise use an objective direct fact, number, named actor, or contrast.
11. Default to one sentence per block. Keep 4–6 visible blocks, but shorten each block before removing event, mechanism, or consequence. Use a second sentence only when it is essential to the same block's job. Let the consequence close the post when it already lands cleanly instead of appending a compulsory forecast paragraph.
12. Calibrate the Chinese draft against `references/house-style.md`. Remove padding, repeated conclusions, secondary examples, and background that does not change interpretation.
13. Lock the Chinese draft, then write English block by block. Preserve paragraph count, information order, figures, attribution, causal limits, and conclusion. Use idiomatic English without adding or dropping meaning.
14. Run the alignment, verification, format, hashtag, sentence-density, X-signal, public-content, duplicate-story, opening-similarity and actual-ending checks. For scheduled output, use `scripts/lint_output.py <output> --history-root <project-root> --as-of <time>`. Revise every error and treat warnings as editorial prompts.
15. Return the complete batch for human review in Markdown. For every `READY` or `REVIEW` result, paste both complete post bodies into the final response; a file link, status summary, notification card, or audit note must never replace the bodies. Never publish, schedule publication, like, reply, repost, follow, or send external messages.

## Scheduled X collection chain

Treat this sequence as a hard gate for scheduled runs:

1. After the device-activity check passes, use the available Chrome/browser-control capability to inspect X through the existing signed-in session in read-only mode. Do not enter, request, reveal, or modify credentials, cookies, storage, proxies, or account settings.
2. If browser control is unavailable, X is signed out, the session is blocked by a CAPTCHA or verification screen, or the page cannot expose post timestamps and visible metrics, stop with `SKIPPED_X_SESSION_UNAVAILABLE`. Do not call this `HOLD`, and do not substitute search-engine `site:x.com` results as an X heat snapshot.
3. Follow `scheduled-research-protocol.md`. Search X's `Latest` results through small fixed queries across trusted accounts, major entities, broad terms, separate high-engagement lanes, and exact X searches seeded by fresh external headlines.
4. Take Snapshot A, gather 15–25 visible candidates when practical, and keep a three-item watchlist for very fresh or near-threshold events. Record URL, post age, visible metrics, author type, fit and first snapshot time before opening articles.
5. Re-search the leading two or three stories by exact entity and event phrase to identify independent X echoes. A single newsroom post with no independent discussion is normally `UNPROVEN`.
6. Use web search, news sites, filings, RSS, and official pages only after the initial X pass, for factual verification, source-time checks, and fresh event seeds. Search every promising external seed back on X and require a qualified X signal before drafting.
7. If Snapshot A has no qualified story, use the interval for watchlist verification, compact external headline discovery and exact X back-searches. Take Snapshot B at least eight minutes after Snapshot A while the run remains active; repeat only high-engagement, major-entity, watchlist and external-seed lanes.
8. If Luna still has only `HOLD` or `UNPROVEN` candidates after Snapshot B, and model delegation is available, run exactly one bounded `gpt-5.6-sol` rescue pass at `xhigh`. Pass both snapshot times, the compact pool, watchlist, external seeds and rejection reasons; do not repeat the complete workflow or launch another rescue.
9. Return `HOLD` only after Snapshot B and the available rescue. Set `scheduled_run: true` and save the structured result under `runtime/predx-x-news-writer/<YYYY-MM-DD>/`, including stable `story_key` and `topic_key` values for every `READY` or `REVIEW` item and the complete research audit.

Never end a scheduled run after only generic web searches. Distinguish three outcomes: `SKIPPED_DISPLAY_INACTIVE`, `SKIPPED_X_SESSION_UNAVAILABLE`, and a fully researched `HOLD`.

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
- For scheduled batches, mark news-only candidates without a qualified X signal `HOLD` unless the user explicitly requests a news-platform fallback.
- Search-engine snippets and `site:x.com` results are discovery hints only; they cannot supply the visible-metric snapshot required for a scheduled `HOT` or `WARM` classification.

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
python3 scripts/lint_output.py output.json
```

Both scripts use only the Python standard library. `lint_output.py` defaults to `reference_long`; set an item's `post_mode` to `standard_x` only when a 280-character post was explicitly requested.
