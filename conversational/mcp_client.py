#!/usr/bin/env python3
"""MCP StreamableHTTP client for turtleatlas-w40k-11e.

Implements the full MCP StreamableHTTP protocol:
  1. POST /mcp with "initialize" -> get Mcp-Session-Id from headers
  2. POST /mcp with "notifications/initialized" (no response body, 202)
  3. POST /mcp with "tools/list" or "tools/call" -> SSE response parsed for JSON-RPC

All responses are SSE-formatted:
    event: message
    data: {"jsonrpc":"2.0","id":1,"result":{...}}

Uses only the `requests` library. No pip installs needed.
"""

import json
import logging
import os
import signal
import subprocess
import time
import traceback

import requests

log = logging.getLogger(__name__)

# -- Configuration -----------------------------------------------------------

MCP_URL = os.environ.get("MCP_URL", "http://localhost:3456/mcp")
HEALTH_URL = os.environ.get("HEALTH_URL", "http://localhost:3456/health")
MCP_SERVER_DIR = os.environ.get(
    "MCP_SERVER_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mcp-server"),
)
PROTOCOL_VERSION = "2025-03-26"
CLIENT_INFO = {"name": "python-streamable-http-client", "version": "1.0.0"}


# -- SSE Parsing -------------------------------------------------------------

def _parse_sse(text):
    """Parse SSE text into list of JSON-RPC message dicts.

    SSE format:
        event: message
        data: {"jsonrpc":"2.0","id":1,"result":{...}}

    Returns list of parsed JSON dicts from all data: lines.
    """
    messages = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            payload = line[6:]
            if payload:
                try:
                    messages.append(json.loads(payload))
                except json.JSONDecodeError as e:
                    log.warning("SSE data line not valid JSON: %s -- %s", payload[:100], e)
    return messages


# -- MCP StreamableHTTP Client -----------------------------------------------

class MCPClient:
    """StreamableHTTP MCP client. Handles session lifecycle and SSE parsing."""

    def __init__(self, url=MCP_URL, timeout=30.0):
        self.url = url
        self.timeout = timeout
        self.session_id = None
        self._call_id = 0
        self._initialized = False
        self._session = requests.Session()
        # Both accept types required by the StreamableHTTP spec
        self._session.headers.update({
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        })

    def _next_id(self):
        self._call_id += 1
        return self._call_id

    def _post(self, payload, extra_headers=None):
        """POST to MCP endpoint with session headers."""
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        headers["Mcp-Protocol-Version"] = PROTOCOL_VERSION
        if extra_headers:
            headers.update(extra_headers)
        return self._session.post(
            self.url, json=payload, headers=headers, timeout=self.timeout,
        )

    def initialize(self):
        """Send initialize request, extract session ID from response headers.

        Returns the server's initialize result (capabilities, serverInfo).
        """
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
        }
        resp = self._post(payload)

        # Extract session ID from response headers (CaseInsensitiveDict)
        self.session_id = resp.headers.get("Mcp-Session-Id")
        if not self.session_id:
            raise RuntimeError(
                f"No Mcp-Session-Id in response headers. "
                f"Status={resp.status_code}, Headers={dict(resp.headers)}"
            )

        # Parse SSE response
        messages = _parse_sse(resp.text)
        if not messages:
            raise RuntimeError(
                f"No JSON-RPC messages in SSE response. Raw: {resp.text[:500]}"
            )

        result_msg = messages[0]
        if "error" in result_msg:
            raise RuntimeError(f"Initialize error: {result_msg['error']}")
        return result_msg.get("result", {})

    def send_initialized(self):
        """Send the notifications/initialized notification.

        Notifications have no 'id' field, server responds with 202.
        """
        payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        resp = self._post(payload)
        if resp.status_code not in (200, 202):
            raise RuntimeError(
                f"Initialized notification failed: "
                f"status={resp.status_code}, body={resp.text[:300]}"
            )
        self._initialized = True

    def connect(self):
        """Full handshake: initialize + send initialized notification.

        Returns server capabilities.
        """
        caps = self.initialize()
        self.send_initialized()
        return caps

    def _call(self, method, params=None):
        """Send a JSON-RPC request and parse the SSE response."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        resp = self._post(payload)

        # Notifications get 202 with no body
        if resp.status_code == 202:
            return {}

        if resp.status_code != 200:
            if resp.status_code in (404, 410):
                self.session_id = None
                self._initialized = False
            raise RuntimeError(
                f"MCP call failed: status={resp.status_code}, body={resp.text[:500]}"
            )

        messages = _parse_sse(resp.text)
        if not messages:
            # Could be a plain JSON response (not SSE)
            try:
                msg = resp.json()
                messages = [msg]
            except (json.JSONDecodeError, ValueError):
                raise RuntimeError(
                    f"No parseable response. "
                    f"Content-Type={resp.headers.get('Content-Type')}, "
                    f"body={resp.text[:500]}"
                )

        # Find the message matching our request id
        req_id = payload["id"]
        for msg in messages:
            if msg.get("id") == req_id:
                if "error" in msg:
                    raise RuntimeError(f"MCP error: {msg['error']}")
                return msg.get("result", {})

        # Fallback: return first message
        msg = messages[0]
        if "error" in msg:
            raise RuntimeError(f"MCP error: {msg['error']}")
        return msg.get("result", {})

    def list_tools(self):
        """List available tools."""
        result = self._call("tools/list")
        return result.get("tools", [])

    def call_tool(self, name, arguments=None):
        """Call a tool and return the text content."""
        result = self._call(
            "tools/call", {"name": name, "arguments": arguments or {}}
        )
        contents = result.get("content", [])
        texts = [c["text"] for c in contents if c.get("type") == "text"]
        return "\n".join(texts) if texts else json.dumps(result)


# -- Server lifecycle --------------------------------------------------------

def start_mcp_server(port=3456, health_timeout=15.0, server_dir=None):
    """Spawn the MCP server as a subprocess, wait for health check.

    Returns the Popen object. Caller is responsible for cleanup.
    """
    server_dir = server_dir or MCP_SERVER_DIR
    cmd = ["node", "index.js", f"--port={port}"]

    proc = subprocess.Popen(
        cmd,
        cwd=server_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )

    # Wait for health check
    health_url = f"http://localhost:{port}/health"
    deadline = time.monotonic() + health_timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode(errors="replace")
            raise RuntimeError(
                f"MCP server exited with code {proc.returncode}.\n"
                f"Stderr: {stderr[-2000:]}"
            )
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                return proc
        except (requests.ConnectionError, requests.Timeout):
            pass
        time.sleep(0.3)

    # Timeout — kill the process
    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        proc.wait(timeout=5)
    stderr = proc.stderr.read().decode(errors="replace")
    raise RuntimeError(
        f"MCP server did not become healthy within {health_timeout}s.\n"
        f"Stderr: {stderr[-2000:]}"
    )


def stop_mcp_server(proc):
    """Gracefully stop the MCP server process."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


