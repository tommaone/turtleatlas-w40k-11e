# Orks

## Faction Identity

- **Full name**: Orks (BSData catalogue: "Orks")
- **Faction keyword**: ORKS
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Waaagh! — friendly ORKS with the ability re-roll advance rolls and can become riled up; while riled up the unit has a 5+ invulnerable save, its ranged attacks gain Assault, and an Advance move does not stop it from declaring a charge. The separate **Void Waaagh!** rule is the melee-stacking variant (+1 Strength, +1 Attacks, 5+ invulnerable save, once per battle at the start of a battle round). Sourced: bsdata/Orks.json (rules `Waaagh!` and `Void Waaagh!`)
- **Keywords every unit should carry**: ORKS
- **Sub-faction keywords** (per research corpus): MOB, SPEED FREEKS, BEAST SNAGGA, WAGON, BOYZ, WARBOSS/NOBZ/MEGANOBZ, KOMMANDOS, STORMBOYZ, GRETCHIN

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/orks.json (2026-08-23, packs v1.1). Army rule paraphrase grounded in bsdata/Orks.json.

### Army Rule
- **Army Rule Rating**: Strong — Waaagh! is the Orks army rule in 11e: friendly ORKS with the ability re-roll advance rolls and can become riled up. While riled up a unit has a 5+ invulnerable save, its ranged attacks gain Assault, and an Advance move does not block it from declaring a charge. The separate Void Waaagh! rule is the melee-stacking variant (+1 Strength and +1 Attacks, 5+ invulnerable save, once per battle at the start of a battle round). Sourced: BSData 9b8207c (rules `Waaagh!` and `Void Waaagh!`).
- **Waaagh!**: re-roll advance rolls, then go riled up — 5+ invulnerable save, ranged attacks gain Assault, Advance does not prevent charging. Units that are riled up are the burst window; the "once per battle" timing sits on the ability/units that grant it, not on a generic army-wide toggle.
- **Play pattern** *(interpretation)*: the army plays on riled-up windows. War Cry (once per battle, per army) makes every Waaagh!-unit riled up until the end of the next turn — while riled up a unit has 5+ invulnerability, its ranged attacks gain Assault, and an Advance no longer blocks charging. Waaagh! is the always-on half: advance-roll re-rolls plus the riled-up state. The detachment decides which window you spend — War Horde (Sustained Hits 1 on all melee) and Green Tide (Sustained Hits, then Lethal Hits on infantry that charged this turn) for melee; Shoota Boyz (ranged Assault, +3" R while riled up) and Flyboyz for shooting; Kult of Speed and Taktikal Brigade for the advance-and-charge package. Void Waaagh! (once per battle at the start of a battle round) is the melee-stacking variant: +1 Strength, +1 Attacks, 5+ invulnerable save, and it counts as a Waaagh! for datasheet abilities. Sourced: BSData 9b8207c (rules `Waaagh!`, `War Cry`, `Void Waaagh!`; detachment rules for War Horde, Green Tide, Shoota Boyz, Flyboyz, Kult of Speed, Taktikal Brigade).

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Green Tide (Sustained Hits 1 for Boyz melee, Lethal Hits on infantry that charged this turn) and War Horde (Sustained Hits 1 on all Orks melee) make cheap bodies hold markers; Taktikal Brigade (Stormboyz Battleline, fall-back no longer blocks a charge) and Blitz Brigade (wagon charge re-rolls) keep them there. |
| Purge the Foe | Strong | War Horde grants army-wide melee Sustained Hits 1 and Bully Boyz the same for Meganobz/Nobz; Da Big Hunt (+1 AP against MONSTER/VEHICLE with Beast Snagga) and Dread Mob (walker re-rolls when selected to attack) add targeted kill pressure, Shoota Boyz gives ranged Assault. |
| Reconnaissance | Situational | Kult Of Speed (Warbikers Battleline, advance unlocks ranged Assault) and Flyboyz (aircraft outside the strategic-reserves count) are real mobility tools — but movement is not scoring in 11e and no Orks detachment targets actions. |
| Priority Assets | Situational | Wreckas (re-roll hit rolls of 1 near objectives) and Runt Swarm (Gretchin Battleline, advance no longer blocks an action) cover the flanks; nothing in the roster protects characters. |
| Disruption | Moderate | Madcap Meks (single-target shooting rolls a random effect) and Wurrband (Psyker +1 S, scaling with unit size) are the shooting picks; the army has no native screening or denial rule. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->
<!-- one block per detachment, ordered by DP -->

#### Equatorial Hordes (1DP → DISRUPTION)
- **Mechanics**: In Declare Battle Formations pick up to three Mob or Kommandos units; those units gain Scouts 6" for the whole battle.
- **Rating**: Situational for Disruption / Take and Hold
- **Synergies**: Boyz, Kommandos — pre-first-turn repositioning onto forward cover or objectives.
- **Limits**: pre-game move only (corpus explicitly warns against misreading as +6" Move characteristic); three-unit cap; no in-game stat change.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### More Dakka! (1DP → DISRUPTION)
- **Mechanics**: Orks Infantry ranged weapons always have Assault. While Waaagh! is active in your Shooting phase, Orks Infantry ranged attacks additionally get Sustained Hits 1.
- **Rating**: Moderate for Purge the Foe / Disruption
- **Synergies**: Boyz, Gretchin screens... primarily Shooty Boyz blocks and Tankbustas/Lootas if fielded as Infantry.
- **Limits**: Assault unmodeled; Sustained Hits component is WAAAGH!-ACTIVE gated — outside that window it's a mobility rule only; Infantry scope excludes vehicles/bikers.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Rollin' Deff (1DP → PRIORITY ASSETS)
- **Mechanics**: Battlewagon/Hunta Rig/Kill Rig units gain the Wagon keyword. Wagon units re-roll charge rolls; when Advancing they may set the Advance roll to a fixed 6 instead of rolling.
- **Rating**: Situational for Priority Assets / Purge the Foe
- **Synergies**: transport-heavy pushes delivering Boyz/Nobz charges turn 2.
- **Limits**: vehicle-family scope; charge rerolls and fixed-6 Advance have no vocabulary keys (unmodeled); fixed 6 replaces variance — good average, no upside spikes.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Taktikal Brigade (1DP → RECONNAISSANCE)
- **Mechanics**: Stormboyz gain BATTLELINE. Boyz, Kommandos and Stormboyz units remain eligible to start an action even after an Advance or Fall Back move.
- **Rating**: Situational for Take and Hold / Reconnaissance
- **Synergies**: Stormboyz jump troops hopping marker to marker while still performing actions.
- **Limits**: action eligibility after moves has no vocabulary key AND actions are structurally weak in this project's 11e read — the headline benefit targets a low-value activity; BATTLELINE grant is list-building only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Blitz Brigade (2DP → RECONNAISSANCE)
- **Mechanics**: Orks units disembarking from a Transport may re-roll their Advance and Charge rolls until end of turn.
- **Rating**: Situational for Reconnaissance / Purge the Foe
- **Synergies**: Trukk-delivered Nobz/Kommandos; transports named in Rollin' Deff corpus entry (Battlewagon family).
- **Limits**: strictly turn-of-disembark conditional; rerolls only — no distance guarantee; requires paying for transports.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Bully Boyz (2DP → PURGE THE FOE)
- **Mechanics**: If a Warboss is on the battlefield, you may call a SECOND Waaagh! in a later turn; that second Waaagh! buffs ONLY Warboss, Nobz and Meganobz units.
- **Rating**: Situational for Purge the Foe (conditional extension of the army rule)
- **Synergies**: Warboss + Nobz/Meganobz core — Ghazghkull Thraka lists double-dip the elite window.
- **Limits**: requires a Warboss on the battlefield (BSData also permits the Warboss being embarked within a Transport that is on the battlefield); second window is elite-keyword scoped, not army-wide; timing of the first vs second Waaagh! is a real sequencing decision.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Da Big Hunt (2DP → PURGE THE FOE)
- **Mechanics**: Each Command phase nominate one enemy MONSTER/VEHICLE/CHARACTER as Prey. Beast Snagga units get +1 AP vs Prey; a declaring Beast Snagga charge may re-roll its charge roll if Prey is within 12", but must then finish engaged with Prey.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Beast Snagga Boyz, Squighog Boyz, Beastboss on Squigosaur, Mozrog Skragbad — monster/vehicle hunters.
- **Limits**: +1 AP applies ONLY to the single nominated Prey (corpus flags target-conditional, not global); engagement-forcing clause can drag chargers into bad positions; keyword-scoped to BEAST SNAGGA.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Dread Mob (2DP → PRIORITY ASSETS)
- **Mechanics**: Mek, Orks Walker and Grots Vehicle units roll a D6 when selected to shoot/fight for a random phase-long weapon buff (Sustained Hits 1, Lethal Hits, or +2 AP on critical wounds); alternatively pick voluntarily but the unit's weapons become Hazardous. Gretchin gain Battleline (list-building).
- **Rating**: Weak for most dispositions; Situational for Priority Assets in dedicated kan-wallie builds
- **Limits**: research confidence MEDIUM on this entry; buff selection random-or-Hazardous — never deterministic; Hazardous self-damage downside unrepresentable; narrow chassis scope.
- **Synergies**: Mek-led walker spam with Gretchin screens holding back markers.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Freebooter Krew (2DP → TAKE AND HOLD)
- **Mechanics**: Each Command phase nominate one objective marker as your loot objective. Orks Infantry/Mounted/Walker units get Sustained Hits 1 on attacks if either the attacking unit or its target is within range of the loot objective.
- **Rating**: Situational for Take and Hold / Purge the Foe
- **Synergies**: mixed infantry/mounted lists fighting over mid-board markers; nomination moves each turn to steer your army's fight.
- **Limits**: Sustained Hits is proximity-gated to ONE nominated marker per turn — off-objective fights get nothing (corpus: never-on otherwise).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Kult Of Speed (2DP → DISRUPTION)
- **Mechanics**: Speed Freeks units remain eligible to shoot and declare a charge in a turn they Advanced or Fell Back.
- **Rating**: Moderate for Purge the Foe (melee/shooting delivery fix for the fast wing); Situational otherwise
- **Synergies**: Warbikers, Deffkilla Wartrike, Wazdakka Gutsmek, fast vehicle elements carrying SPEED FREEKS.
- **Limits**: SPEED FREEKS-keyword scoped only (corpus flags engine understates the Fell Back case if only advance-charge modeled); eligibility ≠ bonus accuracy — shooting after Advance carries its normal penalties.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Speedwaaagh! (2DP → RECONNAISSANCE)
- **Mechanics**: When a Speed Freeks or Trukk unit Advances it may 'turbo': skip the roll, move straight-line at Move 24" that phase; ranged weapons gain Assault until end of turn but the unit cannot declare a charge that turn.
- **Rating**: Situational for Reconnaissance / Disruption
- **Synergies**: Trukk rushes and biker flank grabs — 24" threat projection turn 1.
- **Limits**: optional per-unit choice; line-restricted movement; mutually exclusive with charging THAT turn (Assault granted, charge forbidden); all effects unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### Green Tide (3DP → TAKE AND HOLD)
- **Mechanics**: BOYZ units always have a 6+ invulnerable save vs attacks; BOYZ units of 10+ models instead have a 5+ invulnerable save.
- **Rating**: Strong for Take and Hold — always-on (within scope) durability that stacks with massed bodies
- **Synergies**: max-size Boyz blobs, Beast Snagga Boyz, supported by Painboy characters where fielded.
- **Limits**: BOYZ-units-only scope (engine must filter by keyword, corpus flags); the 5+ tier is size-conditional above the modeled 6+ baseline; invuln does nothing vs mortal wounds unless stated otherwise (not stated — unverified); full-budget 3DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

#### War Horde (3DP → TAKE AND HOLD)
- **Mechanics**: ALL melee weapons equipped by ORKS models have Sustained Hits 1. Unconditional across the entire army.
- **Rating**: Strong for Purge the Foe / Take and Hold — the only unconditional offensive army-wide buff in the corpus
- **Synergies**: every melee profile in the book; compounds with Waaagh!'s +1S/+1A into a single overwhelming melee turn.
- **Limits**: melee weapons ONLY — ranged unaffected (engine must scope sustained_hits_extra to melee profiles, corpus flags); full-budget 3DP cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/orks/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents no individual enhancement/stratagem names for this faction)*
- The research corpus does NOT catalogue individual stratagems or enhancements for Orks — no picks offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: Every grounded Orks detachment reads as a variation on one theme — deliver a critical mass of bodies into melee and make the trade math obscene. The two 3DP anchors define the poles: War Horde makes the whole army's melee permanently better (unconditional Sustained Hits 1), Green Tide makes the bodies themselves stubbornly hard to clear (scaling invulns). Around them, the 2DP options are delivery and focus tools whose value hinges on conditions the opponent can see coming — Prey nomination, loot objectives, transport timings, the second Waaagh!'s elite-only window. The honest weaknesses in the corpus: nearly every non-anchor rule is keyword-scoped or turn-gated, the action-support detachments (Taktikal Brigade) push toward activities this project rates poorly in 11e, and the Waaagh! itself is once-per-battle — after it's spent, the army's ceiling drops sharply unless Bully Boyz kept an elite reserve window in the tank.

### First-Army Fit
- **First-Army Fit**: Good — riled-up Waaagh! and massed mobs reward volume play; fight-phase pressure needs far less staging precision than elite melee. Sourced: user domain call 2026-09-06; warhammer-community.com 2026-08-14.
