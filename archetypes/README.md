# Archetypes — core theory + theory-grounded mutations

**freaktown.archetype.v1** — why a character is funny *at all*, before any
bit exists, and which contradictions land **because** of that core.

The insight (owner, 2026-10-21): define the core theory once, then
mutate it in funny ways — *"an angry Buddha is funny because of their
views on anger."* The mutation's comedy is a GTVH **self-contradiction**:
the character refutes their own script in real time; delivery (NS) stays
true to the archetype so the contradiction has nowhere to hide.

## Shape

```jsonc
{
  "schema": "freaktown.archetype.v1",
  "id": "arch:buddha", "name": "The Awakened Deadpan",
  "members": ["buddha-ultimate-deadpan"],          // packs now or derived
  "core_theory": {
    "funny_because": "character-level SO — one paragraph, why this being
                      doing standup is inherently comic",
    "doctrine_source": "character.json.philosophy | genome-lore | canon",
    "doctrine": { ...the invariant claims (verbatim from pack) },
    "status_model": "...", "register": "...",
    "delivery_default": {"vibe": "...", "style": "...", "punchline_hold_ms": 1500}
  },
  "violations_that_work": [{
    "id": "wrath", "label": "Buddha (Angry)",
    "contradicts": "axiology: Stillness, punchlines and exact change are good",
    "why_funny": "his own thesis refutes him mid-lesson — SO self-contradiction
                  (teacher caught inside his own teaching); NS/timing stay
                  serene so the anger has nowhere to normalize",
    "mutant_premise": "<authored line — engine never invents prose>",
    "mutant_thread": "<authored>",
    "delivery": "preserved"       // doctrine-inversion keeps NS; status-flip may change it
  }],
  "mutation_operators": [ /* shared operators, theory basis each */ ]
}
```

## Operators (theory basis)

| id | theory | what changes | what MUST NOT |
|---|---|---|---|
| `doctrine-inversion` | GTVH SO self-contradiction; the character becomes evidence against their own script | premise + thread + vibe/label; **delivery only if violation declares `delivery_mutate`** (buddha-angry: wrathful vibe + tighter holds + hotter temp, style kept as carrier); **`saying_selector` = curated VIEW of base verbatim sayings by tone (never new words)** | **philosophy (doctrine stays!) + any generated text — EXTRACT-NEVER-WRITE** |
| `status-flip` | status_invert (KR-TA) | vibe, modulators, register | lore facts, doctrine |
| `thread-corruption` | rigidify still, invariant swapped (KR-LM) | one named thread's constant | the rigidify engine itself |
| `lore-injection` | SI addition (KR-SI) from canon/lore | premise/thread w/ sourced lore event | doctrine, TA target |

## Rules

1. **Engine assembles, authors write**: `mutant_premise` / `mutant_thread`
   are authored strings in the archetype; `mutate.py` never generates prose.
2. Mutants inherit SDK fields (voice/delivery) + get fresh identity/profile;
   provenance records `{base, operator, violation, theory_basis}`.
3. Mutants are `characters/<base>-<label>/` with `mutations` provenance —
   same profile pipeline (louis parity) applies to every mutant.
4. Honesty: doctrine quotes are verbatim from the pack (`doctrine_source`).

`python3 mutate.py buddha-ultimate-deadpan --violation wrath` → `buddha-angry`


## Sayings views (curation, not generation)

Base characters own the verbatim canon (`characters/<slug>/sayings.jsonl`;
buddha: 444 — mine + full Dhammapada, tones via lexicon-v1: harsh64/stern53).
A mutant with `saying_selector` gets a **view**: subset by tone, base ids
referenced (`view_of`), texts copied verbatim — asserted in tests that every
view text exists in base. `buddha-angry` = meanest lines (harsh/stern) +
wrathful delivery; base keeps all444.
