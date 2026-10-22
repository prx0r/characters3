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
JONAH_BOOK = ("Jonah", 1, 1, 4, 16)   # whole book — the coward prophet
ELIJAH_RANGES = [
    ("1 Kings", 18, 16, 18, 40),   # Mount Carmel bake-off — the roast battle
    ("1 Kings", 19, 1, 19, 18),    # flight from Jezebel + the still small voice
]
ISAIAH_RANGES = [
    ("Isaiah", 5, 8, 5, 30),       # woe song (vineyard greed)
    ("Isaiah", 10, 1, 10, 19),     # woe against unjust decrees
]
NATHAN_RANGES = [
    ("2 Samuel", 12, 1, 12, 14),   # the parable of the ewe lamb (the long con)
]
CHARACTER_RANGES = {
    "jesus": (JESUS_RANGES, "jesus", "kjv"),
    "jonah": ([JONAH_BOOK], "jonah", "kjv"),
    "elijah": (ELIJAH_RANGES, "elijah", "kjv"),
    "isaiah": (ISAIAH_RANGES, "isaiah", "kjv"),
    "nathan": (NATHAN_RANGES, "nathan", "kjv"),
}

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
            top = min(v2, last) if ch == c2 else last   # clamp: editions vary
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




TAO_URL = "https://www.gutenberg.org/cache/epub/216/pg216.txt"


def fetch_tao() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "tao-legge.txt"
    if p.is_file() and p.stat().st_size > 50_000:
        return p
    urllib.request.urlretrieve(TAO_URL, p)
    return p


def extract_tao() -> tuple[list, list]:
    """Legge 1891 (PD). Chapter markers: 'Ch. 1. 1.' for ch1, then lines
    starting 'N. 1. ' (chapter N, section 1). Sections inside -> aphorism
    sayings; contiguous chapter runs -> passages (~170w, floor 60)."""
    p = CACHE / "tao-legge.txt"
    if not p.is_file():
        raise SystemExit("tao cache missing — run --character laozi (auto-fetch)")
    raw = p.read_text(encoding="utf-8", errors="replace")
    i = raw.find("Ch. 1. 1.")
    if i < 0:
        raise ValueError("chapter markers not found")
    body = raw[i:].replace("Ch. 1. 1.", "1. 1.", 1)
    ch_pat = re.compile(r"(?m)^\s*\d{1,2}\.\s+1\.\s+")
    marks = [m.start() for m in ch_pat.finditer(body)]
    if len(marks) < 70:
        raise ValueError(f"only {len(marks)} chapters found (expected ~81)")
    src_plain = re.sub(r"\s+", " ", body)
    sayings, passages = [], []
    run, run_words, run_from = [], 0, 1
    for ci, mstart in enumerate(marks):
        mend = marks[ci + 1] if ci + 1 < len(marks) else len(body)
        ch = body[mstart:mend]
        ch_no = int(re.match(r"\s*(\d{1,2})\.", ch).group(1))
        secs = re.split(r"(?m)^\s*\d{1,2}\.\s+", ch)
        chap_sayings = []
        for j, sec in enumerate(secs, start=1):
            t = re.sub(r"\s+", " ", sec).strip()
            if len(t.split()) < 6:
                continue
            if t not in src_plain:
                raise ValueError(f"NOT VERBATIM tao ch{ch_no}s{j}: {t[:50]}")
            ref = f"Tao {ch_no}:{j}"
            sayings.append({
                "schema": "freaktown.saying.v1",
                "id": f"tao-{hashlib.sha256(ref.encode()).hexdigest()[:8]}",
                "text": t, "role": "laozi", "origin": "tao-legge",
                "book": "Tao Te Ching", "ref": ref,
                "tone": tone(t), "topics": topics(t),
                "label_source": "lexicon-v1",
                "license": "Tao Teh King, James Legge (1891) — public domain",
                "words": len(t.split())})
            chap_sayings.append(t)
        run.extend(chap_sayings)
        run_words += sum(len(x.split()) for x in chap_sayings)
        if run_words >= 170:
            passages.append(_tao_passage(run, run_from, ch_no))
            run, run_words, run_from = [], 0, ch_no + 1
    if run and run_words >= 60:
        passages.append(_tao_passage(run, run_from, marks and
                      int(re.match(r"\s*(\d{1,2})", body[marks[-1]:]).group(1))))
    return sayings, passages


def _tao_passage(chunks: list, ch_from: int, ch_to: int) -> dict:
    words = sum(len(x.split()) for x in chunks)
    return {"schema": "freaktown.passage.v1",
            "id": f"pass-tao-{ch_from}-{ch_to}", "kind": "text-range",
            "book": "Tao Te Ching", "range": f"ch{ch_from}-{ch_to}",
            "text": " ".join(chunks), "words": words,
            "est_seconds": round(words / 200 * 60 + 1.25, 1),
            "license": "Legge (1891) — public domain"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--character", default=None,
                    choices=[None, "laozi", *sorted(CHARACTER_RANGES)],
                    help="target character")
    a = ap.parse_args(argv)
    if a.character == "laozi":
        fetch_tao()
        sayings, passages = extract_tao()
        dest = HERE / "characters" / "laozi"
        dest.mkdir(parents=True, exist_ok=True)
        for name, rows in (("sayings.jsonl", sayings),
                           ("passages.jsonl", passages)):
            with open(dest / name, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter
        print(f"laozi: {len(sayings)} sayings "
              f"(tones {dict(Counter(s['tone'] for s in sayings))}), "
              f"{len(passages)} passages, "
              f"{sum(x['words'] for x in passages)} passage words")
        return 0
    if a.fetch:
        print("cached:", fetch())
        if not a.character:
            return 0
    bible = load_bible()
    if a.character:
        ranges, role, tag = CHARACTER_RANGES[a.character]
        sayings, passages = extract(bible, ranges, role, tag)
        dest = HERE / "characters" / a.character
        dest.mkdir(parents=True, exist_ok=True)
        for name, rows in (("sayings.jsonl", sayings),
                           ("passages.jsonl", passages)):
            with open(dest / name, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter
        print(f"{a.character}: {len(sayings)} sayings "
              f"(tones {dict(Counter(s['tone'] for s in sayings))}), "
              f"{len(passages)} passages, "
              f"{sum(p['words'] for p in passages)} passage words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
