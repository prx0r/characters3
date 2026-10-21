# characters3 — the finalized characters

Where a character goes when it's done: **identity pack (SDK fields) + mesh
+ graph + bits + delivery + tracked feedback.** Nothing experimental lives
here — this is the roster freaktown performs.

## Topology

| repo | role |
|---|---|
| `characters2` | research archive: experiments, corpora, lore, tools. Packs graduate OUT of it. |
| **`characters3`** | **canonical finalized characters** (this repo). |
| `characters` | delivery engine (render → sealed-set.v1). |
| `freaktown` | stage (consumes sealed sets, live/podcast sets). |
| `gcomedy` | library (knowledge mirror for the book/essays). |

## Layout

```
characters/<slug>/
  character.json     identity: persona, voice.tags, delivery.style/overrides (SDK)
  delivery.json      beat score when authored
  mesh.json          freaktown mesh assignment (default/plausible/confident)
  set.wav            rendered minute (when produced)
  meta.json …        pack extras
graph/
  GRAPH.json         unified graph: characters x bits x canon x lore x theory
  performers/*.json  full performer graphs (stage + AI characters)
bits/
  BIT-LEDGER.json    every AI bit, attributed, ranked (Wilson)
  sets/*.json        sets (hand / mined / generated / rescued)
feedback/
  rewards.jsonl      THE reward log — human + agent events, TRACKED IN GIT
  votes/*            per-audition button presses + feedback.v1 docs
INDEX.json           promotion rollup (tiers, counts, human_judged)
```

## Rules

1. **Characters graduate:** a pack lands here only when SDK-ready
   (voice.tags + delivery + mesh entry). Research stays in characters2.
2. **Feedback is first-class and tracked** — `feedback/rewards.jsonl` is
   the source of truth, not a gitignored cache. Human votes dispose.
3. **Sync direction:** `sync_from_characters2.py` pulls until characters3
   becomes canonical for writes (then the arrow flips and characters2
   reads from here).
4. Nothing here publishes itself — human approves every stage/air push.
