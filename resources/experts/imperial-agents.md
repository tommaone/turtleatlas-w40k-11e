# Expert Assessment: Imperial Agents — 11th Edition

## Faction Identity

- **Full name**: Imperium - Agents of the Imperium (BSData catalogue name)
- **Faction keyword**: Faction: Agents of the Imperium (coalition army — units carry their own agency keywords)
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: no unified army-wide combat rule in merged data or research corpus; identity is a keyword coalition — ADEPTUS ARBITES, INQUISITOR/INQUISITORIAL AGENTS, ORDO HERETICUS/MALLEUS/XENOS, OFFICIO ASSASSINORUM, DEATHWATCH, plus Imperial Navy and Ecclesiarchy attachments. Detachment rules buff these sub-keyword groups, not "the army".
- **Keywords every unit should carry**: Faction: Agents of the Imperium plus an agency sub-keyword (per-unit; see above)
- **Sub-faction keywords** (if any): ADEPTUS ARBITES / INQUISITOR / OFFICIO ASSASSINORUM / DEATHWATCH / etc. — these are the mechanically relevant scoping keywords for detachment rules

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/imperial-agents.json (2026-08-23,
packs v1.1). Edition snapshot date mandatory on this section.
Completeness: research verdict CONFIRMED COMPLETE — exactly 5 matched-play
detachments exist in 11e. Two named formations on Wahapedia (Voidship's Company,
Interdiction Team) belong to Boarding Actions and are excluded from matched play.

### Army Rule
- **None (datasheet-level faction)**: no army-wide combat rule appears in the research corpus or merged data; every unit runs on its own datasheet abilities (assassin once-per-battle abilities such as Overkill/Soulless Horror/Shieldbreaker per research, Inquisitor leader rules, Deathwatch deep strike, etc.).
- **Play pattern**: interpretation — this is a toolbox faction. The list is assembled around a few high-leverage specialists (assassins, named Inquisitors) supported by cheap Arbites/Navy scoring bodies; the detachment chosen decides which sub-keyword group actually gets buffs. Expect it played most often as a secondary/ally-flavoured primary rather than a grind-it-out battleline army.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Situational | Ordo Hereticus Purgation Force targets it but buffs only Arbites/Inquisition keyword models; cheap Vigilant/Subductor/Exaction squads can hold, yet nothing makes them durable. |
| Purge the Foe | Situational | Ordo Xenos Alien Hunters targets it via DEATHWATCH-only Mission Tactics; outside Deathwatch-heavy lists there is no damage engine here. |
| Reconnaissance | Situational | Imperialis Fleet targets it with re-selectable modes, but low model count caps action output like all elite-coalition armies. |
| Priority Assets | Weak | Ordo Malleus Daemon Hunters grants hit rerolls of 1 to three keyword groups — a modest offensive buff that does not protect anything. |
| Disruption | Weak | Veiled Blade Elimination Force doubles assassin once-per-battle abilities — real value in assassin-heavy builds, negligible otherwise. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Veiled Blade Elimination Force (1DP → DISRUPTION)
- **Mechanics**: OFFICIO ASSASSINORUM units may use their once-per-battle Overkill, Soulless Horror and Shieldbreaker abilities twice per battle (never twice in the same battle round); at army muster each assassin gains a temple-specific Extremis ability at added points cost (decoy teleport swap, improved mortal-wound grenades, repeatable Heroic Intervention, anti-monster/vehicle rifle).
- **Rating**: Situational for Disruption — meaningful only if the list commits multiple assassins; Extremis costs push each model's price up.
- **Synergies**: Callidus (decoy swap), Eversor (grenades), Vindicare (anti-monster/vehicle rifle), Culexus — temple-matched Extremis picks per research.
- **Limits**: not_modeled: doubled per-battle uses are a resource mechanic with no modifier expression; Extremis abilities vary per temple and cost extra points.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-agents/

