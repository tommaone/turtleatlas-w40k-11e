# Expert Assessment: Imperial Knights — 11th Edition

## Faction Identity

- **Full name**: Imperium - Imperial Knights (BSData catalogue name)
- **Faction keyword**: Faction: Imperial Knights
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Code Chivalric (Oath of Deeds/Qualities system with Honoured/Debasing states per merged data), Bondsman abilities (big Knights buffing Armigers — referenced by detachment rules in research), Super-Heavy Walker movement, Deadly Demise on nearly every chassis (Canis Rex has no Deadly Demise entry in merged data), army-wide 5+ invulnerable saves on most chassis per merged rules entries
- **Keywords every unit should carry**: IMPERIAL KNIGHTS, TITANIC, WALKER; class keywords ARMIGER / QUESTORIS / CERASTUS / DOMINUS / ACASTUS scope several detachment rules
- **Sub-faction keywords** (if any): class keywords above act as the mechanical sub-keywords; Freeblade/house identities are not modeled in merged data

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/imperial-knights.json (2026-08-23,
packs v1.1). Edition snapshot date mandatory on this section.

### Army Rule
- **Code Chivalric**: an Oath system — Deeds are fulfilled during play, granting rewards and Honoured (or Debasing) states; Qualities grant ongoing benefits. Questoris Companions' rule (research) confirms the structure: fulfilling an Oath determines a new one from unused Deeds/Qualities, fulfilled Qualities stack for the rest of the game, later Deeds reward 1CP.
- **Play pattern**: interpretation — list construction is a small number of huge multi-wound blocks plus Armiger support wings; the Oath system rewards playing actively (fulfilling Deeds mid-battle) rather than castling. Bondsman links between big Knights and Armigers are the faction's force-projection mechanic and two detachments key directly off them.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Gate Warden Lance and Questoris Companions both target it; T10+ OC-heavy Knights sit on objectives well, but low model count means one lost Knight collapses a flank. |
| Purge the Foe | Moderate | Massive shooting (Volcano lances, Thermal cannons, Acastus arrays in merged weapon lists) kills anything it sees; Valourstrike Lance adds tempo. Capped by points efficiency — few shots, big overkill waste into chaff. |
| Reconnaissance | Situational | Spearhead-At-Arms and Throne-Bonded Outriders target it via Bondsman/Armiger play and even make Armigers Battleline, but 6–10 models per list cannot contest wide boards. |
| Priority Assets | Strong | Freeblade Company's always-on 6+ FNP plus per-phase wound regeneration makes already-durable Knights markedly harder to shift; protecting a key model is what this faction does best. |
| Disruption | Weak | No denial/screening mechanics anywhere in the roster or detachment list; Questor Forgepact buffs allies rather than harassing enemies. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Dominus Foebreakers (1DP → PRIORITY ASSETS)
- **Mechanics**: friendly DOMINUS-class Knights gain +1 to hit rolls for any attack targeting a unit located in a terrain area (ranged and melee).
- **Rating**: Situational for Priority Assets — cheap, but only Dominus chassis benefit and only vs targets standing in terrain.
- **Synergies**: Knight Castellan/Knight Valiant (Ion Aegis aura units in merged data) shooting dug-in defenders.
- **Limits**: not_modeled: conditional on target being in/on a terrain feature; DOMINUS keyword scoping. Opponents fighting outside terrain get nothing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Throne-Bonded Outriders (1DP → RECONNAISSANCE)
- **Mechanics**: while an Armiger unit is under any active Bondsman ability effect, its ranged attacks ignore cover. ARMIGERS-tagged (exclusive with other ARMIGERS detachments).
- **Rating**: Situational for Reconnaissance — requires a Knight within range spending Command-phase activation to link before it does anything.
- **Synergies**: Armiger Helverin/Warglaive wings bonded by a Knight Crusader or Preceptor (merged Leader-adjacent chassis).
- **Limits**: not_modeled: ignore-cover strictly conditional on live Bondsman link; tag exclusivity not expressible.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Questor Forgepact (1DP → DISRUPTION)
- **Mechanics**: Knights project an aura giving friendly Adeptus Mechanicus units within 6" +1 BS and Heavy on ranged attacks; Tech-Priests heal D3 wounds on a nearby Knight each Command phase; permits up to 500pts of specified AdMech allies.
- **Rating**: Situational for Disruption — the buffs target AdMech allies, not the Knights; only rated at all in AdMech-partnered builds where the healing loop matters.
- **Synergies**: AdMech infantry/crawler gunlines inside a Knight castle; Tech-Priest healing a damaged Questoris each turn.
- **Limits**: not_modeled: ally inclusion is list-building, not an in-game modifier; healing conditional on allied Tech-Priest proximity. Note: its DISRUPTION objective mapping is nominal — nothing here disrupts the enemy.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Gate Warden Lance (2DP → TAKE AND HOLD)
- **Mechanics**: at battle start pick two objectives forming a "defensive line"; units on that line ignore all modifiers to their hit rolls and their weapons gain Sustained Hits 1.
- **Rating**: Moderate for Take and Hold — a zone the player draws themselves around two objectives they intend to hold anyway; Sustained 1 across a whole gunline is real damage. Not Situational-tier because the zone placement is under player control at muster, but it locks the list into defending that line all game.
- **Synergies**: Castellan/Valiant/Crusader long-range fire parked between the chosen objectives; Armiger Helverins patrolling the line.
- **Limits**: not_modeled: zone-conditional (line between two declared objectives); modifier-negation not expressible. Mobile opponents simply fight outside the line.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Spearhead-At-Arms (2DP → RECONNAISSANCE)
- **Mechanics**: the first Bondsman ability used by a Knight each turn can affect up to three Armigers within 12" (15" if army is Honoured) instead of one; Armiger models gain Battleline.
- **Rating**: Moderate for Reconnaissance — triples the throughput of the faction's buff economy across the Armiger wing and Battleline status improves scoring eligibility; still bounded by how many Armigers fit the list.
- **Synergies**: three-plus Armiger Warglaive/Helverin packs under Knight Preceptor/Warden bonds; Honoured-state extension rewards early Oath completion.
- **Limits**: not_modeled: Bondsman tripling value depends entirely on which abilities are used; Battleline keyword change affects list-building/scoring, not stats; extended range conditional on Honoured.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Valourstrike Lance (2DP → PURGE THE FOE)
- **Mechanics**: each time an Imperial Knights unit Advances, until end of turn its ranged weapons gain Assault — shoot after Advancing without penalty. Army-wide tempo enabler; no stat bonus.
- **Rating**: Moderate for Purge — reposition-and-shoot every turn keeps big guns on targets, but it adds no hit/wound/damage; the kill power remains the datasheets'.
- **Synergies**: advancing Crusader/Magaera/Styrix mid-range pushes; Armiger wings keeping pace with big Knights instead of screening statically.
- **Limits**: not_modeled: Advance-and-shoot interaction has no flat modifier expression. Value drops to zero in static gunline lists.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Freeblade Company (3DP → PRIORITY ASSETS)
- **Mechanics**: all Imperial Knights models get a 6+ Feel No Pain against any damage, and every Knights model regains 1 lost wound at the start of each friendly Command phase. Passive, always-on.
- **Rating**: Strong for Priority Assets — the rare always-on detachment rule in this book, applied to an army of T10+/20W+ multi-wound models where each regenerated wound is disproportionately valuable. Costs the entire 3DP budget.
- **Synergies**: Knight Valiant/Castellan attrition anchors; Cerastus melee Knights grinding through enemy shooting phases.
- **Limits**: not_modeled: per-phase regeneration has no vocabulary key (research). 3DP leaves no second detachment slot.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

