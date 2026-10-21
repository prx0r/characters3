#!/usr/bin/env python3
"""sync_from_characters2 — populate characters3 from the research repo.

Topology (who owns what now):
  characters2   research archive: experiments, corpora, lore, tools.
                Packs that PASS promotion flow here; new research stays there.
  characters3   CANONICAL finalized characters: identity pack (SDK fields +
                mesh), graph, bits, delivery renders, feedback/rewards
                (TRACKED — the reward log finally lives in git).
  characters     engine (delivery render/seal SDK).
  freaktown      stage (consumes sealed-set.v1).
  gcomedy        library (knowledge mirror).

Layout written:
  characters/<slug>/   character.json delivery.json meta… mesh.json set.wav
  graph/               GRAPH.json + performers/<slug>.json (stage graphs)
  bits/                BIT-LEDGER.json + sets/*.json
  feedback/            rewards.jsonl + per-audition votes + feedback docs
  INDEX.json           promotion rollup

Run:  python3 sync_from_characters2.py [--src /root/characters2]
Idempotent: overwrites on rerun (chars3 is a projection of chars2 until
chars3 becomes canonical for writes — flip this script's direction then).
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

DST = Path(__file__).resolve().parent
PACK_FILES = ("character.json", "delivery.json", "meta.json",
              "compose.json", "artist.json", "show.json")


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sync(src: Path) -> dict:
    stats = {"characters": 0, "meshes": 0, "graphs": 0, "sets": 0,
             "bits": 0, "feedback": 0, "reward_events": 0}

    # 1. character packs (finalized: everything with an identity)
    freaks = src / "freaks"
    for f in sorted(freaks.iterdir()):
        if not (f / "character.json").is_file():
            continue
        dest = DST / "characters" / f.name
        dest.mkdir(parents=True, exist_ok=True)
        for name in PACK_FILES:
            if (f / name).is_file():
                shutil.copy2(f / name, dest / name)
        for wav in f.glob("*.wav"):
            shutil.copy2(wav, dest / wav.name)
        stats["characters"] += 1
    # 2. mesh entry per slug (from the engine repo's mesh-map)
    mmap = jload(Path("/root/characters/freaks/mesh-map.json")) or {}
    for slug, entry in (mmap.get("map") or {}).items():
        dest = DST / "characters" / slug
        if not dest.is_dir():
            continue
        (dest / "mesh.json").write_text(
            json.dumps({"schema": "pogtown.mesh.v1", "slug": slug, **entry},
                       indent=1) + "\n", encoding="utf-8")
        stats["meshes"] += 1
    # 3. graph
    gdir = DST / "graph"
    gdir.mkdir(exist_ok=True)
    if (src / "final" / "GRAPH.json").is_file():
        shutil.copy2(src / "final" / "GRAPH.json", gdir / "GRAPH.json")
        stats["graphs"] += 1
    for p in sorted((src / "final" / "stage").glob("*/comedian-graph.json")):
        d = gdir / "performers"
        d.mkdir(exist_ok=True)
        shutil.copy2(p, d / f"{p.parent.name}.json")
        stats["graphs"] += 1
    if (src / "final" / "INDEX.json").is_file():
        shutil.copy2(src / "final" / "INDEX.json", DST / "INDEX.json")
    # 4. bits
    bdir = DST / "bits"
    bdir.mkdir(exist_ok=True)
    if (src / "final" / "BIT-LEDGER.json").is_file():
        shutil.copy2(src / "final" / "BIT-LEDGER.json", bdir / "BIT-LEDGER.json")
        led = jload(src / "final" / "BIT-LEDGER.json") or {}
        stats["bits"] = led.get("bits", 0)
    sdir = bdir / "sets"
    sdir.mkdir(exist_ok=True)
    for p in sorted((src / "theory" / "generated" / "sets").glob("*.json")):
        shutil.copy2(p, sdir / p.name)
        stats["sets"] += 1
    # 5. feedback: THE tracked reward log + every vote artifact
    fdir = DST / "feedback"
    fdir.mkdir(exist_ok=True)
    rlog = src / "theory" / "policy" / "rewards.jsonl"
    if rlog.is_file():
        shutil.copy2(rlog, fdir / "rewards.jsonl")
        stats["reward_events"] = len(
            [l for l in rlog.read_text().splitlines() if l.strip()])
    votes = DST / "feedback" / "votes"
    votes.mkdir(exist_ok=True)
    for aud in src.glob("freaks/*/auditions/*"):
        slug = aud.parts[-3]
        name = f"{slug}__{aud.name}"
        ev = aud / "events.jsonl"
        if ev.is_file():
            shutil.copy2(ev, votes / f"{name}__events.jsonl")
            stats["feedback"] += 1
        for fb in sorted(aud.glob("v*/feedback.json")):
            shutil.copy2(fb, votes / f"{name}__{fb.parent.name}_feedback.json")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/root/characters2")
    a = ap.parse_args()
    s = sync(Path(a.src))
    print(json.dumps(s, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
