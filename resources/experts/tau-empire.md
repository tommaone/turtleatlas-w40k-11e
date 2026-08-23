# T'au Empire

## Faction Identity

- **Full name**: T'au Empire (BSData catalogue: "T'au Empire")
- **Faction keyword**: T'AU EMPIRE
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Observer/Guided pairing system — units paired with an Observer become Guided against the Spotted target (research corpus: Kauyon entry, "Guided units shooting their Spotted target"; bsdata datasheet abilities reference Observer/Guided/Spotted interactions); 11e hidden/detection-range mechanics feature heavily in corpus detachments
- **Keywords every unit should carry**: T'AU EMPIRE
- **Sub-faction keywords** (per research corpus): BATTLESUIT, AUXILIARIES, KROOT, VESPID STINGWINGS, PATHFINDER TEAM / STEALTH BATTLESUITS (detection-rule units)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/tau-empire.json (2026-08-23, packs v1.1).

### Army Rule
- **Observer/Guided (Spotted)**: units act as Observers for paired units; the Guided unit gains benefits against its Spotted unit (Kauyon's ignore-modifiers clause and Mont'Ka's Lethal Hits clause are both explicitly gated on "Guided units shooting their Spotted target"). The corpus does NOT reproduce the full army-rule text — treat the complete Guided benefit list as partially unverified here.
- **Play pattern** *(interpretation)*: shooting is built in pairs — every damage unit wants an Observation partner, which taxes list slots and rewards tight unit counts of high-quality shooters over spam.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Kroot Hunting Pack gives Kroot split invulns and objective fighting bonuses; gunlines can hold but nothing sticky-objective grade exists in corpus. |
| Purge the Foe | Moderate | Real damage packages but every component is conditional: Retaliation Cadre gates +1S at 12"/+1AP at 8", Kauyon's Sustained Hits only fires rounds 3–5, Mont'Ka's Lethal Hits only rounds 1–3 AND for Guided units — no unconditional damage anchor exists anywhere in the corpus. |
| Reconnaissance | Moderate | Kauyon is tagged Recon and Advanced Acquisition Cadre plays the detection game natively; value depends on out-of-corpus hidden rules. |
| Priority Assets | Situational | Experimental Prototype Cadre protects/buffs characters with range extension but no defensive mechanics appear anywhere in corpus. |
| Disruption | Situational | Auxiliary Cadre prey-marking (+3" enemy detection) is genuine anti-stealth disruption but niche. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Advanced Acquisition Cadre (1DP → RECONNAISSANCE)
- **Mechanics**: Expert Fieldcraft — PATHFINDER TEAM / STEALTH BATTLESUITS may make ranged attacks without losing hidden status. Enhancements alter own/enemy detection ranges (own -3", enemy +9"); stratagems secure a held objective, let actions coexist with shooting, or give +1 Sv to hidden units.
- **Rating**: Situational for Reconnaissance / Disruption
- **Synergies**: Pathfinder Team, Stealth Battlesuits — the faction's native scouting units.
- **Limits**: entirely dependent on 11e hidden/detection rules not covered by the modifier vocabulary; every listed effect (remain-hidden, range shifts, conditional +1 Sv) unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Auxiliary Cadre (1DP → DISRUPTION)
- **Mechanics**: Integrated Command Structure — KROOT/VESPID STINGWINGS units prey-mark one visible enemy within 12" (that enemy suffers +3" detection range); GHOSTKEEL/STEALTH BATTLESUITS carry a 6" aura letting friendly Kroot/Vespid shoot while remaining hidden. AUXILIARIES-tagged; cannot combine with another AUXILIARIES detachment.
- **Rating**: Situational for Disruption
- **Synergies**: Kroot Carnivores, Kroot Farstalkers, Vespid Stingwings screened by Stealth Battlesuits or Ghostkeel.
- **Limits**: anti-stealth payoff only matters vs armies that use hiding; stay-hidden aura unmodeled; tag exclusivity; auxiliaries-only scope excludes the battlesuit gunline from all benefits.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Experimental Prototype Cadre (1DP → PRIORITY ASSETS)
- **Mechanics**: Superior Craftsmanship — friendly BATTLESUIT CHARACTER ranged attacks gain +6" Range. Enhancements boost specific named weapon types (Flamer/Plasma/AFP stat bumps); stratagems add ammunition lethality and protection to Characters. BATTLESUIT-tagged; cannot combine with another BATTLESUIT detachment.
- **Rating**: Moderate for Purge the Foe / Priority Assets — simple, always-on, zero conditions
- **Synergies**: Commander in Coldstar/Enforcer Battlesuit, Commander Farsight, Commander Shadowsun — kiter commanders holding maximum-distance firing lanes.
- **Limits**: character-models-only scope; range bonus has no modifier-vocabulary equivalent (unmodeled); enhancement stat boosts individually unsourced beyond the corpus summary.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Kroot Hunting Pack (2DP → TAKE AND HOLD)
- **Mechanics**: Hunter's Instincts — KROOT attacks add +1 to Hit vs targets below Starting Strength, plus +1 to Wound too if target is Below Half-strength. Skirmish Fighters — KROOT models have 6+ invuln vs melee and 5+ vs ranged. KROOT CARNIVORE units gain Battleline.
- **Rating**: Situational for Take and Hold (damage bonuses require the target to be already damaged)
- **Synergies**: massed Kroot Carnivores/Hounds/Farstalkers/Krootox Rampagers — cheap bodies that finish wounded targets.
- **Limits**: hit/wound bonuses both conditional on target damage state (never-on turn 1 vs fresh targets); invuln modeled at worst-case 6+ (melee) — ranged actually gets 5+, attack-type split unrepresentable in vocabulary; KROOT-only scope.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Kauyon (2DP → RECONNAISSANCE)
- **Mechanics**: Patient Hunter — in battle rounds 3–5, ALL T'AU EMPIRE ranged weapons gain Sustained Hits 1; additionally in rounds 3–5, Guided units shooting their Spotted target ignore ALL Ballistic Skill and hit-roll modifiers. An enhancement lets a led unit start benefiting from round 2 instead.
- **Rating**: Situational for Purge the Foe (round-window rule — dead weight in rounds 1–2 without the enhancement)
- **Synergies**: whole-army Sustained Hits on every ranged profile; Guided pairs (Pathfinder-spotted gunlines) become modifier-proof.
- **Limits**: round-gated (corpus flags sustained_hits would apply but ONLY rounds 3–5) — the army must survive to collect; ignore-modifiers requires BOTH the Guided state AND correct target priority.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Mont’Ka (3DP → PRIORITY ASSETS)
- **Mechanics**: Killing Blow — in battle rounds 1–3, T'AU EMPIRE ranged weapons have Assault (shoot after Advance/Fall Back); additionally rounds 1–3, Guided units' ranged weapons have Lethal Hits. An enhancement extends the window to battle round 4 for a led unit.
- **Rating**: Situational for Purge the Foe (mirror image of Kauyon — front-loaded window)
- **Synergies**: mobile battlesuit lists (Coldstar commanders, Stealth Battlesuit skirmishers) repositioning while shooting in the opening rounds; Guided Lethal Hits punishes exposed vehicles early.
- **Limits**: everything expires after round 3 (round 4 for one enhanced led unit); Assault unmodeled; Lethal Hits needs the Guided state maintained; full-budget 3DP for a time-boxed package.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

#### Retaliation Cadre (3DP → PURGE THE FOE)
- **Mechanics**: Bonded Heroes — each time a T'AU EMPIRE BATTLESUIT model makes a ranged attack at a unit within 12", that attack gains +1 Strength; per errata, +1 Armour Penetration applies when the target is within 8" (errata tightened 9" to 8").
- **Rating**: Moderate for Purge the Foe — always-on within its range bands and stacks across every battlesuit
- **Synergies**: broadside/crisis battlesuit walls advancing to 12"/8" brackets; Commander Shadowsun-led suit clusters.
- **Limits**: BATTLESUIT-models-only (infantry/Kroot get nothing); two distance gates — +1S inside 12", +1AP only inside 8"; closing to 8" puts fragile suits in enemy threat range.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/t-au-empire/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents enhancements only at summary level)*
- Kauyon's round-2 extension enhancement (for a led unit): the only way to salvage value from the back-loaded window earlier — worth considering if the meta demands early pressure. Corpus names no individual enhancement title; verify before quoting.
- Mont'Ka's round-4 extension enhancement (led unit): stretches the killing window by one round; same verification caveat.
- Advanced Acquisition Cadre's detection-range enhancements (-3" own visibility / +9" enemy): powerful on paper against hidden-army metas, entirely dependent on detection rules the corpus doesn't model.
- The corpus does NOT catalogue general stratagem names for this faction — no picks offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: The grounded T'au assessment is a study in windows and pairings. Every damage detachment ties its payoff to either a clock (Kauyon rounds 3–5, Mont'Ka rounds 1–3) or a bracket (Retaliation Cadre's 12"/8" rings), and the army rule itself imposes a pairing tax — Guided benefits exist only against Spotted targets with an Observer invested. That produces two coherent builds: the front-loaded battlesuit blitz (Mont'Ka or Retaliation Cadre, accepting 8"-range risk to end games before the window closes), and the patient late-game gunline (Kauyon, surviving rounds 1–2 with zero offensive detachment support to harvest modifier-proof Sustained Hits fire). The auxiliary/detection detachments form a third, matchup-dependent lane whose real power lives in 11e hidden rules outside the modeled vocabulary — treat those ratings as the least certain in this file. Notably absent from the corpus: any defensive mechanic protecting the famously fragile shooting units, which caps how aggressively either build can position.