#### Imperialis Fleet (2DP → RECONNAISSANCE)
- **Mechanics**: at each Command phase pick one mode until your next Command phase: nominate one enemy unit anywhere for +1 to hit rolls against it; or nominate one objective marker so nearby friendly AGENTS units gain +1 OC and Leadership and a 5+ invulnerable save while within range of it.
- **Rating**: Situational for Reconnaissance — the most flexible rule in the book (re-picked every phase) but each mode affects exactly one nominated unit/objective.
- **Synergies**: Voidsmen-at-Arms/Vigilant squads sitting objectives under the 5++ bubble; any shooting block focusing the nominated enemy.
- **Limits**: not_modeled: both effects are player-selected per phase, never always-on; single-target scoping throughout.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-agents/

#### Ordo Hereticus, Purgation Force (2DP → TAKE AND HOLD)
- **Mechanics**: two persistent effects on ADEPTUS ARBITES, INQUISITOR, INQUISITORIAL AGENTS and ORDO HERETICUS models: ranged weapons ignore cover; attacks gain Sustained Hits 1 when targeting a CHAOS unit of 5+ models.
- **Rating**: Situational for Take and Hold — genuinely always-on within its keyword scope, but that scope excludes Deathwatch, assassins and Sisters units in merged data, and the Sustained half is match-up dependent (CHAOS 5+ only).
- **Synergies**: Exaction Squad/Vigilant Squad/Subductor Squad gunlines; Inquisitor Draxus/Greyfax leading them.
- **Limits**: not_modeled: ignore cover scoped to listed keywords and ranged only; Sustained conditional on target. Vs non-Chaos lists the rule halves.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-agents/

#### Ordo Malleus, Daemon Hunters (2DP → PRIORITY ASSETS)
- **Mechanics**: INQUISITOR, INQUISITORIAL AGENTS and ORDO MALLEUS models re-roll Hit rolls of 1 on all attacks; vs DAEMON targets they additionally re-roll Wound rolls of 1.
- **Rating**: Weak for Priority Assets — a small offensive reroll package scoped to characters/small keyword groups does nothing to protect or score assets; even its anti-daemon spike is narrow.
- **Synergies**: Inquisitor Coteaz/Kroyle with Grey Knight Terminator Squad support units present in merged data.
- **Limits**: not_modeled: wound reroll gated on DAEMON target; hit reroll scoped to the three listed keyword groups.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-agents/

#### Ordo Xenos, Alien Hunters (2DP → PURGE THE FOE)
- **Mechanics**: at start of each Command phase select ONE of three Mission Tactics until next Command phase, DEATHWATCH units only, each tactic once per battle: Furor (Sustained Hits 1 all weapons); Malleus (Lethal Hits all weapons); Purgatus (critical wound rolls grant Precision). A stratagem can swap one unit's active tactic.
- **Rating**: Situational for Purge — strong per-turn spikes on Deathwatch Kill Teams, but pick-one-of-three + once-per-battle-each means the buff window closes after ~3 rounds.
- **Synergies**: multiple Deathwatch Kill Teams plus Watch Master/Watch Captain Artemis; Corvus Blackstar delivery.
- **Limits**: not_modeled: player-selected per turn, once-per-battle each; Precision-on-crit-wounds not expressible in vocabulary. Gate: DEATHWATCH units only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/imperial-agents/

### Enhancements & Stratagems Worth Taking
- Interpretation, grounded in merged enhancement lists: Ordo Hereticus's No Escape (25pts) is the premium spend on the detachment with the broadest always-on-in-scope rule set (Purgation Force); Imperialis Fleet's Combat Landers (10pts) cheaply accelerates deployment; Alien Hunters' Universal Anathema (10pts) is efficient filler on a Deathwatch build. No stratagem assessment attempted — stratagem text is outside the research corpus.

Overall army play pattern (interpretation): Imperial Agents do not out-fight dedicated factions; they out-scheme them. The realistic pattern is a lean list of cheap Arbites/Navy objective bodies doing the holding while two-to-four specialists (assassins, named Inquisitors, a Deathwatch element) generate outsized tempo through once-per-battle abilities and targeted buffs. Every detachment reinforces one sub-keyword group at a time, so the faction's ceiling is set by how well the chosen detachment's keyword scope matches the units actually doing the work — misaligned scope leaves most of the list unbuffed, which is why no disposition rates above Situational here.
