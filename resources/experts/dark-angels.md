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
6. **DO NOT include chapter-specific characters from other chapters** — Guilliman, Tigurius, Cato Sicarius, Marneus Calgar, Vulkan He'Stan, etc. are NOT playable as DA. Only generic SM characters (Captains, Lieutenants, Chaplains, Librarians, Techmarines) can be used across chapters. See `data/config/AGENTS.md` for full cross-faction restrictions.

---

*Last updated: 2026-07-17*

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/dark-angels.json (2026-08-23,
packs v1.1). Note: the shared-codex research file
(_space-marines-shared.json) flags official-source deltas that this faction
file inherits silently — see per-detachment ⚠️ flags below; treat affected
disposition labels as provisional until the faction file is corrected.

### Army Rule
- **Army Rule Rating**: Strong — Dark Angels share the Astartes Combat Doctrines army rule (one of three doctrines per Command phase, one per battle, one active per unit) and add no chapter-specific army rule of their own; performance rides on the detachment toolkit.
- **Oath of Moment (RETIRED)**: was the Astartes army rule until Codex: Space Marines (2026-10-03) replaced it with Combat Doctrines. Survives in BSData only as a reference inside the Master of the Deathwing character ability. Sourced: BSData 9b8207c; GW preview 2026-09-10.
- **Play pattern** *(interpretation)*: a mid-range shooting army with two internal toolkits (Deathwing elite terminators, Ravenwing fast bikes) over a generic Astartes core; detachments decide which wing leads, and the 11e chapter detachments (Darkflight Pursuit, Inner Circle Task Force, Wrath of the Rock) are the wing-specific picks.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Deep bench (Assault Brethren, Gladius Task Force, Gravis Linebreaker/Siege Force, Tacticus Attack Force) plus Wrath Of The Rock (Dutiful Tenacity — -1 wound on attacks stronger than the target's toughness), but most options carry positional or behavioural conditions. |
| Purge the Foe | Moderate | Devastator Brethren (Devastator Mastery) and Ironstorm Spearhead (Ironstorm Auto-Targeters) map here; the chapter's own picks are the Deathwing tools in Inner Circle Task Force rather than a dedicated killer. |
| Reconnaissance | Moderate | Darkflight Pursuit (Black-winged Vigilance — Ravenwing ignore cover, Outriders Battleline) gives real tools, all keyword/range-scoped; Gauntlet Task Force and Stormlance Task Force add generic movement. |
| Priority Assets | Strong | Best depth in the codex: Gladius Task Force, Inner Circle Task Force (Vowed Target — Deathwing +1 wound near a vowed objective), Ironclad Champions, Terminator Storm Force and Tacticus Firestorm Force. |
| Disruption | Moderate | Phobos Shadow/Shock Force and Stormlance Task Force (mounted +2" M) support screening; Deathwatch Support (DISRUPTION) is the one detachment listed here, and it is a support package rather than a denial engine. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->
<!-- one block per detachment, ordered by DP -->

#### Dark Age Arsenal (1DP → PRIORITY ASSETS)
- **Mechanics**: All Plasma weapon profiles get +1 Strength. Nothing else.
- **Rating**: Situational for Priority Assets
- **Synergies**: Hellblaster Squad volume plasma.
- **Limits**: Weapon-family scoped; no Strength key in the modifier vocabulary so no honest DPP expression exists (research not_modeled).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Darkflight Pursuit (1DP → RECONNAISSANCE)
- **Mechanics**: Friendly RAVENWING FLY units' ranged attacks gain IGNORES COVER.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Bike-mounted twin-bolter volume into cover-hugging scoring units.
- **Limits**: RAVENWING + FLY ranged attacks only (research stale note confirms scope).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Fulguris Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Land Speeder / Storm Speeder variants gain SPEEDER keyword; SPEEDER units make an ingress move in the first Movement phase.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Storm Speeder alpha-strike packages.
- **Limits**: Turn-1 ingress only, speeders only; deployment benefit not expressible as movement_bonus (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Interrogation Conclave (1DP → TAKE AND HOLD)
- **Mechanics**: CHAPLAIN units have a 6" aura imposing -1 Ld on enemies; when a Chaplain unit destroys an enemy in the Fight phase, enemies within 6" take a battle-shock test.
- **Rating**: Weak for Take and Hold
- **Synergies**: Chaplain-led melee blobs (Assault Intercessors) near objectives.
- **Limits**: Battleshock-domain effects with no numeric expression; cascade requires kills first (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Librarius Conclave (1DP → RECONNAISSANCE)
- **Mechanics**: Each battle round pick one Psychic Discipline for PSYKER units: Biomancy +2" M; Divination re-roll hit/wound 1s; Pyromancy +1 AP ranged within 12"; Telekinesis -1 S vs incoming ranged; Telepathy ignore BS/WS/hit modifiers.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Ezekiel / Librarian-led squads scale with psyker count.
- **Limits**: Rotational selection (nothing always-on); PSYKER-only scope (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Subversion Assets (1DP → DISRUPTION)
- **Mechanics**: PHOBOS and SCOUT SQUAD units mark one visible enemy within 12" during Shooting phase; detected units gain +3" detection range.
- **Rating**: Situational for Disruption
- **Synergies**: Infiltrator Squad / Incursor Squad forward screening.
- **Limits**: Detection mechanic has no modifier representation; unit- and LOS-restricted (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vengeful Hosts (1DP → TAKE AND HOLD)
- **Mechanics**: In a turn a friendly FLY INFANTRY unit made an ingress or charge move, its attacks re-roll hit rolls of 1.
- **Rating**: Situational for Take and Hold
- **Synergies**: Assault Intercessors With Jump Packs and Captain With Jump Pack ingress turns.
- **Limits**: Conditional on ingress/charge that turn; FLY INFANTRY scope only. ⚠️ Shared-codex research flags this detachment's disposition/DP as UNCONFIRMED (confidence low there); this faction file carries it at high confidence — treat fields as provisional.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### 1st Company Task Force (2DP → PURGE THE FOE)
- **Mechanics (10e record)**: Once per battle, activate in a Command phase: models with Oath of Moment also re-roll Wound rolls vs the declared Oath target until next Command phase.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Deathwing Knights / Terminator Squads focusing one high-value target.
- **Limits**: Once-per-battle; single-target window (research not_modeled).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Anvil Siege Force (2DP → TAKE AND HOLD)
- **Mechanics**: All ranged weapons gain HEAVY; weapons that already had HEAVY gain +1 to Wound if the attacking unit Remained Stationary that turn.
- **Rating**: Moderate for Take and Hold (castle builds)
- **Synergies**: Devastator Squad / Desolation Squad / Heavy Intercessor gunlines that don't intend to move.
- **Limits**: HEAVY imposes -1 to hit on moved turns — net effect depends on playstyle (research flags this as unexpressible as always-on bonus); +1 to wound needs existing HEAVY plus stationary.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Bastion Task Force (2DP → TAKE AND HOLD)
- **Mechanics**: BATTLELINE units can shoot/charge/start Actions after Advancing or Falling Back; after BATTLELINE attacks, one enemy unit hit becomes auspex scanned — ADEPTUS ASTARTES models re-roll hit rolls of 1 against it until end of turn.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Intercessor Squad / Tactical Squad / Heavy Intercessor battleline flood feeding rerolls to Deathwing Knights behind them.
- **Limits**: advance_and_charge modeled applies to BATTLELINE only; scan reroll is conditional on a Battleline unit hitting that target first (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Company Of Hunters (2DP → DISRUPTION)
- **Mechanics**: All ranged weapons gain ASSAULT and can shoot after Falling Back; MOUNTED units can also charge after Advancing and shoot+charge after Falling Back; OUTRIDER SQUADS gain BATTLELINE.
- **Rating**: Moderate for Disruption (Ravenwing-heavy builds)
- **Synergies**: Outrider Squad / Invader Atv / Ravenwing-style mounted packs harassing backfield objectives.
- **Limits**: advance_and_charge modeled applies to MOUNTED only; fall-back eligibility and ASSAULT grant not numerically expressible (research stale note).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Firestorm Assault Force (2DP → PRIORITY ASSETS)
- **Mechanics**: All ranged weapons gain ASSAULT; ranged attacks targeting units within 12" get +1 Strength.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Mid-range Gravis and melta/flamer packages (Aggressor Squad, Eradicator Squad, Infernus Squad).
- **Limits**: +1 Strength is profile-dependent (target T matters), no universal wound modifier (research); ASSAULT not modeled. ⚠️ Shared-codex research flags official sources listing Firestorm as PURGE THE FOE, contradicting this file's PRIORITY ASSETS.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Headhunter Task Force (2DP → PRIORITY ASSETS)
- **Mechanics**: Eligible VEHICLES become TANK ACEs (up to three may be CHARACTERS): fixed 6" Advance; if they did not Advance they re-roll Damage rolls when shooting.
- **Rating**: Situational for Priority Assets
- **Synergies**: Gladiator Lancer / Predator Annihilator stationary fire platforms.
- **Limits**: Vehicle-scope; damage reroll lost on advancing turns; list wants multiple hulls (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Inner Circle Task Force (2DP → PRIORITY ASSETS)
- **Mechanics**: Each Movement phase declare Vowed objectives (Defensive Footing: one you control; Aggressive Push: one or more you don't). DEATHWING INFANTRY attacks gain +1 to Wound vs targets within range of a Vowed objective.
- **Rating**: Moderate for Priority Assets (signature Deathwing build)
- **Synergies**: Deathwing Knights and Inner Circle Companions pushing onto contested objectives.
- **Limits**: +1 to wound is conditional on Deathwing Infantry AND target proximity to Vowed objectives (research stale note).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/


#### Lion'S Blade Task Force (2DP → PURGE THE FOE)
- **Mechanics**: Enemy non-MONSTER/non-VEHICLE units Falling Back within Engagement Range of RAVENWING units take Desperate Escape tests (-1 if battle-shocked); DEATHWING units charging targets within Engagement Range of RAVENWING units add 2 to the Charge roll.
- **Rating**: Moderate for Purge the Foe (dual-wing lists)
- **Synergies**: Ravenwing pinning (Outrider Squad screens) into Deathwing Knights charges is the designed combo loop.
- **Limits**: Cross-unit condition (DEATHWING must charge RAVENWING-pinned targets); escape-test attrition has no vocabulary key (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Orbital Assault Force (2DP → TAKE AND HOLD)
- **Mechanics**: Pre-game, selected non-TITANIC units (2-4 by battle size) gain Deep Strike; models set up this turn re-roll Wound rolls of 1; DROP POD disembarkers that turn also re-roll Hit rolls of 1.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Drop Pod-delivered Sternguard/Eradicator alpha turns; Terminator Squad reserve pressure.
- **Limits**: Rerolls arrival-turn only; Deep Strike grant is a deployment option (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Unforgiven Task Force (2DP → TAKE AND HOLD)
- **Mechanics**: Battle-shocked units have OC 1 instead of 0; in your Command phase one unit gains +1 OC until your next Command phase.
- **Rating**: Weak for Take and Hold
- **Synergies**: Pairs conceptually with battleshock-forcing allies, but DA lack strong native battleshock engines.
- **Limits**: Single-unit OC buff per Command phase (not army-wide per research); OC floor only matters against enemy battleshock tech.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vanguard Spearhead (2DP → RECONNAISSANCE)
- **Mechanics**: Ranged attacks targeting your units from beyond 12" grant the target Benefit of Cover.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Phobos/Scout infiltration lists holding exposed forward positions.
- **Limits**: Defensive save-modifier effect with no dedicated vocabulary key (research warns approximating as Stealth would be wrong); does nothing inside 12".
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Armoured Speartip (3DP → TAKE AND HOLD)
- **Mechanics**: Units disembarking from a non-FLY TRANSPORT that made a Normal/Advance move make a free Normal move of D6" (D3+3" from HEAVY TRANSPORTS = W14+ non-FLY transports). Not from Strategic Reserves.
- **Rating**: Situational for Take and Hold
- **Synergies**: Land Raider Redeemer / Land Raider Crusader assault ramps into mid-board objectives.
- **Limits**: Random move distance; requires transport to have moved; 3DP is a heavy investment for a deployment mechanic.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Ceramite Sentinels (3DP → TAKE AND HOLD)
- **Mechanics**: Models in a terrain feature re-roll hit rolls of 1 and wound rolls of 1; units fully within terrain, not set up this turn, moved ≤3", gain ENTRENCHED.
- **Rating**: Situational for Take and Hold
- **Synergies**: Terrain-camping gunlines (Hellblaster Squad, Eradicator Squad).
- **Limits**: Rerolls conditional on terrain presence; ENTRENCHED is behavioural, powering stratagems (research).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Gladius Task Force (3DP → PRIORITY ASSETS)
- **Mechanics**: At each Command phase select one Combat Doctrine (each once per battle) affecting all ADEPTUS ASTARTES units: Devastator = shoot after Advance; Tactical = shoot and charge after Fall Back; Assault = charge after Advance.
- **Rating**: Strong for Priority Assets
- **Synergies**: Everything — doctrine choice adapts to any plan; Terminator pushes use Assault, gunlines use Devastator.
- **Limits**: Each doctrine usable once per battle — sequencing decisions matter; effects are mode-based, never always-on.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/



#### Assault Brethren (1DP → TAKE AND HOLD)
- **Mechanics**: Assault Mastery — select the Assault Doctrine one additional time per battle.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Assault-oriented doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Deathwatch Support (1DP → DISRUPTION)
- **Mechanics**: Inherited cross-chapter package.
- **Rating**: Situational for Disruption
- **Synergies**: Niche use cases.
- **Limits**: Minimal bespoke rule surface.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Devastator Brethren (1DP → PURGE THE FOE)
- **Mechanics**: Devastator Mastery — select the Devastator Doctrine one additional time per battle.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Firepower lists cycling Devastator Doctrine.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Gauntlet Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Combined Deployment — transport shoots, marks target assailed until end of turn; disembarked ADEPTUS ASTARTES get [Sustained Hits 1] vs it.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Transport-delivered pushes.
- **Limits**: Conditional on transport+disembark timing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Gravis Linebreaker Force (1DP → TAKE AND HOLD)
- **Mechanics**: Walking Fortress — Gravis unit moved Normal this turn: ranged attacks lose [Heavy] and get +1 to hit.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Aggressive Gravis.
- **Limits**: Gravis-scoped, Normal-move triggered.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Gravis Siege Force (1DP → TAKE AND HOLD)
- **Mechanics**: Indomitable Defence — while within range of objective, attacks vs Gravis with S>T have -1 to wound.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Gravis holding objectives.
- **Limits**: Objective-range, S>T only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Ironclad Champions (1DP → PRIORITY ASSETS)
- **Mechanics**: Enduring Vengeance — ADEPTUS ASTARTES Dreadnought units re-roll hit rolls of 1.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Dreadnought lists.
- **Limits**: Dreadnought-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Ironstorm Spearhead (1DP → PURGE THE FOE)
- **Mechanics**: Ironstorm Auto-Targeters — ADEPTUS ASTARTES Vehicles (excl Walkers) can re-roll one hit and one wound.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Vehicle gunlines.
- **Limits**: Excludes Walkers, partial re-rolls.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Phobos Shadow Force (1DP → DISRUPTION)
- **Mechanics**: Shadow Masters — Phobos/Scout shoot then don't prevent hidden or make D6" move (no charge until end).
- **Rating**: Moderate for Disruption
- **Synergies**: Phobos recon.
- **Limits**: Phobos/Scout scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Phobos Shock Force (1DP → DISRUPTION)
- **Mechanics**: Vanguard Ambushers — end of Movement if hidden, Phobos attacks re-roll wound rolls of 1 until end of turn.
- **Rating**: Moderate for Disruption
- **Synergies**: Hidden Phobos.
- **Limits**: Requires hidden, re-roll 1s only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Stormlance Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Lightning-Fast Strike — Mounted/Speeder have +2" Move.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Ravenwing mobility.
- **Limits**: Mounted/Speeder only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Tactical Brethren (1DP → PRIORITY ASSETS)
- **Mechanics**: Tactical Mastery — select Tactical Doctrine one additional time per battle.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Tacticus Attack Force (1DP → TAKE AND HOLD)
- **Mechanics**: Wrath of the Chapter — Tacticus units can re-roll advance rolls.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Tacticus advancing to objectives.
- **Limits**: Tacticus-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Tacticus Firestorm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Codex Fire-Patterns — Tacticus [Rapid Fire] benefit from RF at max range.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Tacticus rapid fire.
- **Limits**: Tacticus/RF only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Terminator Storm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Death Blow — Terminator units have +1 to charge rolls.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Deathwing assaults.
- **Limits**: Terminator-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

#### Wrath Of The Rock (2DP → TAKE AND HOLD)
- **Mechanics**: Dutiful Tenacity — while this unit is within range of an objective you control, subtract 1 from the wound roll of attacks made with S greater than this unit's T (Unforgiven keyword context).
- **Rating**: Moderate for Take and Hold
- **Synergies**: Deathwing anchoring objectives against heavy weapons.
- **Limits**: Objective-range, conditional on S>T, 2DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/dark-angels/

### Enhancements & Stratagems Worth Taking
- *(Interpretation — the DA research file names no faction-specific enhancements or stratagems; nothing verifiable to recommend here beyond noting that the shared-codex corpus documents ENTRENCHED-gated stratagems for the equivalent Ceramite Sentinels detachment and doctrine-gated bonuses under Gladius — CP spent there is the documented pattern, but DA-pack-specific stratagems are unverified in this corpus.)*

### Overall Army Play Pattern
*(interpretation)* Dark Angels sit on the generic Adeptus Astartes chassis, and the 11e roster says so plainly: of 19 detachments only Wrath Of The Rock, Inner Circle Task Force, Ironclad Champions, Terminator Storm Force, Tacticus Firestorm Force and Darkflight Pursuit are chapter-flavoured, the rest are inherited Astartes packages. That means the list-building decision is a choice between a Terminator wall (Wrath Of The Rock, Terminator Storm Force, Ironclad Champions for Priority Assets), a generic-but-deep 3DP anchor (Gladius Task Force), or a fast bike game (Darkflight Pursuit) — the chapter's 10e Deathwing/Ravenwing identity survives in the units, not in the detachment rules. Because the army rule is the shared Combat Doctrines, the packages that hand out an extra doctrine (Assault Brethren, Devastator Brethren, Tactical Brethren) multiply their value: doctrine choice, not detachment stats, is the tempo dial. Weak spots are Disruption and Reconnaissance, which run entirely on inherited tools (Phobos Shadow/Shock Force, Stormlance, Gauntlet), and the army's mid-board durability (T5 Deathwing, massed 3+ saves) means it scores while trading inefficiently for the opponent.

### First-Army Fit
- **First-Army Fit**: Great — deep durable bench (Deathwing terminator core), straightforward mid-range shooting, and six 1DP detachments forgive list-building; the classic forgiving first army. Sourced: user domain call 2026-09-06.
