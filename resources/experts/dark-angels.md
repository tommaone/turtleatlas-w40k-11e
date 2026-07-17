# Dark Angels — 11th Edition Expert

Dark Angels are a Space Marine Chapter with two elite wings: **Deathwing** (Terminator-armoured) and **Ravenwing** (fast bikes/vehicles). They specialise in deep strike, durability, and surgical strikes.

---

## Critical 11e Rules for DA

### Inner Circle: -1 Damage (Deathwing)
Deathwing Knights and select units have **-1 Damage** ability:
- D2 weapons → D1, D3 → D2, etc. (minimum 1)
- Massive survivability boost against plasma, melta, lascannon
- **Engine models this via `damage_reduction: 1` in config**

### Deathwing: Ignore BS/WS Modifiers
Deathwing units ignore all BS/WS modifiers:
- Cover penalty (-1 BS) → ignored
- Plunging Fire (-1 BS) → ignored
- Heavy weapon penalty → ignored
- `hit_mode: "normal"` always for Deathwing units

### Ravenwing: Fast + Fly
Ravenwing units have FLY keyword:
- Can advance and shoot without penalty
- Can Fall Back and shoot
- High mobility for objective grabbing

---

## Unit Profiles

### Characters

| Unit | M | T | Sv | W | OC | InSv | Pts | Notes |
|------|---|---|----|---|----|----|-----|-------|
| Azrael | 6" | 4 | 2+ | 6 | 1 | 4+ | 135 | Deathwing, gives 4+ invuln aura |
| Asmodai | 6" | 4 | 3+ | 4 | 1 | 4+ | 70 | Deathwing, melee character |
| Belial | 5" | 5 | 2+ | 6 | 1 | 4+ | 100 | Deathwing, Terminator armour |
| Ezekiel | 6" | 4 | 2+ | 4 | 1 | 4+ | 75 | Deathwing, psychic |
| Lazarus | 6" | 4 | 3+ | 5 | 1 | 4+ | 80 | Deathwing, anti-psyker |
| Sammael | 12" | 5 | 3+ | 7 | 2 | 4+ | 105 | Ravenwing, Jetbike |
| Lion El'Jonson | 8" | 9 | 2+ | 10 | 4 | 3+ | 285 | Primarch, supreme commander |

### Deathwing (Elites)

| Unit | M | T | Sv | W | OC | InSv | Pts | Models | Notes |
|------|---|---|----|---|----|----|-----|--------|-------|
| Deathwing Knights | 5" | 5 | 2+ | 3 | 1 | 4+ | 240 | 5 | -1D, melee only, premium |
| Deathwing Terminator Squad | 5" | 5 | 2+ | 3 | 1 | 5+ | 165 | 5 | Balanced ranged+melee |
| Deathwing Command Squad | 5" | 5 | 2+ | 5 | 1 | 4+ | 110 | 5 | -1D, elite support |
| Deathwing Strikemaster | 5" | 5 | 2+ | 5 | 1 | 4+ | 85 | 1 | Deathwing leader |
| Inner Circle Companions | 6" | 4 | 3+ | 3 | 1 | — | 80 | 3 | Deathwing, melee |

### Ravenwing (Fast Attack)

| Unit | M | T | Sv | W | OC | InSv | Pts | Models | Notes |
|------|---|---|----|---|----|----|-----|--------|-------|
| Ravenwing Black Knights | 12" | 5 | 3+ | 3 | 1 | 4+ | 115 | 3 | Fly, bikes |
| Ravenwing Command Squad | 12" | 5 | 3+ | 4 | 1 | 4+ | 115 | 3 | Fly, bikes |
| Ravenwing Talonmaster | 14" | 5 | 3+ | 7 | 2 | 4+ | 105 | 1 | Fly, Land Speeder |

### Battleline

| Unit | M | T | Sv | W | OC | Pts | Notes |
|------|---|---|----|---|----|-----|-------|
| Intercessor Squad | 6" | 4 | 3+ | 2 | 2 | 80 | Core battleline |
| Assault Intercessor Squad | 6" | 4 | 3+ | 2 | 2 | 80 | Melee battleline |
| Heavy Intercessor Squad | 6" | 6 | 3+ | 3 | 3 | 110 | Heavy battleline |

### Heavy Support

| Unit | M | T | Sv | W | OC | Pts | Notes |
|------|---|---|----|---|----|-----|-------|
| Gladiator Lancer | 10" | 10 | 3+ | 12 | 3 | 160 | Anti-tank |
| Redemptor Dreadnought | 8" | 10 | 2+ | 12 | 4 | 195 | Versatile dread |
| Land Raider | 10" | 12 | 2+ | 16 | 5 | 240 | Transport + fire power |

---

## Squad Limits & Gotchas

### Deathwing Knights
- **5 models only** (no 10-model squad)
- **Melee only** — no ranged weapons
- **-1 Damage** is key — makes them incredibly durable
- Power weapons have strike/sweep profiles
- **Deep Strike** — deploy anywhere turn 2

### Deathwing Terminator Squad
- 5 or 10 models
- Mixed ranged+melee loadout
- Storm bolter + heavy weapon options
- Less durable than Knights (no -1D, 5+ invuln)

### Ravenwing Black Knights
- 3-6 models
- All Fly keyword
- Plasma talons (ranged) + melee weapons
- Fast but fragile compared to Deathwing

### Inner Circle Companions
- 3-6 models
- Deathwing keyword
- Melee focused
- No invulnerable save — fragile for Deathwing

---

## Competitive Builds

### Deathwing Anchor (2000pts)
- Deathwing Knights (240) — objective anchor
- Deathwing Terminator Squad (165) — ranged support
- Azrael (135) — 4+ invuln aura
- Belial (100) — Deathwing leader
- Total: ~640pts of Deathwing

### Ravenwing Pressure (2000pts)
- Sammael (105) — mobile HQ
- Ravenwing Black Knights (115) — fast objective grabbers
- Ravenwing Talonmaster (105) — fire support
- Land Speeders (95) — cheap screening
- Total: ~420pts of Ravenwing

### Balanced DA (2000pts)
- Azrael (135) — HQ
- Deathwing Knights (240) — anchor
- Intercessor Squad (80) — battleline
- Hellblaster Squad (125) — ranged damage
- Gladiator Lancer (160) — anti-tank
- Total: ~740pts core

---

## Mission-Specific Advice

### Take and Hold
- **Best units**: Cheap DS units (Intercessors, Infiltrators)
- **Avoid**: Expensive Deathwing (risky commitment)
- **Strategy**: Spread disposable units, keep 1 alive

### Purge the Foe
- **Best units**: Deathwing Knights (-1D, hard to kill)
- **Avoid**: Many cheap units (more targets for opponent)
- **Strategy**: Elite army, few durable units

### Reconnaissance
- **Best units**: Ravenwing (fast, Fly)
- **Avoid**: Slow Deathwing
- **Strategy**: Mobility wins

---

## Key Detachment Modifiers

### Inner Circle Task Force
- Deathwing units get +1 to wound in melee
- Significant buff for melee-focused builds

### Ravenwing Strike Force
- Ravenwing units can advance and charge
- Massive mobility boost

### Gladius Task Force
- Generic SM detachment
- Works for any DA army composition

---

## Common Mistakes

1. **Taking too many Deathwing** — expensive, fewer objectives
2. **Ignoring Ravenwing** — fast units win missions
3. **Forgetting Deep Strike** — DS is your key advantage
4. **Not using Azrael's aura** — 4+ invuln is huge
5. **Melee-only DWK without support** — they need screening

---

*Last updated: 2026-07-17*
