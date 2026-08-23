# Drukhari

## Faction Identity

- **Full name**: Drukhari (BSData catalogue: "Aeldari - Drukhari")
- **Faction keyword**: DRUKHARI
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Power from Pain — Pain token economy that Empowers unit Pain abilities (per detachment_research/drukhari.json, Realspace Raiders entry); Kabal/Wych Cult/Covens/Blades for Hire sub-army tags gate detachment access
- **Keywords every unit should carry**: DRUKHARI
- **Sub-faction keywords** (per research corpus): KABAL, WYCH CULT, HAEMONCULUS COVENS, BLADES FOR HIRE; HARLEQUINS appear in Reaper's Wager

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/drukhari.json (2026-08-23, packs v1.1).

### Army Rule
- **Power from Pain**: Pain tokens accrue over the battle and Empower the faction's unit-level Pain abilities (research corpus states the mechanism and that Realspace Raiders grants up to 6 starting tokens via pairings). The corpus does NOT enumerate each Empowered tier effect — treat specific tier payoffs as outside this assessment.
- **Play pattern** *(interpretation)*: list construction is a token-engine design problem. Pairings (Archon+Kabalite Warriors, Succubus+Wyches, Haemonculus+Wracks) convert characters from tax into acceleration, and detachments are judged partly by how fast they prime the economy.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Covenite Coterie / Tools of Torment give conditional wound-roll protection to Covens bodies; sticky objective tools absent from corpus for this faction. |
| Purge the Foe | Moderate | Spectacle of Spite per-turn Combat Drugs and Reaper's Wager rerolls push damage; fragile profiles mean trading is unavoidable. |
| Reconnaissance | Situational | Skysplinter transport play and Exhibition of Slaughter are tagged Recon but their buffs are turn-gated or target-restricted. |
| Priority Assets | Weak | Corpus offers no protective or preservation mechanic for keeping your own key units alive — Realspace Raiders accelerates tokens but defends nothing. |
| Disruption | Moderate | Kabalite Agonysts' Sustained Hits 1 ranged buff is always-on within scope (KABAL/BLADES FOR HIRE, ranged only, excluded vs MONSTER/VEHICLE); Kabalite Cartel adds a pick-one-of-three Contract system whose buff applies only vs the matching target type — conditional by design, rated Situational on its own block below. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Exhibition Of Slaughter (1DP → RECONNAISSANCE)
- **Mechanics**: Exacting Cruelty — all friendly WYCH CULT melee attacks have Lethal Hits, except vs MONSTER and VEHICLE targets. WYCH CULT-tagged; exclusive with other WYCH CULT detachments.
- **Rating**: Situational for Disruption / Purge the Foe
- **Synergies**: Wyches, Hellions, Reavers, Lelith Hesperax — volume melee converts Lethal Hits into reliable chip damage.
- **Limits**: explicitly does nothing vs MONSTER/VEHICLE targets; melee-only; tag exclusivity constrains army building.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Kabalite Agonysts (1DP → DISRUPTION)
- **Mechanics**: Contracted Harvest — friendly KABAL and BLADES FOR HIRE ranged attacks gain Sustained Hits 1, except vs MONSTER and VEHICLE targets. KABAL-tagged; exclusive with other KABAL detachments.
- **Rating**: Moderate for Disruption / Purge the Foe
- **Synergies**: Kabalite Warriors, Hand of the Archon, Scourges With Shardcarbines — high-shot poison/small-arms profiles.
- **Limits**: ranged only; dead vs MONSTER/VEHICLE targets; KABAL/BLADES FOR HIRE scope excludes Wych Cult and Covens damage entirely.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Tools Of Torment (1DP → TAKE AND HOLD)
- **Mechanics**: Darkest Artifice — enemy attacks targeting friendly CRONOS or TALOS units subtract 1 from the Wound roll when attacker Strength exceeds unit Toughness. COVENS-tagged; exclusive with other COVENS detachments.
- **Rating**: Situational for Take and Hold
- **Synergies**: Cronos/Talos units sitting on mid-board objectives.
- **Limits**: two-unit scope; conditional on S > T (small arms unaffected); no offensive compensation at 1DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Covenite Coterie (2DP → TAKE AND HOLD)
- **Mechanics**: Stitchflesh Abominations — enemy attacks targeting friendly HAEMONCULUS COVENS units subtract 1 from the Wound roll when attacker Strength exceeds unit Toughness.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Haemonculus-led Wracks blocks and any Covens-tagged units; Haemonculus character anchors.
- **Limits**: same S > T condition as Tools of Torment but broader scope; purely defensive — the detachment adds zero damage output.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Kabalite Cartel (2DP → DISRUPTION)
- **Mechanics**: Murderous Agenda — pick one of three Contracts at battle start (CHARACTER / INFANTRY-MOUNTED / MONSTER-VEHICLE target types). KABAL and BLADES FOR HIRE units gain Precision, Sustained Hits 1, or Lethal Hits respectively vs matching targets. Completing the Contract grants 3 Pain tokens.
- **Rating**: Situational for Disruption / Purge the Foe (pick-one-of-three rule — value swings with opponent list)
- **Synergies**: Kabalite Warriors, Scourges With Heavy Weapons, Hand of the Archon; contract choice made after seeing opponent.
- **Limits**: pick-one rule — wrong guess halves the detachment; bonus applies only vs matching target type; 3-token payoff is one-time.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Realspace Raiders (2DP → PRIORITY ASSETS)
- **Mechanics**: Alliance of Agony — battle start, gain 2 Pain tokens per present pairing (Archon+Kabalite Warriors, Succubus+Wyches, Haemonculus+Wracks), max 6 starting tokens; feeds Power from Pain.
- **Rating**: Moderate for Priority Assets / Take and Hold (economy acceleration, not direct power)
- **Synergies**: any list already running all three pairing pairs — six tokens before turn 1.
- **Limits**: corpus flags both the token economy and which abilities get Empowered as composition-dependent and unmodeled; value inherits whatever the Pain ability tiers actually do.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Skysplinter Assault (2DP → RECONNAISSANCE)
- **Mechanics**: Rain of Cruelty — each time a DRUKHARI unit disembarks from a TRANSPORT, until end of turn its ranged weapons gain Ignores Cover and melee weapons gain Lance.
- **Rating**: Situational for Reconnaissance / Purge the Foe
- **Synergies**: Kabalite Warriors or Wyches delivered by transports; Scourges dropping onto cover-camping targets.
- **Limits**: strictly turn-of-disembark gated; requires spending on transports and accepting delivery risk; no benefit to units that never disembark.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Spectacle Of Spite (2DP → PURGE THE FOE)
- **Mechanics**: Combat Drugs — at each Command phase select one active drug for all WYCH CULT models (each once per battle): +1A melee / +2" Move / +1WS melee / +1T / +1S melee / +1Ld/+1BS. Random two-drug roll alternative exists.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Wyches, Reavers, Hellions, Incubi, Lelith Hesperax — stacking +1S or +1A onto volume melee turns.
- **Limits**: each drug once per battle — the best buff expires; effects rotate turn to turn; none modeled; WYCH CULT-only scope.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

