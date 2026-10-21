#!/usr/bin/env python3
"""build_profiles — assemble theory/profiles/<slug>.json for all characters.

Field parity with louis-ck's funnygraph graph (see theory/README.md).
Assembly rules:
  - mechanical fields computed from packs/sets/ledger/rewards/tier;
  - bio.summary derived from pack + personality.txt (honest, labeled);
  - **authored fields are never overwritten** (merge = fill-missing only):
    gtvh_profile, theory_links, known_bits[].why_it_works, essay_seeds,
    bio.summary once authored, humor_type once authored.
  - rating.headline stays null until Wilson crowns; specials_rated [].

Usage: python3 build_profiles.py [--only slug]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROFILES = HERE / "profiles"

VIBE_HUMOR = {"deadpan": "deadpan", "serene": "observational",
              "smug": "wordplay", "manic": "absurd", "anxious": "selfdep",
              "neutral": "observational"}


def jl(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def personality_parts(pack: Path) -> dict:
    """Parse personality.txt (built from pack + genome) for bio material."""
    p = pack / "personality.txt"
    if not p.is_file():
        return {}
    txt = p.read_text(encoding="utf-8")
    out = {}
    m = re.search(r"PERSONALITY: (.+?)(?:\n\n|\nPremise)", txt, re.S)
    if m:
        out["deal"] = " ".join(m.group(1).split())
    m = re.search(r"FIXED THREADS[^:]*:\n((?:- .+\n?)+)", txt)
    if m:
        out["threads"] = [l[2:].strip() for l in m.group(1).strip().splitlines()]
    m = re.search(r"BACKSTORY[^:]*:\n((?:- .+\n?)+)", txt)
    if m:
        out["lore"] = [l[2:].strip() for l in m.group(1).strip().splitlines()]
    return out


def bio_summary(char: dict, pers: dict) -> str:
    name = char.get("name", "?")
    species = char.get("species", "")
    vibe = char.get("vibe", "neutral")
    deal = (char.get("persona") or {}).get("deal") or pers.get("deal") or ""
    threads = char.get("threads") or pers.get("threads") or []
    bits = []
    bits.append(f"{name} is a {'fictional ' + species if species and 'awakened' not in species else species or 'fictional'} standup performer." if species else f"{name} is a fictional standup performer.")
    if deal:
        bits.append(deal.rstrip(".") + ".")
    if len(threads) >= 2:
        bits.append(f"The act circles {threads[0].split(' (')[0].lower()} and "
                    f"{threads[1].split(' (')[0].lower()}.")
    if vibe:
        bits.append(f"Onstage the register is {vibe}.")
    return " ".join(bits)


def sets_for(slug: str) -> list[dict]:
    out = []
    for f in sorted((ROOT / "bits" / "sets").glob("*.json")):
        d = jl(f) or {}
        if slug in (d.get("agent_id", "") + d.get("set_id", "") + f.stem):
            out.append({"set_id": d.get("set_id", ""), "file": f.name,
                        "n_bits": len(d.get("bits", [])),
                        "authorship": d.get("authorship", "")})
    return out


def metrics_for(slug: str) -> dict:
    w = n = 0
    log = ROOT / "feedback" / "rewards.jsonl"
    if log.is_file():
        for line in log.read_text().splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if not e.get("human", True):
                continue
            if e.get("character_id") != slug and \
               not (e.get("character_id", "").find(slug) >= 0):
                continue
            r = e.get("reaction", "")
            if r in ("haha", "clap", "chuckle", "big_laugh", "like",
                     "replay", "win"):
                w += 1
                n += 1
            elif r in ("skip", "cut", "rewrite", "loss"):
                n += 1
    return {"human_trials": n, "human_wins": w,
            "laugh_rate": round(w / n, 3) if n else None,
            "source": "feedback/rewards.jsonl (human only)"}


def timing_for(pack: Path, char: dict) -> dict:
    d = jl(pack / "delivery.json") or {}
    beats = d.get("beats") or []
    if beats:
        pauses = [b.get("pause_after_ms", 0) for b in beats]
        holds = [b.get("pause_after_ms", 0) for b in beats
                 if b.get("type") == "punchline"]
        return {"measured": False,
                "source": "delivery.json beats (spec, not audio-measured)",
                "n_beats": len(beats),
                "mean_pause_ms": round(sum(pauses) / len(pauses), 1),
                "punch_holds_ms": holds,
                "hypothesis": "spec'd pauses carry the release window; "
                              "audio measurement pending"}
    ov = (char.get("delivery") or {}).get("overrides") or {}
    return {"measured": False,
            "source": "delivery.overrides (engine defaults, no beat score)",
            "punch_holds_ms": [ov.get("punchline_hold_ms", 1500)],
            "hypothesis": "engine hold floor; authored timing pending "
                          "delivery.json beats"}


def known_bits_baseline(slug: str, sets: list[dict]) -> list[dict]:
    out = []
    for s in sets:
        f = ROOT / "bits" / "sets" / s["file"]
        d = jl(f) or {}
        for b in d.get("bits", [])[:6]:
            text = (b.get("text") or "").strip()
            if len(text.split()) < 6:
                continue
            out.append({
                "title": f"{b.get('slot', '?')} — {s['file'].replace('.json', '')}",
                "why_it_works": "baseline: gate-passed machine selection "
                                "(authored analysis pending)",
                "authored": False,
                "theory_links": [],
                "fingerprint": " ".join(text.split()[:7]),
                "joke_id": b.get("joke_id", "")})
    return out[:8]


def tier_of(slug: str) -> str:
    idx = jl(ROOT / "INDEX.json") or {}
    for p in idx.get("performers", []):
        if p.get("slug") == slug:
            return p.get("tier", "DRAFT")
    return "DRAFT"   # pack exists but not promoted -> draft (honest)


def assemble(slug: str, keep_authored: bool = True) -> dict:
    pack = ROOT / "characters" / slug
    char = jl(pack / "character.json") or {}
    ident = jl(pack / "identity.json") or {}
    pers = personality_parts(pack)
    mesh = jl(pack / "mesh.json") or {}
    existing = jl(PROFILES / f"{slug}.json") if keep_authored else None
    base = existing or {}

    def put(key, val, force=False):
        if force or key not in base:
            base[key] = val
        elif isinstance(base.get(key), dict) and isinstance(val, dict):
            for k, v in val.items():            # fill-missing merge
                base[key].setdefault(k, v)

    vibe = char.get("vibe", "neutral")
    put("schema", "freaktown.comedian.v1", force=not existing)
    put("comedian_id", slug, force=True)
    put("name", char.get("name", slug), force=True)
    put("author_type", "ai", force=True)
    put("version", 1, force=True)
    put("created", time.strftime("%Y-%m-%d"), force=not existing)
    put("annotator", "characters3 build_profiles (+ authored tranches)", force=not existing)
    put("note", "AI character profile, louis-parity depth; honesty labels in provenance")
    # bio: fill summary only if missing (authored bio wins)
    bio = {"type": char.get("species") or "fictional",
           "origin": char.get("canon") or mesh.get("status") or "pack",
           "source": "derived-from-pack"}
    if "summary" not in (base.get("bio") or {}):
        bio["summary"] = bio_summary(char, pers)
        bio["source"] = "derived-from-pack+personality"
    put("bio", bio)
    # identity from pack (+ personality threads)
    put("identity", {
        "deal": (char.get("persona") or {}).get("deal") or pers.get("deal"),
        "premise": char.get("premise"),
        "archetype": char.get("archetype"),
        "threads": char.get("threads") or pers.get("threads"),
        "modulator_range": char.get("modulator_range"),
        "dramatic_core": char.get("dramatic_core"),
        "philosophy": char.get("philosophy"),
        "misinterpretation_rule": char.get("misinterpretation_rule"),
        "profile": char.get("profile"),
        "actions": sorted((char.get("actions") or {}).keys()),
    })
    # engine
    put("engine", {
        "delivery_archetype": vibe,
        "delivery_style": (char.get("delivery") or {}).get("style"),
        "delivery_provisional": (char.get("delivery") or {}).get("provisional"),
        "voice_provider": (char.get("voice") or {}).get("provider"),
        "voice_id": (char.get("voice") or {}).get("voice_id"),
        "voice_cast": "fish" if (char.get("voice") or {}).get("fish") else "uncast",
        "mary_coords": None,
    })
    put("humor_type", {"type": VIBE_HUMOR.get(vibe, "observational"),
                       "source": "derived-from-vibe" if not existing else
                       (base.get("humor_type") or {}).get("source",
                                                          "derived-from-vibe")})
    if isinstance(base.get("humor_type"), str):     # authored string form
        base["humor_type"] = {"type": base["humor_type"], "source": "authored"}
    put("modes", {"list": [], "note": "authored pending"})
    put("gtvh_profile", {                       # fill-missing; authored stays
        "SO": None, "LM": None, "SI": None, "TA": None, "NS": None, "LA": None,
        "note": "tranche pending"})
    put("timing_profile", timing_for(pack, char))
    put("theory_links", {"internal": [], "external": [],
                         "note": "authored per tranche"})
    put("known_bits", known_bits_baseline(slug, sets_for(slug)))
    put("essay_seeds", [])
    put("sets", sets_for(slug))
    put("set_queue", {"note": f"{len(sets_for(slug))} sets in bits/sets",
                      "blocked_on": "human votes (judge/duels)"})
    put("metrics", metrics_for(slug))
    put("rating", {"headline": None,
                   "provisional": None,
                   "note": "no human crown yet — Wilson n>=30 pending"})
    put("tier", tier_of(slug))
    put("specials_rated", [])
    put("style", {"delivery_style": (char.get("delivery") or {}).get("style"),
                  "vibe": vibe,
                  "register": ((char.get("voice") or {}).get("tags") or {}
                               ).get("register")})
    # provenance: track which fields are authored vs computed
    authored = [k for k in ("gtvh_profile", "theory_links", "essay_seeds",
                            "bio", "humor_type", "known_bits", "timing_profile")
                if (base.get(k) or {}) and (
                    not isinstance(base[k], dict)
                    or base[k].get("source", "").startswith("authored")
                    or any(isinstance(b, dict) and b.get("authored")
                           for b in base[k] if isinstance(b, dict))
                    or (k == "theory_links" and base[k].get("internal"))
                    or (k == "gtvh_profile" and base[k].get("SO"))
                    or (k == "essay_seeds" and base[k]))]
    base["provenance"] = {
        "pack": f"characters/{slug}/",
        "identity": ident.get("schema"),
        "authored": sorted(set(authored)),
        "computed": ["timing_profile.numbers", "metrics", "sets",
                     "set_queue", "tier", "rating", "engine"],
        "derived": ["bio.summary", "humor_type", "identity", "engine.archetype"],
        "rules": ["rating null until Wilson crown",
                  "measured:false until audio measured",
                  "authored never overwritten by rebuilds"],
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return base


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args(argv)
    PROFILES.mkdir(exist_ok=True)
    slugs = [a.only] if a.only else sorted(
        p.name for p in (ROOT / "characters").iterdir()
        if (p / "character.json").is_file())
    for s in slugs:
        prof = assemble(s)
        (PROFILES / f"{s}.json").write_text(
            json.dumps(prof, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8")
    print(f"profiles: {len(slugs)} written to theory/profiles/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
