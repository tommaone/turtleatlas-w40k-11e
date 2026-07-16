# turtleatlas-w40k-11e

11th Edition Warhammer 40k structured data + DPP engine + turtleatlas-mcp server.

## IP & Copyright Notice

**This repository contains NO Games Workshop copyrighted rule text or PDFs.**
- `data/merged/*.json` — Community-maintained BSData game data (points, profiles, keywords). Game mechanics data only, no verbatim rule text.
- `data/config/*/` — Our own derived configuration files. Machine-readable modifiers only.
- Engine code — Original work. No GW IP.

**NEVER commit GW copyrighted material:**
- ⛔ No PDFs of rulebooks, faction packs, or indexes
- ⛔ No verbatim rule text (ability descriptions, stratagem text, lore)
- ⛔ No official GW images, logos, or artwork

**Safe to include (game mechanics / community data):**
- ✅ Points values (Munitorum Field Manual data)
- ✅ Unit profiles (M/WS/BS/S/T/W/A/Ld/Sv — game stats)
- ✅ Weapon profiles (range, type, S, AP, D, ability keywords)
- ✅ Keywords
- ✅ Machine-readable modifier data (+1 to hit, Sustained Hits, etc.)
- ✅ Our own analysis, rankings, and derived metrics (DPP, SURV)

This is an unofficial, non-commercial fan project. Warhammer 40,000 is a registered trademark of Games Workshop Limited.

## Project Map — What's Where

| Subfolder | What it is | See |
|-----------|-----------|-----|
| `data/config/` | Detachment modifiers per faction | `data/config/AGENTS.md` |
| `engine/` | DPP engine, ranking, weapon loader | `engine/AGENTS.md` |
| `resources/` | Guardrails, experts, non-DPP value | `resources/AGENTS.md` |
| `adapter/` | BSData / MFM parsers | *code comments* |
| `mcp-server/` | MCP server (points to turtleatlas-mcp) | *see turtleatlas-mcp* |
| `tests/` | Engine tests | *code comments* |
| `docs/` | Documentation | *README.md* |

Each subfolder has its own `AGENTS.md` with detailed instructions. Agents working in that directory will automatically pick up the relevant rules.

## Quick Start

```bash
# Start MCP server
node mcp-server/index.js --port 3456
```

## MCP Bootstrap Protocol

This project uses **turtleatlas-mcp** as its MCP knowledge server. Every agent MUST follow the MCP Bootstrap Protocol before answering domain questions:

1. Initialize session
2. `list_experts` + `get_expert("<relevant faction>")`
3. `get_sql_rules`
4. Only then answer

See `mcp-server/AGENTS.md` (or turtleatlas-mcp root) for the full protocol.

## Hard Rules (apply project-wide)

- **No fabricated numbers** — use the engine for ALL numerical output. Never compute DPP/SURV yourself.
- **No fabricated detachment rules** — every modifier needs a verified `_source`. See `data/config/AGENTS.md`.
- **Actions are bad in 11e** — Purge the Foe and Take and Hold are the best dispositions for most factions.
