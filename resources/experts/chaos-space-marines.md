# Expert File: Chaos Space Marines

## Faction Identity

- **Full name**: Chaos Space Marines (BSData catalogue: "Chaos - Heretic Astartes - Chaos Space Marines")
- **Faction keyword**: `Faction: Heretic Astartes`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: **Dark Pacts** — units make a pact (Leadership test) for phase-long benefits, with failure costs; documented throughout the corpus (Cabal Of Chaos keys buffs to successful pacts; Renegade Warband explicitly loses Dark Pacts and Cults of the Dark Gods). Cults of the Dark Gods sub-allegiances exist but their effects are not documented in this corpus [unverified].
- **Sub-faction keywords**: Chaos marks (Khorne/Tzeentch/Nurgle/Slaanesh/Chaos Undivided) appear via Pactbound Zealots' muster requirements.

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/chaos-space-marines.json
(2026-08-23, packs v1.1). 17 detachments, all faction-specific (no SM codex
inheritance).

### Army Rule
- **Dark Pacts**: units take a pact for phase benefits at Leadership-test risk; multiple detachments key bonuses off *successful* pacts (Cabal Of Chaos, Soulforged Warpack, Pactbound Zealots).
- **Play pattern** *(interpretation)*: the detachment choice sets the army's tempo axis — infiltration pressure (Deceptors), battle-shock attrition (Nightmare Hunt/Dread Talons), or blanket stat augmentation (Creations Of Bile); several detachments trade away Dark Pacts entirely, which is itself a list-building cost.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Fellhammer Siege-Host hardens the wall and Veterans Of The Long War deletes one designated threat, but no native sticky-objective mechanic exists. |
| Purge the Foe | Strong | Creations Of Bile augments every Heretic Astartes infantry model; Soulforged Warpack boosts daemon vehicles into kill turns. |
| Reconnaissance | Strong | Renegade Raiders gives army-wide ASSAULT plus AP+1 near objectives — mobile mid-range scoring fire. |
| Priority Assets | Moderate | Pactbound Zealots is powerful but mark-mandated; Arkifane/Warband options are scope-narrow. |
| Disruption | Strong | Deceptors infiltrates up to 6 units; Nightmare Hunt stacks hit/wound bonuses onto a battle-shock engine. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Cabal Of Chaos (1DP → DISRUPTION)
- **Mechanics**: After a successful Dark Pact: non-Daemon PSYKER infantry ranged attacks gain +1 Strength that phase; non-Khorne DAEMON PRINCE melee attacks gain +2 Strength and +1 AP that phase.
- **Rating**: Situational for Disruption
- **Synergies**: Sorcerer / Master Of Possession-led psyker blocks; Heretic Astartes Daemon Prince With Wings melee spikes.
- **Limits**: Buffs strictly conditional on a successful pact that phase; Daemon Prince half excludes KHORNE models; psyker/character scope only.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-chaos-space-marines

#### Devotees Of Destruction (1DP → PRIORITY ASSETS)
- **Mechanics**: HAVOCS and OBLITERATORS ranged attacks gain HEAVY-style bonus: +1 to hit if the unit moved ≤3 inches and was not set up from Reserves this turn.
- **Rating**: Situational for Priority Assets
- **Synergies**: Havocs gunlines holding backfield markers.
- **Limits**: Two-unit scope only; condition conflicts with Obliterators deep-striking (bonus unavailable on arrival turn per research note).
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-chaos-space-marines

#### Murdertalon Raiders (1DP → RECONNAISSANCE)
- **Mechanics**: Friendly INFANTRY FLY units re-roll hit rolls of 1 vs Battle-shocked or Below-Half-strength targets; such targets also get -1 to hit against friendly INFANTRY FLY units. NIGHTMARE tag (cannot combine with Nightmare Hunt).
- **Rating**: Situational for Reconnaissance
- **Synergies**: Raptors / Warp Talons diving wounded or shaken units.
- **Limits**: INFANTRY FLY scope only; offensive reroll target-conditional; ⚠️ merged objective RECONNAISSANCE conflicts with official sources listing PURGE THE FOE.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-chaos-space-marines

#### Chaos Cult (2DP → PRIORITY ASSETS)
- **Mechanics**: Desperate Pact for DAMNED units (Cultist Mob, Traitor Guard, Fellgor Beastmen): +2" Move and +2 to Charge rolls for the phase, failed Leadership test first inflicts D3 mortal wounds. Excludes Reserves arrivals.
- **Rating**: Situational for Priority Assets
- **Synergies**: Mass Cultist Mob boards rushing markers; Traitor Enforcer keeping leadership tests honest.
- **Limits**: DAMNED-keyword scope; self-damaging on failure; no benefit on reserve-arrival turns.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/chaos-cult