# -- OpenAI-compatible tool schemas ------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_factions",
            "description": "List all available Warhammer 40k 11th edition factions with unit/detachment counts.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_units",
            "description": "List units for a faction with points costs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "Optional search filter"},
                    "faction": {"type": "string", "description": "Faction slug, default: grey-knights"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_unit",
            "description": "Get full unit profile: stats, weapons, abilities, keywords.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unit name"},
                    "faction": {"type": "string", "description": "Faction slug"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_dpp",
            "description": "Compute expected damage per point for a weapon vs a target. MANDATORY for damage calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attacks": {"type": "number"},
                    "bs": {"type": "number", "description": "Ballistic Skill as number (e.g. 3 for 3+)"},
                    "strength": {"type": "number"},
                    "ap": {"type": "number"},
                    "damage": {"type": "number"},
                    "target_toughness": {"type": "number"},
                    "target_save": {"type": "number"},
                    "weapon_name": {"type": "string"},
                    "abilities": {"type": "string", "description": "Comma-separated weapon abilities"},
                    "target_invuln": {"type": "number"},
                    "unit_points": {"type": "number"},
                },
                "required": ["attacks", "bs", "strength", "ap", "damage", "target_toughness", "target_save"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_surv",
            "description": "Compute unit survivability: effective wounds at AP0/AP2/AP4, points-per-effective-wound.",
            "parameters": {
                "type": "object",
                "properties": {
                    "toughness": {"type": "number"},
                    "wounds_per_model": {"type": "number"},
                    "save": {"type": "number"},
                    "models": {"type": "number"},
                    "unit_points": {"type": "number"},
                    "invuln": {"type": "number"},
                    "fnp": {"type": "number"},
                },
                "required": ["toughness", "wounds_per_model", "save", "models", "unit_points"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_units",
            "description": "Three-vector (DPS/SURV/MOB) ranking for all units in a faction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "faction": {"type": "string", "default": "grey-knights"},
                    "target": {"type": "string", "description": "Target profile: GEQ, MEQ, TEQ.", "default": "MEQ"},
                    "mission": {"type": "string", "description": "Mission type"},
                    "detachment": {"type": "string"},
                    "top_n": {"type": "number", "default": 10},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_detachment",
            "description": "Get detachment engine-modeled modifiers (DPP/SURV/MOB buffs).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Detachment name"},
                    "faction": {"type": "string", "default": "grey-knights"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ability",
            "description": "Look up a weapon ability by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_core_rules",
            "description": "Get 11e core rules overview: cover, phases, weapon abilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "enum": ["abilities", "stratagems", "phases", "cover", "all"]},
                },
                "required": ["section"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stratagem",
            "description": "Look up a core 11e stratagem by name.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compute_mob",
            "description": "Compute unit mobility: movement tier, Deep Strike, OC, fly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movement": {"type": "number"},
                    "oc": {"type": "number"},
                    "fly": {"type": "boolean"},
                    "deep_strike": {"type": "boolean"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["movement", "oc"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_findings",
            "description": "Retrieve pre-computed DPP/SURV/MOB findings for a faction. Use for unit comparisons, army list analysis, cross-faction evaluation. Baseline values with known assumptions — LLM layers detachment combos and strategy on top.",
            "parameters": {
                "type": "object",
                "properties": {
                    "faction": {"type": "string", "description": "Faction slug (e.g. grey-knights, chaos-knights)"},
                    "mission": {"type": "string", "description": "Mission filter: Take and Hold, Purge the Foe, Reconnaissance, Priority Assets, Disruption"},
                    "top_n": {"type": "number", "description": "Number of top units per mission. Default: 10. Use 0 for all."},
                },
                "required": ["faction"],
            },
        },
    },
]


def get_tool_schemas():
    """Return OpenAI-format tool schemas."""
    return TOOLS


def get_tools_description():
    """Human-readable tool list for system prompt."""
    lines = []
    for t in TOOLS:
        fn = t["function"]
        params = fn["parameters"].get("properties", {})
        param_str = ", ".join(k for k in params)
        lines.append(f"- {fn['name']}({param_str}): {fn['description']}")
    return "\n".join(lines)


# -- Self-test ---------------------------------------------------------------

def _self_test():
    """Integration test: start server, connect, call tools, print results."""
    server_proc = None
    try:
        print("=" * 60)
        print("MCP StreamableHTTP Client - Self Test")
        print("=" * 60)

        # 1. Start server
        print("\n[1/6] Starting MCP server...")
        server_proc = start_mcp_server(port=3456)
        print("      Server is healthy.")

        # 2. Connect (initialize handshake)
        print("\n[2/6] Initializing MCP session...")
        client = MCPClient()
        caps = client.connect()
        print(f"      Session ID: {client.session_id}")
        print(f"      Server: {caps.get('serverInfo', {}).get('name', '?')}")
        print(f"      Capabilities: {list(caps.get('capabilities', {}).keys())}")

        # 3. List tools
        print("\n[3/6] Listing tools...")
        tools = client.list_tools()
        print(f"      {len(tools)} tools available:")
        for t in tools:
            print(f"        - {t['name']}: {t.get('description', '')[:60]}")

        # 4. list_factions
        print("\n[4/6] Calling list_factions...")
        result = client.call_tool("list_factions", {})
        print(f"      {result[:500]}")

        # 5. get_unit("Terminator", "grey-knights")
        print("\n[5/6] Calling get_unit('Terminator', 'grey-knights')...")
        result = client.call_tool("get_unit", {
            "name": "Terminator",
            "faction": "grey-knights",
        })
        print(f"      {result[:500]}")

        # 6. compute_dpp with real weapon stats (Psycannon vs MEQ)
        print("\n[6/6] Calling compute_dpp (Psycannon vs MEQ)...")
        result = client.call_tool("compute_dpp", {
            "weapon_name": "Psycannon",
            "attacks": 2,
            "bs": 3,
            "strength": 8,
            "ap": -2,
            "damage": 2,
            "target_toughness": 4,
            "target_save": 3,
            "target_invuln": 4,
            "unit_points": 55,
        })
        print(f"      {result[:800]}")

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)

    except Exception as e:
        print(f"\nFAILED: {e}")
        traceback.print_exc()
    finally:
        if server_proc:
            print("\nShutting down MCP server...")
            stop_mcp_server(server_proc)


if __name__ == "__main__":
    _self_test()
