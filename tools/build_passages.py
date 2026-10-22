#!/usr/bin/env python3
"""build_passages — contiguous quote-blocks from buddha's sayings.

Sayings are verse/line units (median 23w — no one-liners, verified); a
set wants SUBSTANCE. This groups them into passages:

  kind "dhp-contiguous"  — chapter-contiguous Dhammapada runs, chunked to
                           ~150-180 words (still byte-verbatim joins)
  kind "set-compilation" — multi-bit mine sets (arrow/elephant/dona…),
                           bits joined as a compilation (kind labeled —
                           not contiguous in source)

Minimum 60 words per passage (~18-20s speech; set-fodder, not a floor
enforcer — duration policy lives in minute.py).

Usage: python3 tools/build_passages.py [--min-words 60] [--target 170]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SAY = HERE / "characters" / "buddha-ultimate-deadpan" / "sayings.jsonl"
OUT = HERE / "characters" / "buddha-ultimate-deadpan" / "passages.jsonl"
WPM = 200


def est_s(words: int) -> float:
    return round(words / WPM * 60 + 1.25, 1)   # speech + one hold


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-words", type=int, default=60)
    ap.add_argument("--target", type=int, default=170)
    a = ap.parse_args()
    sayings = [json.loads(l) for l in SAY.read_text().splitlines()]
    passages = []

    # ── dhp contiguous runs (same chapter order preserved) ──
    dhp = [s for s in sayings if s.get("origin") == "dhammapada-mine"]
    cur: list[dict] = []
    cur_ch = None
    def flush():
        nonlocal cur, cur_ch
        if not cur:
            return
        words = sum(x["words"] for x in cur)
        if words >= a.min_words:
            passages.append({
                "schema": "freaktown.passage.v1",
                "id": f"pass-{cur[0]['id']}-{len(cur)}",
                "kind": "dhp-contiguous",
                "chapter": cur_ch,
                "verses": [x["id"] for x in cur],
                "text": " ".join(x["text"] for x in cur),
                "words": words, "est_seconds": est_s(words),
                "license": "CC0 1.0 (Bhikkhu Sujato)",
            })
        cur = []
    for s in dhp:
        ch = s.get("chapter", "")
        w = sum(x["words"] for x in cur)
        if ch != cur_ch and cur:
            flush()
        if cur and w + s["words"] > a.target:
            flush()
        if not cur:
            cur_ch = ch
        cur.append(s)
    flush()

    # ── mine sets as compilations (labeled: multi-bit, same sutta) ──
    for f in sorted((HERE / "bits" / "sets").glob("hand_buddha-*.json")):
        d = json.loads(f.read_text())
        bits = [b for b in d.get("bits", []) if len((b.get("text") or "").split()) >= 8]
        if len(bits) < 2:
            continue
        text = " … ".join(b["text"].strip() for b in bits)
        words = len(text.split())
        if words < a.min_words:
            continue
        src = (d.get("sources") or [{}])
        sutta = src[0].get("sutta") if isinstance(src[0], dict) else None
        passages.append({
            "schema": "freaktown.passage.v1",
            "id": f"pass-set-{f.stem.replace('hand_buddha-', '')}",
            "kind": "set-compilation",
            "sutta": sutta, "set_id": d.get("set_id"),
            "bits": [b.get("joke_id") for b in bits],
            "text": text, "words": words, "est_seconds": est_s(words),
            "license": "CC0 1.0 (Bhikkhu Sujato)",
            "note": "compilation of separate verbatim bits (not contiguous)",
        })

    with open(OUT, "w") as fh:
        for p in passages:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"passages: {len(passages)} | kinds:",
          dict(Counter(p["kind"] for p in passages)))
    print(f"words: total {sum(p['words'] for p in passages)} | "
          f"median {sorted(p['words'] for p in passages)[len(passages)//2]} | "
          f"min {min(p['words'] for p in passages)} "
          f"({min(p['est_seconds'] for p in passages)}s est)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
