#!/usr/bin/env python3
"""W40k Army Architect — agent loop using Big Pickle + MCP tools.

POC: simple pattern-matching router + Big Pickle interpretation.
Big Pickle is small — don't ask it to choose tools, we do that.
"""

import json
import re
import requests

from mcp_client import MCPClient, start_mcp_server, stop_mcp_server

OC = "http://127.0.0.1:32768"


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


def route_question(question: str, client: MCPClient) -> str:
    """Pattern-match the question, call appropriate MCP tool, return result."""
    q = question.lower()

    # Pattern: faction list
    if any(w in q for w in ["faction", "factions", "frakci"]):
        return client.call_tool("list_factions", {})

    # Pattern: findings / comparison
    if any(w in q for w in ["finding", "findings", "compare", "comparison", "efficiency", "dpp"]):
        # Extract faction name
        for faction in ["grey-knights", "chaos-knights", "chaos-daemons", "dark-angels", "space-marines"]:
            if faction.replace("-", " ") in q or faction in q:
                mission = None
                for m in ["Take and Hold", "Purge the Foe", "Reconnaissance", "Priority Assets", "Disruption"]:
                    if m.lower() in q:
                        mission = m
                        break
                return client.call_tool("get_findings", {"faction": faction, "mission": mission} if mission else {"faction": faction})
        # No faction found — ask
        return "Which faction? Available with findings: grey-knights, chaos-knights, chaos-daemons, dark-angels, space-marines"

    # Pattern: rank
    if any(w in q for w in ["rank", "ranking", "best", "top"]):
        for faction in ["grey-knights", "chaos-knights", "chaos-daemons", "dark-angels", "space-marines"]:
            if faction.replace("-", " ") in q or faction in q:
                return client.call_tool("rank_units", {"faction": faction, "top_n": 5})
        return "Which faction? (grey-knights, chaos-knights, chaos-daemons, dark-angels, space-marines)"

    # Pattern: unit lookup
    if any(w in q for w in ["unit", "profile", "stats", "weapon"]):
        # Try to extract unit name
        for faction in ["grey-knights", "chaos-knights", "chaos-daemons", "dark-angels", "space-marines"]:
            if faction.replace("-", " ") in q or faction in q:
                return client.call_tool("list_units", {"faction": faction})
        return client.call_tool("list_units", {})

    # Default: list factions
    return client.call_tool("list_factions", {})


def interpret(question: str, tool_result: str) -> str:
    """Ask Big Pickle to interpret the tool result."""
    sid = requests.post(f"{OC}/api/session", json={}).json()["data"]["id"]

    prompt = f"""You are a W40k expert. Here is data from a calculation engine. Analyze it briefly.

Question: {question}

Data:
{tool_result[:2000]}

Give a concise answer. Use tables if comparing units. Mention key numbers."""

    return send_message(sid, prompt)


def main():
    print("🐢 W40k Army Architect — POC")
    print("Starting MCP server...")

    server_proc = start_mcp_server()
    client = MCPClient()
    client.connect()
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

            # Route to MCP tool
            print("  🔧 Querying engine...")
            tool_result = route_question(user, client)
            print(f"  📊 Got data ({len(tool_result)} chars)")

            # Big Pickle interprets
            print("  🧠 Interpreting...")
            answer = interpret(user, tool_result)
            print(f"\n🤖 {answer}\n")
    finally:
        stop_mcp_server(server_proc)


if __name__ == "__main__":
    main()
