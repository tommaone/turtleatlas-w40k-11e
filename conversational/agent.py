#!/usr/bin/env python3
"""W40k Army Architect — Big Pickle + MCP tools.

Big Pickle has 200k context. Give it the tool schemas, let it call them.
"""

import json
import re
import requests

from mcp_client import MCPClient, start_mcp_server, stop_mcp_server, get_tools_description

OC = "http://127.0.0.1:55187"


def send_message(sid: str, text: str) -> str:
    """Send a message to an OpenCode session, return response text."""
    try:
        r = requests.post(
            f"{OC}/session/{sid}/message",
            json={"parts": [{"type": "text", "text": text}]},
            timeout=180,
        )
        data = r.json()
        for part in data.get("parts", []):
            if part.get("type") == "text":
                return part["text"]
    except requests.exceptions.Timeout:
        print("  ⚠️  OpenCode timed out")
    except Exception as e:
        print(f"  ⚠️  OpenCode error: {e}")
    return ""


def parse_tool_call(text: str) -> dict | None:
    """Extract TOOL_CALL: {...} from LLM response (handles nested JSON)."""
    idx = text.find("TOOL_CALL")
    if idx == -1:
        return None
    start = text.find("{", idx)
    if start == -1:
        return None
    # Count braces to find matching close
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def build_system_prompt(tools_description: str) -> str:
    """Build the system prompt with tool schemas."""
    return f"""Reply with EXACTLY one line starting with TOOL_CALL: followed by JSON.
Example: TOOL_CALL: {{"name": "get_findings", "args": {{"faction": "grey-knights"}}}}

Available tools:
{tools_description}

CRITICAL 11th EDITION RULES:
- NO psychic phase exists in 11e. Psychic weapons are regular weapons with PSYCHIC keyword.
- Cover modifies BS (hit roll), NOT saves. Cover = +1 to hit roll for attacker.
- PSYCHIC weapons ignore cover.
- There are no "psychic phases", "denied the witch", or "psychic tests" in 11e.
- If you mention psychic phase, you are quoting 9th edition rules - STOP.

No explanation. Just TOOL_CALL JSON line."""


def chat(user_input: str, client: MCPClient, system_prompt: str) -> str:
    """Single question with tool calling loop."""
    sid = requests.post(f"{OC}/api/session", json={}).json()["data"]["id"]

    # Send system prompt + user question together
    full_prompt = f"{system_prompt}\n\nQuestion: {user_input}"
    response = send_message(sid, full_prompt)

    # Tool calling loop (max 5 iterations)
    for i in range(5):
        tool_call = parse_tool_call(response)
        if not tool_call:
            return response

        name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        print(f"  🔧 {name}({json.dumps(args, ensure_ascii=False)[:80]})")

        result = client.call_tool(name, args)
        print(f"  📊 {result[:120]}...")

        # Feed result back - ask Big Pickle to interpret
        interpret_prompt = f"""Data engine returned this. Analyze briefly in 4 tiers:
FACTS (raw data)  USE CASES  CONSTRAINTS  STRATEGY

CRITICAL: This is Warhammer 40k 11th Edition. There is NO psychic phase.
Psychic weapons are just weapons with PSYCHIC keyword. Do NOT mention psychic phase.

Question: {user_input}

Data:
{result[:3000]}

Use tables. Be concise. Do not invent rules."""

        response = send_message(sid, interpret_prompt)

    return response or "[tool loop limit]"


def main():
    print("🐢 W40k Army Architect — POC")
    print("Starting MCP server...")

    server_proc = start_mcp_server()
    client = MCPClient()
    client.connect()

    tools_desc = get_tools_description()
    system_prompt = build_system_prompt(tools_desc)

    print(f"MCP connected ({len(client.list_tools())} tools)\n")
    print("Ask anything about W40k units. Type 'quit' to exit.\n")

    try:
        while True:
            try:
                user = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not user or user.lower() in ("quit", "exit", "q"):
                break

            reply = chat(user, client, system_prompt)
            print(f"\n🤖 {reply}\n")
    finally:
        stop_mcp_server(server_proc)


if __name__ == "__main__":
    main()
