#!/usr/bin/env python3
"""Voldus MCP client wrapper — Route 1.

Speaks the Streamable HTTP transport so the agent can call the
turtleatlas-w40k-11e MCP tools the way a real MCP host would.
Usage:
    python3 voldus_mcp.py <tool> '<json-args>'
    python3 voldus_mcp.py list-factions
    python3 voldus_mcp.py compute-dpp '{"attacks":10,...}'
Session persists for the process lifetime only.
"""
import json
import sys
import urllib.request

DEFAULT_PORT = 3456


class MCPClient:
    def __init__(self, port):
        self.url = f"http://localhost:{port}/mcp"
        self.session = None
        self._id = 0

    def _post(self, payload):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session:
            headers["mcp-session-id"] = self.session
        req = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            if not self.session:
                self.session = r.headers.get("mcp-session-id")
            body = r.read().decode()
        for line in body.splitlines():
            if line.startswith("data:"):
                return json.loads(line[len("data:"):].strip())
        return None

    def initialize(self):
        self._id += 1
        self._post({
            "jsonrpc": "2.0", "id": self._id, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "voldus", "version": "1"},
            },
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, name, args):
        self._id += 1
        r = self._post({
            "jsonrpc": "2.0", "id": self._id, "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })
        if r is None or "error" in (r or {}):
            raise RuntimeError(f"{name} failed: {str((r or {}).get('error'))[:300]}")
        return "".join(c.get("text", "") for c in r["result"]["content"])


TOOLS = {
    "get-llm-contract": "get_llm_contract",
    "list-factions": "list_factions",
    "get-core-rules": "get_core_rules",
    "get-ability": "get_ability",
    "get-detachment": "get_detachment",
    "compute-dpp": "compute_dpp",
    "list-units": "list_units",
    "get-unit": "get_unit",
    "get-stratagem": "get_stratagem",
    "compute-surv": "compute_surv",
    "compute-mob": "compute_mob",
    "rank-units": "rank_units",
    "get-findings": "get_findings",
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    tool = sys.argv[1]
    if tool not in TOOLS:
        print(f"unknown tool: {tool}\navailable: {', '.join(sorted(TOOLS))}")
        return 2
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    port = DEFAULT_PORT
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    m = MCPClient(port)
    m.initialize()
    print(m.call(TOOLS[tool], args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
