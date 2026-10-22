#!/usr/bin/env python3
"""text_sources — PD plain-text adapters (bible first) for character sayings.

EXTRACT-NEVER-WRITE: verse text copied verbatim from cached source; ranges
curated by a human (same discipline as the sutta mine); assert per verse.

Source: thiagobodruk/bible JSON (en_kjv cached under tools/cache/, gitignored
— KJV is PD in the US; regenerate: curl raw .../json/en_kjv.json).

Adapters: KJV gospels/epistles ranges -> jesus sayings + bible-range
passages; Jonah whole book (queued for the jonah pack).

Usage:
  python3 tools/text_sources.py --fetch           # cache KJV
  python3 tools/text_sources.py --character jesus # sayings + passages
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CACHE = HERE / "tools" / "cache"
KJV_URL = ("https://raw.githubusercontent.com/thiagobodruk/bible/"
           "master/json/en_kjv.json")

# sys.path for the shared tone/topics lexicon
import sys
sys.path.insert(0, str(Path(__file__).parent))
from mine_sayings import tone, topics  # noqa: E402

# ── curated ranges (human-picked; the EXTRACT side of the contract) ──
JESUS_RANGES = [
    ("Matthew", 5, 1, 7, 29),     # Sermon on the Mount (+ Lord's prayer)
    ("Matthew", 13, 3, 13, 52),   # parables discourse (sower..treasure; intro-narration included, noted)
    ("Matthew", 18, 1, 18, 35),   # child / lost sheep / unforgiving servant
    ("Matthew", 20, 1, 20, 16),   # workers in the vineyard
    ("Matthew", 21, 12, 21, 13),  # THE TEMPLE — den of thieves (wrath core)
    ("Matthew", 22, 1, 22, 46),   # wedding feast + great commandment + caesar
    ("Matthew", 23, 1, 23, 39),   # THE WOES — wrath material
    ("Matthew", 24, 1, 25, 46),   # apocalyptic discourse (doom material)
    ("Luke", 10, 25, 10, 37),     # good samaritan
    ("Luke", 15, 11, 15, 32),     # prodigal son
    ("Luke", 16, 19, 16, 31),     # rich man and lazarus
    ("Luke", 18, 9, 18, 14),      # pharisee + publican
    ("John", 3, 1, 3, 21),        # nicodemus
    ("John", 6, 25, 6, 71),       # bread of life
    ("John", 11, 1, 11, 44),      # lazarus
    ("John", 15, 1, 15, 17),      # vine and branches
    ("John", 17, 1, 17, 26),      # high priestly prayer
    ("John", 18, 33, 18, 38),     # trial: my kingdom not of this world
]
JONAH_BOOK = ("Jonah", 1, 1, 4, 16)   # whole book (queued: jonah pack)

BOOK_ALIASES = {"matthew": "matthew", "mark": "mark", "luke": "luke",
                "john": "john", "jonah": "jonah"}


def fetch() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "en_kjv.json"
    if p.is_file() and p.stat().st_size > 1_000_000:
        return p
    urllib.request.urlretrieve(KJV_URL, p)
    return p


def load_bible() -> dict:
    p = CACHE / "en_kjv.json"
    if not p.is_file():
        raise SystemExit("cache missing — run: python3 tools/text_sources.py --fetch")
    return {b["name"].lower(): b for b in json.loads(p.read_text())}


def verse(bible: dict, book: str, ch: int, v: int) -> str:
    b = bible.get(book.lower())
    if not b:
        raise ValueError(f"no book {book}")
    return b["chapters"][ch - 1][v - 1]


def in_range(book: str, ch: int, v: int, rng) -> bool:
    _, c1, v1, c2, v2 = rng
    return (c1, v1) <= (ch, v) <= (c2, v2)


def assert_verse(text: str, src: str) -> None:
    if not text.strip() or text.strip() not in src:
        raise ValueError(f"NOT VERBATIM: {text[:60]}")


def extract(bible: dict, ranges: list, role: str, tag: str):
    """-> (sayings, passages) for curated ranges. Verse-level sayings +
    one contiguous passage per range."""
    src = "\n".join(v for b in bible.values() for ch in b["chapters"]
                     for v in ch)   # plain-text assert pool (no JSON escapes)
    sayings, passages = [], []
    seen_refs = set()
    for rng in ranges:
        book, c1, v1, c2, v2 = rng
        vs = []
        for ch in range(c1, c2 + 1):
            b = bible[book.lower()]
            last = len(b["chapters"][ch - 1]) if ch == c2 else len(b["chapters"][ch - 1])
            top = v2 if ch == c2 else last
            for v in range(v1 if ch == c1 else 1, top + 1):
                t = b["chapters"][ch - 1][v - 1].strip()
                if not t:
                    continue
                assert_verse(t, src)
                ref = f"{book[:3].capitalize()} {ch}:{v}"
                vs.append((ref, t))
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                sayings.append({
                    "schema": "freaktown.saying.v1",
                    "id": f"{tag}-{hashlib.sha256(ref.encode()).hexdigest()[:8]}",
                    "text": t, "role": role, "origin": tag,
                    "book": book, "ref": ref,
                    "tone": tone(t), "topics": topics(t),
                    "label_source": "lexicon-v1",
                    "license": "KJV public domain (US)",
                    "words": len(t.split()),
                })
        if vs:
            words = sum(len(t.split()) for _, t in vs)
            passages.append({
                "schema": "freaktown.passage.v1",
                "id": f"pass-{tag}-{book[:3].lower()}{c1}-{c2}",
                "kind": "bible-range",
                "book": book, "range": f"{c1}:{v1}-{c2}:{v2}",
                "n_verses": len(vs),
                "text": " ".join(t for _, t in vs),
                "words": words,
                "est_seconds": round(words / 200 * 60 + 1.25, 1),
                "license": "KJV public domain (US)",
                "note": "contiguous KJV range; sermon/discourse ranges may "
                        "contain narrator intro verses (still verbatim)",
            })
    return sayings, passages


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--character", default=None,
                    choices=[None, "jesus"], help="target character")
    a = ap.parse_args(argv)
    if a.fetch:
        print("cached:", fetch())
        if not a.character:
            return 0
    bible = load_bible()
    if a.character == "jesus":
        sayings, passages = extract(bible, JESUS_RANGES, "jesus", "kjv")
        dest = HERE / "characters" / "jesus"
        dest.mkdir(parents=True, exist_ok=True)
        for name, rows in (("sayings.jsonl", sayings),
                           ("passages.jsonl", passages)):
            with open(dest / name, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter
        print(f"jesus: {len(sayings)} sayings "
              f"(tones {dict(Counter(s['tone'] for s in sayings))}), "
              f"{len(passages)} passages, "
              f"{sum(p['words'] for p in passages)} passage words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
