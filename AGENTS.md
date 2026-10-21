# AGENTS.md — characters3

**This repo is the finalized roster.** Read README.md first (topology +
layout). Research never happens here — if you're experimenting, you're in
the wrong repo (characters2). Here you graduate, sync, or maintain.

## Binding rules

1. **Graduate, don't experiment.** A pack arrives via
   `sync_from_characters2.py` only after it's SDK-ready (voice.tags +
   delivery fields + mesh.json). Drafts, corpora, lore and tools stay in
   characters2.
2. **`feedback/rewards.jsonl` is tracked source-of-truth.** Human votes
   dispose; model/gate scores propose (never inverted). Agents may write
   events only with `human:false` + model name (see characters2
   theory/policy/rewards.py schema `freaktown.reward.v1`).
3. **Wilson before crowns** (n>=30, CI excludes 0.5) anywhere a rank or
   "funniest" claim appears in this repo (INDEX.json counts follow it).
4. **Mesh entries are data, not guesses:** `mesh.json` mirrors the engine
   repo's mesh-map (status: confident/plausible/default/todo). Only
   `default` may be assigned without a sniff/BODY_CATALOG pass.
5. **No publishing.** Stage/air pushes are human-approved, never
   automated. Spend: ASK FIRST, free tier only (engine's Fish s2.1-pro-free).
6. Secrets: env/vault only, never the tree. (Secret scanner hooks are
   installed repo-wide; they block `sk-`, `cfat_`, assignment patterns.)
7. Sync direction: characters2 → here, until this repo becomes canonical
   for writes; flipping direction is an owner decision recorded in README.

## Commands

```bash
python3 sync_from_characters2.py            # refresh projection from research
git status --short                          # feedback/ churn = new votes: commit them
```

No test suite yet (projection repo — validate by diff + INDEX counts).
When characters3 becomes canonical for writes, port the small test set
from characters2/theory/policy/.
