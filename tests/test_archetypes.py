#!/usr/bin/env python3
"""Tests for archetypes + mutations — the doctrine-preservation contract.

Run: python3 -m pytest tests/test_archetypes.py -q
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mutate as M

ARCH = ROOT / "archetypes"
REQ = ["schema", "id", "name", "members", "core_theory",
       "violations_that_work", "mutation_operators", "provenance"]


def _all():
    return {f.stem: json.loads(f.read_text()) for f in ARCH.glob("*.json")}


def test_archetype_schema_and_doctrine():
    archs = _all()
    assert {"buddha", "gnome", "reptilian", "grey"} <= set(archs), archs
    for k, a in archs.items():
        assert all(x in a for x in REQ), f"{k} missing {[x for x in REQ if x not in a]}"
        assert a["schema"] == "freaktown.archetype.v1"
        core = a["core_theory"]
        assert len(core.get("funny_because", "")) > 100, k
        assert core.get("doctrine") and core.get("doctrine_source"), k
        ops = {o["id"] for o in a["mutation_operators"]}
        assert {"doctrine-inversion", "status-flip", "thread-corruption",
                "lore-injection"} <= ops, k
        for v in a["violations_that_work"]:
            assert v["contradicts"] and len(v["why_funny"]) > 100, f"{k}:{v['id']}"
            assert v["mutant_premise"] and v["mutant_thread"], k
            assert v.get("mutation") in ("doctrine-inversion", "status-flip",
                                         "thread-corruption", "lore-injection")


def test_flagship_buddha_angry_contract():
    """The user's canonical example: angry Buddha keeps doctrine + slowness."""
    base = json.loads((ROOT / "characters/buddha-ultimate-deadpan"
                       / "character.json").read_text())
    ang = json.loads((ROOT / "characters/buddha-angry/character.json").read_text())
    assert ang["philosophy"] == base["philosophy"], "doctrine must survive"
    assert (ang.get("delivery") or {}).get("style") == \
           (base.get("delivery") or {}).get("style"), "NS must survive"
    assert ang["vibe"] == base["vibe"]
    assert ang["premise"] != base["premise"]
    m = ang["mutations"][0]
    assert m["operator"] == "doctrine-inversion" and m["delivery"] == "preserved"
    assert m["archetype"] == "arch:buddha" and "axiology" in m["contradicts"]
    assert "(Angry)" in ang["name"]


def test_mutate_on_fixture(tmp_path, monkeypatch):
    archdir = tmp_path / "archetypes"
    chardir = tmp_path / "characters"
    archdir.mkdir(); (chardir / "foo").mkdir(parents=True)
    (archdir / "foo.json").write_text(json.dumps({
        "schema": "freaktown.archetype.v1", "id": "arch:foo",
        "name": "Foo", "members": ["foo"],
        "core_theory": {"funny_because": "x" * 120,
                        "doctrine_source": "pack",
                        "doctrine": {"ontology": "invariant"}},
        "violations_that_work": [{
            "id": "flip", "label": "Foo (Flipped)",
            "contradicts": "ontology: invariant",
            "why_funny": "y" * 130,
            "mutant_premise": "authored premise line",
            "mutant_thread": "authored thread",
            "mutation": "status-flip", "delivery": "may_change_register",
            "mutant_vibe": "manic"}],
        "mutation_operators": [], "provenance": {}}), encoding="utf-8")
    (chardir / "foo" / "character.json").write_text(json.dumps({
        "name": "Foo", "vibe": "deadpan", "premise": "base premise",
        "threads": ["base thread"], "philosophy": {"ontology": "invariant"},
        "delivery": {"style": "norm_macdonald"}}), encoding="utf-8")
    monkeypatch.setattr(M, "ARCH", archdir)
    monkeypatch.setattr(M, "CHARS", chardir)
    slug = M.mutate("foo", "flip")
    assert slug == "foo-flip"
    out = json.loads((chardir / "foo-flip/character.json").read_text())
    assert out["premise"] == "authored premise line"   # engine wrote NO prose
    assert out["threads"][0] == "authored thread"
    assert out["philosophy"] == {"ontology": "invariant"}   # doctrine intact
    assert out["vibe"] == "manic"          # status-flip declares mutant_vibe
    assert out["mutations"][0]["operator"] == "status-flip"
    # registered in archetype members
    assert "foo-flip" in json.loads(
        (archdir / "foo.json").read_text())["members"]


def test_mutants_have_identity_and_profile():
    packs = [p for p in (ROOT / "characters").iterdir()
             if (p / "character.json").is_file() and
             (p / "character.json").read_text().find('"mutations"') >= 0]
    assert packs, "no mutants exist"
    for p in packs:
        assert (p / "identity.json").is_file(), f"{p.name} no identity"
        assert (ROOT / "theory/profiles" / f"{p.name}.json").is_file()
