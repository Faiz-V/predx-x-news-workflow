# Verification and release rules

## READY

Use `READY` only when:

- the core event is supported by an eligible source;
- scheduled news selection has a `HOT` or `WARM` X demand signal, unless the user explicitly permits a news-platform fallback;
- the timestamp and story age are known;
- names, figures, units, quotations, and procedural stages are checked;
- the post contains the event, driver or material context, and consequence;
- uncertainty and single-source claims are accurately attributed;
- the Chinese mother draft fits the selected house-style envelope;
- the opening is short and news-forward, and multi-sentence blocks are exceptional;
- English matches Chinese block count, factual sequence, numbers, attribution, causal strength, and ending;
- both copies pass account, hashtag, public-content, and format rules.
- scheduled output includes a stable `story_key` and passes project-history checks for duplicate story, opening wording and actual ending wording.

## REVIEW

Use `REVIEW` when the event is credible but an editor must resolve a material issue, such as:

- a reputable report lacks primary confirmation;
- a translation, legal term, procedural stage, or exact timestamp needs checking;
- two reliable sources disagree on a non-core detail;
- the apparent cause is plausible but not verified;
- the bilingual copies contain a deliberate wording choice that cannot be made strictly equivalent;
- an explicit exception would mention a prediction market or product.

State the exact review item. Do not hide it in a generic caveat.

## HOLD

Use `HOLD` and omit both post bodies when:

- the central claim relies only on anonymous or low-quality material;
- reliable sources contradict the core event and cannot be reconciled;
- the item is outside the permitted freshness window without a live development;
- exact numbers, quotations, or the central causal claim cannot be traced;
- no suitable story exists for the account.
- a scheduled candidate is `UNPROVEN` on X and no fallback was explicitly permitted.
- a scheduled run has not completed Snapshot B from `scheduled-research-protocol.md`.

## Fact discipline

- Distinguish announcement, proposal, vote, approval, implementation, and enforcement.
- Distinguish allegation, confirmation, denial, forecast, and independent verification.
- Do not turn correlation into causation. Use “followed,” “came as,” “according to,” or explicitly limited inference when necessary.
- A “reason” may be a verified mechanism, an attributed explanation, or material context. Never invent causality to complete the house-style spine.
- Keep impact proportional: say what may change, what is already changing, and what evidence is still missing.
- For market moves, state the measurement window and source. Do not assign a headline as the cause unless evidence supports it.
- For injuries, transfers, elections, courts, appointments, and military events, prefer official confirmation or multiple reliable reports.
- Quote only words that appear in the source. Keep quotations short and attributed.

## Editorial discipline

- Do not pad a short story with generic history or repeated conclusions.
- Do not compress a qualified story into a source card that omits driver and consequence.
- Do not let English add analysis absent from Chinese or omit Chinese caveats.
- Keep advice, wagering encouragement, guarantees, partisan persuasion, graphic sensationalism, and engagement manipulation out of public copy.
- Never publish or perform engagement actions; human review remains mandatory.
