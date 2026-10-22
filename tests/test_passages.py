#!/usr/bin/env python3
"""Passages: substance floor + verbatim joins. Run: pytest tests/test_passages.py -q"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "characters/buddha-ultimate-deadpan"


def test_passage_substance():
    ps = [json.loads(l) for l in (P / "passages.jsonl").read_text().splitlines()]
    assert len(ps) >= 60, len(ps)
    assert min(p["words"] for p in ps) >= 60, "thin passage slipped in"
    assert all(p["est_seconds"] >= 15 for p in ps)


def test_dhp_passages_are_verbatim_joins():
    sayings = [json.loads(l) for l in (P / "sayings.jsonl").read_text().splitlines()]
    by_id = {s["id"]: s["text"] for s in sayings}
    ps = [json.loads(l) for l in (P / "passages.jsonl").read_text().splitlines()]
    checked = 0
    for p in ps:
        if p["kind"] != "dhp-contiguous":
            continue
        assert all(vid in by_id for vid in p["verses"]), p["id"]
        joined = " ".join(by_id[vid] for vid in p["verses"])  # order = verses list
        assert joined == p["text"], f"{p['id']}: not a clean contiguous join"
        checked += 1
    assert checked >= 50, checked


def test_set_compilations_labelled():
    ps = [json.loads(l) for l in (P / "passages.jsonl").read_text().splitlines()]
    for p in ps:
        if p["kind"] == "set-compilation":
            assert "not contiguous" in p.get("note", "")
            assert p.get("bits"), p["id"]