#### Questoris Companions (3DP → TAKE AND HOLD)
- **Mechanics**: extends Code Chivalric — when the current Oath is fulfilled a new one is determined immediately from unused Deeds/Qualities; fulfilled Qualities stack permanently; later fulfilled Deeds grant 1CP instead of the normal reward; Enhancement 'expended' states reset on each fulfilment.
- **Rating**: Moderate for Take and Hold — snowball ceiling is the highest in the faction (stacking rerolls/Move/OC-type Qualities per research examples) but every layer is performance-gated on completing Deeds mid-battle, and 3DP consumes the full budget.
- **Synergies**: active, aggressive Questoris/Cerastus knights who complete Deeds early and bank stacking Qualities; CP-hungry builds exploiting repeated 1CP Deed rewards.
- **Limits**: not_modeled: stacked Qualities are conditional on mid-battle Oath completion; extra CP economy not expressible. Weak starts snowball downward just as hard.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-knights/

### Enhancements & Stratagems Worth Taking
- Interpretation, grounded in merged enhancement lists: Gate Warden Lance's Acquisitor-at-Arms (15pts) and Vengeful Tread (15pts) are efficient fills on a defensive-line plan; Freeblade Company's Sanctuary (20pts) compounds the survivability theme; Questoris Companions' Herald of Triumph (15pts) supports the early-Oath push. No stratagem assessment attempted — stratagem text is outside the research corpus.

Overall army play pattern (interpretation): Imperial Knights trade board width for board mass — a handful of near-uncapturable scoring blocks that dictate where the game is fought. The strongest patterns lean into that: Freeblade Company or Questoris Companions double down on the few-models-many-wounds identity, while Gate Warden Lance formalizes the castle into a shooting fortress. The recurring failure mode is dispersion: split the Knights to cover too many objectives and each block becomes isolated meat for anti-tank focus fire. Bondsman-driven Armiger play (Spearhead-At-Arms, Throne-Bonded) is the viable alternative shape but caps out at Moderate because the faction simply cannot be in enough places for action-heavy missions.