#### Cult Of The Arkifane (2DP → PRIORITY ASSETS)
- **Mechanics**: HERETIC ASTARTES VEHICLES gain DAEMON keyword; VEHICLES, LORD DISCORDANT and VASHTORR units gain SOUL FORGE keyword; all SOUL FORGE units have a 5+ invulnerable save.
- **Rating**: Situational for Priority Assets
- **Synergies**: Lord Discordant On Helstalker and Vashtorr The Arkifane-centred armour columns surviving focused fire.
- **Limits**: Keyword-scope only (vehicles/Discordant/Vashtorr) — infantry never benefit; DAEMON grant matters only via external synergies.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/cult-of-the-arkifane

#### Dread Talons (2DP → DISRUPTION)
- **Mechanics**: In the opponent's Command phase Battle-shock step, damaged enemy units within 12" of your HERETIC ASTARTES units test Battle-shock at -1; affected units skip other Battle-shock tests that phase.
- **Rating**: Situational for Disruption
- **Synergies**: Wide Legionaries/Raptors fronts tagging everything so the aura reaches; pairs conceptually with Nightmare Hunt mechanics but stands alone here.
- **Limits**: Morale effects only until Battle-shock converts to OC/action loss; requires damaged targets; opponent-facing dice.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/dread-talons

#### Deceptors (2DP → DISRUPTION)
- **Mechanics**: At battle formation select up to 3 LEGIONARIES and up to 3 CULTIST MOB units (Strike Force scale); those units plus attached non-Epic-Hero Characters gain Infiltrators for the battle.
- **Rating**: Moderate for Disruption
- **Synergies**: Six infiltrating blocks flooding midfield deployment zones before turn 1; Chaos Lord attachments making each blob a real threat.
- **Limits**: Deployment-phase effect only; unit-count cap scales with battle size; no combat modifier once deployed.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/deceptors

#### Fellhammer Siege-Host (2DP → TAKE AND HOLD)
- **Mechanics**: Iron Fortitude — ranged attacks targeting a HERETIC ASTARTES unit (excluding DAMNED) subtract 1 from the wound roll when attacker Strength exceeds the target's Toughness.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Plague-marine-equivalent durable walls: Chosen/Terminator bricks on objectives shrugging off high-Strength ranged fire.
- **Limits**: Defensive reduction conditional on S>T (irrelevant vs small arms); ranged attacks only; no offensive component.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/fellhammer-siege-host

#### Nightmare Hunt (2DP → DISRUPTION)
- **Mechanics**: Four-part rule: forced Battle-shock tests at -1 for damaged enemies within 12" (opponent's Command phase); HERETIC ASTARTES attacks get +1 to Hit vs Below-Half-strength targets and +1 to Wound vs Battle-shocked targets; Battle-shocked attackers get -1 to Hit vs your units. NIGHTMARE tag.
- **Rating**: Moderate for Disruption
- **Synergies**: Raptor/Warp Talon harassment creating the damaged/battle-shocked states the bonuses feed on; Haarken Worldclaimer-led vanguards.
- **Limits**: Both offensive bonuses target-state-conditional; morale layer is opponent-dice dependent; NIGHTMARE tag excludes Murdertalon Raiders.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/nightmare-hunt

#### Renegade Warband (2DP → PRIORITY ASSETS)
- **Mechanics**: Army loses Dark Pacts and Cults of the Dark Gods; all HERETIC ASTARTES ranged weapons gain ASSAULT. Vendetta: designate an enemy unit each Command phase — your attacks vs it re-roll hit rolls. Twisted Doctrine: pass a Battle-shock test after moving to gain fall-back-shoot/charge or advance-and-charge eligibility for the turn.
- **Rating**: Situational for Priority Assets
- **Synergies**: Mark-free mixed legions wanting ASSAULT mobility without Pactbound's muster constraints.
- **Limits**: Loses the baseline army rule — a real offensive utility cut (research flags it as unmodeled negative); Vendetta reroll single-target; Twisted Doctrine eligibility gated on passing tests.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/renegade-warband

#### Soulforged Warpack (2DP → TAKE AND HOLD)
- **Mechanics**: HERETIC ASTARTES DAEMON VEHICLE units invoking a contract via Dark Pact: -1 to that Leadership test, then +1 to Wound on ranged attacks and +2 Attacks on melee for the phase.
- **Rating**: Situational for Take and Hold
- **Synergies**: Forgefiend/Maulerfiend-class daemon engines pushing through midfield with Vashtorr support.
- **Limits**: DAEMON VEHICLE scope only; buff requires a successful pact invocation each time; ⚠️ merged objective TAKE AND HOLD conflicts with official sources listing PURGE THE FOE.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/soulforged-warpack

