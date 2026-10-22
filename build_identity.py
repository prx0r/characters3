#!/usr/bin/env python3
"""build_identity — one stable plug-and-play identity per character.

For every pack in characters/ writes:
  identity.json   the identity contract shared by THREE runtimes:
                    - standup  : characters (delivery_engine --seal) -> freaktown stage
                    - podcast  : LiveKit room agent (voice + face/action events)
                    - party    : freaktown party rooms / LiveKit
                  + stage_compat (freaktown's EXACT closed vocabularies,
                    pack actions validated against them — violations
                    reported, never silently fixed) + livekit config
                    (models/endpoint shape; keys never in the tree).
  personality.txt the qwen-flash-character system message: persona in a
                  stable voice that never breaks character. Deterministic
                  build from pack fields (+ evolve-genome identity when the
                  pack is thin — marked with source).

Closed vocabularies (freaktown origin/main docs/CHARACTER_PACK.md):
  face  = neutral deadpan grin annoyed confused surprised   (editor)
  body  = normal hold still lean in look left look right shrug small gesture big gesture
  trig  = on_enter after_setup after_punchline after_tag on_laugh on_groan
          on_silence before_closer after_closer on_exit manual

Usage: python3 build_identity.py [--src /root/characters2]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

DST = Path(__file__).resolve().parent

FACE = {"neutral", "deadpan", "grin", "annoyed", "confused", "surprised"}

# vibe -> stage default face (EDITOR vocab only — freaktown renders these;
# no 'angry'/'prophetic' exist: closest faces, extension noted not faked)
VIBE_FACE = {"deadpan": "deadpan", "neutral": "neutral", "serene": "neutral",
             "wrathful": "annoyed", "wired": "surprised", "smug": "grin",
             "prophetic": "surprised", "manic": "grin", "anxious": "confused",
             "smug_under_stern": "annoyed"}
FACE_EXPORT = {"deadpan", "smug", "smile", "annoyed", "surprised",
               "frown", "disgusted"}   # delivery exporter may emit these;
                                       # stage maps them onto FACE
BODY = {"normal", "hold still", "lean in", "look left", "look right",
        "shrug", "small gesture", "big gesture"}
TRIGGERS = {"on_enter", "after_setup", "after_punchline", "after_tag",
            "on_laugh", "on_groan", "on_silence", "before_closer",
            "after_closer", "on_exit", "manual"}

PERSONALITY_RULES = [
    "You never break character and never claim to be an AI.",
    "You speak only as yourself — your premise is your worldview.",
    "Stage actions are performed as parentheticals: (holds still), (shrugs).",
    "Same personality in every mode: standup set, podcast, party game.",
]


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def genome_identity(src: Path, slug: str) -> dict:
    p = src / "theory" / "genomes" / f"freak_{slug}.json"
    return (jload(p) or {}).get("identity") or {}


def validate_actions(char: dict) -> tuple[list[dict], list[str]]:
    """Actions against freaktown's closed sets. (name, violations)."""
    out, bad = [], []
    for name, a in (char.get("actions") or {}).items():
        if not isinstance(a, dict):
            bad.append(f"{name}: not an object")
            continue
        v = []
        if a.get("trigger") not in TRIGGERS:
            v.append(f"trigger {a.get('trigger')!r} not in closed set")
        face = a.get("face")
        if face is not None and face not in (FACE | FACE_EXPORT):
            v.append(f"face {face!r} not in vocab")
        body = a.get("body")
        if body is not None and body not in BODY:
            v.append(f"body {body!r} not in vocab")
        out.append({"name": name, "trigger": a.get("trigger"),
                    "face": face, "body": body,
                    "tags": a.get("tags", []),
                    "fallback": a.get("fallback", "hold still")})
        if v:
            bad.append(f"{name}: " + "; ".join(v))
    return out, bad


