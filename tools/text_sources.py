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
QOHELETH_RANGES = [
    ("Ecclesiastes", 1, 2, 1, 11),    # vanity of vanities opener
    ("Ecclesiastes", 2, 1, 2, 26),    # I got everything; meaningless; nothing better
    ("Ecclesiastes", 3, 1, 3, 22),    # a time to laugh (+ to every thing a season)
    ("Ecclesiastes", 4, 4, 4, 16),    # the lonely — two better than one
    ("Ecclesiastes", 5, 10, 5, 19),   # silver loathsome — the dream through riches
    ("Ecclesiastes", 6, 1, 6, 12),    # wealth without enjoyment
    ("Ecclesiastes", 7, 1, 7, 14),    # house of mourning better than laughter; good name
    ("Ecclesiastes", 8, 10, 8, 15),   # wicked burials forgotten — injustice
    ("Ecclesiastes", 9, 2, 9, 12),    # one event to all — time and chance
    ("Ecclesiastes", 10, 1, 10, 20),  # a little folly / a living dog better than dead lion
    ("Ecclesiastes", 11, 1, 11, 8),   # cast thy bread upon the waters
    ("Ecclesiastes", 12, 1, 12, 14),  # keep the creator — the verdict
]
CHARACTER_RANGES = {
    "qoheleth": (QOHELETH_RANGES, "qoheleth", "kjv"),
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




SKIP_TALE = {"FOREWORD", "CONTENTS", "PUBLISHER'S NOTE", "PART II", "PART I"}


def fetch_jataka() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "jataka-babbitt.txt"
    if p.is_file() and p.stat().st_size > 50_000:
        return p
    urllib.request.urlretrieve(
        "https://www.gutenberg.org/cache/epub/62514/pg62514.txt", p)
    return p


def extract_jataka() -> list:
    """Babbitt 1912 (PD, pre-1923) retellings -> buddha tale PASSAGES
    (tales are narrative — no single-saying split; retelling labeled)."""
    p = CACHE / "jataka-babbitt.txt"
    if not p.is_file():
        raise SystemExit("jataka cache missing (auto-fetch with --jataka)")
    raw = p.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    heads = [(i, l.strip()) for i, l in enumerate(lines)
             if re.fullmatch(r"[A-Z][A-Z \-'’,.]{6,60}", l or "") ]
    heads = [(i, h) for i, h in heads if h not in SKIP_TALE
             and not h.startswith("PART")]
    src_plain = re.sub(r"\s+", " ", raw)
    out = []
    for n, (i, h) in enumerate(heads):
        j = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        tale = re.sub(r"\s+", " ", " ".join(lines[i + 1:j])).strip()
        if len(tale.split()) < 60:
            continue
        if tale[:80] not in src_plain:
            raise ValueError(f"NOT VERBATIM jataka: {h}")
        out.append({
            "schema": "freaktown.passage.v1",
            "id": f"pass-jataka-{hashlib.sha256(h.encode()).hexdigest()[:8]}",
            "kind": "jataka-tale", "book": "Jataka Tales (Babbitt 1912)",
            "title": h.title(), "text": tale,
            "words": len(tale.split()),
            "est_seconds": round(len(tale.split()) / 200 * 60 + 1.25, 1),
            "license": "Babbitt, Jataka Tales (1912) — PD US (pre-1923); "
                       "RETOLD collection (not Cowell verbatim)",
            "note": "past-life teaching tale — buddha storytelling lane"})
    return out





def extract_lear() -> tuple[list, list]:
    """Nonsense Books (Gutenberg #13648, PD): limerick = natural bit
    (setup lines + line-4 punch + twist close). Blocks of 4-6 full lines."""
    p = CACHE / "lear-nonsense.txt"
    if not p.is_file():
        raise SystemExit("lear cache missing (auto-fetch with --character lear)")
    raw = p.read_text(encoding="utf-8", errors="replace")
    src_plain = re.sub(r"\s+", " ", raw)
    sayings = []
    for block in re.split(r"\n\s*\n", raw):
        lines = [l.strip() for l in block.splitlines() if l.strip()
                 and not l.startswith("[")]
        if not (4 <= len(lines) <= 6):
            continue
        if any(len(l.split()) < 3 for l in lines):
            continue
        t = re.sub(r"\s+", " ", " ".join(lines))
        if not re.match(r"^(There (was|lived)|I (heard|saw|knew)|An? "
                        r"[A-Z][a-z]+ (of|with|who))", t):
            continue
        if t not in src_plain:
            raise ValueError(f"NOT VERBATIM lear: {t[:50]}")
        sayings.append({
            "schema": "freaktown.saying.v1",
            "id": f"lear-{hashlib.sha256(t.encode()).hexdigest()[:8]}",
            "text": t, "role": "lear", "origin": "lear-nonsense",
            "book": "Nonsense Books", "ref": t.split(",")[0][:40],
            "tone": tone(t), "topics": topics(t),
            "label_source": "lexicon-v1",
            "license": "Gutenberg #13648 (Lear, pre-1923) — public domain",
            "words": len(t.split())})
    # passages: contiguous runs of ~5 limericks (~5 bits a set)
    passages = []
    run, run_w, n = [], 0, 0
    for s2 in sayings:
        run.append(s2); run_w += s2["words"]; n += 1
        if run_w >= 150 or n >= 5:
            words = sum(x["words"] for x in run)
            passages.append({
                "schema": "freaktown.passage.v1",
                "id": f"pass-lear-{run[0]['id'][5:]}",
                "kind": "limerick-run", "book": "Nonsense Books",
                "n_limericks": n, "text": " \u2026 ".join(x["text"] for x in run),
                "words": words,
                "est_seconds": round(words / 200 * 60 + 1.25, 1),
                "license": "Gutenberg #13648 — public domain",
                "note": "contiguous limericks (\u2026 between = form boundary)"})
            run, run_w, n = [], 0, 0
    return sayings, passages



def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--character", default=None,
                    choices=[None, "laozi", "jataka", "lear",
                            *sorted(CHARACTER_RANGES)],
                    help="target character")
    a = ap.parse_args(argv)
    if a.character == "lear":
        from urllib.request import urlretrieve
        CACHE.mkdir(parents=True, exist_ok=True)
        lp = CACHE / "lear-nonsense.txt"
        if not lp.is_file():
            urlretrieve("https://www.gutenberg.org/cache/epub/13648/pg13648.txt", lp)
        sayings, passages = extract_lear()
        dest = HERE / "characters" / "lear"
        dest.mkdir(parents=True, exist_ok=True)
        for name, rows in (("sayings.jsonl", sayings),
                           ("passages.jsonl", passages)):
            with open(dest / name, "w") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        from collections import Counter
        print(f"lear: {len(sayings)} limericks "
              f"(tones {dict(Counter(x['tone'] for x in sayings))}), "
              f"{len(passages)} passages")
        return 0
    if a.character == "jataka":
        fetch_jataka()
        tales = extract_jataka()
        dest = HERE / "characters" / "buddha-ultimate-deadpan"
        existing = [json.loads(l) for l in
                    (dest / "passages.jsonl").read_text().splitlines()]
        have = {x["id"] for x in existing}
        added = [t for t in tales if t["id"] not in have]
        with open(dest / "passages.jsonl", "a") as f:
            for t in added:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        print(f"jataka: {len(tales)} tales, {len(added)} added to buddha "
              f"(total passages now {len(existing) + len(added)})")
        return 0
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
