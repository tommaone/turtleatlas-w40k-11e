# Grey Knights — 11th Edition Expert

The Grey Knights are the Imperium's daemon-hunting Chapter composed entirely of Psykers.
Army strengths: deep strike pressure, durability (Terminator-armoured units: T5, 2+, 3W),
and flexible roles.

---

## Critical 11e Rule for GK

**Every Grey Knights ranged and melee weapon (except Storm Bolters) has the [PSYCHIC] keyword.**

This means:
- **GK weapons ignore Cover penalty** — Cover worsens BS by 1, but [PSYCHIC] [24.29] lets you ignore any BS/WS modifiers
- `hit_mode: "normal"` always for GK weapons (except Storm Bolters)
- Storm Bolters are NOT Psychic — they take the normal Cover penalty
- Purifying Flame IS Psychic — ignores Cover
- Nemesis force weapons are Psychic — they ignore Cover in melee too (WS modifier immunity)

---

## Unit Profiles (from BSData 10e, may be updated in 11e Faction Pack)

### Characters (leaders)

| Unit | M | T | SV | W | LD | OC | Pts |
|------|---|---|----|---|----|----|-----|
| Brother-Captain | 6" | 4 | 2+ | 5 | 6+ | 1 | 95 |
| Brotherhood Champion | 6" | 4 | 2+ | 5 | 6+ | 1 | 70 |
| Brotherhood Chaplain | 6" | 4 | 3+ | 5 | 6+ | 1 | 65 |
| Brotherhood Librarian | 6" | 4 | 2+ | 5 | 6+ | 1 | 90 |
| Brotherhood Techmarine | 6" | 4 | 2+ | 5 | 6+ | 1 | 70 |
| Castellan Crowe | 6" | 4 | 2+ | 5 | 6+ | 1 | 100 |
| Grand Master | 6" | 4 | 2+ | 6 | 6+ | 1 | 95 |
| Grand Master in Nemesis Dreadknight | 8" | 8 | 2+ | 12 | 6+ | 4 | 200 |
| Grand Master Voldus | 6" | 4 | 2+ | 6 | 6+ | 1 | 140 |

### Battleline

| Unit | M | T | SV | W | LD | OC | Pts |
|------|---|---|----|---|----|----|-----|
| Brotherhood Terminator Squad (×5) | 5" | 5 | 2+ | 3 | 6+ | 1 | 140 |
| Strike Squad (×5) | 6" | 4 | 3+ | 2 | 6+ | 2 | 120 |

### Elites

| Unit | M | T | SV | W | LD | OC | Pts |
|------|---|---|----|---|----|----|-----|
| Paladin Squad (×5) | 5" | 5 | 2+ | 3 | 6+ | 1 | 170 |
| Purgation Squad (×4) | 6" | 4 | 3+ | 2 | 6+ | 1 | 110 |
| Purifier Squad (×5) | 6" | 4 | 3+ | 2 | 6+ | 1 | 130 |

### Fast Attack

| Unit | M | T | SV | W | LD | OC | Pts |
|------|---|---|----|---|----|----|-----|
| Interceptor Squad (×5) | 6" | 4 | 3+ | 2 | 6+ | 2 | 125 |

### Heavy Support

| Unit | M | T | SV | W | LD | OC | Pts |
|------|---|---|----|---|----|----|-----|
| Nemesis Dreadknight | 8" | 8 | 2+ | 13 | 6+ | 4 | 195 |
| Venerable Dreadnought | 6" | 8 | 2+ | 8 | 6+ | 3 | 130 |

### Dedicated Transports
- **Rhino** (80pts) — 6 GREY KNIGHTS INFANTRY (no Terminator armour)
- **Razorback** (85pts) — 6 GREY KNIGHTS INFANTRY (no Terminator armour)
- **Land Raider** (220pts) — 12 GREY KNIGHTS INFANTRY (includes Terminators)
- **Land Raider Crusader** (220pts) — 12 INFANTRY
- **Land Raider Redeemer** (250pts) — 12 INFANTRY

