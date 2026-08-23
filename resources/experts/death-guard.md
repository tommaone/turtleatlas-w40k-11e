# Expert File: Death Guard

## Faction Identity

- **Full name**: Death Guard (BSData catalogue faction: "Death Guard")
- **Faction keyword**: `Faction: Death Guard`; daemon-aligned units carry `FACTION: PLAGUE LEGIONS`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: **Nurgle's Gift** — enemies within Contagion Range become Afflicted with a plague effect; the corpus documents effect variants including a save penalty, a melee hit penalty, and a movement/OC/leadership penalty (per Champions Of Contagion's re-selection rule). Contagion Range is a stat some characters and detachments modify.
- **Sub-faction keywords**: `Faction: Plague Legions` (daemon allies)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/death-guard.json (2026-08-23,
packs v1.1). 9 detachments, all chapter-specific (no SM codex inheritance —
Death Guard is not an Astartes successor pack).

### Army Rule
- **Nurgle's Gift**: enemy units within Contagion Range are Afflicted; Affliction applies one of several plague effects (save penalty / melee hit penalty / movement-OC-leadership penalty per the corpus). Detachments extend reach (Paragons, Tallyband), bypass proximity (Mortarion's Hammer), or exploit the Afflicted state (Death Lord's Chosen mortal wounds).
- **Play pattern** *(interpretation)*: attrition army — durable infantry walk the Contagion aura forward while debuffs degrade whatever comes close; detachment choice decides whether you hold ground, flood the board, or reach out and afflict from range.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Virulent Vectorium makes held objectives sticky AND contagious — the army-rule synergy is direct; Champions Of Contagion adds control flexibility. |
| Purge the Foe | Moderate | Mortarion's Hammer extends Affliction to distant targets; Death Lord's Chosen adds conditional mortal wounds — all dice/conditional gated. |
| Reconnaissance | Moderate | Flyblown Host infiltrates two Plague Marines units forward; Contagion Engines let daemon engines shoot after Advancing. |
| Priority Assets | Situational | Paragons Of Putrescence only widens character contagion auras — support-layer value. |
| Disruption | Moderate | Shamblerot Poxwalker flood and Tallyband daemon allies contest and screen, but the army's slow movement caps tempo plays. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Contagion Engines (1DP → RECONNAISSANCE)
- **Mechanics**: Warped And Rusted Animus — designated daemon-engine units (Foetid Bloat-Drone class, Blight-Haulers, Helbrutes) gain a keyword letting ranged weapons fire after Advancing. ENGINES tag: cannot combine with other ENGINES-tagged detachments.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Foetid Bloat-Drone With Heavy Blight Launcher mobile fire bases keeping pace with the infantry wall.
- **Limits**: Unit-gated to specific daemon engines; ENGINES tag restricts combination; 1DP add-on scope.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Flyblown Host (1DP → RECONNAISSANCE)
- **Mechanics**: Verminous Haze — up to two friendly Plague Marines units gain Infiltrators at battle formation. FLYBLOWN tag prevents combination with other FLYBLOWN detachments.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Two Plague Marines blocks starting on mid-board markers — for an otherwise slow army this is the fastest route to early board presence.
- **Limits**: Two-unit cap; deployment trickery only, no combat modifier; FLYBLOWN tag.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Paragons Of Putrescence (1DP → PRIORITY ASSETS)
- **Mechanics**: Hypervirulent Strains — friendly DEATH GUARD CHARACTER units get +3 inches Contagion Range, hard-capped at 12 inches total.
- **Rating**: Situational for Priority Assets
- **Synergies**: Daemon Prince Of Nurgle / Malignant Plaguecaster-centred aura stacks spreading Nurgle's Gift across the midfield.
- **Limits**: Aura-radius buff only — no offensive/durability stats; cap limits stacking; 1DP add-on scope.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-death-guard

#### Champions Of Contagion (2DP → TAKE AND HOLD)
- **Mechanics**: Manifold Maladies — re-select which Nurgle's Gift plague effect Afflicted enemies suffer at the start of each battle round (instead of locking one in at list building).
- **Rating**: Moderate for Take and Hold
- **Synergies**: Rotating between save penalty (shooting turns) and melee hit penalty (opponent's assault turns) around objective-holding Plague Marines / Deathshroud Terminators.
- **Limits**: Flexibility upgrade only — adds no raw stat value; payoff depends on reading each round correctly.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Death Lord'S Chosen (2DP → PRIORITY ASSETS)
- **Mechanics**: Deadly Vectors — in the opponent's Command phase roll 2D6 per Afflicted enemy unit (-1 if below half strength); each result of 6 or less deals D3 mortal wounds. Terminator-character-focused enhancements.
- **Rating**: Situational for Priority Assets
- **Synergies**: Lord Of Virulence / Lord Of Contagion-led Blightlord Terminators holding ground while the passive grind chips wounded units down.
- **Limits**: Dice-gated (needs rolls of ≤6 on 2D6); requires targets already Afflicted; enhancements restricted to Terminator characters.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Mortarion'S Hammer (2DP → PURGE THE FOE)
- **Mechanics**: Miasmic Bombardment — at start of each battle round designate 1/2/3 enemy units more than 12 inches away; those count as Afflicted without contagion-range proximity. ENGINES tag restriction applies.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Mortarion plus vehicle shooting reaching out to pre-debuff backfield targets the aura can't touch yet.
- **Limits**: Remote Affliction enables other conditional effects rather than dealing damage directly; unit-count cap scales by battle size; ENGINES tag.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Shamblerot Vectorium (2DP → DISRUPTION)
- **Mechanics**: Numberless Horde — from battle round 2 onward receive a free unit of ten Poxwalkers into Strategic Reserves each applicable turn; Poxwalkers also count as Battleline.
- **Rating**: Situational for Disruption
- **Synergies**: Typhus leading Poxwalker waves; free bodies screening the advance and capping objectives by presence.
- **Limits**: Spawn window starts round 2; Poxwalkers are low-quality bodies — flood trades space for time, not kills.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Tallyband Summoners (2DP → DISRUPTION)
- **Mechanics**: Reverberant Rancidity — allied Plague Legions (daemon) units within 7 inches of a Death Guard unit gain the Nurgle's Gift aura, while Death Guard units within 7 inches of daemons gain +3 inches Contagion Range. Unlocks daemon allies up to a points cap.
- **Rating**: Situational for Disruption
- **Synergies**: Nurglings/Plaguebearers screens extending contagion coverage; Great Unclean One or Rotigus anchoring the joint aura web.
- **Limits**: Both halves proximity-dependent (7 inches); requires spending points on daemon allies; ally mechanic unmodeled.
- **_source**: https://1d6chan.miraheze.org/wiki/Warhammer_40,000/11th_Edition_Tactics/Death_Guard

#### Virulent Vectorium (3DP → TAKE AND HOLD)
- **Mechanics**: Worldblight — at end of your Command phase, objectives controlled by friendly Death Guard units become secured (sticky); while held, enemies within range are Afflicted by your chosen plague. Reroll-focused stratagem toolbox targeting Afflicted units.
- **Rating**: Strong for Take and Hold
- **Synergies**: Plague Marines / Deathshroud Terminators planting flags that stay yours after falling back; the contagion-on-held-objectives clause turns every marker into army-rule coverage.
- **Limits**: Sticky control still requires taking the objective first; rerolls CP-gated and target-gated to Afflicted units.
- **_source**: https://www.tabletopbattles.com/detachment-focus-virulent-vectorium/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* The corpus documents enhancement families thinly for this faction: Paragons carries action-while-shooting and OC-boost stratagems (CP-gated, character-only); Virulent Vectorium's reroll stratagems are the named CP sink but require Afflicted targets. No single standout enhancement emerges from the sources — treat enhancement picks as unresolved pending primary-source verification.

### Overall Army Play Pattern
*(interpretation)* Death Guard wins by making the board itself hostile: Nurgle's Gift degrades everything near the line of advancing Plague Marines, and the best detachments amplify that axis directly — Virulent Vectorium converts held objectives into permanent contagion zones, Champions Of Contagion retunes the debuff every round, and Mortarion's Hammer projects Affliction beyond the aura's reach. Expect a mid-tempo attrition game: take ground early with Flyblown-infiltrated Plague Marines, anchor it, and let sticky objectives plus passive debuffs out-score faster armies. The weaknesses are structural — Priority Assets has no real tool, and every offensive-leaning detachment is dice- or condition-gated, so games that demand burst damage find the faction playing its worst plan.
