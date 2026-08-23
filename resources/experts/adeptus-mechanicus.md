# Expert: Adeptus Mechanicus

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide Adeptus Mechanicus-specific ground truth so Shredder can identify WRONG data.
> Scope: Faction Identity + Army Rules & Detachments Expert Assessment. Unit-by-unit cheat sheets not yet written.

## Faction Identity

- **Full name**: Adeptus Mechanicus
- **Faction keyword**: `Faction: Adeptus Mechanicus` (all units also `Imperium`)
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Doctrina Imperatives — an army-wide toggle chosen each battle round between Protector and Conqueror stances; several detachments key their buffs off whichever imperative is active. Keyword families (`SKITARII`, `CULT MECHANICUS`, `LEGIO CYBERNETICA`) are the main scoping device for detachment rules.
- **Keywords every unit should carry**: `Imperium`, `Faction: Adeptus Mechanicus`, plus family keywords (`Skitarii` on Rangers/Vanguard/Sicarian/Serberys/Pteraxii frames, `Cult Mechanicus` on Kataphron/Electro-Priest/Kastelan frames)
- **Sub-faction keywords**: Forge Worlds exist as flavour, not selectable sub-factions.

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/adeptus-mechanicus.json (2026-08-23, packs v1.1).

### Army Rule
- **Doctrina Imperatives**: Exactly one imperative is active each battle round — Protector or Conqueror. Detachments such as Eradication Cohort convert the active imperative into rerolls for Skitarii attacks.
- **Play pattern**: *(interpretation)* The toggle forces sequencing decisions: shoot-oriented turns want Protector, melee/pressure turns want Conqueror. Lists built around Skitarii shooting get the most from the cycle; pure Kataphron/Kastelan builds interact with it only through specific detachments.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Cohort Cybernetica (+2" Move/+1 OC robots) and Rad-Zone Corps map here, but both are keyword-scoped or opponent-positioning-dependent; engine's holders (Skitarii Vanguard/Rangers, Servitor Battleclade) carry the mission regardless. |
| Purge the Foe | Situational | Eradication Cohort is the only purge-mapped detachment; its rerolls never stack (one imperative at a time). |
| Reconnaissance | Moderate | Two recon-mapped detachments; engine ranks Pteraxii Sterylizors/Skystalkers and Serberys Sulphurhounds top of recon natively. |
| Priority Assets | Moderate | Explorator Maniple objective-proximity rerolls and Haloscreed's flexible per-turn overrides fit objective-sitting play. |
| Disruption | Moderate | Rad-Zone Corps mortal-wound pressure, Data-Psalm Conclave half-range AP and Luminen Auto-Choir give real disruption tools, though all conditional. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Cohort Acquisitus (1DP → RECONNAISSANCE)
- **Mechanics**: Specific Skitarii-type units (Rangers, Pteraxii, Serberys, Infiltrator-class) may designate one visible enemy within 12" as analysed in Shooting, granting a detection-range benefit tied to the Hidden rule.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Pteraxii Sterylizors and Serberys Sulphurhounds (both engine-ranked in Reconnaissance) as forward analysers.
- **Limits**: Scoped to listed Skitarii types only; detection mechanic has no modifier vocabulary equivalent; research confidence medium — source rendering of the rule appeared garbled, paraphrased cautiously.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Lords Of The Forge (1DP → PRIORITY ASSETS)
- **Mechanics**: All friendly Tech-Priest models permanently gain a 4+ invulnerable save and Feel No Pain 5+; once per turn a non-Battle-shocked Tech-Priest can force a nearby enemy vehicle (within 12") to take a Battle-shock test at −1.
- **Rating**: Situational for Priority Assets
- **Synergies:** Tech-Priest Dominus/Manipulus-led gunlines surviving focused fire; anti-vehicle Battle-shock pressure vs vehicle-heavy metas.
- **Limits**: Save/FNP bonuses apply only to TECH-PRIEST characters, not the army; enemy debuff is once per turn per target and vehicle-only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Luminen Auto-Choir (1DP → DISRUPTION)
- **Mechanics**: Corpuscarii Electro-Priests' ranged attacks have Lethal Hits; Fulgurite Electro-Priests heal D3 wounds after their unit has fought. Carries the DATA-PSALM tag (exclusivity constraint).
- **Rating**: Situational for Disruption
- **Synergies**: Electro-Priest blocks — Corpuscarii shooting into chaff, Fulgurite grinding through melee trades.
- **Limits**: Both halves apply only to Electro-Priest datasheets; post-fight healing has no vocabulary equivalent; tag restricts pairing with other DATA-PSALM detachments.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Cohort Cybernetica (2DP → TAKE AND HOLD)
- **Mechanics**: All LEGIO CYBERNETICA units (Kastelan Robots, Servitors) get +2" Move and +1 Objective Control unless Battle-shocked.
- **Rating**: Situational for Take and Hold
- **Synergies**: Kastelan Robot blocks walking up the table; Servitor screens (Servitor Battleclade is engine-ranked in Take and Hold).
- **Limits**: Keyword-scoped to LEGIO CYBERNETICA units only; +1 OC lost while Battle-shocked; narrow unit pool caps list options.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Data-Psalm Conclave (2DP → DISRUPTION)
- **Mechanics**: At battle start pick one Benediction for Cult Mechanicus units, active all game: ranged attacks vs targets within half range get +1 AP, OR melee weapons get +1 Strength and +1 Attacks on turns the unit Charged. An enhancement can temporarily grant both.
- **Rating**: Situational for Disruption
- **Synergies:** Kataphron Destroyer gunlines under the half-range AP benediction; Sicarian Ruststalker melee waves under the charge benediction.
- **Limits**: Mutually exclusive all-battle choice — committing at list check; each half is condition-gated (half range / charged turn); no always-on component.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Explorator Maniple (2DP → PRIORITY ASSETS)
- **Mechanics**: In your Command phase designate one objective marker; until your next Command phase, all AdMech models re-roll wound rolls of 1 on attacks where their unit or the attack's target is within range of that marker.
- **Rating**: Situational for Priority Assets
- **Synergies:** Objective-holding firebases — Skitarii Ranger/Vanguard squads plus Onager Dunecrawler support sitting on the designated marker.
- **Limits**: Single designated objective; proximity condition must hold per attack (unit or target near the marker); re-designation is phase-bound.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Rad-Zone Corps (2DP → TAKE AND HOLD)
- **Mechanics**: At battle start, enemy units in the enemy deployment zone either stand firm (D3 mortal wounds on 3+) or take cover (Battle-shocked; D3 mortal wounds on 5+). Rounds 2–5, enemy units in the enemy deployment zone suffer 1 mortal wound and a Battle-shock test on a 3+ roll each Command phase.
- **Rating**: Situational for Take and Hold
- **Synergies:** Castle-style AdMech that punishes opponents who hold back — pressure compounds vs reserve-dependent enemies only if they stay home.
- **Limits**: Entire effect depends on opponent positioning in their deployment zone; dice-gated mortal wounds and Battle-shock tests; opponent's round-1 choice changes the outcome distribution.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Skitarii Hunter Cohort (2DP → RECONNAISSANCE)
- **Mechanics**: Friendly Skitarii Infantry, Skitarii Mounted and Ironstrider Ballistarii units have Stealth permanently and unconditionally.
- **Rating**: Moderate for Reconnaissance
- **Synergies:** The broadest-scoped defensive rule in the faction — covers most of a Skitarii-heavy list (Vanguard, Rangers, Sicarians, Serberys, Ironstriders); stacks conceptually with terrain-heavy play.
- **Limits**: Does not cover vehicles outside Ironstrider Ballistarii or non-Skitarii characters; purely defensive — no output increase.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Eradication Cohort (3DP → PURGE THE FOE)
- **Mechanics**: Skitarii units' attacks follow the active Doctrina Imperative: Protector gives re-roll hit rolls of 1, Conqueror gives re-roll wound rolls of 1. One imperative is always active, so every attack gets one of the two rerolls.
- **Rating**: Moderate for Purge the Foe
- **Synergies:** Massed Skitarii Vanguard/Ranger shooting (engine-ranked across dispositions) cycling rerolls with the Doctrina toggle; Thulia Ghuld-led builds.
- **Limits**: SKITARII keyword units only; the two rerolls are mutually exclusive per battle round — never model both; Kataphron/Kastelan-heavy lists get nothing from the rule itself despite paying 3DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

#### Haloscreed Battle Clade (3DP → PRIORITY ASSETS)
- **Mechanics**: Each Command phase select up to N AdMech units (1 Incursion / 2 Strike Force / 3 Onslaught) and assign one Override until next Command phase: +2" Move, OR +1 Toughness, OR eligibility to charge after Advancing, OR Stealth.
- **Rating**: Moderate for Priority Assets
- **Synergies:** Flexible coverage across mixed lists — Toughness onto objective sitters (Kataphron Breachers), advance-charge onto Ruststalkers, Stealth onto backfield guns.
- **Limits**: Nothing is always-on — capped unit count scales with battle size; one effect per selected unit per turn; +1 Toughness and Stealth have no vocabulary keys.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-mechanicus/

### Enhancements & Stratagems Worth Taking
*(interpretation — enhancement effect text is NOT yet captured in the research corpus; names verified against data/merged only. Verify effects against the faction pack before citing mechanics.)*
- **Haloscreed Battle Clade** ships four enhancements (Cognitive Reinforcement, Inloaded Lethality, Sanctified Ordnance, Transoracular Dyad Wafers) on the faction's most flexible detachment — likely picks by placement alone.
- Data-Psalm Conclave's Mantle of the Gnosticarch plausibly relates to the research-noted enhancement that grants both Benedictions temporarily — effect unverified; do not assert.
- No stratagem effects were captured in the research corpus for this faction — do not assert any stratagem mechanics as fact.

### Overall Play Pattern
*(interpretation)* Adeptus Mechanicus plays as a layered shooting castle with surgical mobility tools: cheap Skitarii bodies screen and score while Kataphron/Kastelan frames and Onager platforms do damage, and the detachment roster decides which slice of the army gets amplified. The Doctrina toggle keeps the faction honest — no accuracy buff is ever unconditional — so the strongest shells are those with the fewest gates (Haloscreed's per-turn Overrides, Skitarii Hunter Cohort's permanent Stealth) rather than the biggest nominal numbers. Weaknesses are keyword fragmentation (several detachments buff disjoint slices of the codex) and heavy reliance on conditions the opponent can play around.

Assumptions:
- opponent unknown (all-comers)
- no cover factored beyond what detachment rules state
- battle size assumed Strike Force for Haloscreed override counts where relevant
- no CP economy modeling for stratagems
