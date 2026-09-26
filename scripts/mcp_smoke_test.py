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
import subprocess
import sys
import urllib.error
import urllib.request

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
        got = head.rsplit("(", 1)[-1].split(" pts")[0] if " pts)" in head else None
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

    # The engine path, not just the stored number.
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
