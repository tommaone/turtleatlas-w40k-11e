#!/usr/bin/env python3
"""Big Pickle demo — call via local OpenCode server, zero cost."""

import requests

OC = "http://127.0.0.1:55187"


def chat(text: str) -> str:
    # Create session
    sid = requests.post(f"{OC}/api/session", json={}).json()["data"]["id"]

    # Send message (synchronous — waits for response)
    r = requests.post(
        f"{OC}/session/{sid}/message",
        json={"parts": [{"type": "text", "text": text}]},
        timeout=60,
    )
    data = r.json()
    tokens = data.get("info", {}).get("tokens", {})
    print(f"Tokens: {tokens.get('input', 0)} in / {tokens.get('output', 0)} out")

    for part in data.get("parts", []):
        if part.get("type") == "text":
            return part["text"]
    return "[no response]"


if __name__ == "__main__":
    reply = chat("What is 2+2? Reply with just the number.")
    print(f"Big Pickle: {reply}")
