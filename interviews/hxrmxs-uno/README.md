# HXRMXS UNO corpus — interview dialogue for characters

**Source:** `prx0r/geometricengine` (GitHub redirects to `prx0r/hxrmxs-uno-engine`,
"graph-native pedagogical policy engine"), `uno.txt` — imported 2026-10-21.
Same owner; no repo license file. Raw source-of-truth kept verbatim
(`uno.txt`); `episodes.jsonl` = the same data normalized one-episode-per-line
(the raw file is5 concatenated JSON arrays).

## What it is

- **343 therapy/pedagogy episodes** across6 lineages:
  Socratic 60, Therapeutic 58, Gurdjieffian 56, Buddhist **74**, Realist 55,
  Advaita 40 — the Buddhist block is sutta-adapted (asitis_*: AN3.65 kalama
  overlaps our sutta mine; AN4.111 horse-trainer) and the shelf includes
  classical interlocutors (Gorgias, Diogenes — matches diogenes-tub-cynic)
- **763 real human lines** (user role): disclosures, pushback, doubt,
  stage directions (`[Fidgets.]`, `[Laughs.]`) — actual interlocutor speech
- Assistant turns are HXRMXS pedagogy blocks: `lineage/phase/function_id/
  student_state/mechanism_shape/teaching_actions/register/style/intent/
  approach/impact_*` — a complete response-strategy scaffold
- Taxonomies (`taxonomies/`): **registers.txt** (24 registers × 6
  dimensions: intensity/intimacy/attunement/…), mechanisms.txt,
  functions-taxonomy.txt

## How we use it (characters/interviews)

1. **Interview prompt set** — the763 user lines are ready-made *real*
   interviewer/audience inputs: run a character (qwen-flash-character +
   personality.txt) against them and you get interview behavior for free
   ("That's not what I meant." is a better probe than anything we'd write).
2. **Lineages as reply modes** — mapping is almost one-to-one with our cast:
   buddha ← Buddhist/Advaita; grey ← Realist; interrogators ← Socratic;
   containment ← Therapeutic. The assistant blocks show *how* each mode
   steers (intent/approach/impact), usable as interview-agent instructions.
3. **Registers → voice** — the 24-register set is a speech-mode dial for
   `identity voice.tags` / interview_style (which register a character
   speaks an interview in), pending a wiring pass.

## Load

```python
import json
eps = [json.loads(l) for l in open("episodes.jsonl")]
users = [m["content"] for e in eps for m in e["messages"]
         if m["role"] == "user"]
```

`stats.json` = counts. Nothing here is for joke-gating — this is
discourse/interview material, not comedy eval.
