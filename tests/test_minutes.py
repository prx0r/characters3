#!/usr/bin/env python3
"""Tests for minute.py duration floor + estimator. No network, no spend.

Run: python3 -m pytest tests/test_minutes.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import minute as M


def test_estimate_seconds_sanity():
    char = {"delivery": {"style": "norm_macdonald",
                         "overrides": {"punchline_hold_ms": 1500,
                                       "post_punch_ms": 1000}}}
    short = [{"text": "x " * 30}]                 # 30 words, 1 bit
    e1 = M.estimate_seconds(short, char)
    assert 5 < e1 < 20, e1
    long_ = [{"text": "y " * 60} for _ in range(4)]   # 240 words, 4 bits
    e2 = M.estimate_seconds(long_, char)
    assert 65 < e2 < 95, e2
    assert e2 > e1
    # calibration anchor: dona (177w/3bits) ests ~55-60
    dona = [{"text": "z " * 59} for _ in range(3)]
    assert 50 <= M.estimate_seconds(dona, char) <= 65


def test_style_wpm_reads_engine_recipe():
    char = {"delivery": {"style": "norm_macdonald"}}
    assert M._style_wpm(char) == 200
    assert M._style_wpm({"delivery": {"style": None}}) == M.STYLE_WPM_DEFAULT


def test_duration_floor_topup(tmp_path, monkeypatch):
    """Short first pass -> top-up rounds until >= min or rounds exhausted."""
    monkeypatch.setattr(M, "setup_env", lambda: None)
    monkeypatch.setattr(M, "wire_chars2", lambda: None)
    monkeypatch.setattr(M, "OUT", tmp_path)
    monkeypatch.setattr(M, "edge_bit",
        lambda b, c, aud, dial: {
            "ladder": {"renders": []},
            "selected": {"pick": "L2_line", "edginess": 0.4,
                         "text": b, "reason": "mock"}})
    monkeypatch.setattr(M, "slop_mask", lambda t, c: {"passed": True,
                                                      "problems": []})
    calls = {"n": 0}
    def fake_writer(system, seed_bit=""):
        calls["n"] += 1
        filler = " ".join(["words"] * 18)
        if calls["n"] == 1:
            return f"{filler}\n---\n{filler}"
        return f"{filler}\n---\n{filler}"
    monkeypatch.setattr(M, "write_base_minute", fake_writer)

    rc = M.main(["buddha-ultimate-deadpan", "--min-seconds", "60",
                 "--max-seconds", "90"])
    assert rc == 0
    files = list(tmp_path.glob("*.json"))
    assert files, "no minute written"
    doc = json.loads(files[0].read_text())
    assert doc["duration"]["topup_rounds"] >= 1, "floor never triggered top-up"
    assert doc["duration"]["min_s"] == 60.0
    # model honesty: fields present either way
    assert "model" in doc["duration"]
    assert doc["metrics"]["words_total"] > 0


def test_short_is_flagged_not_hidden(tmp_path, monkeypatch):
    monkeypatch.setattr(M, "setup_env", lambda: None)
    monkeypatch.setattr(M, "wire_chars2", lambda: None)
    monkeypatch.setattr(M, "OUT", tmp_path)
    monkeypatch.setattr(M, "edge_bit",
        lambda b, c, aud, dial: {"ladder": {"renders": []},
                                 "selected": {"pick": "L1_safe",
                                              "edginess": 0.1, "text": b,
                                              "reason": "m"}})
    monkeypatch.setattr(M, "slop_mask", lambda t, c: {"passed": True,
                                                      "problems": []})
    # writer keeps returning nothing usable -> stays short after 3 rounds
    tiny = " ".join(["w"] * 16)          # one small bit per call
    monkeypatch.setattr(M, "write_base_minute",
                        lambda s, seed_bit="": tiny)
    rc = M.main(["buddha-ultimate-deadpan", "--min-seconds", "60"])
    assert rc == 0
    doc = json.loads(sorted(tmp_path.glob("*.json"))[-1].read_text())
    assert doc["duration"]["ok"] is False      # honest SHORT flag
    assert doc["duration"]["topup_rounds"] == 3  # gave up after caps


def test_chunk_sentences():
    long_sent = "The sage does not hoard anything at all in this world " \
                "because he knows the way operates by emptying"
    bits = M._chunk_sentences(
        f"{long_sent}. {long_sent} always. {long_sent} however ends here now.",
        max_w=20)
    assert bits and len(bits) >= 2
    assert all(8 <= len(b.split()) for b in bits)


def test_extract_minute_verbatim(tmp_path):
    import argparse
    packdir = tmp_path / "characters" / "laozi"
    packdir.mkdir(parents=True)
    (packdir / "character.json").write_text(json.dumps(
        {"name": "Laozi", "delivery": {"style": "louis",
         "overrides": {"punchline_hold_ms": 2200}}}), encoding="utf-8")
    (packdir / "passages.jsonl").write_text(json.dumps({
        "schema": "freaktown.passage.v1", "id": "pass-tao-1", "kind": "text-range",
        "range": "ch1", "words": 60,
        "text": " ".join(["The way is dark and deep and old and true"] * 4)}) + "\n",
        encoding="utf-8")
    monkey_args = argparse.Namespace(
        slug="laozi", extract=True, passage=None, min_seconds=60.0,
        max_seconds=90.0, seal=False, audience="club_latenight", edge=None,
        bits=5)
    import minute as MM
    real = MM.HERE
    MM.HERE = tmp_path          # point the loader at the fixture
    MM.OUT = tmp_path / "out"
    try:
        rc = MM.extract_minute(monkey_args,
                               {"name": "Laozi",
                                "delivery": {"style": "louis",
                                             "overrides": {"punchline_hold_ms": 2200}}})
    finally:
        MM.HERE = real
    assert rc == 0
    doc = json.loads(sorted((tmp_path / "out").glob("*.json"))[-1].read_text())
    assert doc["mode"] == "extractive-verbatim"
    assert doc["writer_model"] is None                      # no generation
    assert all(b["selected_level"] == "verbatim" for b in doc["bits"])
    assert doc["source_passages"] == ["ch1"]
