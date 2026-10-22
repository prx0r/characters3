#!/usr/bin/env python3
"""minute — a character writes their own minute, then edges it.

The loop chars2 never closed, with the pieces chars2 proved:

  brief   personality.txt + archetype doctrine + authored known_bits (style
          exemplars) + mutation premise when a mutant
  write   unslopnemo-12b (deslopinated — attacks formulaic slop at SOURCE;
          house mimo flinches on L2/L3, EDGE.md) via OpenRouter
  edge    per-bit ladder L1/L2/L3 (jokegate/edge.py) — the line needs a
          ladder, not a point. select(audience) or select_near(--edge dial).
          L3 never selectable (by construction). roster='freaks' => THE-LINE
          distance 0.7 (packs carry no roster field — default 0.5 was part
          of the 'not edgy enough' bug).
  mask    EdgyGate veto (victim/benign) + NoSlop band — filter only, never
          reward.
  out     minutes/<slug>-<ts>.json (full ladder provenance) + .txt for seal
  judge   -> characters2 judge.py -> chars3 feedback/rewards.jsonl (tracked)

Spend: OpenRouter unslopnemo ≈ $0.002-0.005 per minute (directed by owner).

Usage:
  python3 minute.py buddha-angry [--audience club_latenight] [--edge 0.7]
  python3 minute.py buddha-ultimate-deadpan --seal
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARS2 = Path("/root/characters2")
ENGINE = Path("/root/characters")          # delivery engine + freaks mirror
OUT = HERE / "minutes"

EDGE_MODEL = "thedrummer/unslopnemo-12b"


def setup_env() -> None:
    """Keys from vault -> env only. Model pinned to unslopnemo."""
    os.environ.setdefault("OPENROUTER_EDGE_MODEL", EDGE_MODEL)
    if not os.environ.get("OPENROUTER_API_KEY"):
        try:
            out = subprocess.run(
                ["agent-vault", "vault", "credential", "get",
                 "OPENROUTER_API_KEY", "--vault", "oracle"],
                capture_output=True, text=True, timeout=30).stdout.strip()
            if out:
                os.environ["OPENROUTER_API_KEY"] = out
        except Exception:
            pass
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("OPENROUTER_API_KEY missing (vault/env)")


def wire_chars2() -> None:
    sys.path.insert(0, str(CHARS2 / "theory"))      # jokegate package root


def load_pack(slug: str) -> dict:
    p = HERE / "characters" / slug / "character.json"
    if not p.is_file():
        raise SystemExit(f"no pack: {p}")
    d = json.loads(p.read_text())
    d.setdefault("roster", "freaks")   # THE-LINE distance 0.7 for our freaks
    d.setdefault("agent_id", f"freak:{slug}")
    return d


def archetype_for(slug: str) -> dict | None:
    for f in sorted((HERE / "archetypes").glob("*.json")):
        a = json.loads(f.read_text())
        if slug in (a.get("members") or []):
            return a
    return None


def writer_system(slug: str, char: dict, arch: dict | None) -> str:
    pers = (HERE / "characters" / slug / "personality.txt")
    pers_txt = pers.read_text() if pers.is_file() else f"You are {char.get('name')}."
    core = ((arch or {}).get("core_theory") or {})
    L = [pers_txt.strip(), ""]
    if core.get("funny_because"):
        L += ["WHY YOU ARE FUNNY (your core theory — the minute must prove it):",
              core["funny_because"], ""]
    for v in ((arch or {}).get("violations_that_work") or [])[:1]:
        if v.get("mutant_premise") and v["mutant_premise"] in str(char.get("premise", "")):
            L += [f"YOUR CURRENT OPERATING CONTRADICTION: {v['contradicts']}", ""]
    L += [
        "WRITE A ONE-MINUTE SET: 4-6 bits, each 25-90 words, self-contained,",
        "separated by a line containing only ---.",
        "STEP OVER THE LINE where your doctrine allows it: commit to the turn,",
        "no retreating last line, butt on yourself/the powerful/the species only.",
        "Output ONLY the bits. No preamble, no numbering, no titles.",
    ]
    return "\n".join(L)


def write_base_minute(system: str, seed_bit: str = "") -> str:
    """Own OpenRouter call: shared llm.chat caps max_tokens=500 (fine for
    ladder rewrites, truncates a whole minute). unslopnemo, 1600 tokens."""
    import urllib.request
    user = ("Write the set now." if not seed_bit else
            f"Open the set with a variation of this your own line, then "
            f"continue: {seed_bit}")
    body = {"model": os.environ.get("OPENROUTER_EDGE_MODEL", EDGE_MODEL),
            "temperature": 0.95, "max_tokens": 1600,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    req = urllib.request.Request(
        os.getenv("OPENROUTER_BASE_URL",
                  "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                 "User-Agent": "Mozilla/5.0",
                 "HTTP-Referer": "https://auditions.pogtown.com/",
                 "X-Title": "Pogtown minute writer"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode())
        text = (data.get("choices") or [{}])[0].get("message", {}).get(
            "content", "").strip()
    except Exception as e:
        raise SystemExit(f"writer failed: {str(e)[:160]}")
    if not text:
        raise SystemExit("writer returned empty")
    low = text.lower()
    if any(m in low for m in ("i can't", "as an ai", "against my")) and len(text.split()) < 120:
        raise SystemExit(f"writer refused: {text[:120]}")
    return text


def split_bits(minute: str) -> list[str]:
    import re as _re
    chunks = [c.strip() for c in _re.split(r"\n\s*-{3,}[ \t]*\n", minute)
              if c.strip()]
    if len(chunks) == 1 and len(minute.split()) > 160:
        # writer ignored separators: fall back to blank-line chunks
        chunks = [c.strip() for c in _re.split(r"\n[ \t]*\n", minute)
                  if c.strip()]
    out = []
    for c in chunks:
        c = "\n".join(l for l in c.splitlines()
                      if l.strip() and not l.strip().startswith(("#", "SET", "BIT ")))
        if 15 <= len(c.split()) <= 140:
            out.append(c.strip())
    return out



STYLE_WPM_DEFAULT = 180
WPM_BY_STYLE = {"norm_macdonald": 200, "louis": 170}   # engine style recipes


def _style_wpm(char: dict) -> int:
    style = (char.get("delivery") or {}).get("style")
    if style in WPM_BY_STYLE:
        return WPM_BY_STYLE[style]
    # ask the engine's harvested style if present (authoritative when local)
    p = ENGINE / "audition" / "voicelab" / "styles" / f"{style}.json"
    try:
        w = json.loads(p.read_text()).get("engine_recipe", {}).get("wpm")
        if isinstance(w, (int, float)) and 80 <= w <= 320:
            return int(w)
    except (OSError, ValueError, AttributeError):
        pass
    return STYLE_WPM_DEFAULT


def estimate_seconds(bits: list, char: dict) -> float:
    """Speech time + beat pauses. Calibrated vs delivery_engine renders
    (177w/3bits buddha = 53.8s actual vs ~57 est)."""
    words = sum(len(b["text"].split()) for b in bits)
    if not bits:
        return 0.0
    ov = (char.get("delivery") or {}).get("overrides") or {}
    hold = (ov.get("punchline_hold_ms") or 1500) / 1000.0
    post = (ov.get("post_punch_ms") or 1000) / 1000.0
    n = len(bits)
    speech = words / _style_wpm(char) * 60.0
    pauses = n * (hold + post) / 2.0          # one build+release per bit
    inter = max(0, n - 1) * 0.6               # bit transitions
    return round(speech + pauses + inter, 1)

def edge_bit(bit: str, char: dict, audience: str, dial: float | None) -> dict:
    from jokegate import edge as E
    ladder = E.render_ladder(bit, character=char, prefer="openrouter")
    sel = (E.select_near(ladder, dial) if dial is not None
           else E.select(ladder, audience))
    # belt+suspenders: chosen must be gated-pass and victim-veto free
    pick = sel.get("pick")
    if pick and sel.get("text"):
        rec = next((r for r in ladder["renders"]
                    if r.get("level") == pick and r.get("text") == sel["text"]), None)
        g = (rec or {}).get("gate") or {}
        if not g.get("passed") or g.get("target") == "victim":
            sel = {**sel, "pick": None, "text": None,
                   "reason": f"veto after select: passed={g.get('passed')} "
                             f"target={g.get('target')}"}
    return {"ladder": ladder, "selected": sel}


def slop_mask(text: str, char: dict) -> dict:
    from jokegate import slop as S
    try:
        v = S.SlopGate().classify(text, char)
        return {"passed": bool(v.get("passed")),
                "problems": v.get("problems", [])}
    except Exception as e:                     # mask never crashes the loop
        return {"passed": True, "problems": [f"slop check error: {e}"]}




def _chunk_sentences(text: str, max_w: int = 70) -> list[str]:
    """Greedy sentence chunks <= max_w words (reads as standup bits)."""
    import re as _re
    sents = [x for x in _re.split(r"(?<=[.;:?])\s+", text.strip()) if x]
    bits, cur = [], []
    w = 0
    for sn in sents:
        n = len(sn.split())
        if cur and w + n > max_w:
            bits.append(" ".join(cur))
            cur, w = [], 0
        cur.append(sn)
        w += n
    if cur:
        bits.append(" ".join(cur))
    return [b for b in bits if len(b.split()) >= 8]


def extract_minute(a, char: dict) -> int:
    """VERBATIM minute: the character reads the canon. No LLM, $0.
    Humor = delivery over doctrine (pack holds/style) — the punch is the
    room waiting for a resolution the aphorism refuses to give."""
    OUT.mkdir(parents=True, exist_ok=True)
    plist = HERE / "characters" / a.slug / "passages.jsonl"
    if not plist.is_file():
        raise SystemExit("no passages for this character")
    passages = [json.loads(l) for l in plist.read_text().splitlines()]
    by_id = {x.get("range") or x.get("id"): x for x in passages}
    if a.passage:
        if a.passage not in by_id:
            raise SystemExit(f"unknown passage {a.passage} (ids: "
                             f"{sorted(by_id)[:8]}...)")
        start = passages.index(by_id[a.passage])
    else:
        start = 0
    chosen, i, est = [], start, 0.0
    while i < len(passages) and (est < a.min_seconds or not chosen):
        chosen.append(passages[i])
        bits_tmp = [{"text": t} for c in chosen
                    for t in _chunk_sentences(c["text"])]
        est = estimate_seconds(bits_tmp, char)
        i += 1
        if i - start >= 4 and est >= a.min_seconds:
            break
    bits = []
    for c in chosen:
        for t in _chunk_sentences(c["text"]):
            bits.append({"slot": f"b{len(bits)+1}", "text": t,
                         "base_text": t, "selected_level": "verbatim",
                         "edginess": None, "select_reason":
                         f"extract from {c.get('range') or c.get('id')} "
                         f"({c.get('kind','text-range')})",
                         "ladder": [], "slop_mask": {"passed": True,
                             "note": "canonical text — mask not applicable"}})
    est = estimate_seconds(bits, char)
    duration_ok = est >= a.min_seconds
    doc = {
        "schema": "pogtown.minute.v1", "character": a.slug,
        "name": char.get("name"), "roster": "freaks",
        "mode": "extractive-verbatim",
        "source_passages": [c.get("range") or c.get("id") for c in chosen],
        "audience": None, "edge_dial": None,
        "writer_model": None,   # no generation — EXTRACT-NEVER-WRITE
        "archetype": (archetype_for(a.slug) or {}).get("id"),
        "doctrine_preserved": True,
        "delivery_note": "punch timing = pack delivery (holds/style); comedy "
                         "is the non-release: the room waits for a resolution "
                         "the aphorism refuses to give",
        "bits": bits, "dropped": [],
        "duration": {"estimate_s": est, "min_s": a.min_seconds,
                     "ok": duration_ok, "model": "words/wpm + holds"},
        "metrics": {"n_bits": len(bits),
                    "words_total": sum(len(b["text"].split()) for b in bits)},
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "next": "delivery_engine --seal (sync pack to engine first) -> stage",
    }
    jp = OUT / f"{a.slug}-{time.strftime('%Y%m%d-%H%M%S')}-verbatim.json"
    jp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    tp = jp.with_suffix("").with_suffix(".txt")
    tp.write_text("\n\n".join(b["text"] for b in bits) + "\n")
    print(f"extract minute: {len(bits)} bits, {doc['metrics']['words_total']}w, "
          f"est {est}s ({'OK' if duration_ok else 'SHORT'}) "
          f"from {doc['source_passages']}")
    if a.seal:
        return _seal(a, tp)
    return 0


def _seal(a, txt_path) -> int:
    import subprocess as sp
    if not (ENGINE / "freaks" / a.slug / "character.json").is_file():
        raise SystemExit(f"--seal: sync pack first "
                         f"(cp -r characters/{a.slug} {ENGINE}/freaks/)")
    out = sp.run([sys.executable, "delivery_engine.py", str(txt_path),
                  "--comedian", a.slug, "--out", f"minute_{a.slug}",
                  "--seal", f"/tmp/sealed_minute_{a.slug}"],
                 cwd=ENGINE / "audition", capture_output=True, text=True,
                 timeout=280)
    print((out.stdout or out.stderr)[-800:])
    print("sealed ->", f"/tmp/sealed_minute_{a.slug}")
    return 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--audience", default="club_latenight",
                    choices=["club_latenight", "club_early", "theater",
                             "corporate", "broadcast"])
    ap.add_argument("--edge", type=float, default=None,
                    help="edge dial 0..1 (select_near) instead of audience select")
    ap.add_argument("--bits", type=int, default=5)
    ap.add_argument("--min-seconds", type=float, default=60.0,
                    help="floor: keep writing/edging until est >= this")
    ap.add_argument("--max-seconds", type=float, default=90.0)
    ap.add_argument("--extract", action="store_true",
                    help="verbatim mode: read the canon (no generation, $0)")
    ap.add_argument("--passage", default=None,
                    help="extract mode: passage range id, e.g. ch56-57")
    ap.add_argument("--seal", action="store_true",
                    help="render sealed-set via characters engine (pack must "
                         "exist in /root/characters/freaks)")
    a = ap.parse_args(argv)

    setup_env()
    wire_chars2()
    char = load_pack(a.slug)
    arch = archetype_for(a.slug)
    OUT.mkdir(exist_ok=True)

    if a.extract:
        return extract_minute(a, char)

    system = writer_system(a.slug, char, arch)
    t0 = time.time()
    raw = write_base_minute(system,
                            seed_bit=((char.get("premise") or "")[:160]
                                      if arch else ""))
    bits = split_bits(raw)[: a.bits]
    if not bits:
        raise SystemExit("writer produced no usable bits")
    print(f"writer: {len(bits)} bits in {time.time()-t0:.1f}s "
          f"(model {os.environ.get('OPENROUTER_EDGE_MODEL')})")

    final_bits, dropped = [], []
    for i, b in enumerate(bits, 1):
        res = edge_bit(b, char, a.audience, a.edge)
        sel = res["selected"]
        lad = res["ladder"]
        ladder_summary = [
            {"level": r["level"],
             "edginess": (r.get("gate") or {}).get("edginess"),
             "target": (r.get("gate") or {}).get("target"),
             "passed": (r.get("gate") or {}).get("passed"),
             "refused": r.get("refused", False)}
            for r in lad["renders"]]
        if not sel.get("text"):
            dropped.append({"base": b, "reason": sel.get("reason"),
                            "ladder": ladder_summary})
            print(f"  bit {i}: DROPPED ({sel.get('reason')})")
            continue
        m = slop_mask(sel["text"], char)
        if not m["passed"]:
            # try L1 fallback from the ladder before dropping
            l1 = next((r for r in lad["renders"]
                       if r["level"] == "L1_safe" and r.get("text")
                       and (r.get("gate") or {}).get("passed")), None)
            if l1:
                sel = {**sel, "pick": "L1_safe", "text": l1["text"],
                       "reason": sel.get("reason", "") + " | sop-mask -> L1"}
            else:
                dropped.append({"base": b, "reason": "slop mask",
                                "problems": m["problems"],
                                "ladder": ladder_summary})
                print(f"  bit {i}: DROPPED (slop mask: {m['problems'][:1]})")
                continue
        print(f"  bit {i}: {str(sel.get('pick') or '?'):9s} "
              f"edge={sel.get('edginess')} "
              f"cap/dial={'dial '+str(a.edge) if a.edge is not None else a.audience} "
              f"| {sel['text'][:70]}...")
        final_bits.append({
            "slot": f"b{i}", "base_text": b,
            "selected_level": sel.get("pick"),
            "edginess": sel.get("edginess"),
            "text": sel["text"],
            "select_reason": sel.get("reason"),
            "ladder": ladder_summary,
            "slop_mask": m})

    if not final_bits:
        raise SystemExit("no bits survived the masks")

    # ── 60s floor: top-up rounds (each = fresh writer bits through the
    #    same ladder+masks) until estimate clears --min-seconds ──
    est = estimate_seconds(final_bits, char)
    rounds = 0
    while est < a.min_seconds and rounds < 3 and len(final_bits) < a.bits + 6:
        rounds += 1
        need = int((a.min_seconds - est) / 8) + 2
        print(f"\n  duration {est}s < {a.min_seconds}s -> top-up round "
              f"{rounds} (+~{need} bits)")
        try:
            more = split_bits(write_base_minute(
                system, seed_bit=f"continue the set (already "
                f"{len(final_bits)} bits done) with {need} more bits "
                f"in your voice"))
        except SystemExit as e:
            print(f"  top-up writer failed: {e}")
            break
        added = 0
        for b in more:
            if added >= need or len(final_bits) >= a.bits + 6:
                break
            res = edge_bit(b, char, a.audience, a.edge)
            sel = res["selected"]
            if not sel.get("text"):
                continue
            m = slop_mask(sel["text"], char)
            if not m["passed"]:
                continue
            final_bits.append({
                "slot": f"b{len(final_bits) + 1}", "base_text": b,
                "selected_level": sel.get("pick"),
                "edginess": sel.get("edginess"), "text": sel["text"],
                "select_reason": sel.get("reason"),
                "ladder": [], "slop_mask": m, "topup_round": rounds})
            added += 1
        est = estimate_seconds(final_bits, char)

    est = estimate_seconds(final_bits, char)
    duration_ok = est >= a.min_seconds
    duration_over = est > a.max_seconds
    if not duration_ok:
        print(f"  WARNING: estimated {est}s < {a.min_seconds}s floor after "
              f"{rounds} top-up(s) — flagged SHORT in the doc")
    doc = {
        "schema": "pogtown.minute.v1",
        "character": a.slug, "name": char.get("name"),
        "roster": "freaks",
        "audience": a.audience, "edge_dial": a.edge,
        "writer_model": EDGE_MODEL,
        "archetype": (arch or {}).get("id"),
        "doctrine_preserved": True,
        "bits": final_bits,
        "dropped": dropped,
        "duration": {"estimate_s": est,
                     "min_s": a.min_seconds, "max_s": a.max_seconds,
                     "ok": duration_ok, "over": duration_over,
                     "topup_rounds": rounds,
                     "model": "words/wpm(style) + holds + transitions "
                              "(calibrated vs delivery_engine renders)"},
        "metrics": {
            "n_bits": len(final_bits),
            "words_total": sum(len(b["text"].split()) for b in final_bits),
            "mean_selected_edge": round(sum(
                (b.get("edginess") or 0) for b in final_bits) / len(final_bits), 3),
            "levels": {lv: sum(1 for b in final_bits
                               if b["selected_level"] == lv)
                       for lv in ("L1_safe", "L2_line")}},
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "next": "delivery_engine --seal (characters engine) -> judge.py -> "
                "characters3/feedback/rewards.jsonl",
    }
    jp = OUT / f"{a.slug}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    jp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    txt = "\n\n".join(b["text"] for b in final_bits)
    tp = jp.with_suffix(".txt")
    tp.write_text(txt + "\n")
    print(f"\nminute: {jp.name} | est {est}s "
          f"({'OK' if duration_ok else 'SHORT <' + str(a.min_seconds) + 's'}) "
          f"| mean edge {doc['metrics']['mean_selected_edge']} "
          f"| levels {doc['metrics']['levels']} | dropped {len(dropped)}")
    if a.seal:
        return _seal(a, tp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
