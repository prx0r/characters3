#!/usr/bin/env python3
"""mutate — derive characters/<base>-<label>/ packs from archetype theory.

The engine NEVER invents prose: mutant_premise/mutant_thread are authored
strings in archetypes/<x>.json (violations_that_work). What the operator
guarantees per theory:

  doctrine-inversion : premise+thread+label change; philosophy and
                       delivery.style/timing PRESERVED (the contradiction
                       is content, not delivery — angry Buddha stays slow)
  status-flip        : premise+thread+label; vibe may change only if the
                       violation declares mutant_vibe
  thread-corruption / lore-injection : same assemblage, different basis

Usage:
  python3 mutate.py --list
  python3 mutate.py buddha-ultimate-deadpan --violation wrath [--as buddha-angry]
  python3 mutate.py --all   # every violation of every archetype
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCH = HERE / "archetypes"
CHARS = HERE / "characters"


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def find_archetype(slug: str) -> dict | None:
    for f in sorted(ARCH.glob("*.json")):
        d = load(f)
        if slug in (d.get("members") or []):
            return d
    return None


def find_violation(arch: dict, vid: str) -> dict | None:
    for v in arch.get("violations_that_work", []):
        if v.get("id") == vid:
            return v
    return None


def mutate(base_slug: str, violation_id: str, as_slug: str | None = None) -> str:
    arch = find_archetype(base_slug)
    if not arch:
        raise SystemExit(f"{base_slug}: no archetype claims this pack "
                         f"(see archetypes/)")
    v = find_violation(arch, violation_id)
    if not v:
        ids = [x["id"] for x in arch.get("violations_that_work", [])]
        raise SystemExit(f"violations for {arch['id']}: {ids}")
    base_dir = CHARS / base_slug
    base_char = load(base_dir / "character.json")
    slug = as_slug or f"{base_slug}-{v['id']}"

    mut_op = v.get("mutation", "doctrine-inversion")
    char = json.loads(json.dumps(base_char))   # deep copy
    char["schema"] = "freaktown.character.v1"
    char["name"] = f"{base_char.get('name', base_slug)} ({v['label'].split('(')[-1].rstrip(')')})"
    char["premise"] = v["mutant_premise"]
    threads = list(char.get("threads") or [])
    threads.insert(0, v["mutant_thread"])
    char["threads"] = threads
    if v.get("mutant_vibe"):
        char["vibe"] = v["mutant_vibe"]
    # philosophy/doctrine and delivery.style NEVER touched (theory: the
    # contradiction must be real against intact doctrine; NS preserved)
    char["mutations"] = [{
        "base": base_slug, "archetype": arch["id"],
        "violation": v["id"], "operator": mut_op,
        "contradicts": v.get("contradicts"),
        "theory_basis": v.get("why_funny", "")[:400],
        "delivery": v.get("delivery", "preserved"),
        "created": time.strftime("%Y-%m-%d"),
        "engine_note": "assembled from authored archetype strings; no "
                       "generated prose; doctrine+style preserved by operator",
    }]

    dest = CHARS / slug
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "character.json").write_text(
        json.dumps(char, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    # copy non-text pack assets that stay true (actions/tags) — character.json
    # already carries them. delivery.json/set.wav deliberately NOT copied:
    # they contain the BASE set's text (pending a mutant render).
    # register in archetype
    if slug not in arch.get("members", []):
        arch.setdefault("members", []).append(slug)
        (ARCH / f"{arch['id'].split(':')[1]}.json").write_text(
            json.dumps(arch, indent=1, ensure_ascii=False) + "\n",
            encoding="utf-8")
    return slug


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", nargs="?")
    ap.add_argument("--violation", default=None)
    ap.add_argument("--as", dest="as_slug", default=None)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.list:
        for f in sorted(ARCH.glob("*.json")):
            d = load(f)
            print(f"{d['id']:16s} {d['name']}")
            for v in d.get("violations_that_work", []):
                print(f"   - {v['id']:12s} {v['label']:24s} [{v.get('mutation')}] "
                      f"delivery={v.get('delivery')}")
        return 0
    if a.all:
        n = 0
        for f in sorted(ARCH.glob("*.json")):
            d = load(f)
            for v in d.get("violations_that_work", []):
                base = (d.get("members") or [None])[0]
                if base:
                    try:
                        mutate(base, v["id"]); n += 1
                    except SystemExit as e:
                        print("skip:", e)
        print(f"{n} mutants built")
        return 0
    if not (a.base and a.violation):
        ap.error("need BASE --violation ID (or --list / --all)")
    slug = mutate(a.base, a.violation, a.as_slug)
    print(f"mutant: characters/{slug}/  "
          f"(next: build_identity.py && build_profiles.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
