# Roadmap — turtleatlas-w40k-11e

## Done ✅

### Engine Core
- DPP engine with 3-vector ranking (DPP × SURV × MOB)
- Weapon loader with faction overlays (Psychic/Torrent keywords)
- Invuln save support (armour vs invuln priority, AP floor)
- BSData parser with sharedProfiles resolution (entryLinks)
- Merge script (BSData + MFM) with `--faction` flag
- Detachment modifier system (WeaponModifier, DetachmentModifier)
- Meta/mission profile weighting

### Factions
- **Grey Knights** — full setup, 9 detachments, 5 dispositions ranked
- **Chaos Knights** — full setup, 8 detachments
- **Chaos Daemons** — full setup, 9 detachments
- **Space Marines** — full setup, 22 detachments (10 with modifiers), expert file, findings
- **Dark Angels** — merged data, config files, 8 DA-specific detachment modifiers

### Tests
- 66 tests passing (DPP, Psychic overlay, invuln, detachment modifiers, SM detachments)

### Documentation
- GK expert file (490 lines), CK expert, Daemons expert, SM expert
- GK mission analysis + power armour efficiency findings
- SM mission analysis findings
- Guardrails (11e rules reference)
- Non-DPP value framework

---

## In Progress 🔄

### Dark Angels (DA)
- [x] Merged data (160 units, 23 detachments)
- [x] Config files (SM base + 4 DA-specific units)
- [x] 8 DA-specific detachment modifiers
- [ ] **DA ranking only shows 4 units** — SM base units not ranking (resolve_loadout issue)
- [ ] **Deathwing Knights weapons missing** from BSData — need manual weapon entry
- [ ] **Inner Circle -1 Damage** ability — not modeled in engine (needs `damage_reduction` modifier)
- [ ] DA expert file
- [ ] DA findings

---

## Backlog 📋

### Engine Improvements
- [ ] **Damage reduction modifier** — for Inner Circle (DWK), similar abilities
- [ ] **FNP (Feel No Pain) modifier** — currently only in SURV, not in DPP
- [ ] **Transport support** — model unit delivery (Rhino, Impulsor, Land Raider)
- [ ] **Multi-unit synergies** — character auras, buff stacking
- [ ] **Variance bands** — instead of average dice, show ±1σ range
- [ ] **Points efficiency frontier** — Pareto front of DPP vs SURV vs cost

### Factions
- [ ] **Adeptus Custodes** — BSData available
- [ ] **Aeldari** — BSData available
- [ ] **Orks** — BSData available
- [ ] **Tyranids** — BSData available
- [ ] **T'au Empire** — BSData available
- [ ] **Necrons** — BSData available
- [ ] **Leagues of Votann** — BSData available
- [ ] **Genestealer Cults** — BSData available
- [ ] **Death Guard** — BSData available
- [ ] **Thousand Sons** — BSData available
- [ ] **World Eaters** — BSData available
- [ ] **Emperor's Children** — BSData available
- [ ] **Chaos Space Marines** — BSData available

### Findings & Analysis
- [ ] DA mission analysis (after DA ranking fixed)
- [ ] Cross-faction comparison (GK vs SM vs DA)
- [ ] Meta analysis — which factions dominate which dispositions
- [ ] Points efficiency ranking across all factions

### Infrastructure
- [ ] MCP server integration for live queries
- [ ] CI/CD pipeline (automated tests on push)
- [ ] Web dashboard for rankings (nice-to-have)

---

## Known Issues 🐛

1. **DA ranking incomplete** — SM base units not showing in rankings despite being in config. Likely a resolve_loadout path issue.
2. **Deathwing Knights weapons** — BSData parser didn't extract weapon profiles. Need to add manually to config.
3. **Inner Circle -1 Damage** — engine has no damage reduction modifier. DWK SURV is underestimated.
4. **`ranged_a` type** — config expects float but can get dict `{}`. Need validation.

---

*Last updated: 2026-07-12*
