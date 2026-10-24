# Expert File: Space Wolves

## Faction Identity

- **Full name**: Space Wolves (BSData catalogue: "Imperium - Adeptus Astartes - Space Wolves")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Space Wolves`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Adeptus Astartes framework — the shared **Combat Doctrines** army rule (one doctrine per Command phase: Assault, Devastator or Tactical; one selection per battle; one active per unit) plus the chapter rule **Curse of the Wulfen**. The chapter-specific suite is organised around named Sagas — kill-tally and boast progression systems that escalate army-wide buffs mid-battle. Sourced: BSData 9b8207c (SW sharedRules: `Curse of the Wulfen`); GW preview 2026-09-10.
- **Sub-faction keywords**: `Faction: Space Wolves`

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/space-wolves.json +
_space-marines-shared.json (2026-08-23, packs v1.1). 23 detachments total:
7 chapter-specific, 16 inherited from the shared Space Marines codex pack
(rated here in Space Wolves context, not re-assessed).

### Army Rule
- **Army Rule Rating**: Moderate — Space Wolves use the Astartes Combat Doctrines army rule (three doctrines, one per Command phase, one per battle, one active per unit) plus the chapter rule Curse of the Wulfen; identity comes from chapter tools (Curse, Sagas).
- **Oath of Moment (RETIRED)**: was the Astartes army rule until Codex: Space Marines (2026-10-03) replaced it with Combat Doctrines. Sourced: BSData 9b8207c (SW sharedRules: `Curse of the Wulfen`); GW preview 2026-09-10.
- **Play pattern** *(interpretation)*: Saga detachments build a mid-battle escalation arc — early rounds the army plays on conditional buffs, late rounds (Saga complete) it plays on near-army-wide bonuses; list construction revolves around which saga completes fastest against the mission pair.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Saga Of The Great Wolf (Master of Wolves — Encircling Jaws on the assault doctrine, +1 advance) and the inherited bench (Assault Brethren, Gladius Task Force, Gravis Linebreaker/Siege Force, Tacticus Attack Force) hold, but the saga tools are doctrine- and unit-gated. |
| Purge the Foe | Strong | Saga Of The Beastslayer (Legendary Slayers — Lethal Hits against Character/Monster/Vehicle) is the dedicated killer, with Devastator Brethren and Ironstorm Spearhead behind it. |
| Reconnaissance | Moderate | Only inherited Gauntlet Task Force / Stormlance Task Force plus the Wolf Scouts and Wulfen units; no chapter-specific recon detachment in 11e. |
| Priority Assets | Moderate | Champions Of Fenris (The Great Wolf Watches — Countercharge for characters) and Saga Of The Great Wolf hinge on Character units completing reactive objectives first; Gladius Task Force, Ironclad Champions, Terminator Storm Force and Tacticus Firestorm Force are the generalists. |
| Disruption | Strong | Stormlance Task Force (mounted +2" M) plus Thunderwolf Cavalry/Outrider units and Phobos Shadow/Shock Force support the harassment game. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->

### Chapter-Specific Detachments
<!-- ordered by DP -->

#### Champions Of Fenris (1DP → PRIORITY ASSETS)
- **Mechanics**: The Great Wolf Watches — ADEPTUS ASTARTES INFANTRY CHARACTERS get a Counter Charge ability usable once per battle round per unit (Heroic Intervention eligibility without consuming the stratagem's availability for other units). Stratagems include sticky objectives (Runes of Claiming) and FNP vs mortals on characters.
- **Rating**: Situational for Priority Assets
- **Synergies**: Wolf Guard Battle Leader / Wolf Priest-led forward units punishing enemy charges; Runes of Claiming locking an objective held by an Infantry unit.
- **Limits**: Counter Charge still costs CP unless discounted (research note); character-scope only; 1DP add-on.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-space-wolves (fetched); https://www.warhammer-community.com/en-gb/articles/2ekfivpk/new40k-download-new-space-marine-faction-packs-today/

#### Legends Of Saga And Song (1DP → TAKE AND HOLD)
- **Mechanics**: Loping Charge — ADEPTUS ASTARTES TERMINATOR units add +1 to charge rolls. Stratagems: mass Precision melee, opponent-command-phase battle-shock howl, reserve-bounce returning an unengaged Terminator unit to Strategic Reserves. Upgrades grant OC/Toughness.
- **Rating**: Situational for Take and Hold
- **Synergies**: Wolf Guard Terminators / Terminator Squad walls walking onto markers; Arjac Rockfist-led bricks.
- **Limits**: TERMINATOR keyword scope only; charge-roll modifier is not eligibility; 1DP add-on scope.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-space-wolves (fetched); https://www.warhammer-community.com/en-gb/articles/2ekfivpk/new40k-download-new-space-marine-faction-packs-today/

#### Veterans Of The Fang (1DP → DISRUPTION)
- **Mechanics**: Old Greymanes — Grey Hunters starting an action remain eligible to shoot; Grey Hunters may split into two 5-model units at deployment. Stratagems add sustained-or-lethal melee hits, action-after-move, detection-range debuff. Army restricted to SPACE WOLVES units.
- **Rating**: Situational for Disruption
- **Synergies**: Twin 5-man Grey Hunters units performing actions while threatening return fire; Eye of the Hunter enhancement turns one unit into an ignore-cover shooter.
- **Limits**: GREY HUNTERS keyword scope throughout; action-interaction effects have no stat expression; 1DP add-on.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-space-wolves (fetched); https://www.40k.app/factions/space-wolves/detachments/veterans-of-the-fang

#### Saga Of The Beastslayer (2DP → PURGE THE FOE)
- **Mechanics**: All ADEPTUS ASTARTES attacks gain LETHAL HITS vs CHARACTER/MONSTER/VEHICLE targets. Saga track: destroy enough such units (half the enemy army count, rounded up) and all attacks gain Lethal Hits vs everything.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Wulfen and Thunderwolf Cavalry chewing into monster/vehicle metas; massed bolt volume fishing for 6s into elite targets.
- **Limits**: Baseline buff strictly keyword-target-conditional; army-wide Lethal Hits only after the kill tally completes (late-game gate); lethal_hits withheld from modifiers for this reason.
- **_source**: https://www.tabletopbattles.com/detachment-focus-saga-of-the-beastslayer; https://www.40k.app/879/factions/space-wolves/detachments/saga-of-the-beastslayer

#### Saga Of The Bold (2DP → PRIORITY ASSETS)
- **Mechanics**: Heroes All — each SPACE WOLVES CHARACTER unit re-rolls one hit OR wound OR damage roll when shooting/fighting. Characters complete Boasts; three different Boasts done → every ADEPTUS ASTARTES unit re-rolls one of EACH category.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Multiple cheap characters (Wolf Guard Headtakers) each hunting their own Boast; Ragnar Blackmane spearheading.
- **Limits**: Per-unit reroll is single-die until the saga completes (earliest round 2 Command phase); completion depends on Boast feasibility vs the matchup; Birth of a Saga stratagem needed to extend CHARACTER keyword to non-characters.
- **_source**: https://www.tabletopbattles.com/detachment-focus-saga-of-the-bold

#### Saga Of The Great Wolf (2DP → TAKE AND HOLD)
- **Mechanics**: Master of Wolves — each Command phase select one Hunting Pack (each once per battle): Encircling Jaws (re-roll Advance and Charge), Hunter's Eye (+1 ranged hit rolls), Ferocious Strike (per-unit choice of Lethal Hits or Sustained Hits 1 in the Fight phase). Logan Grimnar allows one used pack to be reused.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Logan Grimnar doubling pack usage; Ferocious Strike turn timed with the army's big charge round.
- **Limits**: Each pack once per battle — sequencing decisions, nothing always-on; Hunter's Eye covers ranged only; reuse gated on Grimnar's survival.
- **_source**: https://www.tabletopbattles.com/detachment-focus-saga-of-the-great-wolf; https://spikeybits.com/40ks-new-saga-of-the-great-wolf-makes-grimnar-more-ferocious/

#### Saga Of The Hunter (2DP → DISRUPTION)
- **Mechanics**: Pack's Quarry — SPACE WOLVES melee attacks get +1 to hit if the target is within Engagement Range of another friendly ADEPTUS ASTARTES unit OR the attacker has more models. Melee kills build a Quarry tally (2/3/4 by battle size); completion adds +1 to wound.
- **Rating**: Moderate for Disruption (and Purge the Foe)
- **Synergies**: Blood Claws and Grey Hunters swarming tagged targets; Outrider/Fenrisian Wolves screening units setting up the outnumbering condition.
- **Limits**: Hit bonus dual-conditional (tagged or outnumbering) and SPACE WOLVES-units-only; wound bonus only after tally completion.
- **_source**: https://www.tabletopbattles.com/detachment-focus-saga-of-the-hunter; https://www.goonhammer.com/detachment-focus-saga-of-the-hunter

### Inherited From Space Marines Codex
<!-- shorter blocks; mechanics per _space-marines-shared.json, rated in SW context -->

#### Fulguris Task Force (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Skystrike — SPEEDER units ingress in Movement phase 1 (inherited from SM codex).
- **Rating**: Situational for Reconnaissance; ⚠️ shared-codex delta flags official sources listing DISRUPTION.
- **_source**: inherited:_space-marines-shared.json

#### Subversion Assets (1DP → DISRUPTION) — *inherited*
- **Mechanics**: Nowhere to Hide — Scout/Phobos detection manipulation (inherited from SM codex).
- **Rating**: Situational for Disruption — Wolf Scouts synergy; ⚠️ shared-codex delta flags official sources listing RECONNAISSANCE.
- **_source**: inherited:_space-marines-shared.json

#### Vengeful Hosts (1DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Imperator Unleashed — FLY INFANTRY re-roll hit 1s on ingress/charge turns (inherited from SM codex).
- **Rating**: Situational for Take and Hold — modest jump presence in roster. ⚠️ Research confidence LOW: objective/DP sourcing unconfirmed by fetched sources.
- **_source**: inherited:_space-marines-shared.json

#### Librarius Conclave (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Rotating Psychic Disciplines for PSYKER units (inherited from SM codex).
- **Rating**: Situational for Reconnaissance — Njal Stormcaller-led psyker density dependent.
- **_source**: inherited:_space-marines-shared.json

#### 1st Company Task Force (2DP → PURGE THE FOE) — *inherited*
- **Mechanics (10e record)**: Once-per-battle wound re-rolls vs the Oath target (inherited from SM codex).
- **Rating**: Situational for Purge the Foe — overlaps what the Saga detachments do more often.
- **_source**: inherited:_space-marines-shared.json

#### Anvil Siege Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: All ranged weapons gain HEAVY (+1 Wound stationary if already HEAVY) (inherited from SM codex).
- **Rating**: Weak for Take and Hold — gunline theme against a melee/mounted chapter identity.
- **_source**: inherited:_space-marines-shared.json

#### Bastion Task Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Battleline act after Advance/Fall Back + Auspex scan rerolls (inherited from SM codex).
- **Rating**: Situational for Take and Hold — Grey Hunters/Intercessor flood playstyle possible but off-brand.
- **_source**: inherited:_space-marines-shared.json

#### Firestorm Assault Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: ASSAULT on all ranged, +1 Strength within 12" (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — suits close-range hybrid pushes; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Headhunter Task Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Tank Ace vehicles: flat 6" Advance, stationary damage re-rolls (inherited from SM codex).
- **Rating**: Situational for Priority Assets — vehicle roster thin beyond Gladiator/Repulsor hulls.
- **_source**: inherited:_space-marines-shared.json

#### Ironstorm Spearhead (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: One hit/wound/damage re-roll per unit per phase (inherited from SM codex).
- **Rating**: Weak for Take and Hold — single-die insurance mismatch; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Orbital Assault Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: 2-4 units gain Deep Strike + arrival-turn wound-1s rerolls (inherited from SM codex).
- **Rating**: Moderate for Take and Hold — Drop Pod/Wolf Guard delivery complements saga pressure.
- **_source**: inherited:_space-marines-shared.json


#### Vanguard Spearhead (2DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Benefit of Cover vs ranged attacks from beyond 12" (inherited from SM codex).
- **Rating**: Moderate for Reconnaissance — best inherited option for Wolf Scout infiltration playstyles.
- **_source**: inherited:_space-marines-shared.json

#### Armoured Speartip (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Post-disembark follow-up moves from moved Transports (inherited from SM codex).
- **Rating**: Situational for Take and Hold — Land Raider Crusader delivery of Wolf Guard Terminators.
- **_source**: inherited:_space-marines-shared.json

#### Ceramite Sentinels (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Terrain-based hit/wound-1s rerolls + Entrenched status (inherited from SM codex).
- **Rating**: Situational for Take and Hold — static theme, off-brand.
- **_source**: inherited:_space-marines-shared.json

#### Gladius Task Force (3DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Rotating Combat Doctrines, each once per battle (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — generalist fallback; Encircling Jaws-style mobility exists natively in the sagas.
- **_source**: inherited:_space-marines-shared.json


#### Assault Brethren (1DP → TAKE AND HOLD)
- **Mechanics**: Assault Mastery — select the Assault Doctrine one additional time per battle.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Assault doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Deathwatch Support (1DP → DISRUPTION)
- **Mechanics**: Inherited cross-chapter package.
- **Rating**: Situational for Disruption
- **Synergies**: Niche.
- **Limits**: Minimal bespoke rules.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Devastator Brethren (1DP → PURGE THE FOE)
- **Mechanics**: Devastator Mastery — select the Devastator Doctrine one additional time per battle.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Firepower doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Gauntlet Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Combined Deployment — transport shoots marks target assailed; disembarked ADEPTUS ASTARTES get [Sustained Hits 1] vs it.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Transport delivery.
- **Limits**: Conditional timing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Gravis Linebreaker Force (1DP → TAKE AND HOLD)
- **Mechanics**: Walking Fortress — Gravis moved Normal: ranged lose [Heavy] and get +1 to hit.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Aggressive Gravis.
- **Limits**: Gravis-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Gravis Siege Force (1DP → TAKE AND HOLD)
- **Mechanics**: Indomitable Defence — while in range of objective, attacks with S>T vs Gravis have -1 to wound.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Gravis anchoring.
- **Limits**: Objective-range, S>T only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Ironclad Champions (1DP → PRIORITY ASSETS)
- **Mechanics**: Enduring Vengeance — Dreadnoughts re-roll hit rolls of 1.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Dreadnought lists.
- **Limits**: Dreadnought-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Phobos Shadow Force (1DP → DISRUPTION)
- **Mechanics**: Shadow Masters — Phobos/Scout shoot then don't prevent hidden or make D6" move (no charge until end).
- **Rating**: Moderate for Disruption
- **Synergies**: Phobos recon.
- **Limits**: Scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Phobos Shock Force (1DP → DISRUPTION)
- **Mechanics**: Vanguard Ambushers — end of Movement if hidden, Phobos attacks re-roll wound rolls of 1 until end of turn.
- **Rating**: Moderate for Disruption
- **Synergies**: Hidden Phobos.
- **Limits**: Requires hidden.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Stormlance Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Lightning-Fast Strike — Mounted/Speeder have +2" Move.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Bike/Speeders.
- **Limits**: Mounted/Speeder only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Tactical Brethren (1DP → PRIORITY ASSETS)
- **Mechanics**: Tactical Mastery — select Tactical Doctrine one additional time per battle.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Tacticus Attack Force (1DP → TAKE AND HOLD)
- **Mechanics**: Wrath of the Chapter — Tacticus units can re-roll advance rolls.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Tacticus advancing.
- **Limits**: Tacticus-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Tacticus Firestorm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Codex Fire-Patterns — Tacticus [Rapid Fire] at max range count as Rapid Fire.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Tacticus rapid fire.
- **Limits**: Tacticus/RF only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

#### Terminator Storm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Death Blow — Terminator units have +1 to charge rolls.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Terminator assaults.
- **Limits**: Terminator-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-wolves/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* Champions Of Fenris' Runes of Claiming (sticky objective at end of Movement phase, 1CP) is the named Take-and-Hold scoring tool. Legends Of Saga And Song's Wings of the Blizzard reserve-bounce gives Terminators a redeploy exit. In Saga Of The Great Wolf, Grimnar's Command (activate a pack for one unit only) stretches the once-per-battle packs; Unrelenting Hunters grants fall-back-and-charge (advance-and-charge for Space Wolves units) as a CP burst. All CP-gated, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Space Wolves run a two-act game, but in 11e the acts are shorter and the tools are named: the chapter ships two Sagas — Saga Of The Great Wolf (2DP, Take and Hold) and Saga Of The Beastslayer (1DP, Purge the Foe) — and everything else is inherited Astartes (Gladius Task Force, Terminator Storm Force, Champions Of Fenris, Ironstorm Spearhead, Stormlance, Tacticus x2, Gauntlet, Phobos x2, Devastator/Assault/Tactical Brethren). The army rule layer is the shared Combat Doctrines plus the chapter's Curse of the Wulfen, so the Saga's payoff is what the detachment choice is really buying. The correct pattern is to pick the Saga whose completion condition matches the mission pair, then fill the list with the inherited package that covers the other disposition: kill-heavy pairs take Saga Of The Beastslayer, objective pairs take Saga Of The Great Wolf, and the 1DP doctrine packages (Assault/Devastator/Tactical Brethren) are the cheap way to add a second doctrine without a Saga. Weak spots: Disruption and Reconnaissance run on inherited tools only (Phobos Shadow/Shock Force, Stormlance, Gauntlet), and mounted melee (Thunderwolf Cavalry) is the cleanest melee package without a chapter detachment rule to drive it.