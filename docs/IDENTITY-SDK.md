# IDENTITY-SDK — plug-and-play characters across runtimes

> One bundle per character in `characters/<slug>/`: `identity.json` +
> `personality.txt` (built by `build_identity.py`). The same identity is
> served by three runtimes — standup, podcast, party — with freaktown's
> face/action systems and a LiveKit voice pipeline.

## The promise

A character graduates once and performs everywhere:

| runtime | engine | voice | face/actions |
|---|---|---|---|
| **standup** | `characters` repo `delivery_engine.py --seal` → sealed-set.v1 | Fish $0 + delivery style | `set_plan.json` beats (`performance.expression/gesture`, pauses delivery-authoritative) |
| **podcast** | LiveKit room agent | Qwen realtime (`qwen3.8-omni-flash-realtime`, OpenAI-shaped wss) | face/action events on the LiveKit data channel, freaktown vocabulary |
| **party** | freaktown party rooms (and/or LiveKit) | same as podcast | actions fire as buttons (`manual` triggers) |

## personality.txt — the stable self

A **qwen-flash-character** system message: name, personality, fixed
threads, backstory (genome lore), speech style, stage actions as
parentheticals, and the four rules (never break character, never claim
AI, parenthetical actions, same self in every mode).

- Built **deterministically** from pack fields — same input, same text.
- Thin packs fall back to their evolve-genome identity; `personality.source`
  says `pack` or `genome`.
- Regenerate only when the pack's identity changes (commit the diff —
  personality changes are *identity changes*, review them).

## stage_compat — freaktown's closed vocabularies

Validated against `freaktown:docs/CHARACTER_PACK.md` (origin/main):

- face: `neutral deadpan grin annoyed confused surprised`
- export face (delivery may emit; stage maps down): `smug smile frown disgusted`
- body: `normal hold still lean in look left look right shrug small gesture big gesture`
- triggers: `on_enter after_setup after_punchline after_tag on_laugh on_groan on_silence before_closer after_closer on_exit manual`

**Violations are reported, never auto-fixed** (`violations[]` in
identity.json). A stage that can't perform an action degrades to
`fallback`/`hold still` — silent degradation is their contract; ours is
to show you the mismatch first.

## livekit — voice wiring

```json
"livekit": {
  "personality_model": "qwen-flash-character",
  "realtime_model": "qwen3.8-omni-flash-realtime",
  "realtime_protocol": "OpenAI-realtime-shaped wss (session.update / response.create)",
  "endpoint_env": "QWEN_REALTIME_URL + QWEN_API_KEY (env/vault, never the tree)",
  "face_action_channel": "data channel messages, freaktown vocabulary"
}
```

Agent shape (when `pip install livekit-agents` lands in the runtime box):

1. room joins → load `identity.json` + `personality.txt`
2. `session.update` with instructions = personality.txt; audio 16k PCM in/out (Qwen realtime)
3. laughter/room events (party) → trigger map from `stage_compat.actions`
4. face/action events emitted as data-channel JSON:
   `{"face":"deadpan","body":"hold still","trigger":"after_punchline","action":"koan_hold"}`
   — always within the closed vocab, else the stage would degrade anyway.

**Status:** identity bundles built + committed. LiveKit runtime
**installed on the box** in a dedicated venv (PEP 668 — not system pip):

```
/root/venvs/livekit/   livekit-agents 1.8.8 + livekit-plugins-openai 1.8.8
```

Verified: `RealtimeModel(model="qwen3.8-omni-flash-realtime",
base_url="https://ws-…maas.aliyuncs.com/api-ws/v1", api_key=QWEN_API_KEY
from env)` constructs cleanly — the Qwen OpenAI-shaped wiring the config
describes is real. Pending for a live session: LiveKit server
(`LIVEKIT_URL` + `LIVEKIT_TOKEN`), the agent entrypoint itself, and a
room test. Run the agent from the venv:
`/root/venvs/livekit/bin/python <agent>.py`.

## Known issues (open, honest)

| pack | violation |
|---|---|
| anansi-spider | trigger `on_emphasis`; body `expansive`; face `confident` |
| baba-yaga-crone | triggers `on_emphasis`/`on_tag`; face `confident`; body `expansive` |
| diogenes-tub-cynic | trigger `on_emphasis`; face `self_satisfied`; body `expansive` |
| hera-queen-ledger | trigger `on_emphasis`; face `self_satisfied`; body `expansive` |
| yuki-snow-narrator | triggers `on_pause`/`on_emphasis` |
| zeus-sky-sovereign | trigger `on_emphasis`; face `confident`; body `expansive gesture` |

Fix at source (pack `actions`) or add to freaktown's closed set — their
call. Until then those actions degrade on stage.
