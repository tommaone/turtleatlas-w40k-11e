# Findings Comparison — Old vs New

## Summary

| Aspect | Old Findings | New Findings |
|--------|--------------|--------------|
| **Scope** | Detachment-specific | Generic mission rankings |
| **Modifiers** | Applied (Warpbane, Infernal Lance, etc.) | Not applied |
| **Scoring** | DPP-focused | Tri-vector (DPP + SURV + MOB) |
| **Focus** | Which detachment for which mission | Which units for which mission |

---

## Grey Knights

### Old Findings (Detachment-Specific)

| Mission | Best Detachment | Best Unit | DPP |
|---------|-----------------|-----------|-----|
| Purge the Foe | Warpbane Task Force | Nemesis Dreadknight | 0.1690 (+24.4%) |
| Take and Hold | Hallowed Conclave | — | — |
| Priority Assets | Immaterial Interdiction | — | — |
| Disruption | Fires of Purgation | — | — |
| Reconnaissance | Augurium Task Force | — | — |

### New Findings (Mission Weights)

| Mission | Best Unit | Score | DPP |
|---------|-----------|-------|-----|
| Take and Hold | Stormraven Gunship | 83.0 | 0.0584 |
| Purge the Foe | Nemesis Dreadknight | 93.2 | 0.1218 |
| Reconnaissance | Nemesis Dreadknight | 76.3 | 0.1218 |
| Priority Assets | Nemesis Dreadknight | 88.2 | 0.1218 |
| Disruption | Nemesis Dreadknight | 84.1 | 0.1218 |

### Key Differences

1. **Nemesis Dreadknight dominates** — top in 4/5 missions (new findings)
2. **Stormraven Gunship** — #1 in Take and Hold (new) — wasn't in old findings
3. **DPP values match** — 0.1218 for NDK (consistent)
4. **Old findings had detachment bonuses** — +24.4% for Warpbane (not in new)

---

## Chaos Knights

### Old Findings (Detachment-Specific)

| Mission | Best Detachment | Best Unit | DPP |
|---------|-----------------|-----------|-----|
| Purge the Foe | Infernal Lance | Knight Tyrant | 0.1690 (+24.4%) |
| Take and Hold | Iconoclast Fiefdom | — | — |
| Priority Assets | Lords of Dread | — | — |
| Disruption | Helhunt Lance | — | — |
| Reconnaissance | Houndpack Lance | — | — |

### New Findings (Mission Weights)

| Mission | Best Unit | Score | DPP |
|---------|-----------|-------|-----|
| Take and Hold | Chaos Cerastus Knight Lancer | 73.2 | 0.0665 |
| Purge the Foe | Knight Tyrant | 86.7 | 0.1358 |
| Reconnaissance | — | — | — |
| Priority Assets | — | — | — |
| Disruption | — | — | — |

### Key Differences

1. **Knight Tyrant** — #1 in Purge the Foe (both old and new)
2. **Chaos Cerastus Knight Lancer** — #1 in Take and Hold (new) — expensive but mobile
3. **DPP values match** — 0.1358 for Tyrant (consistent)
4. **Old findings had detachment bonuses** — +24.4% for Infernal Lance (not in new)

---

## Chaos Daemons

### New Findings (Mission Weights)

| Mission | Best Unit | Score | DPP |
|---------|-----------|-------|-----|
| Take and Hold | — | — | — |
| Purge the Foe | — | — | — |
| Reconnaissance | — | — | — |
| Priority Assets | — | — | — |
| Disruption | — | — | — |

*Note: Daemons have limited data in merged JSON*

---

## Space Marines

### New Findings (Mission Weights)

| Mission | Best Unit | Score | DPP |
|---------|-----------|-------|-----|
| Take and Hold | — | — | — |
| Purge the Foe | — | — | — |
| Reconnaissance | — | — | — |
| Priority Assets | — | — | — |
| Disruption | — | — | — |

*Note: SM has 84 units ranked*

---

## Recommendations

### For Players
- **Use old findings** when you know your detachment — they have detachment-specific bonuses
- **Use new findings** when you want generic unit rankings — tri-vector scoring

### For Engine
- **Add detachment modifiers to new findings** — combine mission weights with detachment bonuses
- **Add disposition constraints** — only show units valid for the mission

### For Future
- **Cross-faction comparison** — GK vs SM vs DA vs CK
- **Meta analysis** — which factions dominate which missions
- **Points efficiency** — cost vs performance analysis

---

*Last updated: 2026-07-17*
