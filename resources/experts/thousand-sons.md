# Expert: Thousand Sons

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide Thousand Sons-specific ground truth so Shredder can identify WRONG data.
> Scope: Faction Identity + Army Rules & Detachments Expert Assessment. Unit-by-unit cheat sheets not yet written.

## Faction Identity

- **Full name**: Thousand Sons
- **Faction keyword**: `Faction: Thousand Sons` (units also `Chaos`, many `Tzeentch`)
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Psychic Ritual economy — Psyker units manifest Rituals via psychic tests at the start of the Shooting phase, generating effects; heavy `Psyker` keyword density means detachment rules that buff Psychic weapons or gate on Psykers touch most of the army. Daemons and Mutant units (Tzaangors) are scoped-in subsets of several detachments.
- **Keywords every unit should carry**: `Chaos`, `Faction: Thousand Sons`; psyker units carry `Psyker`; daemon allies carry daemon keywords; Tzaangor/Mutant keywords gate specific detachments
- **Sub-faction keywords**: Cults exist as flavour, not selectable sub-factions; detachment tags (`MUTANT`) gate pairing.

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/thousand-sons.json (2026-08-23, packs v1.1).

### Army Rule
- **Rituals (Cabal economy)**: Thousand Sons Psyker units take psychic tests at the start of the Shooting phase to manifest Rituals; effects scale with manifestation success. Detachments add Ritual-adjacent payoffs (healing, aura-granted access for daemons).
- **Play pattern** *(interpretation)*: The army sequences Ritual manifestations around shooting phases — every Psyker is both a gun and a resource engine. List construction pushes Psyker density because most detachment buffs key on Psychic weapons or Psyker proximity; non-Psyker units need explicit detachment support to keep pace.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Three detachments map here including Rubricae Phalanx's unconditional defence and Hexwarp Thrallband's reroll floor; Rubric Marines and Scarab Occult Terminators rank top of engine in Take and Hold. |
| Purge the Foe | Moderate | Warpmeld Pact is the only purge-mapped detachment and its buffs cost mortal wounds; engine purge leaders (Daemon Prince Of Tzeentch With Wings, Forgefiend) succeed largely natively. |
| Reconnaissance | Moderate | Kairos Fateweaver ranks #1 in recon across the engine; Servants Of Change enables cheap Tzaangor bodies but its detection mechanic is narrow. |
| Priority Assets | Moderate | Grand Coven psychic spikes and Warpforged Cabal vehicle rerolls fit objective bursts; both conditional. |
| Disruption | Situational | Only Sekhetar Cohort maps here and it touches a single robot datasheet line. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Ritual Of Regeneration (1DP → TAKE AND HOLD)
- **Mechanics**: Once per turn per unit, when a non-Monster Thousand Sons Psyker unit successfully manifests a Ritual, that unit heals D3 lost wounds.
- **Rating**: Situational for Take and Hold
- **Synergies:** Multi-wound Psyker blocks grinding on objectives — Exalted Sorcerer-led foot units holding mid-board.
- **Limits**: Healing only — no offensive output anywhere in the rule; trigger depends on successful Ritual manifestation (2D6 test); non-Monster Psykers only; D3 healing not representable in modifier vocabulary.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Sekhetar Cohort (1DP → DISRUPTION)
- **Mechanics**: Sekhetar Robot units' attacks gain the Psychic weapon ability; Thousand Sons Psyker units project a 12" aura giving nearby Sekhetar Robots +1 melee Weapon Skill.
- **Rating**: Weak for Disruption
- **Synergies:** Sekhetar Robots hunting enemy characters with Psychic-tagged attacks where anti-Psyker interactions apply.
- **Limits**: Entire rule touches one robot datasheet line — no benefit to any other unit; Psychic keyword grant and aura WS have no vocabulary equivalents; disruption payoff depends on opponent interactions not captured here.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Servants Of Change (1DP → RECONNAISSANCE)
- **Mechanics**: Tzaangor units gain the Battleline role; while a friendly Mutant unit is shooting, enemy units have their detection range increased by 6". Carries the MUTANT tag (exclusivity constraint).
- **Rating**: Situational for Reconnaissance
- **Synergies:** Cheap Tzaangor swarms filling Battleline slots while screening units push board control.
- **Limits**: Detection increase requires an actively-shooting Mutant unit — positional and phase-gated; Battleline reassignment is list-building value, not combat math; MUTANT tag restricts pairing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Changehost Of Deceit (2DP → RECONNAISSANCE)
- **Mechanics**: Daemon units project an aura granting nearby TS Psyker units a 4+ invulnerable save vs ranged attacks; Mortal Psyker units project an aura letting nearby daemon Psyker units use the army's Ritual ability. Daemon inclusion capped at mission-size points allowance; daemons cannot be the Warlord.
- **Rating**: Situational for Reconnaissance
- **Synergies:** Mixed lists pairing daemon bodies (Flamers, Screamers) with Rubric/Exalted Psyker gunlines inside the invuln aura.
- **Limits**: All benefits proximity-based between two halves of the army; daemon points cap constrains list shape; no daemonic Warlord; nothing applies without mixed deployment.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Warpforged Cabal (2DP → PRIORITY ASSETS)
- **Mechanics**: When a TS Vehicle shoots or fights: if within 6" of a friendly Psyker, re-roll one hit AND one wound AND one damage roll; otherwise re-roll one hit OR wound OR damage roll. Vehicles with Deadly Demise within 6" of a friendly Psyker inflict mortal wounds on a 5+ instead of a 6.
- **Rating**: Situational for Priority Assets
- **Synergies:** Forgefiend and Defiler (both engine-ranked in Purge/Priority contexts) escorted by Psyker handlers for the triple reroll.
- **Limits**: Selective single-die rerolls — not blanket rerolls, and the full triple needs Psyker proximity maintained every activation; vehicle-only rule in a predominantly infantry/psyker faction; enhanced Deadly Demise is a death-trigger bonus.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Warpmeld Pact (2DP → PURGE THE FOE)
- **Mechanics**: Mutant infantry/mounted units may opt to sacrifice D3 mortal wounds at phase end for either −1 to wound rolls against them or +1 to their wound rolls until end of phase. Tzaangors gain Battleline and, while not Battle-shocked, +1 Objective Control. MUTANT tag restricts pairing.
- **Rating**: Situational for Purge the Foe
- **Synergies:** Tzaangor swarms pushing objectives with the OC boost; Mutant melee waves taking the +1 to wound sacrifice into a decisive charge turn.
- **Limits**: Buffs are opt-in and paid in D3 mortal wounds per use — attrition you must budget; oc_boost void while Battle-shocked; Mutant/Tzaangor-scoped only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Grand Coven (3DP → PRIORITY ASSETS)
- **Mechanics**: In your Command phase, once per battle each: choose one of three effects lasting until your next Command phase — add 6" to ranged Psychic weapon range, add 1 to wound rolls with Psychic weapons, or give Psychic weapons Devastating Wounds. Each option once per battle.
- **Rating**: Moderate for Priority Assets
- **Synergies:** The whole Psychic weapon suite — Magnus The Red, Ahriman, Exalted Sorcerers and Rubric Marines — sequencing the three boosts onto the three biggest damage turns.
- **Limits**: Depleting resource — three buffed rounds out of five, then nothing; Psychic weapons only; once-per-battle choices cannot be reused even if wasted on a whiffed round; 3DP cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Hexwarp Thrallband (3DP → TAKE AND HOLD)
- **Mechanics**: Defines the Flow of Magic zone: own deployment zone always qualifies; controlling half the No Man's Land or half the enemy deployment objectives extends the zone that phase. Psychic attacks always re-roll wound rolls of 1; attackers wholly within the zone instead add 1 to Psychic wound rolls.
- **Rating**: Moderate for Take and Hold
- **Synergies:** Rubric Marines and Scarab Occult Terminators advancing through the mid-board while Kairos Fateweaver anchors the backfield — objective control extends the zone that feeds their psychic output.
- **Limits:** Unconditional component is only the re-roll-1s floor; the stronger +1 to wound requires being wholly within a zone whose reach depends on holding half the objectives — self-reinforcing when winning, weak when losing ground; modeled convention keeps only the baseline as modifier.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

