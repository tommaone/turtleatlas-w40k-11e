# Tyranids

## Faction Identity

- **Full name**: Tyranids (BSData catalogue: "Tyranids")
- **Faction keyword**: TYRANIDS
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Synapse Range gating — several detachment benefits apply only to units within Synapse Range (per detachment_research/tyranids.json, Synaptic Nexus entry); unit-family keywords (BURROWER, ENDLESS MULTITUDE, HARVESTER, VANGUARD INVADER) gate detachment rules. NOTE: the research corpus does NOT reproduce the full army-rule text — only Synapse Range is grounded here.
- **Keywords every unit should carry**: TYRANIDS
- **Sub-faction keywords** (per research corpus): SYNAPSE (implied by range gating), BURROWER, ENDLESS MULTITUDE, HARVESTER, VANGUARD INVADER, NORN EMISSARY/NORN ASSIMILATOR, Lictor family (Deathleaper/Lictor/Neurolictor)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/tyranids.json (2026-08-23, packs v1.1).

### Army Rule
- **Synapse Range**: the corpus grounds this as a gating condition — detachment benefits (Synaptic Nexus imperatives) require units within Synapse Range. Units outside Synapse lose access to those buffs.
- **Play pattern** *(interpretation)*: list construction clusters scoring and melee units around synapse creatures; anything operating independently must be worth its points WITHOUT detachment buffs. The corpus does not cover the rest of the army rule — no claims made about it here.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Three TaH detachments: Unending Swarm surge moves on model loss, Assimilation Swarm regeneration, Invasion Fleet army-wide pick-one buff; horde bodies + healing hold ground. |
| Purge the Foe | Moderate | Crusher Stampede monster scaling and Subterranean Assault army-wide hit rerolls push damage; delivery for slow monsters remains the constraint. |
| Reconnaissance | Situational | Vanguard Onslaught charge-eligibility rules are real but narrow; single dedicated Recon detachment. |
| Priority Assets | Situational | Assimilation Swarm heals characters' units but nothing specifically preserves key pieces. |
| Disruption | Moderate | Ambush Predators lictor deep strike network and Synaptic Nexus defensive imperatives; Subterranean tunnel markers disrupt enemy movement planning. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Ambush Predators (1DP → DISRUPTION)
- **Mechanics**: Lictor-family units (Deathleaper/Lictor/Neurolictor) gain Deep Strike; Lictor/Neurolictor attacks targeting CHARACTER units may re-roll hit rolls of 1.
- **Rating**: Situational for Disruption
- **Synergies**: Deathleaper, Lictor, Neurolictor — cheap character-hunting skirmishers.
- **Limits**: three-unit scope; reroll only vs CHARACTER targets; Deep Strike deployment unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Talons Of The Norn Queen (1DP → TAKE AND HOLD)
- **Mechanics**: NORN EMISSARY/NORN ASSIMILATOR units may once per battle each, in the Command phase, re-select which Singular Purpose option they use.
- **Rating**: Weak for most dispositions; Situational for Take and Hold only if running both Norn units
- **Synergies**: Norn Emissary, Norn Assimilator.
- **Limits**: two-unit scope, once-per-battle each, flexibility-only benefit (no new stats); value depends entirely on how swingy the Singular Purpose choice actually is mid-game.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Warrior Bioform Onslaught (1DP → TAKE AND HOLD)
- **Mechanics**: Tyranid Warriors with ranged/melee bio-weapons gain BATTLELINE; Tyranid Prime/Winged Tyranid Prime/Lash Whip Prime models gain a 5+ invulnerable save.
- **Rating**: Situational for Take and Hold / Purge the Foe
- **Synergies**: Tyranid Warriors With Ranged/Melee Bio-Weapons led by any Prime variant.
- **Limits**: invuln applies to PRIME LEADER MODELS ONLY, not their squads (corpus flags this explicitly); BATTLELINE grant is list-building only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Assimilation Swarm (2DP → PRIORITY ASSETS)
- **Mechanics**: In your Command phase each HARVESTER unit regenerates one friendly unit within 6": one model regains D3+1 lost wounds, or return destroyed models (one non-CHARACTER INFANTRY model; up to 3 for ENDLESS MULTITUDE units). Each unit once per phase.
- **Rating**: Moderate for Priority Assets / Take and Hold (attrition war)
- **Synergies**: HARVESTER units (corpus names none individually beyond the keyword) healing Termagants, Tyranid Warriors, Hive Tyrant blocks.
- **Limits**: healing/resurrection has no modifier equivalent — engine-blind; requires HARVESTER units to survive in 6" range; per-unit-per-phase cap.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Crusher Stampede (2DP → PURGE THE FOE)
- **Mechanics**: MONSTER models gain +1 to Hit if their unit is below Starting Strength, +1 to Wound if also Below Half-strength; non-Battle-shocked MONSTER units at FULL Starting Strength gain +2 Objective Control instead.
- **Rating**: Situational for Purge the Foe (strength-state dependent — bonuses flip as units take damage)
- **Synergies**: Old One Eye, The Swarmlord, Hive Tyrant, Winged Hive Tyrant and any MONSTER-dense build.
- **Limits**: every bonus is state-conditional (below Starting Strength / Below Half / full strength) — none modeled; damaged units get damage buffs but lost OC; inverse incentive structure needs deliberate sequencing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Synaptic Nexus (2DP → DISRUPTION)
- **Mechanics**: Each battle round select one Synaptic Imperative (each usable ONCE per battle), active for units within Synapse Range: 5+ invulnerable save, +1 to Advance and Charge rolls, or +1 to melee Hit rolls.
- **Rating**: Situational for Disruption / Take and Hold
- **Synergies**: synapse-anchored cores — Tyranid Warriors, Hive Tyrant, Neurotyrant, Swarmlord-led blobs.
- **Limits**: pick-one-per-round AND each once per battle — the pool empties by late game; all effects Synapse Range gated; melee hit bonus is melee-only; none modeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Unending Swarm (2DP → TAKE AND HOLD)
- **Mechanics**: ENDLESS MULTITUDE units that lose a model to enemy shooting may make a D6" surge move after the attacking enemy unit finishes shooting.
- **Rating**: Moderate for Take and Hold (reactive re-positioning keeps bodies on markers)
- **Synergies**: Termagants, Hormagaunts, Gargoyles — high-model ENDLESS MULTITUDE screens.
- **Limits**: conditional on losing a model to shooting; random D6 distance; move happens after damage — cannot prevent casualties.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Vanguard Onslaught (2DP → RECONNAISSANCE)
- **Mechanics**: Units are eligible to charge in a turn they Fell Back; VANGUARD INVADER units additionally eligible to charge in a turn they Advanced. Deathleaper loses Hunter Organism and may be Warlord.
- **Rating**: Situational for Reconnaissance / Purge the Foe
- **Synergies**: Genestealers, Von Ryan's Leapers, Raveners and other VANGUARD INVADER units; engaged-and-trapped escapes into counter-charges.
- **Limits**: Fell Back charging helps only when you're already engaged; Advance-and-Charge is VANGUARD INVADER-keyword scoped; charge distance still rolled normally.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Invasion Fleet (3DP → TAKE AND HOLD)
- **Mechanics**: Pick ONE army-wide Hyper-adaptation at battle start: Sustained Hits 1 vs INFANTRY/SWARM targets, Lethal Hits vs MONSTER/VEHICLE targets, or Precision on critical hits vs CHARACTER targets.
- **Rating**: Moderate for Purge the Foe with Lethal Hits chosen (anti-tank coverage); Situational otherwise — pick-one-of-three means the other two modes are dead weight each game
- **Synergies**: whole-army scope makes it stack with everything; volume-shooting Termagants or melee Genestealers scale whichever mode is picked.
- **Limits**: mutually exclusive modes — Sustained Hits mode does nothing vs vehicles, Lethal Hits mode does nothing vs infantry hordes, Precision mode is narrowest of all; none modeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