def personality_text(char: dict, gid: dict, slug: str,
                     actions: list[dict]) -> tuple[str, str]:
    """Deterministic qwen-flash-character system message.
    Returns (text, source)."""
    persona = char.get("persona") or {}
    name = char.get("name") or gid.get("name") or slug
    deal = persona.get("deal") or char.get("deal") or ""
    src = "pack"
    if not deal and gid.get("deal"):
        deal, src = gid["deal"], "genome"      # thin pack: real identity in genome
    premise = char.get("premise") or ""
    species = char.get("species") or ""
    vibe = char.get("vibe") or ""
    speech = persona.get("interview_style") or ""
    threads = char.get("threads") or gid.get("threads") or []
    lore = gid.get("lore") or []
    tags = (char.get("voice") or {}).get("tags") or {}

    L = [f"You are {name}."]
    if species:
        L.append(f"Species: {species}.")
    if deal:
        L.append(f"\nPERSONALITY: {deal}")
    if premise:
        L.append(f"Premise: {premise}")
    if vibe:
        L.append(f"Delivery energy: {vibe}." + (
            f" Register: {tags.get('register')}." if tags.get("register") else ""))
    if threads:
        L.append("\nFIXED THREADS (your obsessions — rotate freely):")
        L += [f"- {t}" for t in threads[:5]]
    if lore:
        L.append("\nBACKSTORY (true for you, always):")
        L += [f"- {x[:160]}" for x in lore[:4]]
    if speech:
        L.append(f"\nSPEECH: {speech}")
    if tags.get("texture"):
        L.append(f"Voice texture: {tags['texture']}")
    if actions:
        L.append("\nYOUR STAGE ACTIONS (perform as parentheticals):")
        L += [f"- ({a['name'].replace('_', ' ')}) on {a['trigger']}"
              for a in actions[:6]]
    L.append("\nRULES:")
    L += [f"- {r}" for r in PERSONALITY_RULES]
    return "\n".join(L).strip() + "\n", src




def ident_declared_visual(char: dict) -> dict | None:
    """Archetype violation 'visual' block, carried via mutations provenance."""
    for m in (char.get("mutations") or []):
        v = (m.get("visual") or {})
        if v:
            return {**v, "declared_by": m.get("violation"),
                    "contract": "must stay inside FACE|BODY|TRIGGERS sets"}
    return None


def build(slug: str, pack_dir: Path, src: Path | None) -> dict:
    char = jload(pack_dir / "character.json") or {}
    mesh = jload(pack_dir / "mesh.json") or {}
    delivery = jload(pack_dir / "delivery.json")
    gid = genome_identity(src, slug) if src else {}
    actions, violations = validate_actions(char)
    persona_text, psrc = personality_text(char, gid, slug, actions)
    d = char.get("delivery") or {}
    ident = {
        "schema": "pogtown.identity.v1",
        "slug": slug,
        "name": char.get("name") or gid.get("name") or slug,
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "personality": {
            "file": "personality.txt",
            "model": "qwen-flash-character",
            "source": psrc,
            "rules": PERSONALITY_RULES,
        },
        "stage_compat": {
            "face_vocabulary": sorted(FACE),
            "export_face_vocabulary": sorted(FACE_EXPORT),
            "body_vocabulary": sorted(BODY),
            "trigger_vocabulary": sorted(TRIGGERS),
            "actions": actions,
            "violations": violations,
            "mesh": {k: mesh.get(k) for k in ("mesh", "status", "why")
                     if k in mesh},
            "default_face": VIBE_FACE.get(char.get("vibe", ""), "neutral"),
            "mutant_visual": (ident_declared_visual(char)),
            "face_vocab_extension_wanted": sorted(
                {"wrathful", "prophetic"} & {char.get("vibe", "")}),
        },
        "delivery": ({k: d.get(k) for k in ("style", "archetype",
                                            "overrides", "provisional")
                      if k in d} if d else None),
        "delivery_beats_authored": bool(delivery),
        "livekit": {
            "personality_model": "qwen-flash-character",
            "realtime_model": "qwen3.8-omni-flash-realtime",
            "realtime_protocol": "OpenAI-realtime-shaped wss "
                                 "(session.update / response.create)",
            "endpoint_env": "QWEN_REALTIME_URL + QWEN_API_KEY (env/vault, "
                            "never the tree)",
            "face_action_channel": "data channel messages, freaktown "
                                   "vocabulary above (face/body/trigger)",
        },
        "runtimes": {
            "standup": "characters repo: delivery_engine.py --seal -> "
                       "sealed-set.v1 -> freaktown stage",
            "podcast": "LiveKit room agent: personality.txt -> "
                       "qwen-flash-character; audio -> qwen realtime",
            "party": "freaktown party room + LiveKit voice; manual "
                     "actions fire as buttons",
        },
    }
    (pack_dir / "identity.json").write_text(
        json.dumps(ident, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (pack_dir / "personality.txt").write_text(persona_text, encoding="utf-8")
    return ident


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/root/characters2",
                    help="characters2 root (genome identity for thin packs)")
    a = ap.parse_args(argv)
    src = Path(a.src) if Path(a.src).is_dir() else None
    packs = sorted((DST / "characters").iterdir())
    n = viol = 0
    for p in packs:
        if not (p / "character.json").is_file():
            continue
        ident = build(p.name, p, src)
        n += 1
        v = ident["stage_compat"]["violations"]
        if v:
            viol += 1
            print(f"  VIOLATIONS {p.name}: {v}")
    print(f"identities: {n} built, {viol} with vocab violations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