#### Reaper’S Wager (3DP → PURGE THE FOE)
- **Mechanics**: Callous Competition — army-wide wager between DRUKHARI and HARLEQUINS units, flipped by whichever side last destroyed an enemy unit. While winning: re-roll Hit 1s. While losing: re-roll Hit 1s AND Wound 1s. Drukhari start winning. Allows Harlequins points allowance.
- **Rating**: Situational for Purge the Foe
- **Synergies**: entire army benefits; Harlequins inclusion (Solitaire, Troupe) enables mixed lists.
- **Limits**: reroll value depends on a fluctuating state you partially control but can lose; paradoxically the LOSING state has better rerolls; full-budget 3DP cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/drukhari/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents no individual enhancement/stratagem names for this faction)*
- The research corpus does NOT catalogue individual stratagems or enhancements for Drukhari beyond the detachment rules above — no picks offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: Drukhari assessments revolve around two engines running simultaneously: the Pain token economy and the sub-army tag system. Because every damage detachment is keyword-scoped (KABAL gets ranged Sustained Hits, WYCH CULT gets melee Lethal Hits, COVENS gets defensive wound penalties), the faction cannot stack all its buffs in one list — you choose a damage lane per detachment and the exclusivity tags enforce it. The strongest grounded pattern is a hybrid: Kabalite Agonysts' cheap always-on shooting buff plus Covenite Coterie durability for objective-holding, with Realspace Raiders priming the token bank if the list naturally fields all three pairings. Fragile profiles across the board mean the faction trades tempo for damage; nothing in the corpus protects Priority Assets, which caps how greedy a glass-hammer build can afford to be.
