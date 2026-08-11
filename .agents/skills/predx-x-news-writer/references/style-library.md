# Style library

Select structure from the news rather than filling a fixed template. Record a style fingerprint before drafting:

`opening type / evidence path / ending function / block count`

Example: `number-led / data stack / next catalyst / 5 blocks`.

## Opening types

1. **Breaking label** — `JUST IN:` plus one short, newly verified development. Reserve for events inside the normal 60-minute window with a qualified X signal.
2. **Direct fact** — state the change immediately in one short objective sentence without a label.
3. **Number-led** — open with the scale, record, vote, price, score, or flow.
4. **Named actor** — start with the person, institution, company, team, or regulator making the decision.
5. **Contrast** — place the new result against the prior expectation or trend.
6. **Timeline** — begin with the earlier position, then introduce the new step.

## Evidence paths

1. **Fact → driver → consequence** — the default for explained news.
2. **Data stack → interpretation** — two to five material figures followed by what they show.
3. **Decision → procedure → next vote** — legislation, courts, appointments, and regulation.
4. **Claim → response → unresolved fact** — diplomacy, conflict, investigations, and disputed reports.
5. **Prior state → reversal → next catalyst** — markets, policy expectations, and technology shifts.
6. **Fixture → form or availability → competition stakes** — football and other sports.
7. **Capability or incident → mechanism → broader implication** — AI, chips, cybersecurity, and science.
8. **Record → comparison → structural driver** — milestones and exceptional data.

## Ending functions

1. Next observable catalyst.
2. Procedural checkpoint.
3. Constraint or evidence gap.
4. Limited implication.
5. Specific unresolved factual question.
6. Audience-facing question tied to the real choice or uncertainty, such as `你认为真正的变量是需求还是供应？`; never use a bare `你怎么看？`.
7. Short verdict or takeaway, such as `这才是真正的考验。`, `The margin is now the story.`, or another source-grounded one-line close.
8. No separate ending when the consequence already closes the post.

Ending variation is checked from the actual final sentence, not only the declared function. Before drafting the last block, read the same-day ending texts from `build_run_context.py` and avoid reusing their lead-in grammar or rhetorical frame. In particular, do not repeat families such as `能否……取决于`, `真正的考验`, `关键在于`, `这意味着`, `The test is whether`, `The question is whether`, or `What matters now` within one account's day.

Do not treat `接下来`, `下一步`, `Next`, `The next signal`, and `What happens next` as neutral defaults. Use them only for functions 1–2 when the source provides an observable catalyst. Preserve the selected ending function across Chinese and English: a question remains a question, a short verdict remains a short verdict, and an omitted ending stays omitted.

## Account tendencies

- PolymarketAlpha: number-led, contrast, data stack, measured implication, next catalyst.
- PolyPredX: named actor, timeline, decision-procedure, claim-response, next vote or unresolved provision.
- PredX_Labs: direct fact, fixture-form-stakes, milestone, availability, next leg or competition consequence.
- PredX_News: direct fact, contrast, incident-mechanism, measured implication, capability limit or next verification.

These are tendencies, not account templates. Choose a different structure when the event demands it.

## Batch variation controls

- Use at least three evidence paths across a four-account batch when qualified material allows.
- Do not use the same opening type more than twice.
- Do not use the same evidence path more than twice.
- Use at least three ending functions across a four-account batch when the evidence allows, and use at least two block counts when natural.
- Use `JUST IN:` for no more than two posts and normally no more than one.
- Do not use an abstract thesis as the opening when a shorter event statement is available.
- Use an audience-facing closing question for no more than one post in a four-account batch, and only when it is specific to a real uncertainty.
- Do not let more than two posts in a four-account batch start the final block with next-step language; never allow all four to do so.
- Across four scheduled drafts for one account, use an audience-facing question no more than once unless the user explicitly asks for more interaction.
- Avoid repeating the same first three words of a closing block in consecutive same-day drafts.
- If the history-aware lint reports a repeated ending phrase family or similar final wording, rewrite the whole rhetorical frame rather than swapping one transition word.
- Compare with available same-day outputs. Treat the same opening plus the same paragraph-role sequence as a near-duplicate even when nouns change.
- Do not manufacture variety with slang, memes, outrage, excessive emoji, unsupported opinions, or arbitrary sentence fragments.

## Anti-template check

Before release, hide the account names and compare the four drafts. Revise if they share the same:

- first-line grammar;
- number and order of paragraph roles;
- transition phrases;
- final sentence function;
- rhythm of long and short sentences.

Preserve common house voice while changing the route through the facts.
