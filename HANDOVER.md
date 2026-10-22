# HANDOVER — characters3: what's built, how to use it, how to continue

> Session 2026-10-21/22. Read with `README.md` (topology) and `AGENTS.md`
> (rules). STATUS-equivalent: this file. Last state: **19 commits on
> master, unpushed** (owner pushes). Tests: `python3 -m pytest tests/ -q`
> → 35 green. Secrets: scanner hooks installed repo-wide (sk-, cfat_, assignment patterns blocked).

## 0. The system in one paragraph

characters3 is the canonical roster of finalized AI characters. A
character = identity pack (persona/philosophy/threads/voice/delivery) +
**verbatim sayings canon** + **archetype theory** (why they're funny +
which contradictions land) + identity bundle (qwen personality + stage
vocab) + louis-parity profile. Mutants are **curation + doctrine
contradiction**, never new prose (EXTRACT-NEVER-WRITE). Human votes are
the only reward; gates mask, never score.

## 1. Inventory (what this session created)

| area | files | what |
|---|---|---|
| minute loop | `minute.py` | character writes own minute → unslopnemo writer → per-bit L1/L2/L3 edge ladder → select(audience or `--edge` dial) → slop/victim masks → **60s floor with top-up rounds** → `minutes/*.json + .txt` (seal-ready) |
| mutation engine | `mutate.py` + `archetypes/*.json` | 6 archetypes: buddha, gnome, reptilian, grey, jesus, jonah, elijah, laozi (8) — violations with authored premise/thread + `saying_selector` (tone/topic views) + `delivery_mutate` + optional `visual` (freaktown closed vocab) |
| mutants built | `characters/buddha-*` etc. | buddha-angry/greedy/impatient/boastful/doom/passive, jesus-temple, jonah-eager, elijah-quiet, laozi-severe (doctrine byte-intact, tested) |
| sayings canons | `characters/*/sayings.jsonl` | buddha 444 (mine+Dhammapada, tone/topic lexicon), jesus 611 (KJV18 ranges), jonah 48, elijah 43, isaiah 42, nathan 14, laozi 236 (Legge) |
| passages | `characters/*/passages.jsonl` | buddha 95 (68 dhp +6 compilations +**21 Jataka tales**), jesus 18, jonah1, elijah2, laozi42 — all ≥60w, verbatim-asserted |
| profiles | `theory/profiles/*.json` + `build_profiles.py` | **53 packs** at louis-parity depth (bio, 6KR GTVH, theory_links, known_bits why-it-works, essay_seeds); tranche1+2 fully authored (buddha/grey/ralph/sef/britt/kyle/agent-black) |
| identity SDK | `build_identity.py` | personality.txt (qwen-flash-character system msg) + identity.json (stage vocab validated, default_face per vibe, livekit config) per pack |
| interviews corpus | `interviews/hxrmxs-uno/` | 343 episodes / 914 human lines / 6 lineages + 3 taxonomies; buddha↔Buddhist/Advaita, grey↔Realist, ella↔Socratic |
| tools | `tools/mine_sayings.py` (Dhammapada423 + tone/topic lexicon), `tools/text_sources.py` (KJV/Tao/Jataka adapters, verbatim assert), `tools/build_passages.py` | source adapters: bilara-json, bible-json, plain-text PD |
| tests | `tests/` (35) | passage floors, EXTRACT-NEVER-WRITE subsets, doctrine-preservation, duration floor (mocked), comedy markers (gourd, Cry aloud, ewe lamb, Crocodile) |
| docs | `docs/IDENTITY-SDK.md`, `docs/ZEN-SOURCE-TRIAGE.md`, `docs/SOURCES.md`, `archetypes/README.md`, `theory/README.md` | contracts + source queue |

## 2. How to use — the commands

```bash
# --- build a character's material from PD sources ---
python3 tools/text_sources.py --character jesus      # KJV ranges -> sayings+passages
python3 tools/text_sources.py --character jataka     # -> buddha passages
python3 tools/text_sources.py --character laozi      # Legge auto-fetches
python3 tools/mine_sayings.py                        # Dhammapada + tone/topics (buddha)
python3 tools/build_passages.py                      # group sayings -> passages

# --- mutate (archetype violations; doctrine preserved by construction) ---
python3 mutate.py --list                             # see all violations
python3 mutate.py buddha-ultimate-deadpan --violation wrath --as buddha-angry
python3 mutate.py --all                              # every violation
python3 build_identity.py                            # personality + identity.json (all packs)
python3 theory/build_profiles.py [--only slug]       # louis-parity profile (authored fields kept)

# --- perform: the character writes a minute, edged ---
python3 minute.py buddha-angry --audience club_latenight   # 60s floor + top-ups
python3 minute.py buddha-angry --edge 0.7                  # JEV edge dial (select_near)
python3 minute.py <slug> --seal                            # -> sealed-set.v1 (engine pack must be synced)
python3 theory/policy/judge.py --set <set.json>            # (chars2) human buttons -> rewards

# --- interviews (corpus as probes) ---
# personality.txt + episode user-lines; see interviews/hxrmxs-uno/README.md
# 4 working recipes: probe / lineage-briefed / cross-classical / pressure

# --- quality gates ---
python3 -m pytest tests/ -q      # 35 green; run after ANY pack/archetype change
python3 mutate.py --list         # roster + violations + delivery flags
```

