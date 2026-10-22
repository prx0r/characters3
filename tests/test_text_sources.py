#!/usr/bin/env python3
"""text_sources: verbatim extraction from PD bible text. No network.

Run: python3 -m pytest tests/test_text_sources.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import text_sources as T


def _bible():
    return {"matthew": {"name": "Matthew", "chapters": [
        ["v1:1", "v1:2", "v1:3"],
        ["b5-1 mount", "b5-2 blessed", "b5-3 lilies"]}]}}


def test_range_extraction_is_verbatim():
    sayings, passages = T.extract(_bible(), [("Matthew", 2, 1, 2, 3)],
                                  "jesus", "kjv")
    assert [s["text"] for s in sayings] == ["v1:1", "v1:2", "v1:3"]
    assert passages[0]["text"] == "v1:1 v1:2 v1:3"
    assert passages[0]["kind"] == "bible-range"


def test_assert_verse_catches_fabrication():
    try:
        T.assert_verse("and then he improvised", "v1:1\nv1:2")
    except ValueError:
        return
    raise AssertionError("fabrication passed")


def test_curated_jesus_ranges_nonempty():
    assert len(T.JESUS_RANGES) >= 15
    books = {r[0] for r in T.JESUS_RANGES}
    assert {"Matthew", "Luke", "John"} <= books
    # wrath + temple ranges present
    assert any(r[:3] == ("Matthew", 23, 1) for r in T.JESUS_RANGES)
    assert any(r[:3] == ("Matthew", 21, 12) for r in T.JESUS_RANGES)


def test_jesus_shipped():
    d = ROOT / "characters" / "jesus"
    assert (d / "character.json").is_file()
    sayings = [json.loads(l) for l in (d / "sayings.jsonl").read_text().splitlines()]
    assert len(sayings) > 300, len(sayings)
    assert any("den of thieves" in s["text"] for s in sayings)
    assert all(s["role"] == "jesus" and s["origin"] == "kjv" for s in sayings)
    passages = [json.loads(l) for l in (d / "passages.jsonl").read_text().splitlines()]
    assert passages and min(p["words"] for p in passages) > 30


def test_jesus_temple_mutant():
    c = json.loads((ROOT / "characters/jesus-temple/character.json").read_text())
    base = json.loads((ROOT / "characters/jesus/character.json").read_text())
    assert c["philosophy"] == base["philosophy"]          # doctrine intact
    assert c["vibe"] == "wrathful" and \
        c["delivery"]["overrides"]["punchline_hold_ms"] == 900
