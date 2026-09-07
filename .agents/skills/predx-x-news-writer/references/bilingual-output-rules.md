# Bilingual output rules

## Chinese mother draft

Write Chinese first and treat it as the only content authority.

- Produce a complete, polished, reference-style post—not a bullet-point review brief.
- Include the verified event, driver or material context, and consequence.
- Preserve uncertainty, disputed claims, source attribution, and the next checkpoint when relevant.
- Keep source metadata and internal product relevance outside the post body.
- Lock the Chinese content before drafting English.

## English publication copy

Translate the locked Chinese draft with semantic one-to-one alignment and natural English phrasing.

- Use the same number of content blocks in the same order.
- Map each Chinese block to the corresponding English block.
- Preserve every material fact, number, unit, name, time, office, team, procedural stage, attribution, qualifier, and conclusion.
- Do not summarize, omit, reorder, amplify, soften, or add analysis.
- Do not add a title, question, CTA, or prediction that is absent from Chinese.
- Do not remove a limitation or uncertainty stated in Chinese.
- Regenerate the English copy after any material Chinese edit.

Semantic alignment does not require awkward word-for-word translation. English should sound native to readers in Europe and North America while carrying exactly the same information and emphasis.

## Alignment audit

Before release, compare the two bodies block by block:

1. Paragraph or content-block counts match.
2. Each block performs the same role.
3. All numerical claims and named entities appear in both.
4. Causal language has the same strength in both.
5. Allegations, forecasts, and uncertainty have the same attribution in both.
6. The ending reaches the same conclusion or next checkpoint.
7. Neither language contains facts missing from the other.

If alignment fails, revise English from the Chinese mother draft. Do not rewrite Chinese to justify an English addition.

## Public-copy controls

- Use the format envelopes in `house-style.md`; reference-style posts are not limited to 280 characters.
- Use zero hashtags by default and no more than one relevant hashtag.
- Keep URLs outside both post bodies unless the user explicitly requests an in-post link.
- Do not directly mention Polymarket, another prediction-market brand, probabilities, betting, wallet performance, or PredX features unless explicitly requested for that post.
- For PolymarketAlpha, convert explicit clock times to UTC before locking the Chinese draft, label them `UTC`, and mirror the same UTC time in English. This does not require a clock time or `UTC` label in every post. Keep collection, snapshot, verification, and audit wording outside the body; when a live-state qualifier matters, prefer “截至目前” in Chinese and natural `currently` phrasing in English. The automation's `Asia/Shanghai` trigger time is not publication time; never carry `UTC+8`, `GMT+8`, `CST`, “北京时间”, ET, CET/CEST or another local timezone into Alpha copy unless the user explicitly requests that timezone for the current run.
- Avoid routine “What do you think?”, “Share your thoughts,” and “Stay tuned” endings. A specific open question is allowed only when uncertainty is central to the story.
