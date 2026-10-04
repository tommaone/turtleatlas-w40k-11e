#!/usr/bin/env python3
"""Live smoke test for the MCP server.

The pricing fix in adapter/merge.py was verified against the engine, the
suite and the findings — but the MCP server was only ever READ, never
exercised. An LLM consuming this server sees only what these tools return,
so "the data is correct" and "the server serves the correct data" are
different claims. This closes the second one.

Usage:
    node mcp-server/index.js --port=3456 &
    python3 scripts/mcp_smoke_test.py [--port 3456]

Exits non-zero on any mismatch. Requires a running server and node on PATH.
Not part of the pytest suite: it needs a live process and a free port, and
the suite is already 9 minutes.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_JS = os.path.join(ROOT, "mcp-server", "index.js")
FINDINGS = os.path.join(ROOT, "findings")
ADVISOR_JSON = os.path.join(FINDINGS, "advisor.json")
TIERS_JSON = os.path.join(FINDINGS, "army_tiers.json")
SIDECAR = os.path.join(FINDINGS, "imperial-agents", "data.json")

# Display labels #handleGetArmyIndex renders, keyed by advisor.json field name.
FIELD_LABELS = {
    "overall_index": "Overall index",
    "ceiling": "Ceiling",
    "floor": "Floor",
    "versatility": "Versatility",
    "roster_depth": "Roster depth",
    "points_churn": "Points churn",
}

# Points the server must serve for imperial-agents. These are MFM base rates
# (mfm/data/imperial-agents.yaml), the entry WITHOUT groupTitle. Before the
# fix the server returned the "Every Model Has The Imperium Keyword" tier:
# 65/95/110/60/105/110/100/90/175/105/100/85/125/70 respectively.
EXPECTED_IA_POINTS = {
    "Inquisitor": 55,
    "Exaction Squad": 90,
    "Grey Knights Terminator Squad": 175,
    "Navigator": 60,
    "Vindicare Assassin": 110,
    "Inquisitor Coteaz": 75,
    "Sisters Of Battle Squad": 100,
    "Subductor Squad": 85,
    "Eversor Assassin": 100,
    "Rogue Trader Entourage": 75,
    "Inquisitor Draxus": 75,
    "Inquisitorial Agents": 50,
    "Sisters Of Battle Immolator": 90,
    "Voidsmen-At-Arms": 50,
}


class MCP:
    def __init__(self, port):
        self.url = f"http://localhost:{port}/mcp"
        self.session = None
        self._id = 0

    def _post(self, payload):
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream",
                     **({"mcp-session-id": self.session} if self.session else {})},
            method="POST")
        with urllib.request.urlopen(req, timeout=300) as r:
            if not self.session:
                self.session = r.headers.get("mcp-session-id")
            body = r.read().decode()
        # Streamable HTTP replies as SSE: "event: message" then "data: {json}".
        for line in body.splitlines():
            if line.startswith("data:"):
                return json.loads(line[len("data:"):].strip())
        return None

    def call(self, name, args):
        self._id += 1
        r = self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                        "params": {"name": name, "arguments": args}})
        if r is None or "error" in (r or {}):
            raise RuntimeError(f"{name} failed: {str((r or {}).get('error'))[:200]}")
        return "".join(c.get("text", "") for c in r["result"]["content"])

    def initialize(self):
        self._id += 1
        self._post({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "smoke", "version": "1"}}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=3456)
    args = ap.parse_args()

    failures = []

    m = MCP(args.port)
    m.initialize()
    print("  ok   initialize + session")

    contract = m.call("get_llm_contract", {})
    if "engine_output" in contract:
        print("  ok   get_llm_contract exposes the truth/interpretation boundary")
    else:
        failures.append("get_llm_contract missing the engine_output classification")

    # Points, via two independent tools.
    for name, want in EXPECTED_IA_POINTS.items():
        out = m.call("get_unit", {"name": name, "faction": "imperial-agents"})
        head = out.splitlines()[0] if out else ""
        # Headline is "(N pts @ M models)" — match the number, not the shape.
        # A literal " pts)" check breaks the day the label changes.
        m_pts = re.search(r"\((\d+) pts", head)
        got = m_pts.group(1) if m_pts else None
        if got != str(want):
            failures.append(f"get_unit {name}: served {got!r}, want {want}")

    listing = m.call("list_units", {"faction": "imperial-agents"})
    for name, want in EXPECTED_IA_POINTS.items():
        row = [ln for ln in listing.splitlines() if ln.startswith(f"| {name} |")]
        if not row:
            failures.append(f"list_units: {name} missing")
            continue
        got = row[0].split("|")[2].strip()
        if got != str(want):
            failures.append(f"list_units {name}: served {got!r}, want {want}")
    if not any(f.startswith("list_units") for f in failures):
        print(f"  ok   all {len(EXPECTED_IA_POINTS)} imperial-agents prices served correctly "
              f"(get_unit + list_units)")

    # The engine path, not just the stored number. rank_units is raw DPP vs a
    # target with no mission penalties, so it surfaces a different set than
    # get_findings (the pre-computed competition table) — Grey Knights
    # Terminator is #1 there but outside this top 8, and is asserted below.
    ranked = m.call("rank_units", {"faction": "imperial-agents", "top_n": 8})
    for name, want in (("Inquisitorial Agents", 50), ("Inquisitor Draxus", 75),
                       ("Inquisitor", 55)):
        cells = next((c for c in ([p.strip() for p in ln.split("|")]
                                  for ln in ranked.splitlines())
                      if len(c) > 3 and c[2] == name), None)
        if cells is None:
            failures.append(f"rank_units: {name} not in the top 8 table")
        elif cells[3] != str(want):
            failures.append(f"rank_units {name}: {cells[3]!r}, want {want}")
    if not any(f.startswith("rank_units") for f in failures):
        print("  ok   rank_units engine path serves corrected points")

    findings = m.call("get_findings", {"faction": "imperial-agents"})
    if "175" in findings and "81.5" in findings:
        print("  ok   get_findings reflects the recalculated imperial-agents table")
    else:
        failures.append("get_findings does not show the corrected GK Terminator row (175/81.5)")

    if "[object Object]" in m.call("get_unit", {"name": "Inquisitor", "faction": "imperial-agents"}):
        failures.append("get_unit still renders abilities as [object Object]")

    # ---- get_unit must fail closed, and must serve the real stats ----------
    # Three separate ways this tool used to answer confidently and wrongly:
    # an empty name matched the first roster entry via includes(""), the save
    # was read as s.SV while merged stores Sv (so every unit printed SV=?),
    # and the headline quoted costs[0] — the smallest model count, not the
    # squad (a 5-model Paladin Squad priced as its 4-model cost).
    empty = m.call("get_unit", {"faction": "grey-knights"})
    if "Missing required parameter: name" not in empty:
        failures.append("get_unit: an empty name did not fail closed")
    if "Grey Knights Terminator" in empty or "# " in empty.split("\n")[0]:
        failures.append("get_unit: an empty name still returned a unit")
    wrongkey = m.call("get_unit", {"faction": "grey-knights", "unit": "Paladin Squad"})
    if 'the parameter is "name"' not in wrongkey:
        failures.append("get_unit: passing 'unit' instead of 'name' is not diagnosed")

    pal = m.call("get_unit", {"faction": "grey-knights", "name": "Paladin Squad"})
    if "SV=?" in pal:
        failures.append("get_unit: save still renders as SV=? (merged stores Sv)")
    if "INV=4+" not in pal:
        failures.append("get_unit: invuln (InSv) is not rendered")
    if "215 @ 5" not in pal:
        failures.append("get_unit: points ladder missing the 5-model cost (215 @ 5)")
    if not any(f.startswith("get_unit") for f in failures):
        print("  ok   get_unit fails closed, serves Sv/InSv and the points ladder")

    # ---- compute_dpp wound pool -------------------------------------------
    # The tool used to hardcode TargetProfile defaults, so a caller could not
    # model a multi-wound or multi-model target and the output silently
    # under-reported. Assert the cap is both applied AND disclosed.
    base = dict(weapon_name="Incinerator", attacks=10, bs=3, strength=6, ap=-1,
                damage=2, target_toughness=4, target_save=3, unit_points=100)
    flat = m.call("compute_dpp", dict(base))
    deep = m.call("compute_dpp", dict(base, wounds_per_model=2, model_count=5))

    def dpp_of(text):
        for ln in text.splitlines():
            if "Damage Per Point" in ln:
                return ln.split("**")[-2].strip()
        return None

    if "wound pool 1" not in flat:
        failures.append("compute_dpp: omitted pool does not disclose 'wound pool 1'")
    if "wound pool 10" not in deep:
        failures.append("compute_dpp: 2x5 pool does not disclose 'wound pool 10'")
    if dpp_of(flat) != "0.01":
        failures.append(f"compute_dpp 1W pool: dpp {dpp_of(flat)!r}, want '0.01'")
    if dpp_of(deep) != "0.0444":
        failures.append(f"compute_dpp 2x5 pool: dpp {dpp_of(deep)!r}, want '0.0444'")
    if not any(f.startswith("compute_dpp") for f in failures):
        print("  ok   compute_dpp exposes the wound pool and caps damage by it")

    # A 0/negative/fractional pool would print a "wound pool N" line that
    # disagrees with what the engine clamped to. Must refuse, not coerce.
    # NaN is not sent: it is not valid JSON, so the transport 400s before any
    # handler runs. A JSON *string* is the reachable coercion path instead.
    for bad in (0, -1, 2.5, "2", "abc", True):
        out = m.call("compute_dpp", dict(base, wounds_per_model=bad))
        if "must be a whole number >= 1" not in out and "must be a finite number" not in out:
            failures.append(f"compute_dpp: wounds_per_model={bad!r} was not rejected")
    if not any("wounds_per_model" in f for f in failures):
        print("  ok   compute_dpp rejects invalid wound-pool values")

    # Datasheet strings must flatten via the engine's own _parse_attacks and
    # land on exactly the same number as the equivalent flat value.
    flat = dict(base, bs="3+", attacks=4, damage=1)
    def hits_of(**kw):
        o = m.call("compute_dpp", dict(flat, **kw))
        for line in o.splitlines():
            if "Expected Hits" in line:
                return line.split("|")[2].strip()
        return "?"

    for expr, equivalent in [("D6", 3.5), ("2D6", 7.0), ("D3", 2.0)]:
        if hits_of(attacks=expr) != hits_of(attacks=equivalent):
            failures.append(
                f"compute_dpp: attacks {expr!r} != flat {equivalent}"
            )
    if not any("attacks" in f for f in failures):
        print("  ok   compute_dpp flattens dice attacks via the engine parser")

    # Multi-weapon: the wound pool caps the SUM once. Two weapons that each
    # exceed the pool must not report double the target's wounds.
    heavy = [
        {"weapon_name": "heavy A", "attacks": 20, "bs": "3+", "strength": 8, "ap": -2, "damage": 6},
        {"weapon_name": "heavy B", "attacks": 20, "bs": "3+", "strength": 8, "ap": -2, "damage": 6},
    ]
    unit = m.call(
        "compute_unit_dpp",
        dict(weapons=heavy, unit_points=100, target_toughness=4, target_save=3,
             wounds_per_model=2, model_count=5),
    )
    m2 = re.search(r"Total Damage \(capped\).*?\*\*(\d+\.?\d*)\*\*", unit)
    if not m2 or float(m2.group(1)) != 10.0:
        failures.append(
            f"compute_unit_dpp: summed damage must cap at the 10-wound pool, got "
            f"{m2.group(1) if m2 else unit[:80]}"
        )
    if "Damage Before Cap" not in unit:
        failures.append("compute_unit_dpp: missing uncapped disclosure")
    if not any("compute_unit_dpp" in f for f in failures):
        print("  ok   compute_unit_dpp caps the summed total at the wound pool")

    # ---- get_findings reads the JSON sidecar, not the report ---------------
    # Decoupling proof, two halves. The structural half asserts the scraper is
    # gone from the source; the data half asserts a served row matches the
    # sidecar on disk. A future restyle of the HTML cannot fail either.
    server_src = open(SERVER_JS, encoding="utf-8").read()
    if "const\\s+DATA\\s*=" in server_src:
        failures.append("get_findings: the findings.html DATA regex is back in index.js")
    sidecar = json.load(open(SIDECAR, encoding="utf-8"))
    served = sidecar["meta"]["competitive"]["Take and Hold"]
    probe = served[0]
    row = f"| {probe['pts']} | {probe['score']} | {probe['dpp']} |"
    if row not in findings:
        failures.append(f"get_findings: sidecar row not served verbatim ({row!r})")
    if not any(f.startswith("get_findings") for f in failures):
        print("  ok   get_findings serves the data.json sidecar (HTML scraper gone)")

    # ---- army-level indices -----------------------------------------------
    idx = m.call("get_army_index", {"faction": "grey-knights"})
    advisor = json.load(open(ADVISOR_JSON, encoding="utf-8"))
    gk = next(f for f in advisor["factions"] if f["fid"] == "grey-knights")
    # Compare numerically: advisor.json holds 58.0, the server renders 58, and
    # a substring check on the raw float fails on formatting alone.
    served_fields = {}
    for ln in idx.splitlines():
        if ln.startswith("| ") and " | " in ln:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            if len(cells) == 2:
                served_fields[cells[0]] = cells[1]
    for field in ("overall_index", "ceiling", "versatility", "roster_depth"):
        # Server renders display labels; advisor.json uses snake_case keys.
        label = FIELD_LABELS.get(field, field)
        want, got = gk[field], served_fields.get(label)
        try:
            ok = got is not None and abs(float(got) - float(want)) < 1e-9
        except (TypeError, ValueError):
            ok = False
        if not ok:
            failures.append(f"get_army_index: {field} served {got!r}, want {want}")
    if "Not modeled" not in idx:
        failures.append("get_army_index: missing the not-modeled contract block")
    if not any(f.startswith("get_army_index") for f in failures):
        print("  ok   get_army_index serves advisor.json fields + contract block")

    tiers = json.load(open(TIERS_JSON, encoding="utf-8"))
    ranked = m.call("get_faction_tiers", {"mission": "Purge the Foe", "top_n": 5})
    best = max(tiers.items(), key=lambda kv: kv[1]["missions"]["Purge the Foe"])
    if str(best[1]["missions"]["Purge the Foe"]) not in ranked:
        failures.append("get_faction_tiers: top mission score not served")
    if not any(f.startswith("get_faction_tiers") for f in failures):
        print("  ok   get_faction_tiers ranks by mission from army_tiers.json")

    cmp_out = m.call("compare_factions", {"factions": ["grey-knights", "orks"]})
    for fid in ("grey-knights", "orks"):
        if fid not in cmp_out:
            failures.append(f"compare_factions: {fid} absent")
    if "rules-free" not in cmp_out or "rules-aware" not in cmp_out:
        failures.append("compare_factions: missing the two-source distinction")
    if not any(f.startswith("compare_factions") for f in failures):
        print("  ok   compare_factions serves both source tables")

    topics = m.call("list_findings_topics", {"faction": "dark-angels"})
    if "take-and-hold-trivector.html" not in topics:
        failures.append("list_findings_topics: misses the dark-angels topic report")
    if not any(f.startswith("list_findings_topics") for f in failures):
        print("  ok   list_findings_topics surfaces the extra topic report")

    print()
    if failures:
        print(f"FAIL — {len(failures)} problem(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — MCP server serves the corrected pricing end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
