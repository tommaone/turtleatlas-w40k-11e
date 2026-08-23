# Orks

## Faction Identity

- **Full name**: Orks (BSData catalogue: "Orks")
- **Faction keyword**: ORKS
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Waaagh! — once per battle, at the start of your Command phase; while active (until your next Command phase): units with the ability may declare charges in a turn they Advanced, melee weapons gain +1 Strength and +1 Attacks, and models gain a 5+ invulnerable save (paraphrased from bsdata/Orks.json army-rule entry)
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
- **Waaagh!**: once per battle burst window. While active: Advance-and-Charge eligibility, +1S/+1A on melee weapons, and a 5+ invulnerable save across units with the ability.
- **Play pattern** *(interpretation)*: the whole faction plans around a single turn of supercharged melee. Detachments that extend or amplify the window (Bully Boyz second Waaagh!) or reward being mid-Waaagh! (More Dakka!'s Sustained Hits gate) change WHEN you want to press, not WHETHER the plan is a timed assault.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Green Tide (Boyz invulns scaling with unit size), War Horde objective tag and Freebooter Krew loot-objective buffs; mass cheap bodies own markers. |
| Purge the Foe | Strong | War Horde grants unconditional army-wide melee Sustained Hits 1; Waaagh! itself is a damage window; Bully Boyz/Da Big Hunt add targeted kill pressure. |
| Reconnaissance | Situational | Speedwaaagh!/Blitz Brigade mobility is real but movement ≠ scoring in an action-hostile edition; Taktikal Brigade's action-eligibility fights the meta directly. |
| Priority Assets | Situational | Rollin' Deff supports vehicle pushes; nothing in corpus preserves characters or key units. |
| Disruption | Moderate | Equatorial Hordes Scouts redeploy and More Dakka! screening fire; horde bodies naturally clog lanes. |

### Detachment Assessments
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
