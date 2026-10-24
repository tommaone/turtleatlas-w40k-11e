# Expert File: Deathwatch

## Faction Identity

- **Full name**: Deathwatch (BSData catalogue: "Imperium - Adeptus Astartes - Deathwatch")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Deathwatch`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Adeptus Astartes framework — the shared **Combat Doctrines** army rule (Assault / Devastator / Tactical, one per Command phase, one per battle, one active per unit) plus the Kill Team unit family (Fortis, Spectrus, Talonstrike, Decimus, Indomitor per data/config). The chapter's distinct identity lives in Black Spear Task Force (Mission Tactics system + restricted army list). Sourced: BSData 9b8207c; GW preview 2026-09-10.
- **Sub-faction keywords**: `Faction: Deathwatch`

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/deathwatch.json (2026-08-23,
packs v1.1). 17 detachments total: 1 chapter-specific (Black Spear Task
Force), 16 inherited from the Space Marines codex pack (rated here in
Deathwatch context, not re-assessed).

### Army Rule
- **Army Rule Rating**: Strong — Deathwatch use the Astartes Combat Doctrines army rule (one of three doctrines per Command phase, one per battle, one active per unit) plus Kill Teams (mixed-unit rosters; Mission Tactics lives in the Black Spear Task Force detachment).
- **Oath of Moment (RETIRED) + Kill Teams**: Oath of Moment was the Astartes army rule until Codex: Space Marines (2026-10-03) replaced it with Combat Doctrines. Sourced: BSData 9b8207c (no "Oath of Moment" rule entity; SM army-rule infoLinks = `Combat Doctrines` + `Templar Vows`); GW preview 2026-09-10.
- **Play pattern** *(interpretation)*: elite mixed-specialist shooting army; the detachment choice mostly decides which inherited generic package wraps around Black Spear-style veteran units.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Inherited bench (Assault Brethren, Gladius Task Force, Gravis Linebreaker/Siege Force, Tacticus Attack Force) is deep but all conditional; no native sticky-objective tool documented. |
| Purge the Foe | Moderate | Black Spear Task Force (3DP — Mission Tactics turns the active doctrine into Sustained Hits, Lethal Hits or Precision for Kill Teams) is the chapter's own answer; Devastator Brethren and Ironstorm Spearhead are the inherited backups. |
| Reconnaissance | Moderate | Gauntlet Task Force (transport deployment) plus Stormlance Task Force; no chapter-specific recon detachment. |
| Priority Assets | Moderate | Black Spear Task Force and Gladius Task Force head the list, with Ironclad Champions, Terminator Storm Force and Tacticus Firestorm Force behind them. |
| Disruption | Situational | Phobos Shadow/Shock Force and Stormlance Task Force exist, but the elite-shooting roster converts poorly into melee tempo or screening denial. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->

#### Chapter-Specific Detachment

#### Black Spear Task Force (3DP → PURGE THE FOE)
- **Mechanics**: Each Command phase select one active Mission Tactics, each once per battle, affecting only units whose datasheets natively list Mission Tactics: Furor (Sustained Hits 1), Malleus (Lethal Hits), Purgatus (Precision on Critical Hits). Restricted army list: no other Chapters' units, some generic Astartes units excluded. FAQ: Adaptive Tactics stratagem can grant Mission Tactics to other ADEPTUS ASTARTES units.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Deathwatch Veterans and Fortis Kill Teams switching between anti-horde (Furor), anti-elite (Malleus) and character-hunting (Purgatus) modes round by round.
- **Limits**: Choose-one rotation, each tactic once per battle — never always-on; FAQ narrows scope to native-Mission-Tactics datasheets; army composition restrictions cut the inherited detachment pool's synergy surface; full 3DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

### Inherited From Space Marines Codex
<!-- shorter blocks; mechanics per deathwatch research file / shared corpus -->

#### Fulguris Task Force (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Skystrike — SPEEDER units ingress in Movement phase 1 (inherited).
- **Rating**: Situational for Reconnaissance; ⚠️ shared-codex delta flags official sources listing DISRUPTION.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Subversion Assets (1DP → DISRUPTION) — *inherited*
- **Mechanics**: Nowhere to Hide — Phobos/Scout detection manipulation (inherited).
- **Rating**: Situational for Disruption — Spectrus Kill Team / Infiltrator Squad utility; ⚠️ shared-codex delta flags official sources listing RECONNAISSANCE.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vengeful Hosts (1DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: FLY INFANTRY re-roll hit 1s on ingress/charge turns (inherited).
- **Rating**: Situational for Take and Hold. ⚠️ Research confidence LOW: objective/DP sourcing unconfirmed by primary sources (dp second-hand sourced per shared corpus).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Anvil Siege Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: All ranged weapons gain HEAVY (+1 Wound stationary if already HEAVY) (inherited).
- **Rating**: Moderate for Take and Hold — actually fits an elite gunline of Devastator/Eliminator/Sternguard-type units better than most chapters.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Bastion Task Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Battleline act after Advance/Fall Back + Auspex scan rerolls (inherited).
- **Rating**: Situational for Take and Hold — Intercessor/Heavy Intercessor bodies needed to feed scans.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Firestorm Assault Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: ASSAULT on all ranged, +1 Strength within 12" (inherited).
- **Rating**: Moderate for Priority Assets — close-range veteran volume; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Headhunter Task Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Tank Ace vehicles: flat 6" Advance, stationary damage re-rolls (inherited).
- **Rating**: Situational for Priority Assets — Gladiator Lancer/Repulsor hull lines only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Ironstorm Spearhead (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: One hit/wound/damage re-roll per unit per phase (inherited).
- **Rating**: Weak for Take and Hold — single-die insurance on few high-value shots; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Orbital Assault Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: 2-4 units gain Deep Strike + arrival-turn wound-1s rerolls (inherited).
- **Rating**: Moderate for Take and Hold — Drop Pod-delivered Eradicator alpha suits the elite profile.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Stormlance Task Force (2DP → DISRUPTION) — *inherited*
- **Mechanics**: All units charge after Advancing or Falling Back (inherited; merged data lists 2DP vs 3DP shared cost — delta unresolved).
- **Rating**: Situational for Disruption — eligibility exists but the elite-shooting roster has few units that want it.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Vanguard Spearhead (2DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Benefit of Cover vs ranged attacks from beyond 12" (inherited).
- **Rating**: Moderate for Reconnaissance — strong fit for small elite units holding ground at range.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Armoured Speartip (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Post-disembark follow-up moves from moved Transports (inherited).
- **Rating**: Situational for Take and Hold — transport count is low in typical builds.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Ceramite Sentinels (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Terrain-based hit/wound-1s rerolls + Entrenched status (inherited).
- **Rating**: Situational for Take and Hold — terrain-dense tables only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Gladius Task Force (3DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Rotating Combat Doctrines, each once per battle (inherited).
- **Rating**: Moderate for Priority Assets — generalist fallback that adapts to whatever the kill teams are doing that round.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### Librarius Conclave (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Rotating Psychic Disciplines for PSYKER units (inherited).
- **Rating**: Situational for Reconnaissance — Watch Captain Artemis lists aside, psyker density is low.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

#### 1st Company Task Force (2DP → PURGE THE FOE) — *inherited*
- **Mechanics (10e record)**: Once-per-battle wound re-rolls vs the Oath target (inherited).
- **Rating**: Situational for Purge the Foe — Deathwatch Terminator Squad focus-fire turns.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* Black Spear's Adaptive Tactics stratagem is the named force-multiplier — extending Mission Tactics to non-native ADEPTUS ASTARTES units widens the detachment's narrow FAQ scope. Inherited tools worth noting: Gladius Storm of Fire (ignore-cover) under Devastator Doctrine for veteran shooters; Anvil's Not One Backwards Step (double OC stationary near an objective) for gunline scoring. All CP-gated, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Deathwatch is a compact elite shooting force with one bespoke option: Black Spear Task Force (3DP, Priority Assets + Purge the Foe, Mission Tactics and a restricted army list) against fifteen inherited Astartes packages (Gladius, Terminator Storm Force, Ironstorm Spearhead, Tacticus x2, Stormlance, Gauntlet, Phobos x2, doctrine packages). The actual list decision is Black Spear or a chapter-flavoured character package, and the structural ceiling is breadth: the roster is built around Kill Team specialists and characters, not massed melee or vehicles, so the inherited packages that fight a different army shape (Devastator Brethren, Assault Brethren) are the ones that need doctrine support to pay off. The army rule layer is the shared Combat Doctrines with no separate chapter rule, which means every Deathwatch list is a doctrine puzzle: the detachment decides which doctrine you get, and the characters decide what it is spent on.