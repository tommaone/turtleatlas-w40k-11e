# 🐢 Conversational Layer

W40k Army Architect — conversational agent backed by the turtleatlas-w40k-11e MCP engine.

## Architecture

```
User → agent.py → Big Pickle (OpenCode) → TOOL_CALL → mcp_client.py → MCP Server → Python engine
                                                ↓
                                          Final answer ← LLM interpretation
```

**Key principle:** LLM never computes. It interprets MCP engine output. All numbers come from the engine.

## Quick Start

```bash
# From turtleatlas-w40k-11e root:
cd conversational

# Run the agent (starts MCP server automatically)
python3 agent.py

# Or test MCP client standalone
python3 mcp_client.py
```

**Prerequisites:**
- Node.js (for MCP server)
- OpenCode running on port 32768 (for Big Pickle)
- Python 3.10+ with `requests` library

## Files

| File | Purpose |
|------|---------|
| `mcp_client.py` | MCP StreamableHTTP client — handles protocol, SSE parsing, session management |
| `agent.py` | Agent loop — Big Pickle + tool calling + MCP integration |
| `demo_call.py` | Minimal Big Pickle demo (OpenCode API) |
| `ROADMAP.md` | Implementation roadmap |

## MCP Tools Available

| Tool | Description | Example Query |
|------|-------------|---------------|
| `list_factions` | List all 30 factions | "What factions are available?" |
| `list_units` | List units with points | "What units does Grey Knights have?" |
| `get_unit` | Full unit profile | "What weapons does a Terminator have?" |
| `compute_dpp` | Damage per point | "What's the DPP of a Psycannon vs MEQ?" |
| `compute_surv` | Survivability metrics | "How survivable are Terminators?" |
| `compute_mob` | Mobility tier | "How fast are Interceptors?" |
| `rank_units` | Three-vector ranking | "Rank Grey Knights units" |
| `get_detachment` | Detachment modifiers | "What buffs does Warpbane Task Force give?" |
| `get_ability` | Weapon ability lookup | "What does Sustained Hits do?" |
| `get_core_rules` | Core rules overview | "How does cover work in 11e?" |
| `get_stratagem` | Stratagem lookup | "What does Command Reroll do?" |
| `get_findings` | Pre-computed findings | "Compare Purifiers vs Strikes" |

## Tool Calling Flow

1. User asks question
2. Big Pickle decides which tool to call
3. Outputs `TOOL_CALL: {"name": "tool_name", "args": {...}}`
4. `mcp_client.py` executes via MCP protocol
5. Result fed back to Big Pickle
6. Big Pickle interprets and responds

## Data Flow

```
MFM (static) + BSData (static)
    ↓ adapter (merge)
Merged JSON (30 factions)
    ↓ engine (compute)
DPP / SURV / MOB / Rankings
    ↓ MCP server (expose)
12 tools via StreamableHTTP
    ↓ mcp_client.py (consume)
Agent loop (Big Pickle)
    ↓
User response
```

## Assumptions (every response)

All engine output carries these assumptions:
- Target profile: MEQ (T4, SV3+) unless noted
- No cover on saves (11e cover is BS-only)
- No detachment buffs, stratagems, or command rerolls
- Average dice (no variance band)
- Pricing: Munitorum Field Manual 1st tier

## Finding Factions (get_findings)

Pre-computed findings available for:
- chaos-daemons
- chaos-knights
- dark-angels
- grey-knights
- space-marines

Other factions: use `rank_units` for live computation.