### Flyers
- **Stormraven Gunship** (280pts) — 12 INFANTRY + 1 DREADNOUGHT
- **Stormhawk Interceptor** (160pts)
- **Stormtalon Gunship** (170pts)

---

## Weapon Profiles

All GK weapons have the [PSYCHIC] keyword except Storm Bolters.
*Profiles from BSData 10e; 11e Faction Pack may update these.*

### Ranged Weapons

| Weapon | RNG | A | BS | S | AP | D | Abilities |
|--------|-----|---|----|----|----|---|-----------|
| Storm Bolter | 24" | 2 | 3+ | 4 | 0 | 1 | Rapid Fire 2 |
| Storm Bolter (Paladin) | 24" | 2 | **2+** | 4 | 0 | 1 | Rapid Fire 2 |
| Incinerator | 12" | D6 | N/A | 6 | -1 | 1 | Torrent, Ignores Cover, Psychic |
| Psilencer | 24" | 6 | 3+ | 5 | 0 | 1 | Sustained Hits 1, Psychic |
| Psilencer (Paladin) | 24" | 6 | **2+** | 5 | 0 | 1 | Sustained Hits 1, Psychic |
| Psycannon | 24" | 3 | 3+ | 8 | -1 | 2 | Sustained Hits 1, Psychic |
| Psycannon (Paladin) | 24" | 3 | **2+** | 8 | -1 | 2 | Sustained Hits 1, Psychic |
| Gatling Psilencer | 24" | 12 | 3+ | 6 | 0 | 1 | Sustained Hits 2, Psychic |
| Heavy Psycannon | 24" | 6 | 3+ | 10 | -2 | 3 | Sustained Hits 1, Psychic |
| Heavy Incinerator | 12" | 2D6 | N/A | 6 | -1 | 1 | Torrent, Ignores Cover, Psychic |
| Purifying Flame | 12" | 1 | 3+ | 4 | -2 | 1 | Torrent, Ignores Cover, Psychic |

*Incinerator/Psilencer/Psycannon: Paladin Squads have BS 2+ instead of 3+. This matters for DPP calculations.*
*Purifying Flame has Torrent (auto-hit) so BS is irrelevant.*

### Melee Weapons

| Weapon | A | WS | S | AP | D | Abilities |
|--------|----|----|----|----|---|-----------|
| Nemesis Force Weapon (Terminator/Paladin) | 4 | 3+ | 6 | -2 | 2 | Psychic |
| Nemesis Force Weapon (power armour) | 3 | 3+ | 6 | -2 | 2 | Psychic |
| Close Combat Weapon | 3 | 3+ | 4 | 0 | 1 | — |
| Nemesis Daemon Hammer | 3 | 4+ | 9 | -3 | 3 | Psychic, Heavy |
| Black Blade of Antwyr (Draigo) | 5 | 2+ | 6 | -2 | 2 | Psychic, Sustained Hits 1 |
| The Titansword (Stern) | 6 | 2+ | 8 | -4 | 3 | Psychic, Anti-Daemon 2+ |
| Malleus Argyrum (Voldus) | 5 | 2+ | 10 | -2 | 3 | Psychic |

**Key difference:** Terminator-armoured units (Terminator Squad, Paladin Squad) have A=4 on Nemesis Force Weapon.
Power-armour units (Strike, Interceptor, Purifier, Purgation) have A=3. Some models in power armour
squads that take a special weapon replace their Nemesis Force Weapon with a Close Combat Weapon (A=3, S=4, AP=0, D=1).

---

## Squad Weapon Limits (11e Faction Pack)

These are HARD limits per datasheet. Never assume all models take the best weapon.

