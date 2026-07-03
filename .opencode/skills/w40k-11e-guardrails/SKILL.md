# w40k-11e-guardrails

Guardrails for LLM agents using turtleatlas-w40k-11e MCP server.
Load this skill BEFORE calling MCP tools.

---

## MCP Tools

| Tool | When |
|------|------|
| `get_core_rules` | Verify rules (Psychic, Cover, abilities) |
| `get_ability` | Ability description |
| `get_detachment` | Detachment analysis |
| `get_unit` | Unit profile |
| `list_units` | Browse units |
| `compute_dpp` | Damage per point |
| `get_stratagem` | Strategy analysis |

---

## 11e Rules — Apply These

### PSYCHIC [24.29]
Psychic weapons ignore ALL BS/WS modifiers and hit roll modifiers.
→ Cover (worsen BS by 1) does NOT affect Psychic.
→ `hit_mode: "normal"` always for Psychic weapons.

### Cover in 11e
Cover = worsen BS by 1 (not save modifier).
Plunging Fire = +1 BS.
Psychic GK weapons ignore all of this.

### Ability effects
| Ability | Effect |
|---------|--------|
| **Torrent** | Auto-hit, no BS needed |
| **Sustained Hits 1** | +1 hit on 6+ |
| **Devastating Wounds** | Mortal wounds on 6+ to wound |
| **Twin-Linked** | Reroll wounds |
| **Anti-Infantry X+** | Wound on X+ vs INFANTRY |
| **Ignores Cover** | Negates cover penalty |

---

## Squad Weapon Limits — #1 Mistake

Each squad has FIXED special weapon count and fixed melee loadout per model type.
NEVER assume all models take the best weapon. See `resources/experts/grey-knights.md` for full GK details.

| Squad | Pts | Models | Specials | Melee | Storm Bolters |
|-------|-----|--------|----------|-------|---------------|
| Purifier | 130 | 5 | max 2× Inc/Psil/Psyc | 3× NFW (A3), 2× CCW (A3) | 3× SB |
| Purgation | 110 | 4 | 1× Inc + 1× Psil + 1× Psyc | 1× NFW (A3), 3× CCW (A3) | 1× SB |
| Strike | 120 | 5 | max 1× special | 4× NFW (A3), 1× CCW (A3) | 4× SB |
| Interceptor | 125 | 5 | max 1× special | 4× NFW (A3), 1× CCW (A3) | 4× SB |
| Terminator | 140 | 5 | max 2× special | 5× NFW (**A4**) | 3× SB |
| Paladin | 170 | 5 | max 2× special | 5× NFW (**A4**) | 3× SB (**BS 2+**) |

**Key rules:**
- A model taking a special weapon loses its Storm Bolter
- Terminator/Paladin NFW = A=4; power armour NFW = A=3
- Power armour special weapon model loses NFW → gets CCW (A=3, S=4, AP=0, D=1)
- Purifying Flame is **additional** (not a replacement) — every Purifier has it
- Paladins have **BS 2+** (all others except characters are BS 3+)
- Paladins **do** have the `Terminator` keyword

---

## DPP for Squads — Correct Method

1. Use actual loadout (table above)
2. Multiply attacks × model count per weapon type
3. `unit_points` = full squad cost
4. Sum damage from all weapons

---

## Common Mistakes

- ❌ "Every model has special weapon" — NO, squad has limits
- ❌ "Cover modifies saves in 11e" — NO, modifies BS
- ❌ "Psychic cares about cover" — NO, ignores it
- ❌ "DPP with 1 model, unit_points for squad" — multiply attacks × models
