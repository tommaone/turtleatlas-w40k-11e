# 🐢 W40k Army Architect — Conversational Layer

## ✅ Done
- [x] Big Pickle via OpenCode — free, synchronous, zero cost
- [x] MCP server analysis (12 tools, 30 factions, engine ready)
- [x] Architecture designed (minimal, no overengineering)
- [x] MCP StreamableHTTP client (mcp_client.py) — full protocol, SSE parsing
- [x] Agent loop (agent.py) — Big Pickle + TOOL_CALL format + MCP tools
- [x] get_findings tool in MCP server — pre-computed pipeline output
- [x] Demo: rank_units call through full chain works
- [x] Documentation (README.md)

## 🔜 Next — v2

### Phase 3: Guardrail
- [ ] `guardrail.py` — parse output, extract numbers
- [ ] Compare with MCP response in history
- [ ] Flag [Unverified Stat] for uncited numbers

### Phase 4: Deployment
- [ ] Hugging Face Spaces (Docker/FastAPI with MCP SDK)
- [ ] Containerize MCP server + engine + conversational layer

### Phase 5: Findings Integration
- [ ] get_findings in agent.py tool list (done)
- [ ] NewRecruit army list import → findings lookup
- [ ] Cross-faction comparisons

## 💡 Nice to Have (v2)
- [ ] LangGraph wrapper (if it makes sense)
- [ ] Army list builder (built on `rank_units`)
- [ ] Export to Battlescribe format
- [ ] Web UI (Gradio/Streamlit)

---

## Structure
```
turtleatlas-w40k-11e/
├── mcp-server/            ✅ 12 MCP tools (incl. get_findings)
├── engine/                ✅ DPP, SURV, MOB, ranking
├── conversational/        ✅ conversational layer
│   ├── mcp_client.py      ✅ MCP StreamableHTTP client
│   ├── agent.py           ✅ Big Pickle + tool calling loop
│   ├── demo_call.py       ✅ Big Pickle via OpenCode
│   ├── README.md          ✅ documentation
│   └── ROADMAP.md         ✅ roadmap
├── data/                  ✅ 30 factions
├── findings/              ✅ 5 factions with pre-computed findings
├── adapter/               ✅ data pipeline
└── tests/                 ✅ 46 tests
```

## Tech Stack
- **LLM**: Big Pickle (free, via OpenCode local server)
- **MCP**: turtleatlas-w40k-11e (12 tools, Python engine)
- **Observability**: LangFuse
- **Framework**: none (conversation loop is enough)
