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
- **Damage reduction** — flat reduction (e.g. DWK -1D), applied in `_shots_to_kill`
- **Multi-model melee damage** — squads sum all melee profiles, characters pick best
- **DS tier upgrade** — slow+DS → fast, standard+DS → very_fast
- **Fake FNP removal** — infantry no longer get fake FNP 6+
- **Take and Hold weights** — DPP=0% SURV=60% MOB=40% (no melee penalty)

### Factions
- **Grey Knights** — full setup, 9 detachments, 5 dispositions ranked
- **Chaos Knights** — full setup, 8 detachments
- **Chaos Daemons** — full setup, 9 detachments
- **Space Marines** — full setup, 22 detachments (10 with modifiers), expert file, findings
  - 84 units ranked (auto-generated configs)
- **Dark Angels** — 103 units ranked, all datasheets present
  - 34 squads, 38 vehicles, 31 characters
  - DWK damage_reduction=1 configured
  - Lion El'Jonson weapon fix (Fealty=melee, Arma Luminis=ranged)

### Tests
- 81 tests passing (DPP, Psychic overlay, invuln, detachment modifiers, SM detachments)
- 9 pre-existing GK/CK/Daemons validation failures (not our changes)

### Documentation
- GK/CK/Daemons/SM expert files
- GK + SM mission analysis findings
- Guardrails (11e rules reference)
- Non-DPP value framework

### Findings
- DA Take & Hold tri-vector HTML (findings/dark-angels/)

---

## In Progress 🔄

### Dark Angels
- [ ] **DA expert file** — squad limits, Deathwing/Ravenwing specifics
- [ ] **DA findings** — mission analysis, competitive builds

### Duplicate MFM entries
- Many units have 2 MFM price entries (different loadouts), only first used
- Need loadout-dependent pricing support

---

## Backlog 📋

### Engine Improvements
- [ ] **Transport support** — model unit delivery (Rhino, Impulsor, Land Raider)
- [ ] **Multi-unit synergies** — character auras, buff stacking
- [ ] **Unit role tags** — objective holder, support, damage dealer (role-based scoring)
- [ ] **Variance bands** — instead of average dice, show ±1σ range
- [ ] **Points efficiency frontier** — Pareto front of DPP vs SURV vs cost

### Factions (priority order)
- [ ] **Adeptus Custodes** — BSData available
- [ ] **Aeldari** — BSData available
- [ ] **Necrons** — BSData available
- [ ] **Tyranids** — BSData available
- [ ] **Orks** — BSData available
- [ ] **T'au Empire** — BSData available
- [ ] **Leagues of Votann** — BSData available
- [ ] **Death Guard** — BSData available
- [ ] **Thousand Sons** — BSData available
- [ ] **World Eaters** — BSData available
- [ ] **Emperor's Children** — BSData available
- [ ] **Chaos Space Marines** — BSData available
- [ ] **Genestealer Cults** — BSData available

### Findings & Analysis
- [ ] Cross-faction comparison (GK vs SM vs DA)
- [ ] Meta analysis — which factions dominate which dispositions
- [ ] Points efficiency ranking across all factions

### Infrastructure
- [ ] MCP server integration for live queries
- [ ] CI/CD pipeline (automated tests on push)
- [ ] Web dashboard for rankings (nice-to-have)

---

## Known Issues 🐛

1. **`ranged_a` type** — config expects float but can get dict `{}`. Need validation.
2. **Weapon name normalization** — mixed apostrophes (U+0027 vs U+2019) between config and catalog keys

---

*Last updated: 2026-07-17*