| Squad | Models | Specials | Default Loadout |
|-------|--------|----------|-----------------|
| Strike Squad | 5 | max 1× special | 4× SB, 4× NFW, 1× CCW |
| Interceptor Squad | 5 | max 1× special | 4× SB, 4× NFW, 1× CCW |
| Purifier Squad | 5 | max 2× special | 5× PF, 3× SB, 3× NFW, 2× CCW |
| Purgation Squad | 4 | 1× Inc + 1× Psil + 1× Psyc | 1× SB, 1× NFW, 3× CCW |
| Terminator Squad | 5 | max 2× special | 5× NFW, 3× SB |
| Paladin Squad | 5 | max 2× special | 5× NFW, 3× SB |

**Key rules:**
- A model that takes a special weapon loses its Storm Bolter, BUT:
  - Terminator/Paladin keeps its Nemesis Force Weapon (A=4)
  - Power armour model replaces NFW with a Close Combat Weapon (A=3, S=4, AP=0, D=1)
- Purifying Flame is ADDITIONAL — every Purifier has it regardless of other weapons
- Specials can be mixed: one model takes Incinerator, another takes Psycannon
- Terminator/Paladin 10-model squads can take up to 4 specials
- Purgation has a fixed loadout: exactly 1× Incinerator + 1× Psilencer + 1× Psycannon per squad
  (The 4th model keeps Storm Bolter + CCW)

### Correct DPP Modeling Examples

**5× Purifiers (130pts)** — the most complex squad:
- 5× Purifying Flame = 5 Torrent auto-hit attacks, S=4 AP=-2 D=1 (Psychic)
- 2× Incinerator = ~7 attacks total (D6 each), Torrent, S=6 AP=-1 D=1 (Psychic)
- 3× Storm Bolter = 6 attacks (12 at Rapid Fire range), S=4 AP=0 D=1 (NOT Psychic — takes Cover penalty)
- 3× NFW (A=3) + 2× CCW (A=3) = melee
- Call `compute_dpp` separately for each weapon type with correct model counts

