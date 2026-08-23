# Expert File: Deathwatch

## Faction Identity

- **Full name**: Deathwatch (BSData catalogue: "Imperium - Adeptus Astartes - Deathwatch")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Deathwatch`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Adeptus Astartes framework. The chapter's distinct identity lives almost entirely in Black Spear Task Force (Mission Tactics system + restricted army list) and the Kill Team unit family (Fortis, Spectrus, Talonstrike, Decimus, Indomitor per data/config). No separate army-rule text exists in the research corpus [unverified].
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
- **Adeptus Astartes framework**: the corpus confirms Oath-of-Moment-referencing detachments (1st Company Task Force) available to Deathwatch armies. No chapter-specific army rule is documented in this research file — claims about a unique faction rule are unsupported here.
- **Play pattern** *(interpretation)*: elite mixed-specialist shooting army; the detachment choice mostly decides which inherited generic package wraps around Black Spear-style veteran units.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Inherited bench (Anvil/Bastion/Orbital/Ironstorm/Ceramite) is deep but all conditional; no native sticky-objective tool documented. |
| Purge the Foe | Moderate | Black Spear Task Force rotating Mission Tactics plus inherited 1st Company TF single-target rerolls. |
| Reconnaissance | Moderate | Vanguard Spearhead cover core + Subversion detection on Spectrus/Infiltrator-type units. |
| Priority Assets | Moderate | Firestorm/Gladius/Headhunter inherited; nothing chapter-specific outside Black Spear. |
| Disruption | Situational | Stormlance/Subversion exist but the elite-shooting roster converts poorly into melee tempo or screening denial. |

### Detachment Assessments

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
- **Mechanics**: Once-per-battle wound re-rolls vs the Oath target (inherited).
- **Rating**: Situational for Purge the Foe — Deathwatch Terminator Squad focus-fire turns.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* Black Spear's Adaptive Tactics stratagem is the named force-multiplier — extending Mission Tactics to non-native ADEPTUS ASTARTES units widens the detachment's narrow FAQ scope. Inherited tools worth noting: Gladius Storm of Fire (ignore-cover) under Devastator Doctrine for veteran shooters; Anvil's Not One Backwards Step (double OC stationary near an objective) for gunline scoring. All CP-gated, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Deathwatch plays as a compact elite shooting force whose actual detachment decision is "Black Spear or which inherited package": the one chapter-specific option trades army-list freedom for round-by-round tactical flexibility, while the sixteen inherited options supply competent-but-generic support. The correct pattern is Black Spear into Purge-oriented pairs with Adaptive Tactics stretching the tactics pool, or Vanguard Spearhead/Anvil into defensive pairs where the small-unit durability does the work. The structural ceiling is breadth: with one bespoke detachment and a roster built around Kill Team specialists rather than massed melee or vehicles, several dispositions rely entirely on inherited tools designed for a different army shape.
