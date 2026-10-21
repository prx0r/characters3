#!/usr/bin/env python3
"""Tests for build_identity.py — vocab closure, violations, personality.

Run: python3 -m pytest tests/test_identity.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_identity as B


def _pack(tmp: Path, slug: str, char: dict) -> Path:
    p = tmp / slug
    p.mkdir(parents=True)
    (p / "character.json").write_text(json.dumps(char), encoding="utf-8")
    return p


def test_vocab_sets_frozen():
    assert len(B.FACE) == 6 and len(B.BODY) == 8 and len(B.TRIGGERS) == 11
    assert not (B.FACE & B.BODY) and not (B.FACE & B.TRIGGERS)
    assert "hold still" in B.BODY and "on_laugh" in B.TRIGGERS


def test_validate_flags_off_vocabulary():
    char = {"actions": {
        "good": {"trigger": "after_punchline", "face": "deadpan",
                 "body": "hold still", "tags": ["gaze.audience"]},
        "bad": {"trigger": "on_emphasis", "face": "confident",
                "body": "expansive"},
    }}
    acts, viol = B.validate_actions(char)
    assert len(acts) == 2
    assert len(viol) == 1 and "on_emphasis" in viol[0]
    assert "confident" in viol[0] and "expansive" in viol[0]


def test_build_required_keys_and_rules(tmp_path):
    p = _pack(tmp_path, "x", {"name": "X", "persona": {"deal": "d"},
                              "vibe": "deadpan",
                              "actions": {"stare": {"trigger": "after_punchline",
                                                    "face": "deadpan"}}})
    ident = B.build("x", p, src=None)
    for k in ("schema", "slug", "personality", "stage_compat", "livekit",
              "runtimes"):
        assert k in ident
    assert ident["schema"] == "pogtown.identity.v1"
    assert ident["personality"]["model"] == "qwen-flash-character"
    txt = (p / "personality.txt").read_text()
    assert "You are X." in txt and "never claim to be an AI" in txt
    assert "runtimes" in ident and "podcast" in ident["runtimes"]


def test_genome_fallback_labels_source(tmp_path):
    src = tmp_path / "src"
    g = src / "theory" / "genomes"
    g.mkdir(parents=True)
    (g / "freak_thin.json").write_text(json.dumps({
        "identity": {"deal": "genome deal wins", "threads": ["t1"],
                     "lore": ["lore line"]}}), encoding="utf-8")
    p = _pack(tmp_path / "packs", "thin", {"name": "Thin"})  # no persona
    ident = B.build("thin", p, src=src)
    assert ident["personality"]["source"] == "genome"
    txt = (p / "personality.txt").read_text()
    assert "genome deal wins" in txt and "FIXED THREADS" in txt


def test_deterministic_build(tmp_path):
    char = {"name": "D", "persona": {"deal": "deal"}, "vibe": "serene"}
    p1 = _pack(tmp_path / "a", "d", dict(char))
    p2 = _pack(tmp_path / "b", "d", dict(char))
    B.build("d", p1, src=None)
    B.build("d", p2, src=None)
    assert (p1 / "personality.txt").read_bytes() == \
           (p2 / "personality.txt").read_bytes()


def test_repo_identities_exist():
    packs = [p for p in (ROOT / "characters").iterdir()
             if (p / "character.json").is_file()]
    ids = list((ROOT / "characters").glob("*/identity.json"))
    assert len(ids) == len(packs), \
        f"{len(ids)} identities for {len(packs)} packs"
    d = json.loads((ROOT / "characters/buddha-ultimate-deadpan/identity.json")
                   .read_text())
    assert d["stage_compat"]["violations"] == []   # buddha must stay clean
    gray = json.loads((ROOT / "characters/gray-x/identity.json").read_text())
    assert gray["personality"]["source"] == "genome"
