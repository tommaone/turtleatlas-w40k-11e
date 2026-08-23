# Necrons

## Faction Identity

- **Full name**: Necrons (BSData catalogue: "Necrons")
- **Faction keyword**: NECRONS
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Reanimation Protocols — at the end of your Command phase, each friendly unit with the ability on the battlefield activates it and heals D3 wounds (paraphrased from bsdata/Necrons.json army-rule entry)
- **Keywords every unit should carry**: NECRONS; most units carry Reanimation Protocols
- **Sub-faction keywords** (per research corpus): NOBLE, CRYPTEK, CANOPTEK, DESTROYER CULT, DYNASTY, HYPERCRYPT, TOMB BLADES, FLAYED ONES, LYCHGUARD, TRIARCH

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/necrons.json (2026-08-23, packs v1.1). Army rule paraphrase grounded in bsdata/Necrons.json.

### Army Rule
- **Reanimation Protocols**: end of your Command phase, every on-board unit with the ability heals D3 wounds. (This assessment covers only the army-rule baseline as grounded in BSData; datasheet-level modifiers to the roll are out of scope here.)
- **Play pattern** *(interpretation)*: passive attrition baked into every list — opponents must overkill units to remove them, which inflates the effective durability of cheap battleline. Detachments that add positioning tricks (Hypercrypt) or hit buffs (Awakened Dynasty) layer on top of a faction that already wins long games.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Three TaH detachments including Awakened Dynasty's +1 to Hit led-units and Canoptek Court's objective-zone Power Matrix; Reanimation makes holding bodies self-repairing. |
| Purge the Foe | Moderate | Annihilation Legion (Destroyer Cult focus) and Cursed Legion (+2S spread buff) are real damage packages but unit-scoped. |
| Reconnaissance | Situational | Hypercrypt redeployment and Skyshroud Tomb Blade deep strike are mobility tricks, not scoring engines. |
| Priority Assets | Moderate | Starshatter Arsenal buffs objective-proximate hitting; Cryptek Conclave flexible shooting; inherent durability protects assets passively. |
| Disruption | Situational | Obeisance Phalanx single-mark debuff-focus and Pantheon of Woe monster auras are narrow; no screening/action-denial tools in corpus. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Hand Of The Dynasty (1DP → TAKE AND HOLD)
- **Mechanics**: IMMORTALS and NECRON WARRIORS ranged attacks gain [ASSAULT]; when such a unit Advances it remains eligible to start an action. DYNASTY-tagged; exclusive with other DYNASTY detachments.
- **Rating**: Situational for Take and Hold
- **Synergies**: Immortals, Necron Warriors — battleline that repositions and still shoots or starts actions.
- **Limits**: two-unit scope; ASSAULT unmodeled; action eligibility after Advance has no vocabulary key; tag exclusivity.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Skyshroud Spearhead (1DP → RECONNAISSANCE)
- **Mechanics**: Friendly TOMB BLADES gain Deep Strike; shooting in the turn of ingress gives +1 to Hit.
- **Rating**: Situational for Reconnaissance / Disruption
- **Synergies**: Tomb Blades — fast jetbikes appearing on flanks.
- **Limits**: single-unit-type scope; hit bonus only on ingress turn; Deep Strike unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### The Phaeron'S Armoury (1DP → PRIORITY ASSETS)
- **Mechanics**: Friendly TITANIC FLY units get +6" Move characteristic. HYPERCRYPT-tagged; exclusive with other HYPERCRYPT detachments.
- **Rating**: Weak for most dispositions; Situational for Priority Assets only in C'tan-heavy lists
- **Synergies**: Transcendent C'Tan and other Titanic Fly models in config characters.json.
- **Limits**: applies ONLY to TITANIC FLY units (corpus flags explicitly); value scales directly with how many such units you own — likely zero or one in most lists; tag exclusivity.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Annihilation Legion (2DP → PURGE THE FOE)
- **Mechanics**: DESTROYER CULT and FLAYED ONES units may re-roll charge rolls and add 1 to the charge roll if any target is Below Half-strength; DESTROYER CULT ranged attacks vs the CLOSEST eligible target get +1 AP.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Skorpekh Destroyers, Lokhust Destroyers, Lokhust Heavy Destroyers, Ophydian Destroyers, Flayed Ones; Skorpekh Lord leading the push.
- **Limits**: +1 AP is position-conditional (closest eligible target only — corpus flags it was provisionally mis-modeled as flat); charge bonuses are rerolls/+1, not auto-successes.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Cryptek Conclave (2DP → PRIORITY ASSETS)
- **Mechanics**: CRYPTEK ranged weapons gain [ASSAULT]; each time a CRYPTEK unit is selected to shoot choose ONE for the phase: ANTI-INFANTRY 3+, ANTI-MOUNTED 4+, ASSAULT, HEAVY, or IGNORES COVER.
- **Rating**: Situational for Priority Assets / Purge the Foe
- **Synergies**: Plasmancer, Illuminor Szeras, Chronomancer-led shooting characters.
- **Limits**: pick-one-per-phase choice system — never stacked; character-model scope means tiny attack counts unless leading units inherit (corpus does not state inheritance — unverified); none modeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Cursed Legion (2DP → PURGE THE FOE)
- **Mechanics**: DESTROYER CULT weapons get +2 Strength. First time each turn a DESTROYER CULT unit destroys a unit or drops one Below Half-strength, all other friendly NECRONS (excluding DESTROYER CULT, MONSTER, TITANIC) also get +2 Strength until end of turn.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Destroyer wing plus Immortals/Warriors melee follow-up... note: spread buff covers ALL non-excluded attacks, ranged included.
- **Limits**: +2S does not map to modifier vocabulary (unmodeled); spread trigger fires only ONCE per turn and needs a kill/break first; MONSTER/TITANIC excluded from the spread.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Hypercrypt Legion (2DP → RECONNAISSANCE)
- **Mechanics**: At end of opponent's turn, remove unengaged friendly NECRONS units into Strategic Reserves (max 1/2/3 units by battle size). Enables repeated redeployment.
- **Rating**: Situational for Reconnaissance / Take and Hold
- **Synergies**: anything expensive enough to dodge an alpha strike — C'Tan shards stepping out of danger then returning.
- **Limits**: removal trick outside modifier vocabulary; battle-size-capped withdrawal count; units removed are absent from scoring while in Reserve.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Obeisance Phalanx (2DP → DISRUPTION)
- **Mechanics**: In your Command phase mark one enemy unit; until your next Command phase, NOBLE, LYCHGUARD and TRIARCH units add 1 to Wound rolls attacking that marked unit.
- **Rating**: Situational for Disruption / Purge the Foe
- **Synergies**: Overlord-led Lychguard, Triarch Praetorians — a focused kill column.
- **Limits**: ONE marked enemy at a time; three-keyword attacker scope; +1 to wound only (no hit/AP help); single-target focus wastes the buff against horde boards.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Pantheon Of Woe (2DP → DISRUPTION)
- **Mechanics**: NECRONS MONSTER units carry Distortion Fields: enemy units within 6" are 'unravelling' — all attacks targeting an unravelling unit improve AP by 1. Each phase, each MONSTER may voluntarily take 3 mortal wounds to extend the aura to 9" for that phase. MONSTER units cost extra points and carry Necrodermal Binding restrictions.
- **Rating**: Situational for Disruption / Purge the Foe
- **Synergies**: C'Tan shards (Deceiver, Nightbringer, Void Dragon) and Transcendent C'Tan anchoring mid-board kill zones.
- **Limits**: aura range-gated (6", 9" paid in mortal wounds); MW cost compounds with Necrodermal Binding restrictions; extra points cost on MONSTER units; none modeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Awakened Dynasty (3DP → TAKE AND HOLD)
- **Mechanics**: While a NECRONS CHARACTER model is leading a unit, every attack made by models in that unit adds 1 to the Hit roll.
- **Rating**: Strong for Take and Hold / Purge the Foe — the condition is a list-building choice, not a battlefield gamble: build every combat block around a leader and the buff is effectively always-on
- **Synergies**: Overlord/Royal Warden-led Warriors, Immortals blocks; Skorpekh Lord + Skorpekh Destroyers; Plasmancer gun lines.
- **Limits**: +1 to hit ONLY while led (unled units get nothing); leader attachment caps how many units benefit; full-budget 3DP cost; leadership-state conditional flagged in corpus as unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Canoptek Court (3DP → TAKE AND HOLD)
- **Mechanics**: Defines a 'Power Matrix' zone: deployment zone always included; No Man's Land and enemy deployment zone join during phases where you control at least half of that area's objectives. CRYPTEK/CANOPTEK units re-roll Hit rolls of 1; wholly within the Matrix they re-roll ALL Hit rolls instead.
- **Rating**: Moderate for Take and Hold (zone control IS the detachment's win condition and its buff gate simultaneously)
- **Synergies**: Canoptek Wraiths, Canoptek Scarab Swarms, Canoptek Spyders, Tomb Crawlers, Macrocytes plus Cryptek support.
- **Limits**: full-reroll upgrade requires being WHOLLY within a zone that shrinks if you lose board control — feedback loop can starve the buff exactly when losing; keyword scope excludes standard Dynasty infantry; 3DP full-budget.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

#### Starshatter Arsenal (3DP → PRIORITY ASSETS)
- **Mechanics**: NECRONS models (excluding MONSTERS) add 1 to Hit rolls targeting a unit within range of an objective marker; ranged weapons of VEHICLE and MOUNTED models (excluding TITANIC) gain [ASSAULT].
- **Rating**: Moderate for Priority Assets / Take and Hold
- **Synergies**: vehicle/mounted gun platforms pushing up; any shooter contesting markers.
- **Limits**: +1 to hit is position-conditional (objective proximity — flagged unmodeled); MONSTER exclusion removes C'Tan from the hit buff; ASSAULT unmodeled; full-budget 3DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/necrons/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents no individual enhancement/stratagem names for this faction)*
- The research corpus does NOT catalogue individual stratagems or enhancements for Necrons — no picks offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: Necron assessments start from free durability: Reanimation Protocols heals every protocol-bearing unit D3 at the end of each Command phase before any detachment rule is counted, so the faction's baseline expectation is winning wars of attrition and grinding objectives. On top of that floor, the corpus shows two viable spines. The leader-based spine (Awakened Dynasty) trades 3DP for an effectively always-on +1 to hit across leader-built combat blocks — simple, robust, and the closest thing the faction has to unconditional power. The zone-based spine (Canoptek Court, Starshatter Arsenal) ties buffs to board position, which rewards good play but introduces failure loops where losing the board removes the buffs needed to retake it. Everything else in the corpus is scoped utility: Destroyer Cult damage packages, Hypercrypt dodging, single-mark focus fire. The consistent limitation is that nearly every offensive rule is conditional (position, leadership, target selection), so raw engine numbers systematically overstate what a careless Necron list actually outputs.
