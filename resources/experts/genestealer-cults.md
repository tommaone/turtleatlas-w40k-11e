# Expert Assessment: Genestealer Cults — 11th Edition

## Faction Identity

- **Full name**: Xenos - Genestealer Cults (BSData catalogue name)
- **Faction keyword**: Faction: Genestealer Cults
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Cult Ambush (marker-based hidden deployment and redeployment for units with the ability), ubiquitous Deep Strike on hybrid/Purestrain units, cheap multi-wound battleline bodies
- **Keywords every unit should carry**: Faction: Genestealer Cults plus each unit's own name keyword and INFANTRY; battleline units carry BATTLELINE (e.g. Neophyte Hybrids) and GREAT DEVOURER appears across the range. No CULT/PURESTRAIN-style sub-faction keywords exist as mechanical keywords in merged data
- **Sub-faction keywords** (if any): none modeled as separate keywords in merged data (cult names are not mechanical keywords here)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/genestealer-cults.json (2026-08-23,
packs v1.1). Edition snapshot date mandatory on this section.

### Army Rule
- **Cult Ambush**: units with the Cult Ambush ability deploy and can be set back up via Cult Ambush markers instead of normal deployment; markers are removed if an opponent moves too close. Unit-level interactions in merged data: Nexos moves an unmoved marker up to 6" in each Command phase; Acolyte Iconward's Summon the Cult relocates a marker once per battle rather than losing it; Atalan Jackals re-enter from marker within 9" of a battlefield edge. Research notes a v1.1 errata reducing the marker setup distance from 9" to 8".
- **Play pattern**: interpretation — the army wants to arrive from unexpected angles mid-game, contest early with cheap Neophyte/Hybrid bodies, and mass reserves for a decisive wave. List construction rewards many small Cult Ambush-capable units over few durable ones.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Three of nine detachments map to TAKE AND HOLD; cheap OC-bearing battleline (Neophyte Hybrids 10/20-model blocks, Acolyte Hybrids) plus marker deployment lets scoring bodies appear on objectives late. |
| Purge the Foe | Moderate | Melee core (Purestrain Genestealers, Aberrants, Metamorphs) kills well but is fragile once visible; damage is concentrated in short-lived assault waves. |
| Reconnaissance | Moderate | Outlander Claw and Xenocult Masses both target RECONNAISSANCE and Atalan Jackals/Jackal Alphus give scout mobility; capped by actions being weak in 11e generally. |
| Priority Assets | Moderate | Xenocreed Congregation and Purestrain Broodswarm serve it, but the army prefers trading cheap bodies, not protecting expensive ones. |
| Disruption | Weak | Only Heroes Of The Uprising targets DISRUPTION, and it buffs four character models' damage rather than providing denial tools. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Heroes Of The Uprising (1DP → DISRUPTION)
- **Mechanics**: Kelermorph, Locus, Reductus Saboteur and Sanctus gain KILLER; their attacks may re-roll hit rolls of 1 and wound rolls of 1.
- **Rating**: Situational for Disruption — buffs only four named character units; no actual denial/screening mechanic.
- **Synergies**: Kelermorph and Reductus Saboteur — characters with multiple low-AP shots/mines where rerolling 1s compounds.
- **Limits**: not_modeled: applies only to the four named independent characters, not the army. Rerolls modeled as always-on; they are in fact unconditional per attack, so modeling risk is low here.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Purestrain Broodswarm (1DP → PRIORITY ASSETS)
- **Mechanics**: at end of the opponent's Fight phase, unengaged Purestrain Genestealer units may be removed into Strategic Reserves. PURESTRAIN-tagged (exclusive with other PURESTRAIN detachments).
- **Rating**: Situational for Priority Assets — hit-and-fade survival for one unit type only; protects nothing else in the list.
- **Synergies**: Purestrain Genestealers (Deep Strike + Infiltrators + Cult Ambush in merged data) loop back in from reserves repeatedly.
- **Limits**: not_modeled: voluntary end-of-phase redeploy has no vocabulary equivalent; tag exclusivity not expressible. Gate: unit must survive its own Fight phase engagement unengaged at the trigger moment.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Xenocult Masses (1DP → RECONNAISSANCE)
- **Mechanics**: each Neophyte Hybrids unit within a terrain area regains 3 lost wounds in your Command phase. HOSTS-tagged (exclusive with other HOSTS detachments).
- **Rating**: Situational for Reconnaissance — healing only matters when damaged units reach terrain; 3W on T3-ish bodies is modest attrition, not durability.
- **Synergies**: large 20-model Neophyte Hybrids blocks holding terrain-adjacent objectives (merged pricing: 135pts at 20 models).
- **Limits**: not_modeled: conditional in-terrain healing not expressible; HOSTS exclusivity not expressible.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Biosanctic Broodsurge (2DP → TAKE AND HOLD)
- **Mechanics**: Aberrants, Biophagus and Purestrain Genestealer units get +1 to Charge rolls; a charged unit from that set gains +1 Attacks on its melee weapons when selected to fight that turn.
- **Rating**: Situational for Take and Hold and Purge — payoff is real (+1A melee swings) but gated on charging with three specific unit types.
- **Synergies**: Aberrants (with Biophagus attached for FNP per merged data) and Purestrain Genestealers as the charge wave.
- **Limits**: research flags the +1 Attacks characteristic bonus as not expressible in the modifier vocabulary, and notes the +1-to-Charge component was mislabeled as advance_and_charge — treat engine output for this detachment as carrying NO detachment modifiers until config is corrected.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Brood Brothers Auxilia (2DP → TAKE AND HOLD)
- **Mechanics**: includes points-capped Astra Militarum allies (GSC warlord required); each AM shooting attack may mark one visible enemy within 18", GSC ranged attacks vs that marked unit gain +1 to Hit for the rest of the phase.
- **Rating**: Moderate for Take and Hold — AM bodies (infantry, tanks) add exactly what GSC lacks: ranged staying power and durable scoring; the mark buff is a genuine conditional damage lift.
- **Synergies**: AM tank/infantry gunlines marking targets for Neophyte/Acolyte shooting and Ridgerunner fire.
- **Limits**: not_modeled: +1 to Hit requires the ally to have shot earlier in the phase (sequencing); ally caps and keyword exclusions not expressible.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Final Day (2DP → PURGE THE FOE)
- **Mechanics**: includes Tyranid Vanguard Invader allies; GSC attacks gain +1 to Hit against enemies within 6" of a friendly Tyranid unit; Synapse units can drain D3+1 wounds from nearby GSC units at end of Movement phase to heal Tyranids and give their attacks +1 to Hit.
- **Rating**: Situational for Purge — the +1 aura is strong while it lasts but demands tight Tyranid/GSC positioning and self-damages the cult.
- **Synergies**: Tyranid frontline (synapse beasts screening) + GSC melee following behind the 6" aura boundary.
- **Limits**: not_modeled: aura conditionality, drain/heal loop, ally construction all unexpressible. Gate: enemy must sit within 6" of a Tyranid unit during your attack.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Outlander Claw (2DP → RECONNAISSANCE)
- **Mechanics**: Mounted/Vehicle models get +1 OC while not Battle-shocked; at end of your Command phase, objectives controlled with an Atalan Jackals unit in range stay under your control unless the opponent's Level of Control later exceeds yours (sticky-objective effect).
- **Rating**: Moderate for Reconnaissance — direct OC boost on the faction's mounted wing plus sticky objectives make it the most directly Recon-serving package among the nine detachments in this book.
- **Synergies**: Atalan Jackals, Jackal Alphus, Achilles Ridgerunners, Goliath Truck/Rockgrinder (all Mounted/Vehicle in merged data).
- **Limits**: not_modeled: OC boost scoped to MOUNTED/VEHICLE and non-Battle-shocked; sticky objective effect not expressible in vocabulary.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Xenocreed Congregation (2DP → PRIORITY ASSETS)
- **Mechanics**: Acolyte Hybrids, Hybrid Metamorphs and Neophyte Hybrids led by a CHARACTER re-roll Advance and Charge rolls; if the leader is a Magus, Primus or Acolyte Iconward, that model has Feel No Pain 3+ while leading.
- **Rating**: Situational for Priority Assets and Take and Hold — broad application across all three battleline types, but every component is gated on a CHARACTER being attached and FNP protects only the leader model.
- **Synergies**: Acolyte Iconward-led Hybrid Metamorphs or Aberrant-style blocks advancing up the board; Primus/Nexos attach options per merged Leader entries.
- **Limits**: not_modeled: rerolls require a led unit; FNP 3+ is leader-only while leading. Both conditional — never present them as army-wide.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

