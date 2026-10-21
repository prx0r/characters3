#!/usr/bin/env python3
"""Tests for theory profiles — louis parity, bio ×37, tranche depth.

Run: python3 -m pytest tests/test_profiles.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "theory"))

import build_profiles as B

PROFILES = ROOT / "theory" / "profiles"
TRANCHE1 = ["buddha-ultimate-deadpan", "gray-x",
            "reptilian-ralph-middle-management"]
TRANCHE2 = ["sef-jinn-wish-lawyer", "britt-nordic-coach",
            "kappa-kyle-cucumber-debt", "agent-black-field-visit"]

# louis-ck parity: keys every profile must carry
PARITY = ["schema", "comedian_id", "name", "bio", "identity", "engine",
          "humor_type", "gtvh_profile", "timing_profile", "theory_links",
          "known_bits", "essay_seeds", "sets", "set_queue", "metrics",
          "rating", "tier", "specials_rated", "style", "provenance"]


def _all():
    return {f.stem: json.loads(f.read_text())
            for f in PROFILES.glob("*.json")}


def test_all_profiles_exist_with_bio_and_parity():
    profs = _all()
    packs = [p for p in (ROOT / "characters").iterdir()
             if (p / "character.json").is_file()]
    assert len(profs) == len(packs), (len(profs), len(packs))
    for slug, p in profs.items():
        missing = [k for k in PARITY if k not in p]
        assert not missing, f"{slug} missing {missing}"
        assert (p["bio"] or {}).get("summary", "").strip(), f"{slug} no bio"
        assert p["humor_type"], slug


def test_louis_has_no_deeper_field_than_ours():
    louis = json.loads(
        (ROOT / "graph" / "performers" / "louis-ck.json").read_text())
    ours = json.loads(
        (PROFILES / "buddha-ultimate-deadpan.json").read_text())
    louis_theory_keys = {"bio", "gtvh_profile", "timing_profile",
                         "theory_links", "known_bits", "essay_seeds",
                         "humor_type", "metrics", "rating", "tier"}
    assert louis_theory_keys <= set(ours.keys())
    # ours adds honesty machinery louis (wikidata) doesn't need
    assert "provenance" in ours and "author_type" in ours


def test_tranche1_full_depth():
    for slug in TRANCHE1:
        p = json.loads((PROFILES / f"{slug}.json").read_text())
        g = p["gtvh_profile"]
        krs = [g.get(k) for k in ("SO", "LM", "SI", "TA", "NS", "LA")]
        assert all(krs), f"{slug} KR gap: {[(a, b) for a, b in
                     zip(('SO','LM','SI','TA','NS','LA'), krs) if not b]}"
        assert len(p["theory_links"]["internal"]) >= 3, slug
        assert any(s.get("thesis") for s in p["essay_seeds"]), slug
        bits = p["known_bits"]
        authored = [b for b in bits if b.get("authored")]
        assert len(authored) >= 3, f"{slug} only {len(authored)} authored bits"
        for b in authored:
            assert len(b["why_it_works"]) > 120, f"{slug}: thin why"
            assert b.get("theory_links"), f"{slug}: bit without links"


def test_rating_null_until_crown():
    for p in _all().values():
        assert p["rating"]["headline"] is None


def test_rebuild_preserves_authored(tmp_path, monkeypatch):
    """assemble() must never overwrite authored fields."""
    monkeypatch.setattr(B, "ROOT", ROOT)
    before = (PROFILES / "buddha-ultimate-deadpan.json").read_text()
    prof = B.assemble("buddha-ultimate-deadpan")
    g = prof["gtvh_profile"]
    assert g.get("SO") and g.get("LA"), "authored gtvh lost"
    assert prof["essay_seeds"], "authored seeds lost"
    assert "gtvh_profile" in prof["provenance"]["authored"], \
        "authored field list incomplete"
    # and the file on disk untouched by dry assemble
    assert before == (PROFILES / "buddha-ultimate-deadpan.json").read_text()


def test_no_cjk_or_mojibake_in_authored():
    for slug in TRANCHE1:
        t = (PROFILES / f"{slug}.json").read_text()
        assert not any('一' <= c <= '鿿' for c in t), slug


def test_tranche2_full_depth():
    """Same depth bar as tranche 1; bit floor is 1+ (harness-only sets)."""
    for slug in TRANCHE2:
        p = json.loads((PROFILES / f"{slug}.json").read_text())
        g = p["gtvh_profile"]
        assert all(g.get(k) for k in ("SO", "LM", "SI", "TA", "NS", "LA")), slug
        assert len(p["theory_links"]["internal"]) >= 3, slug
        assert any(s.get("thesis") for s in p["essay_seeds"]), slug
        authored = [b for b in p["known_bits"] if b.get("authored")]
        assert authored, f"{slug} no authored known bits"
        for b in authored:
            assert len(b["why_it_works"]) > 120 and b.get("theory_links")
        assert "bio" in p["provenance"]["authored"], slug