#### Veterans Of The Long War (2DP → TAKE AND HOLD)
- **Mechanics**: Focus of Hatred — at each Command phase designate one enemy unit; until your next Command phase, HERETIC ASTARTES attacks (excluding DAMNED models) re-roll Hit rolls against it.
- **Rating**: Situational for Take and Hold
- **Synergies**: Obliterators / Havocs deleting one priority hull or character per turn.
- **Limits**: Full rerolls apply only to the single designated target (re-designatable each round); no effect on the rest of the army's accuracy.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/veterans-of-the-long-war

#### Warpstrike Champions (2DP → DISRUPTION)
- **Mechanics**: Warp Portals — at end of the opponent's turn remove up to 2 (Strike Force) TERMINATOR, OBLITERATORS or MUTILATORS units into Strategic Reserves for later redeployment.
- **Rating**: Situational for Disruption
- **Synergies**: Chaos Terminator Squad teleport-hopping between threats; Obliterators repositioning to fresh angles.
- **Limits**: Redeploy tempo only — no combat modifier; cap scales with battle size; units in Engagement Range excluded.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/warpstrike-champions

#### Huron'S Marauders (3DP → DISRUPTION)
- **Mechanics**: Each Command phase pick one mode for all HERETIC ASTARTES INFANTRY until next Command phase: Huron's Elite (+1 to Hit on all attacks) OR Mobile Marauders (shoot and charge after Falling Back). Units visible to Huron Blackheart get both.
- **Rating**: Moderate for Disruption
- **Synergies**: Huron Blackheart positioned centrally turning the pick-one into pick-two for large portions of the board.
- **Limits**: Choice-based — normally one mode at a time; both-modes state depends on Huron's survival and positioning; INFANTRY scope.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/hurons-marauders

#### Creations Of Bile (3DP → PURGE THE FOE)
- **Mechanics**: Every HERETIC ASTARTES INFANTRY model (excluding DAMNED) gets one fixed battle-long augmentation chosen or rolled from six: +1 melee Attacks, +2" Move, +1 WS, +1 T, +1 melee S, or +1 BS. Fabius Bile as Warlord may re-roll the random dice.
- **Rating**: Strong for Purge the Foe
- **Synergies**: Legionaries/Possessed/Chosen bodies with tailored stat bumps; Fabius Bile guaranteeing the rolls you wanted.
- **Limits**: Random-roll risk without Bile; five of six outcomes unexpressible in the modifier vocabulary; infantry-only (vehicles excluded).
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/creations-of-bile

#### Pactbound Zealots (3DP → PRIORITY ASSETS)
- **Mechanics**: Every non-Epic-Hero HERETIC ASTARTES unit takes a Chaos mark at muster. On a successful Dark Pact, marked units' granted abilities upgrade: Chaos Undivided re-rolls hit 1s; the four gods make unmodified 5+ hit rolls Critical Hits when the pact granted Lethal/Sustained Hits. Shared marks required for character attachment/transports.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Slaanesh-marked Sustained Hits units critting on 5+; Khorne-marked Possessed melee waves.
- **Limits**: All bonuses conditional on successful pacts; mark mandates constrain list building (no-mark units forbidden, matching marks for transports); crit-widening unmodeled.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/pactbound-zealots

#### Renegade Raiders (3DP → RECONNAISSANCE)
- **Mechanics**: All HERETIC ASTARTES ranged weapons gain ASSAULT (shoot after Advance), and any attack against a unit within range of an objective marker gains +1 AP.
- **Rating**: Strong for Reconnaissance
- **Synergies**: Chaos Bikers, Raptors and advancing Legionaries firing on the move while contesting markers — the whole army shoots at full effect mid-push.
- **Limits**: AP bonus conditional on target near an objective; ASSAULT is eligibility, not accuracy.
- **_source**: https://www.40k.app/875/factions/chaos-space-marines/detachments/renegade-raiders

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* The corpus documents few named enhancements for this faction beyond detachment-level notes (Cabal Of Chaos lists Conduit of Chaos / Touched by the Warp enhancement slots in merged data). Named CP tools concentrate in the battle-shock suite around Nightmare Hunt/Dread Talons. Treat specific enhancement picks as unresolved pending primary-source verification — do not plan around them.

### Overall Army Play Pattern
*(interpretation)* Chaos Space Marines win by choosing a tempo axis and committing: Renegade Raiders for objective-hopping shooting pressure, Creations Of Bile for a stat-augmented infantry wave, Deceptors/Nightmare Hunt for board denial through deployment and morale. The faction's breadth cuts both ways — every detachment is genuinely different, but almost every payoff is conditional (pact success, target states, proximity), so the army underperforms when its conditions aren't met. Take and Hold remains the weakest disposition: durability exists (Fellhammer) but nothing makes ground sticky, so CSM should plan to out-tempo opponents rather than out-grind them.