#### Host Of Ascension (3DP → TAKE AND HOLD)
- **Mechanics**: each GSC unit set up as Reinforcements gains Sustained Hits 1 and Ignores Cover on its weapons until the end of your next Fight phase.
- **Rating**: Situational for Take and Hold and Purge — powerful burst window that syncs with mass Cult Ambush/reserve lists, but the buff exists only inside the Reinforcements→next-Fight-phase window and 3DP consumes the entire budget.
- **Synergies**: whole reserve wave — Purestrains, Metamorphs, Acolyte Hybrids arriving via Cult Ambush/Deep Strike together.
- **Limits**: not_modeled: windowed buff never modeled as always-on (research explicitly time-boxes it). CP economy note: 3DP leaves nothing for a second detachment.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/genestealer-cults/

### Enhancements & Stratagems Worth Taking
- Interpretation, grounded in merged enhancement lists: Outlander Claw's Cartographic Data-leech (10pts) and Serpentine Tactics (10pts) are cheap fills on a detachment whose rule already does heavy lifting; Host Of Ascension's Assassination Edict (15pts) fits the reserve-wave plan; Biosanctic Broodsurge's Mutagenic Regeneration (10pts) keeps the Aberrant anvil alive between charges. No stratagem assessment attempted — stratagem text is outside the research corpus.

Overall army play pattern (interpretation): Genestealer Cults win by board presence asymmetry — flood cheap scoring bodies onto objectives early, hide the real threat in Cult Ambush markers and reserves, then deliver one overwhelming assault wave timed to strip the enemy off the middle while reinforcements reclaim what was conceded. The detachment roster reinforces this: every high-performing pick either adds foreign durability (Brood Brothers), multiplies OC (Outlander Claw), or sharpens the reserve wave (Host Of Ascension); none of them turn the cult into a grinding attrition force, and lists built to trade blow-for-blow consistently underperform the ambush pattern.