#### Rubricae Phalanx (3DP → TAKE AND HOLD)
- **Mechanics**: Each time an attack with unmodified Damage characteristic of 1 is allocated to a Rubricae model, add 1 to any armour saving throw against it. Unconditional passive defence for Rubricae units only.
- **Rating**: Situational for Take and Hold
- **Synergies:** Rubric Marines blobs sitting on objectives vs small-arms volume (bolter/shuriken-class D1 fire).
- **Limits**: Applies only to RUBRICAE units and only vs Damage-1 attacks — worthless vs D2+ profiles and anything that bypasses armour saves entirely; opponent-dependent value; 3DP for a purely defensive, matchup-gated rule.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/thousand-sons/

### Enhancements & Stratagems Worth Taking
*(interpretation — enhancement effect text is NOT yet captured in the research corpus; names verified against data/merged only. Verify effects against the faction pack before citing mechanics.)*
- **Hexwarp Thrallband** carries four enhancements (Arcane Might, Empowered Manifestation, Empyric Onslaught, Noctilith Mantle) on one of the faction's two flagship 3DP shells — likely picks by placement alone.
- Grand Coven's Lord of Forbidden Lore plausibly relates to coven/psychic-economy themes per naming, but effect is unverified — do not assert synergy.
- No stratagem effects were captured in the research corpus for this faction — do not assert any stratagem mechanics as fact.

### Overall Play Pattern
*(interpretation)* Thousand Sons plays as a psychic battery: dense Psyker units manifest Rituals every shooting phase while Rubricae bodies hold ground, and the detachment roster decides whether the army leans defensive-stacking (Hexwarp's zone control plus Phalanx armour boosts), burst damage (Grand Coven's three once-per-battle spikes), or hybrid ally/mutant boards (Changehost, Servants Of Change, Warpmeld Pact). Because the strongest buffs are either depleting (once-per-battle picks) or zone/positioning-gated, the faction rewards planning which turns the big swings land rather than assuming persistent bonuses. Its structural weakness is that several detachments buff disjoint slices (vehicles, robots, mutants, daemons) of an army whose core is Psychic infantry.

Assumptions:
- opponent unknown (all-comers)
- no cover factored beyond what detachment rules state
- Ritual manifestation assumed probabilistic (2D6 test), never assumed auto-success
- Flow of Magic extension assumed contested (requires holding half the objectives)
- no CP economy modeling for stratagems
