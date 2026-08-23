# Expert File: Emperor's Children

## Faction Identity

- **Full name**: Emperor's Children (BSData catalogue faction: "Emperor's Children")
- **Faction keyword**: `Faction: Emperor's Children`; daemon-aligned units carry `Faction: Legions of Excess`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Per the Mercurial Host research note, the army rule supports advance-and-act interactions (units doing things in turns they Advanced); exact army-rule text is not documented in this corpus [unverified name/mechanics]. Daemon allies (Legions of Excess: Daemonettes, Fiends, Seekers, Keeper Of Secrets, Shalaxi Helbane) integrate via Carnival Of Excess.
- **Sub-faction keywords**: `Faction: Legions of Excess` (daemon units)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/emperors-children.json
(2026-08-23, packs v1.1). 10 detachments, all faction-specific.

### Army Rule
- **Advance-and-act framework**: the corpus documents that the faction army rule interacts with Advance moves (Mercurial Host's Advance-reroll "stacks with the faction's advance-and-act army rule"); the rule's exact text is not restated anywhere in the research files [unverified].
- **Play pattern** *(interpretation)*: fast melee/flavour army built on charge-triggered buffs — nearly every detachment pays out on the turn a unit charges, disembarks, or advances, so list construction revolves around delivering the right unit into combat on round 2-3.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Situational | Only Elegant Brutes touches objective play (+1 charge rolls for arriving Terminators); elite melee armies trade poorly holding ground. |
| Purge the Foe | Strong | Court Of The Phoenician (+1S/+1AP melee when charging), Peerless Bladesmen (chosen crit effects on charges) and Slaanesh'S Chosen wound rerolls all target kill missions. |
| Reconnaissance | Moderate | Mercurial Host advance reliability and Frenzied Host post-move Strength support fast board reach, but no scoring-action tools documented. |
| Priority Assets | Moderate | Peerless Bladesmen headline; Coterie Of The Conceited has high ceiling but pays out late and risks the Warlord. |
| Disruption | Moderate | Carnival Of Excess aura pressure, Rapid Evisceration transport loops and Spectacle Fights First grind engagements but lack denial mechanics. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Elegant Brutes (1DP → TAKE AND HOLD)
- **Mechanics**: Friendly Emperor's Children Terminator units get +1 to Charge rolls on the turn they are set up (reserves/deep strike arrivals).
- **Rating**: Situational for Take and Hold
- **Synergies**: Chaos Terminators arriving mid-board and charging straight onto markers.
- **Limits**: Turn-of-setup only; TERMINATOR scope; 1DP add-on with no other effect.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-emperors-children

#### Frenzied Host (1DP → RECONNAISSANCE)
- **Mechanics**: EC BATTLELINE units' attacks gain +1 Strength until end of turn after an Advance or Fall Back move (shooting and melee). HOST tag: cannot combine with other HOST detachments.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Infractors/Tormentors advancing and shooting at boosted Strength while crossing to objectives.
- **Limits**: Battleline scope; strictly conditional on moving; HOST tag restricts combination.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-emperors-children

#### Spectacle Of Slaughter (1DP → DISRUPTION)
- **Mechanics**: Friendly Flawless Blades units have Fights First. Enhancements add +2" Movement or snap-shot targeting immunity.
- **Rating**: Situational for Disruption
- **Synergies**: Flawless Blades duelling into enemy charges without losing initiative.
- **Limits**: Single-unit-type scope; reviewers note reduced Fights First impact under 11th-edition fight sequencing; 1DP add-on.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-emperors-children

#### Carnival Of Excess (2DP → DISRUPTION)
- **Mechanics**: Marine units within 6" of friendly Legions of Excess daemon units (and vice versa) gain Sustained Hits 1; units already having Sustained Hits score critical hits on 5+. Grants a Legions of Excess daemon ally allowance.
- **Rating**: Moderate for Disruption
- **Synergies**: Noise Marines shooting alongside Daemonettes/Seekers screens; Lucius The Eternal-led blocks inside the aura.
- **Limits**: Proximity-dependent aura (6 inches both ways); crit-on-5+ upgrade unmodeled; ally allowance unmodeled.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

#### Court Of The Phoenician (2DP → PURGE THE FOE)
- **Mechanics**: In the Fight phase, units that made a Charge move this turn improve melee Strength and AP by 1. Fulgrim gains CP discounts on two named stratagems (Sinuous Breach / Prideful Superiority). January 2026 update removed one targeting restriction on the buff.
- **Rating**: Strong for Purge the Foe **on charge turns**
- **Synergies**: Every charge in the book — Flawless Blades, Daemon Prince Of Slaanesh With Wings, Seekers — hits harder on its charge turn; Fulgrim leading from the front compounds it.
- **Limits**: Melee only; strictly charge-turn conditional (no bonus on counter-attack turns without a charge); CP discount requires Fulgrim alive.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

#### Mercurial Host (2DP → RECONNAISSANCE)
- **Mechanics**: Army-wide re-roll of Advance rolls, stacking with the faction's advance-and-act army rule for highly reliable mobility.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Fast battleline (Infractors/Tormentors) and Seeker cavalry consistently reaching distant markers while still acting.
- **Limits**: Reliability buff, not distance or eligibility; no combat modifier.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

#### Peerless Bladesmen (2DP → PRIORITY ASSETS)
- **Mechanics**: Whenever a unit charges, its attacks gain Lethal Hits OR Sustained Hits 1 — player's choice per unit per charge.
- **Rating**: Strong for Priority Assets
- **Synergies**: High-attack duelists (Flawless Blades, Lord Exultant retinues) choosing Lethal vs multi-wound elites and Sustained vs hordes.
- **Limits**: Mutually exclusive choice per unit; charge-turn conditional only; no defensive component.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

#### Rapid Evisceration (2DP → DISRUPTION)
- **Mechanics**: All models re-roll hit rolls of 1 and wound rolls of 1 on the turn they disembark from a transport; December 2025 dataslate extended the benefit to the transport itself.
- **Rating**: Moderate for Disruption
- **Synergies**: Rhino-delivered Noise Marines / Flawless Blades alpha turns; transport shooting also buffed post-dataslate.
- **Limits**: Disembark-turn conditional; requires building around transports.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

#### Slaanesh'S Chosen (2DP → PURGE THE FOE)
- **Mechanics**: Internal Rivalries — all units ignore modifiers to Movement and to Advance/Charge rolls. At battle start the Warlord's unit becomes Favoured Champions (full wound re-rolls); whenever another Character unit destroys an enemy unit the keyword transfers to it.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Multiple character-led blades hunting kills to capture and pass the Favoured Champions buff.
- **Limits**: Full wound re-rolls restricted to one Character unit at a time (transfers on kill); modifier-immunity layer covers movement only; ⚠️ research confidence MEDIUM.
- **_source**: https://www.goonhammer.com/detachment-focus-slaaneshs-chosen/

#### Coterie Of The Conceited (3DP → PRIORITY ASSETS)
- **Mechanics**: Each battle round the Warlord pledges how many enemy units will be destroyed; meeting/beating the pledge earns Pact Points, missing costs the Warlord D3 mortal wounds. Tiers: 1 point = re-roll hit 1s; 3 = re-roll wound 1s; 5 = melee weapons gain Lethal Hits and Sustained Hits 1; 7 = criticals on 5+ (per research note).
- **Rating**: Situational for Priority Assets
- **Synergies**: Aggressive multi-unit kill plans feeding early Pact Points; Daemon Prince Of Slaanesh With Wings clearing chaff to bank points.
- **Limits**: Nothing active at game start — fully earned progression; pledge failure wounds the Warlord; top tiers realistically late-game; every buff tier conditional.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Emperor%27s_Children

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* Spectacle Of Slaughter's enhancements (+2" Movement, snap-shot immunity) are the named unit-scoped upgrades; Court Of The Phoenician's value rises with Fulgrim alive thanks to discounted Sinuous Breach / Prideful Superiority stratagems. No broader enhancement consensus emerges from the sources — treat specific picks as unresolved pending primary-source verification.

### Overall Army Play Pattern
*(interpretation)* Emperor's Children play a delivery game: almost every meaningful buff triggers on the charge, the disembark, or the advance, so the list is built around getting one or two elite blades into the decisive fight on round 2-3 with their trigger armed — Court Of The Phoenician or Peerless Bladesmen as the main detachment, Rapid Evisceration or Spectacle Of Slaughter layered where transports or duellists lead. The army punishes itself structurally elsewhere: no detachment generates objective stickiness or scoring actions (Take and Hold is the weakest disposition), and the one escalation package (Coterie Of The Conceited) demands perfect kill tempo while gambling the Warlord's wounds. Expect a fragile, high-tempo army whose games end quickly in one direction or the other.
