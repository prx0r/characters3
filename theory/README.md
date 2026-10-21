# Theory profiles — full comedian depth for our characters

**Target depth: louis-ck's graph** (funnygraph `comedian-graph.json`, 34 top
keys) — applied to our37 characters in `profiles/<slug>.json`.

## Field map (louis parity + our additions)

| field | louis has | our rule |
|---|---|---|
| `bio` | wikidata facts | `{type, origin, summary}` — **summary is prose bio** (3-5 sentences: who they are, what the act is, the tell). historical/entity/fictional — never invented wikidata |
| `identity` | d17 deal/premise/threads/etc | packed from character.json (+genome when thin) |
| `engine` | delivery archetype + MARY + voice | delivery style/archetype + voice cast state; MARY = null until measured |
| `gtvh_profile` | SO/LM/TA/NS (+note) | **all six KRs** (SO, LM, SI, TA, NS, LA) + `note` (authored vs derived) |
| `timing_profile` | hypothesis + measured | computed pause/hold numbers from delivery/style + honest hypothesis (`measured:false` until audio) |
| `known_bits` | `{title, why_it_works, theory_links[]}` | **why_it_works = real analysis prose** citing the mechanism (which KRs fire, bv, target) — NOT tier strings (tier strings = baseline only, `authored:false`) |
| `theory_links` | internal/external cites (dpv, Attardo…) | `{id, cite, claim, applies_to}` — `applies_to` must point at THEIR bits, never generic |
| `essay_seeds` | n seeds w/ thesis+outline | ≥1 per character at tranche completion |
| `humor_type / modes / style` | typed vocab | mapped from vibe/actions; `source: derived` until authored |
| `rating / metrics` | headline + boards | rating = `{headline: null, note: "no human votes — Wilson pending"}` until judged; metrics = human trial counts from ledger |
| `tier / sets / set_queue / specials_rated / provenance` | ✓ | tier from INDEX readiness; specials_rated = `[]` + honest note (no specials yet) |

## Honesty labels (binding)

Every authored claim carries provenance: `provenance.authored` vs
`provenance.derived` vs `provenance.computed` lists. `rating.headline`
stays null until Wilson crowns (n≥30, CI excludes .5). Never wikidata-
invent for fictional/entity characters.

## Tiers of depth

1. **tranche 1 (done first):** buddha, gray-x, ralph — full authored
   everything (6KR w/ per-bit evidence, theory_links with real cites,
   essay_seeds, prose bio polish).
2. tranches 2-4: remaining FINAL+CONTENDER → DRAFTs (thinner is OK for
   DRAFTs but every profile gets bio + humor_type + gtvh + timing + sets).

## Build

```bash
python3 build_profiles.py            # assemble all 37 (authored fields preserved)
python3 build_profiles.py --only gray-x
python3 -m pytest ../tests/test_profiles.py -q
```
