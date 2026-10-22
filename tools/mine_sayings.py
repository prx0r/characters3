#!/usr/bin/env python3
"""mine_sayings — expand buddha's verbatim canon from cached Dhammapada files.

The planned batch: all423 Dhammapada verses (Sujato CC0, bilara downloads
cached at SUTTA_DIR/dhp). VERSE = key prefix before ':' (dhp1:3 -> verse
'dhp1'); chapter titles from the 0.x header segments.

Each verse gets an authored-ish TONE label via a transparent lexicon
(label_source: "lexicon-v1" — re-placeable by a richer pass later):
  harsh   > stern > gentle > neutral   (first match wins)
Angry mutants select from harsh/stern — his meanest words, still verbatim.

Usage: python3 tools/mine_sayings.py [--sutta-dir /tmp/sutta]
Idempotent: re-running rebuilds the dhp block (existing mine/hxrmxs kept).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SAYINGS = HERE / "characters" / "buddha-ultimate-deadpan" / "sayings.jsonl"
DEFAULT_SUTTA = Path("/tmp/sutta/dhp")

HARSH = re.compile(
    r"\b(fools?|stupid|wretch\w*|wicked|corrupt\w*|condemn\w*|blam\w*|"
    r"hatred|anger|hostile|sword|slaughter|kill\w*|envy|greed|foolish)\b", re.I)
STERN = re.compile(
    r"\b(should not|do not|don’t|avoid|abandon|refrain|give up|let go|"
    r"never|must|train yourself|guard)\b", re.I)
GENTLE = re.compile(
    r"\b(friendliness|loving-kindness|compassion|gentle\w*|console\w*|"
    r"patient\w*|mercy|kind\w*)\b", re.I)


def tone(text: str) -> str:
    if HARSH.search(text):
        return "harsh"
    if STERN.search(text):
        return "stern"
    if GENTLE.search(text):
        return "gentle"
    return "neutral"


def verse_id(s_id: str) -> str | None:
    m = re.match(r"^(dhp\d+):", s_id)
    return m.group(1) if m else None


def mine(sutta_dir: Path) -> list[dict]:
    entries = []
    for f in sorted(sutta_dir.glob("dhp*.json")):
        data = json.loads(f.read_text())
        verses: dict[str, list[str]] = {}
        order: list[str] = []
        ch_of: dict[str, str] = {}
        ch_title = ""
        for k in sorted(data, key=lambda x: [int(p) if p.isdigit() else p
                                             for p in re.split(r"(\d+)", x)]):
            if re.match(r"^[^:]+:0\.\d+$", k):     # chapter header (interleaved)
                t = " ".join(data[k].split())
                if re.match(r"^\d+\.", t):
                    ch_title = t
                continue
            v = verse_id(k)
            if not v or not data[k].strip():
                continue
            if v not in verses:
                verses[v] = []
                order.append(v)
                ch_of[v] = ch_title
            verses[v].append(data[k].strip())
        for v in order:
            text = " ".join(verses[v])
            entries.append({
                "schema": "freaktown.saying.v1",
                "id": f"dhp-{v}",
                "text": text,
                "role": "buddha",
                "origin": "dhammapada-mine",
                "sutta": v,
                "chapter": ch_of.get(v, ""),
                "tone": tone(text),
                "label_source": "lexicon-v1",
                "license": "CC0 1.0 (Bhikkhu Sujato via SuttaCentral)",
                "words": len(text.split()),
            })
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sutta-dir", default=str(DEFAULT_SUTTA))
    a = ap.parse_args()
    existing = [json.loads(l) for l in SAYINGS.read_text().splitlines()]
    kept = [e for e in existing if e.get("origin") != "dhammapada-mine"]
    dhp = mine(Path(a.sutta_dir))
    if not dhp:
        raise SystemExit(f"no dhp files under {a.sutta_dir}")
    out = kept + dhp
    with open(SAYINGS, "w") as f:
        for e in out:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    from collections import Counter
    print(f"sayings: {len(out)} total ({len(kept)} prior + {len(dhp)} dhp)")
    print("dhp tones:", dict(Counter(e["tone"] for e in dhp)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
