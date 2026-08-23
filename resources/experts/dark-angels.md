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
- **Oath of Moment**: Adeptus Astartes army rule referenced throughout the research corpus — units declare an Oath of Moment enemy target and gain targeting-reroll benefits against it [unverified: the base Oath benefit itself is not stated in the corpus; only detachment extensions to it are documented]. Several detachments add wound re-rolls vs the Oath target. Exact per-unit timing/scope not detailed in the DA corpus.
- **Play pattern** *(interpretation)*: a mid-range shooting army with three internal toolkits (Deathwing elite terminators, Ravenwing fast bikes, Greenwing massed marines); detachments decide which wing leads.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Deep bench (Anvil Siege Force, Bastion Task Force, Orbital Assault Force) but most options carry positional or behavioural conditions. |
| Purge the Foe | Moderate | 1st Company Task Force and Lion's Blade Task Force both map here; both are single-target/conditional. |
| Reconnaissance | Moderate | Vanguard Spearhead's long-range cover benefit and Darkflight Pursuit's ignore-cover give real tools, all keyword/range-scoped. |
| Priority Assets | Strong | Best depth in the codex: Gladius Task Force, Inner Circle Task Force, Firestorm Assault Force and Wrath Of The Rock. |
| Disruption | Moderate | Stormlance Task Force is army-wide charge-after-advance/fallback; Company Of Hunters supports mounted harassment. |

### Detachment Assessments
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
- **Mechanics**: Once per battle, activate in a Command phase: models with Oath of Moment also re-roll Wound rolls vs the declared Oath target until next Command phase.
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

#### Ironstorm Spearhead (2DP → TAKE AND HOLD)
- **Mechanics**: Once per phase per unit, re-roll one Hit roll OR one Wound roll OR one Damage roll for a model in that unit.
- **Rating**: Weak for Take and Hold
- **Synergies**: Dreadnought-heavy lists get marginal insurance on key shots.
- **Limits**: Single-die reroll is materially weaker than blanket rerolls (research wording) — cannot be honestly represented as stronger.
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

#### Stormlance Task Force (3DP → DISRUPTION)
- **Mechanics**: All ADEPTUS ASTARTES units may declare charges in turns they Advanced or Fell Back.
- **Rating**: Strong for Disruption (aggressive/melee lists)
- **Synergies**: Bladeguard Veteran Squad, Inner Circle Companions and jump units converting every Advance into charge threat.
- **Limits**: Charge eligibility ≠ charge success — 9" charges remain risky; research notes fall-back-then-charge also granted but unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Wrath Of The Rock (3DP → PRIORITY ASSETS)
- **Mechanics**: Attacks targeting your INFANTRY or MOUNTED units subtract 1 from the Wound roll when attacker Strength exceeds unit Toughness.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Deathwing Knights (T5) and Outrider Squads shrug off lascannon/melta-class fire.
- **Limits**: Conditional on attacker S > T — does nothing vs S ≤ T volume fire (research stale note); purely defensive, adds no damage.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

### Enhancements & Stratagems Worth Taking
- *(Interpretation — the DA research file names no faction-specific enhancements or stratagems; nothing verifiable to recommend here beyond noting that the shared-codex corpus documents ENTRENCHED-gated stratagems for the equivalent Ceramite Sentinels detachment and doctrine-gated bonuses under Gladius — CP spent there is the documented pattern, but DA-pack-specific stratagems are unverified in this corpus.)*

### Overall Army Play Pattern
*(interpretation)* Dark Angels are a chapter-scheme of the Adeptus Astartes chassis that wins through detachment choice more than army rule: pick Inner Circle Task Force or Wrath Of The Rock to make the Deathwall grind onto Priority Assets, Company Of Hunters/Darkflight Pursuit for a Ravenwing mobility game, or default to Gladius-style flexibility. Because Oath of Moment provides only modest targeted rerolls, the army's identity comes from durable mid-board bodies (T5 Deathwing, massed 3+ saves) that score while trading inefficiently for the opponent — strongest where objectives reward standing still (Priority Assets, Take and Hold) and weakest in pure disruption where its tools are once-per-game or cross-unit conditional.
