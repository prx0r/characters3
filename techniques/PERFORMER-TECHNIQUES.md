# Performer techniques — archetypes of PERFORMANCE (not of character)

Character archetypes (archetypes/) answer *who the comic IS*. This answers
*how the act is built* — the technique layer a character can wear. Families
asked for: **surreal / spoken-word / performance / spirituality / music**
+ anti-comedy. Each entry: the mechanic, the timing profile it demands
(our engine knobs), how a character adopts it, and sources (researched
2026-10-22; local data cited where it exists).

## Index

| id | family | one-line mechanic | keeper example |
|---|---|---|---|
| `pull-back-and-reveal` | anti/comic-form | conceal the TRUE subject until the last moment (Lee's own name for it) | Stewart Lee |
| `deconstruction-meta` | anti | the act dissects its own joke in real time; refuses the "comic alibi" | Stewart Lee, Daniels' "comedy in a vacuum" critique |
| `repetition-erosion` | anti/surreal | say it again until it breaks or transmutes (Lee: repetition, callbacks) | Lee's Ang-Lee routine (academic analysis on file search) |
| `limerick-documentary` | surreal/spoken | form supplies punch position; performer supplies only sincerity about nonsense | **Edward Lear (in-repo: sayings 99, passages 19)** |
| `patter-speed` | music/spoken | metrical rapid-fire as a value in itself; speed contrast vs holds | W.S. Gilbert patter songs |
| `iambic-break` | spoken/performance | fixed meter, broken on the punch — variance becomes measurable | Shakespeare's fools/braggarts (queue) |
| `suspension-deadpan` | spiritual/surreal | "enters his own reality; deadpan authority over absurd premises" | Norm Macdonald (voicelab archetypes.json, measured: pitch std~10, dyn~13) |
| `non-release-holds` | spiritual | the punch is the REFUSAL of resolution — long holds with no switch | **buddha / laozi (in-repo: built this session)** |
| `deflation` | surreal | cosmic premise executed by procedure until it's plumbing | grey (arch:grey) |
| `mock-indignant-velocity` / `roast-bravado` / `manic-swing` / `whimsical-float` | (music/roast/surreal) | delivery archetypes with measured numbers | voicelab `archetypes.json` (6 archetypes, engine-side) |

## Entry: pull-back-and-reveal (the one we were reaching for)

- **Named by Stewart Lee himself**: "concealing the true subject of a joke
  until the last moment" (Wikipedia/Lee sources; also documented method of
  German performance — his note says it's harder there).
- **Toolkit around it**: repetition, internal reference, deadpan, fourth-
  wall breaks, *rhetorical deconstruction of the comedy itself* — the
  academic term on file is "deconstruction" (Bennett: "When Is a Joke Not
  a Joke?"); the punchline's comic alibi gets refused rather than honored.
- **Timing profile**: long patient setup (patience-testing tension) →
  snap reward. Maps to our knobs: hold floor 2500ms+ on setup, then
  Norrick fast punch; audience-co-performer does the rest.
- **Adoption for characters**: technique = `delivery_mutate` direction +
  a set-order rule (set up topic A, reveal topic-B-as-subject at close).
  Doesn't change sayings (EXTRACT holds) — it changes WHEN the subject
  lands.
- **Lineage note**: Lee's 2001 show *Pea Green Boat* = deconstruction of
  **Edward Lear's "Owl and the Pussycat"**. We now own both ends: Lear
  (arch:lear, 99 PD limericks) and the technique that ate him.

## How to use

1. Pick a technique → its timing profile becomes a `delivery_mutate`
   (or a full delivery recipe when a style is harvested).
2. Character keeps doctrine + sayings; technique changes order/timing.
3. Techniques with measured numbers (voicelab archetypes) plug into
   `delivery_engine` today; the doc-only ones (Lee) need a scribe →
   style_harvest pass first.

## Queue (not yet entries)

- Shakespeare fools: Falstaff/Dogberry selection + iambic-break entry
  (Gen Z modernization = edge-ladder-style REWRITE of delivery — a render
  mode, not sayings; do not put modernized text in any sayings canon).
- Gilbert patter (PD d1911), Chaucer comic tales (PD) — SOURCES.md rows.
- Modern slam/spoken word: blocked (copyright + earnest) — excluded by
  the comedy-first filter.