#### Subterranean Assault (3DP → DISRUPTION)
- **Mechanics**: ALL attacks re-roll hit rolls of 1. BURROWER units arriving from Reserves place Tunnel Markers; Reserves units may arrive within 9" of a marker; markers removed if enemies end moves within 3". Mawloc/Trygon gain BURROWER; up to 2 Trygons become CHARACTERS.
- **Rating**: Strong for Purge the Foe (the army-wide hit-reroll component is unconditional); the tunnel network itself is Situational
- **Synergies**: entire army gets the reroll; Trygon/Mawloc delivery enables reserve-heavy builds.
- **Limits**: tunnel markers are destructible-by-proximity and geometry-dependent; Trygon CHARACTER upgrade is list-building; full-budget 3DP cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/tyranids/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents no individual enhancement/stratagem names for this faction)*
- The research corpus does NOT catalogue individual stratagems or enhancements for Tyranids — no picks offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: The grounded Tyranids package splits into three honest archetypes. First, the attrition board: Unending Swarm plus Assimilation Swarm turns cheap ENDLESS MULTITUDE and healed bodies into objective glue that punishes under-invested enemy shooting phases. Second, the unconditional damage floor: Subterranean Assault's army-wide hit-reroll is the only always-on offensive rule in the corpus and anchors any Purge plan regardless of what the gimmicks do. Third, the conditional layer — Crusher Stampede's strength-state bonuses and Synaptic Nexus's once-per-battle imperatives — which demands active management and emptying pools on schedule rather than hoarding. Across all three, the Synapse Range gate means independent operators must justify themselves without buffs, and Invasion Fleet's pick-one design confirms the faction philosophy: broad-but-mediocre beats narrow-and-strong nowhere except when the meta guess (Lethal Hits into vehicle metas) is right.