**5× Terminators (140pts):**
- 2× Psycannon = 6 attacks, S=8 AP=-1 D=2 (Psychic)
- 3× Storm Bolter = 6 attacks (12 at ≤12"), S=4 AP=0 D=1 (NOT Psychic)
- 5× Nemesis Force Weapon = 20 attacks in melee, S=6 AP=-2 D=2 (Psychic)

---

## Detachments

GK have 9 detachments in 11e. Detachments cost DP (Detachment Points) — you have a
DP budget per game (typically 2-3DP for standard games).

### New Detachments (from 11e Faction Pack v1.0)

#### Argent Assault (1DP) — Purge the Foe

**Detachment Rule — DAUNTLESS CHAMPIONS**
When a friendly PALADIN SQUAD unit is selected to fight, it gains a bonus based on
its Strength compared to the target's Toughness. Paladins seek out the deadliest foes.

**Stratagems:**
| Stratagem | CP | When | Target | Effect |
|-----------|----|------|--------|--------|
| Truesilver Aegis | 1 | Any phase, when a PALADIN SQUAD suffers damage | That PALADIN SQUAD | Feel No Pain 4+ vs mortal wounds |
| A Threat Ended | 1 | Fight phase, when a PALADIN SQUAD fights | That PALADIN SQUAD | Melee attacks have [PRECISION] |
| Aura of Vengeance | 1 | Fight phase, when enemy targets a PALADIN SQUAD | That PALADIN SQUAD | Enemy unit's melee attacks have [HAZARDOUS] |

**Enhancements:**
| Enhancement | Pts | Restriction | Effect |
|-------------|-----|-------------|--------|
| Psychic Celerity | 15 | TERMINATOR model only | This unit has +1 to charge rolls |
| Vigilance of Titan | 20 | TERMINATOR model only | *(See faction pack for full effect)* |

#### Fires of Purgation (1DP) — Disruption

**Detachment Rule — SEARING SOULFLAME**
When a friendly PURGATION SQUAD unit is selected to shoot, or when it would pin a unit,
it gains additional benefits. Purgation Squads purify the battlefield through ferocious
firepower.

**Stratagems:**
| Stratagem | CP | When | Target | Effect |
|-----------|----|------|--------|--------|
| Soul-Locked | 1 | Your Movement phase, when a PURGATION SQUAD moves | That PURGATION SQUAD | That move does not prevent your unit from being eligible to shoot |
| Focused Immolation | 1 | Your Shooting phase, when a PURGATION SQUAD shoots | That PURGATION SQUAD | Select one enemy unit. Your unit's ranged attacks that target that unit gain bonuses |
| Spiritsear | 1 | Your Shooting phase, when a PURGATION SQUAD shoots | That PURGATION SQUAD | Select one battle-shocked enemy unit hit by those attacks — suffers additional mortal wounds |

**Enhancements (Upgrades):**
| Enhancement | Pts | Restriction | Effect |
|-------------|-----|-------------|--------|
| Precognicient Vollies | 10 | PURGATION SQUAD only | This unit's snap shooting hits on unmodified 5+ |
| Boons of Deimos | 20 | PURGATION SQUAD only | Ranged attacks have +2 S. When selected to shoot: [DEVASTATING WOUNDS] and [SUSTAINED HITS 1]. After shooting: target suffers D3+1 mortal wounds |

#### Immaterial Interdiction (1DP) — Priority Assets

**Detachment Rule — ECHOJUMP**
In your Shooting phase, when a friendly INTERCEPTOR SQUAD unit shoots, it can make
a surge move of up to D6+1". It cannot use its Personal Teleporters ability that phase.

**Stratagems:**
| Stratagem | CP | When | Target | Effect |
|-----------|----|------|--------|--------|
| Blades from the Beyond | 1 | Fight phase, when an INTERCEPTOR SQUAD fights | That INTERCEPTOR SQUAD | Melee attacks have [LANCE] |
| By Thought Alone | 1 | Your Shooting phase, when an INTERCEPTOR SQUAD starts an action | That INTERCEPTOR SQUAD | That action does not prevent shooting |
| Responsive Displacement | 1 | Opponent's Movement phase, when enemy ends move within 9" | That INTERCEPTOR SQUAD | Normal move of up to D3+3" |

**Enhancements (Upgrades):**
| Enhancement | Pts | Restriction | Effect |
|-------------|-----|-------------|--------|
| Predestined Coordinates | 10 | INTERCEPTOR SQUAD only | In your first Movement phase, this unit can make an ingress move |
| Astral Overlap | 10 | INTERCEPTOR SQUAD only | This unit has the Stealth ability |

#### Warpbane Task Force (3DP — MFM) — Purge the Foe
*Note: Faction Pack PDF v1.0 says 2DP, but MFM points file lists 3DP. MFM is likely the more current.*

**Detachment Rule — HALLOWED GROUND**
Certain battlefield areas are within your army's Hallowed Ground:
- **Your deployment zone** is always Hallowed Ground
- Area within **6" of PURIFIER SQUAD units** is Hallowed Ground
- If you control ≥ half the objectives in **No Man's Land** at start of phase, that area is Hallowed Ground
- If you control ≥ half the objectives in **opponent's DZ**, that area is Hallowed Ground

**Hit roll bonus:** GREY KNIGHTS units re-roll Hit rolls of 1. If the unit is a PURIFIER SQUAD
and/or wholly within Hallowed Ground, re-roll the Hit roll (any failed hits) instead.

**Stratagems:**
| Stratagem | CP | When | Target | Effect |
|-----------|----|------|--------|--------|
| Sanctified Kill Zone | 1 | Your Shooting or Fight phase | One GREY KNIGHTS unit wholly within HG that hasn't shot/fought yet | Re-roll Wound roll of 1; if Purifier, re-roll the Wound roll instead |
| Flames of Sanctity | 1 | End of Fight phase | One PURIFIER SQUAD that was eligible to fight | D3 mortals to each enemy within 6" (4+; +1 with Crowe) |
| Hallowed Beacon | 1 | Reinforcements step | One GREY KNIGHTS INFANTRY (excluding TERMINATOR) arriving via Deep Strike | Set up wholly within HG, >6" from enemy |
| Fires of Covenant | 1 | Start of opponent's Movement phase | One GREY KNIGHTS INFANTRY | D3 mortals (4+) when enemy sets up/ends move within 6" (+2 to roll if wholly within HG) |
| Aegis Eternal | 1 | Opponent's Shooting phase, after targets selected | One GREY KNIGHTS INFANTRY targeted by enemy attacks | 4+ invulnerable save for models wholly within HG |
| Repelling Sphere | 1 | Start of opponent's Charge phase | One GREY KNIGHTS INFANTRY | -1 to charge rolls (or -2 if wholly within HG) |

**Enhancements:**
| Enhancement | Pts | Restriction | Effect |
|-------------|-----|-------------|--------|
| Mandulian Reliquary | 20 | GREY KNIGHTS model only | While bearer's unit is not Battle-shocked, +3 OC |
| Radiant Champion | 15 | GREY KNIGHTS INFANTRY only | Melee: [PRECISION]. While wholly within HG, each melee wound causes 1 mortal wound in addition |
| Phial of the Abyss | 15 | GREY KNIGHTS INFANTRY only | Bearer's unit has Stealth |
| Paragon of Sanctity | 10 | GREY KNIGHTS model only | 1/ battle, at start of any phase, select one friendly GK unit within 18". Until end of phase, that unit is within HG |

### Updated Detachments (carried forward from 10e with 11e rules updates)

#### Brotherhood Strike (2DP) — Purge the Foe
*Rules update from Faction Pack: change 3" to 6".*

**Detachment Rule — (from 10e BSData)**
Re-roll 1s to hit/wound after Deep Strike. *(Verify specific 11e wording in Core Rules.)*

**Enhancements:**
| Enhancement | Pts |
|-------------|-----|
| Banishing Wave | 20 |
| Blinding Aura | 10 |
| Purity of Purpose | 15 |
| Tome of Forbidden Ways | 25 |

#### Hallowed Conclave (2DP) — Take and Hold
*Rules update: Heroic Intervention stratagem on GREY KNIGHTS model only, -1 CP cost,
does not prevent other uses.*

**Enhancements:**
| Enhancement | Pts |
|-------------|-----|
| Eye of the Augurium | 25 |
| Inescapable Judgement | 20 |
| Nemesis Rounds | 10 |
| Sanctic Reaper | 15 |

#### Banishers (2DP) — Disruption
*From 10e BSData. *(Full rules in Core Rules / BSData.)*

**Enhancements:**
| Enhancement | Pts |
|-------------|-----|
| Ephemeral Tome | 15 |
| Pyresoul | 20 |
| Sigil of the Hunt | 10 |
| Sixty-sixth Seal | 25 |

#### Augurium Task Force (2DP) — Reconnaissance
*From 10e BSData. *(Full rules in Core Rules / BSData.)*

**Enhancements:**
| Enhancement | Pts |
|-------------|-----|
| Doomseer's Amulet | 25 |
| Grimoire of Conjunctions | 10 |
| One Foot in the Future | 15 |
| Shield of Prophecy | 20 |

#### Sanctic Spearhead (2DP) — Priority Assets
*From 10e BSData. *(Full rules in Core Rules / BSData.)*

**Enhancements:**
| Enhancement | Pts |
|-------------|-----|
| Driven by Duty | 10 |
| Quickening Foci | 15 |
| Sigil of Exigence | 30 |
| Spiritus Machina | 25 |

---

## Army Rule: Gate of Infinity

At the end of your opponent's Fight phase, select up to 3 GREY KNIGHTS INFANTRY units
(or 1 DREADNOUGHT/VEHICLE unit) and redeploy them via Deep Strike. Units removed via
Gate of Infinity arrive at the end of your next Movement phase.

**Does not affect:** Rhinos, Razorbacks, Land Raiders, Flyers.

---

## Core Abilities (All GREY KNIGHTS INFANTRY)

All GREY KNIGHTS INFANTRY datasheets have:
- **Deep Strike** — can be set up in the Reinforcements step
- **Feel No Pain 6+** — the Aegis, protects against mortal wounds
- **Stealth** — -1 to hit against ranged attacks

These are baked into every INFANTRY datasheet as the mechanical representation of
the Aegis and Teleport Assault.

**Note:** Nemesis Dreadknights, Venerable Dreadnoughts also have Deep Strike natively.
This is unusual — most factions' Vehicle/Walker units do not.

---

## Gotchas

### Paladins have the TERMINATOR keyword
Paladin Squads **do** have the `Terminator` keyword in the BSData data. Detachment rules
that affect TERMINATOR models (e.g. Argent Assault's Psychic Celerity enhancement)
also affect Paladins. Always verify keyword on the specific datasheet.

### Purifying Flame is additional, not a replacement
Every Purifier model fires Purifying Flame PLUS their Storm Bolter or special weapon.
It is an extra weapon, not a substitution.



### Purgation Squad is fire support, not melee
Purgation has a fixed loadout: 1 model keeps Nemesis Force Weapon (A=3), the other 3 have
Close Combat Weapons (A=3, S=4, AP=0, D=1). They're a shooting unit — don't charge them in.

### Interceptors cannot charge after Personal Teleporters
Personal Teleporters lets them move 6" after shooting, but they cannot charge in the
same turn.

### Storm Bolter is NOT Psychic
Storm Bolters lack the [PSYCHIC] keyword. When a model with a Storm Bolter shoots
at a target in cover, the Cover penalty applies. Only special weapons, Nemesis force
weapons, and Purifying Flame have [PSYCHIC].

### Terminator/Paladin have A=4 NFW, power armour has A=3
When computing melee DPP, use A=4 for Terminator-armoured units, A=3 for power armour.

### Power armour special weapon model loses NFW
A Strike/Interceptor/Purifier model that takes a special weapon replaces Nemesis Force
Weapon (A=3, S=6, AP=-2, D=2) with Close Combat Weapon (A=3, S=4, AP=0, D=1). This
significantly reduces its melee output.

### Warpbane Task Force DP cost discrepancy
Faction Pack v1.0 says 2DP, MFM points file says 3DP. Use MFM as the authoritative
source for points/DP costs.

### Hallowed Ground needs Purifiers
Without Purifier Squads in your army, Warpbane Task Force's Hallowed Ground is only
your deployment zone and captured objectives — much harder to use offensively.

### Detachment DP costs
| Detachment | DP |
|------------|----|
| Argent Assault | 1 |
| Fires of Purgation | 1 |
| Immaterial Interdiction | 1 |
| Augurium Task Force | 2 |
| Banishers | 2 |
| Brotherhood Strike | 2 |
| Hallowed Conclave | 2 |
| Sanctic Spearhead | 2 |
| Warpbane Task Force | 3 |

Total DP across all detachments cannot exceed the mission's DP budget.

### Multiple special weapons can be mixed
Within squad limits, you can mix special weapon types. A Terminator Squad with 2 specials
could take 1× Incinerator + 1× Psycannon. The restriction is per-model, not per-squad.

### Weapon stats note
The weapon profiles above are from BSData 10e data. The 11e Faction Pack v1.0 PDF may
update these (e.g. Psycannon AP, Purifying Flame attacks). If the faction pack PDF is
re-parsed with better extraction, update these values.
