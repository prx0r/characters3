#!/usr/bin/env python3
"""Prophets: substance + comedy-curation quality gates.

Run: python3 -m pytest tests/test_prophets.py -q
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

PROPHETS = ["jonah", "elijah", "isaiah", "nathan"]
# curated-for-comedy: every passage must be substantial set-fodder
PASSAGE_MIN_WORDS = 60


def test_prophet_collections_substantial():
    for slug in PROPHETS:
        d = ROOT / "characters" / slug
        sayings = [json.loads(l) for l in (d / "sayings.jsonl").read_text().splitlines()]
        assert len(sayings) >= 10, f"{slug}: only {len(sayings)} sayings"
        assert all(s["origin"] == "kjv" and s["role"] == slug for s in sayings)
        passages = [json.loads(l) for l in (d / "passages.jsonl").read_text().splitlines()]
        assert passages, slug
        assert min(p["words"] for p in passages) >= PASSAGE_MIN_WORDS, \
            f"{slug}: thin passage (<{PASSAGE_MIN_WORDS}w)"
    # comedy-curation markers: the funny ranges are actually in there
    jonah = "".join((ROOT / "characters/jonah/sayings.jsonl").read_text().splitlines())
    assert "gourd" in jonah and "angry" in jonah          # the gourd grievance (KJV word)
    eli = "".join((ROOT / "characters/elijah/sayings.jsonl").read_text().splitlines())
    assert "Cry aloud" in eli and "sleepeth" in eli        # the roast-battle mockery
    nath = "".join((ROOT / "characters/nathan/sayings.jsonl").read_text().splitlines())
    assert "ewe lamb" in nath                              # the long-con parable


def test_prophet_packs_doctrine():
    for slug in PROPHETS:
        c = json.loads((ROOT / "characters" / slug / "character.json").read_text())
        ph = c["philosophy"]
        assert all(k in ph for k in ("ontology", "epistemology", "axiology",
                                     "causality", "agency")), slug
        assert c["voice"]["tags"]["casting_query"], slug


def test_prophet_mutants():
    for slug, vibe, hold in (("jonah-eager", "wired", 900),
                             ("elijah-quiet", "serene", 1400)):
        c = json.loads((ROOT / "characters" / slug / "character.json").read_text())
        base = json.loads((ROOT / "characters" / slug.split("-")[0]
                           / "character.json").read_text())
        assert c["philosophy"] == base["philosophy"], slug   # doctrine intact
        assert c["vibe"] == vibe, slug
        assert c["delivery"]["overrides"]["punchline_hold_ms"] == hold
        assert (ROOT / "characters" / slug / "identity.json").is_file()
        assert (ROOT / "theory/profiles" / f"{slug}.json").is_file()


def test_laozi_tao_pipeline():
    d = ROOT / "characters/laozi"
    sayings = [json.loads(l) for l in (d / "sayings.jsonl").read_text().splitlines()]
    assert len(sayings) > 150 and all(s["origin"] == "tao-legge" for s in sayings)
    passages = [json.loads(l) for l in (d / "passages.jsonl").read_text().splitlines()]
    assert len(passages) >= 30 and min(p["words"] for p in passages) >= 60
    # the severe mutant: doctrine intact + ONLY his meanest aphorisms
    c = json.loads((ROOT / "characters/laozi-severe/character.json").read_text())
    base = json.loads((ROOT / "characters/laozi/character.json").read_text())
    assert c["philosophy"] == base["philosophy"]
    assert c["vibe"] == "wrathful" and c["delivery"]["overrides"]["punchline_hold_ms"] == 900
    view = [json.loads(l) for l in
            (ROOT / "characters/laozi-severe/sayings.jsonl").read_text().splitlines()]
    assert view and all(v["tone"] in ("harsh", "stern") for v in view)
    base_texts = {s["text"] for s in sayings}
    assert all(v["text"] in base_texts for v in view)


def test_jataka_tales_in_buddha():
    p = [json.loads(l) for l in
         (ROOT / "characters/buddha-ultimate-deadpan/passages.jsonl")
         .read_text().splitlines()]
    tales = [x for x in p if x["kind"] == "jataka-tale"]
    assert len(tales) >= 15, len(tales)
    assert min(t["words"] for t in tales) >= 60
    assert any("Crocodile" in t["title"] for t in tales)
    assert all("Babbitt" in t["license"] for t in tales)   # honest retelling label
    assert all(t["note"].startswith("past-life") for t in tales)


def test_qoheleth_philosopher_pipeline():
    d = ROOT / "characters/qoheleth"
    sayings = [json.loads(l) for l in (d / "sayings.jsonl").read_text().splitlines()]
    assert len(sayings) > 100 and all(s["origin"] == "kjv" for s in sayings)
    joined = " ".join(s["text"] for s in sayings)
    assert "vanity" in joined.lower() and "time to laugh" in joined.lower()
    passages = [json.loads(l) for l in (d / "passages.jsonl").read_text().splitlines()]
    assert len(passages) >= 8 and min(x["words"] for x in passages) >= 60
    # hopeful mutant: doctrine intact, wired delivery, view is base subset
    c = json.loads((ROOT / "characters/qoheleth-hopeful/character.json").read_text())
    base = json.loads((ROOT / "characters/qoheleth/character.json").read_text())
    assert c["philosophy"] == base["philosophy"]
    assert c["vibe"] == "wired" and c["delivery"]["overrides"]["punchline_hold_ms"] == 400
    view = [json.loads(l) for l in
            (ROOT / "characters/qoheleth-hopeful/sayings.jsonl").read_text().splitlines()]
    base_texts = {s["text"] for s in sayings}
    assert view and all(v["text"] in base_texts for v in view)
