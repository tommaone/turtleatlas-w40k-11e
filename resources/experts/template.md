# Expert Template: {FACTION NAME}

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide faction-specific ground truth so Shredder can identify WRONG data.
> Format: concise cheat-sheet style. No fluff. Per-unit expectations + red flags.

## Faction Identity

- **Full name**: {BSData catalogue name}
- **Faction keyword**: {e.g. "Faction: Grey Knights"}
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: {unique faction rule(s), e.g. "Gate of Infinity (Deep Strike + teleport)"}
- **Keywords every unit should carry**: {shared keywords}
- **Sub-faction keywords** (if any): {e.g. "Chapter: Ultramarines"}

## Stat Baseline Expectations

Use these as a sanity check for any unit's stat line:

| Stat | Typical range | Notes |
|------|--------------|-------|
| M | 4"-12" | Infantry 6", Cavalry 10", Vehicles 6-12" |
| T | 3-14 | Infantry 4-5, Bikes 5-6, Vehicles 6-14 |
| Sv | 2+-7+ | Power armour 3+, Terminator 2+, Guard 5+ |
| W | 1-8+ | Basic Infantry 1-2, Terminators 3, Characters 4-6 |
| LD | 4+-8+ | Elite 6+, Horde 7-8+ |
| OC | 0-2 | Battleline 2, Elite 1, Vehicles 0 |
| InSv (invuln) | 4+-6+ | Characters often get invuln saves |

## Unit-by-Unit Cheat Sheet

### {Unit Name 1}
- **Role**: {character/battleline/elite/vehicle/etc}
- **Stats**: M{X}" T{Y} Sv{Z}+ W{W} LD{LD}+ OC{OC} InSv{optional}
- **Keywords**: [{list of expected keywords}]
- **Weapons expected**: [{weapon names with key stats}]
- **Abilities expected**: [{ability names}]
- **Rules expected**: [{e.g. Deep Strike, Leader, etc}]
- **Red flags**:
  - {specific things to watch for this unit}

### {Unit Name 2}
...etc

## Generic Red Flags (all units in this faction)

- {Flag 1}: {why it's wrong}
- {Flag 2}: {why it's wrong}
- ...

## Weapon Profile Reference

Common weapons and their CORRECT profiles for this faction:

| Weapon | Range | A | BS/WS | S | AP | D | Keywords |
|--------|-------|---|-------|---|---|---|----------|
| {weapon} | {range} | {A} | {BS} | {S} | {AP} | {D} | {keywords} |

## Ability Reference

| Ability | Expected effect |
|---------|----------------|
| {name} | {brief expected effect — enough to spot a swapped/missing ability} |

## Known Tricky Areas

- {Nuance 1}: {what to double-check}
- {Nuance 2}: {what to double-check}

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/<faction>.json (2026-08-23,
packs v1.1). Edition snapshot date mandatory on this section.

### Army Rule
- **{rule name}**: {mechanics paraphrase}
- **Play pattern**: {how it shapes list construction / tempo}

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong/Moderate/Situational/Weak | {why} |
| Purge the Foe | ... | ... |
| Reconnaissance | ... | ... |
| Priority Assets | ... | ... |
| Disruption | ... | ... |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### {DETACHMENT NAME} ({dp}DP → {objective})
- **Mechanics**: {paraphrase from research file}
- **Rating**: {Strong/Moderate/Situational/Weak} for {disposition(s)}
- **Synergies**: {which unit archetypes light up — reference engine top units by name only}
- **Limits**: {not_modeled items, conditional gates, CP economy}
- **_source**: {research URL}

### Enhancements & Stratagems Worth Taking
- {top picks with why — labelled interpretation}
