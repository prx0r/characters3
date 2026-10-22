# Zen source triage — what we may quote (sayings) vs what we may only study

Zen koans ARE jokes (setup → no mechanism → the pause does the work), and
a zen character with genuinely slow delivery (holds 3000ms+) is a top-tier
idea. But **English zen translations are mostly modern copyright** — unlike
the KJV/Jataka/Legge batch. Rule: sayings.jsonl only receives text we
clear. Study-only material goes to research reading, never to sayings.

## Likely CLEAR (PD in US — verify edition date at fetch, pre-1930 US)

| candidate | why |
|---|---|
| D.T. Suzuki, *Essays in Zen Buddhism* vol.1 (1927) | pre-1930 → PD-US; includes koan material (Hakuin chapters) |
| D.T. Suzuki, *The Zen Doctrine of No-Mind* (1929) | pre-1930 → PD-US |
| Soyen Shaku, *Zen for Americans* (1906) | pre-1930, sermons w/ koan usage |
| Any pre-1923 US-published English edition | standard PD rule |
| Chinese/Japanese originals | ancient → PD by age; translation is the issue, not the source |

## BLOCKED (contemporary translations — study only)

- Huang-Po (*Awakening of the Heart* / Bloom) ✗
- Blue Cliff Record (Cleary 1977) ✗ / Gateless Gate (modern trans) ✗
- Watts, Red Pine, Leighton/Shibayama, contemporary Roshi books ✗

## Also verify per-import (not blocked, not clear yet)

- Hakuin English translations (mix of eras)
- *The Record of Linji*, *Ching-te Record* (which English edition?)

## Procedure when a candidate clears

`tools/text_sources.py` gains an adapter (zen adapter: koan = unit,
attribution = collection + case number), then same pipeline:
sayings → passages → archetype (slowest holds in the system) →
delivery_mutate with 3000ms+ floors. The delivery IS the joke.