**Model/cost:** writer + ladders = OpenRouter `thedrummer/unslopnemo-12b`
(key: vault `OPENROUTER_API_KEY` → env only). ~$0.002-0.005 per minute.
qwen-flash-character for interview/personality tests (~$0.001/call).

## 3. Contracts worth knowing (read before changing)

1. **EXTRACT-NEVER-WRITE** — mutants' sayings are tone/topic *views* of
   base canon; `tests/test_archetypes.py` asserts every view text exists
   in base. Archetype `mutant_premise/thread` strings are authored once
   by us, never generated by code.
2. **Doctrine preservation** — `mutate.py` never touches `philosophy`;
   doctrine-inversion keeps delivery unless the violation declares
   `delivery_mutate`. Tested per mutant.
3. **Freaktown closed vocabs** — face `neutral/deadpan/grin/annoyed/
   confused/surprised`, body8, triggers11. `identity.json` validates +
   reports violations (6 packs still use off-vocab triggers — known
   issues table in IDENTITY-SDK.md). `wrathful`/`prophetic` faces are a
   *requested extension*, not faked.
4. **Honest labels** — rating.headline null until Wilson; tone/topics =
   `lexicon-v1` (negation-blind: known flaw, e.g. boastful pool took a
   "the conqueror is NOT…" verse); Jataka = Babbitt *retelling*; zen =
   blocked translations (ZEN-SOURCE-TRIAGE).
5. **Sync direction** — chars2 → chars3 (`sync_from_characters2.py`)
   until owner flips canonical-for-writes (README rule). Engine mirror:
   packs must exist in `/root/characters/freaks` for `--seal`.

## 4. How to continue (ordered queue)

1. **Push** the 19 commits (owner button).
2. **Judge something** — render one minute (`minute.py buddha-angry
   --seal`) and get human buttons into `feedback/rewards.jsonl` (tracked
   here; judge CLI lives in chars2 `theory/policy/judge.py`). The loop
   still has ~4 reward events total — human votes are the bottleneck.
3. **SOURCES queue** (docs/SOURCES.md): WEB cross-check → Desert Fathers
   (Budge 1907) → Pirkei Avot → stoics (Seneca Gummere) → Enoch + Kybalion
   (lore feeds for grey/hermetic canon). Each = one adapter run.
4. **Isaiah/Nathan archetypes** (sayings+packs exist; needs core_theory +
   violations) → mutants.
5. **Zen**: only after a PD source clears per ZEN-SOURCE-TRIAGE.md; the
   zen character needs the slowest delivery (3000ms+ holds) — timing IS
   the joke.
6. **Face vocab extension request** to freaktown (wrathful/prophetic) +
   adopt kenney mesh candidates (their `inbox/` — sniff/BODY_CATALOG is
   their gate).
7. **Profile tranches 3-4**: remaining CONTENDER + DRAFT profiles at
   authored depth (specs + baseline exist; authoring pending).
8. **Lexicon-v2** (negation-aware: "is not the conqueror") for
   self_praise/harsh pools; then re-run affected saying views.
9. **Funnygraph bridge**: export profiles to their `comedians/` schema;
   verify `agent/navigate.py` reads them.
10. **LiveKit podcast**: agent entrypoint spec'd (IDENTITY-SDK), venv at
    `/root/venvs/livekit`, self-hosted server running (config+token in
    `/root/.livekit-env` 600) — needs the ~50-line entrypoint + a room.

## 5. Cross-repo map

| repo | role | state |
|---|---|---|
| **characters3** (here) | canonical roster + theory + loops | active, 19 unpushed |
| characters2 | research archive (jokegate, sutta mine, ledger, judge CLI) | archived-ish; packs graduate out |
| characters | delivery engine + freaks mirror (render/seal) | SDK live; packs synced |
| freaktown | stage/live/party (consumes sealed sets, face/actions) | origin/main pulled; delivery-SDK handoff docs |
| gcomedy | library (Attardo graph, knowledge mirror) | synced via `agent/sync_characters2.py` |
| influence2 | archaeology only (mined for LEARN-LOOP/feedback) | stale |

## 6. Session receipts (what landed when)

1. policy/judge/ingest/sheet/duel/brief (chars2) → tracked rewards.
2. sutta mine (7 sets, assert_verbatim) → promotion system → audits →
   **chars3 created + pushed** (public).
3. theory profiles (louis parity, tranches 1-2 authored).
4. archetype theory + mutation engine + buddha mutant shelf.
5. edge-ladder minute writer (unslopnemo) + 60s floor.
6. HXRMXS corpus import (343 episodes) + 4 interview recipes proven live.
7. KJV/Tao/Jataka/Dhammapada pipelines → 8 prophet/sage packs + 10
   mutants; zen triage + SOURCES queue.
