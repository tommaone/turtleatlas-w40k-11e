# Expert Assessment: Chaos Titan Legions (Titanicus Traitoris) — 11th Edition

## Faction Identity

- **Full name**: Chaos - Titanicus Traitoris (BSData catalogue name — its own merged file with Chaos-prefixed titan datasheets). No separate GW product/pack carries chaos titans; the rules are an overlay on the Adeptus Titanicus pack, per research
- **Faction keyword**: TITANICUS TRAITORIS (substituted for ADEPTUS TITANICUS; IMPERIUM → CHAOS on all datasheets and army rules) — this substitution is stated at pack level in the research corpus; merged adapter output currently shows only neutral unit keywords (VEHICLE / WALKER / TITANIC / TOWERING / FRAME / model name) with no CHAOS or TITANICUS TRAITORIS keyword applied
- **Game edition**: 11th (Adeptus Titanicus Faction Pack v1.0 June 2026 / v1.1 July 2026 — per research corpus)
- **Core mechanics**: Titanicus Traitoris army rule — players use the four ADEPTUS TITANICUS datasheets (Warhound, Reaver, Warbringer Nemesis, Warlord) to represent traitor titans by substituting IMPERIUM→CHAOS and ADEPTUS TITANICUS→TITANICUS TRAITORIS keywords, using the loyalist points values. Inherits Towering Example: pure-titan armies skip detachment selection entirely and take Take and Hold. There is NO separate Chaos faction pack containing titans (June 2026 Chaos packs cover CSM/DG/EC/TS/WE/Daemons/Knights only, per research).
- **Keywords every unit should carry** (per merged adapter output): VEHICLE, WALKER, TITANIC, TOWERING, FRAME, plus each model's own name keyword (e.g. "Chaos Reaver Titan" as the datasheet name). Per the pack's substitution rule these models should also carry CHAOS / TITANICUS TRAITORIS — not reflected in current merged output; treat per-unit keywords here as adapter lag, pack text as authoritative
- **Sub-faction keywords** (if any): none modeled in merged data

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/chaos-titan-legions.json
(2026-08-23, packs v1.1). Edition snapshot date mandatory on this section.

### Detachment list
None — by design. Because the traitor rule is a keyword-substitution overlay on
the same Adeptus Titanicus pack whose Towering Example rule makes pure-titan
armies SKIP the Select Detachment Rules step entirely (Take and Hold disposition
instead), chaos titans inherit the identical zero-detachment structure. No chaos
titan detachment list exists anywhere per research corroboration (40k.app returns
no detachments for any titan faction; no 2026 pack coverage shows one).

### Army Rule
- **Titanicus Traitoris**: keyword substitution overlay on the Adeptus Titanicus rules — same datasheets, same profiles, same loyalist points values, with IMPERIUM→CHAOS and ADEPTUS TITANICUS→TITANICUS TRAITORIS swapped throughout.
- **Inherited Towering Example**: pure-titan armies ignore the Select Detachment Rules step; one titan is WARLORD; Take and Hold disposition is forced. All mechanics consequences are identical to the loyalist entry (see resources/experts/titan-legions.md).
- **How chaos players field titans in 11e** (per research):
  1. Pure TITANICUS TRAITORIS army — same structure and practical points ceiling as loyalist pure-titan play (Warhound ~1,100pts, Warlord ~3,500pts); no detachments, no enhancements or stratagems of their own.
  2. Ally into an existing CHAOS army — ⚠ SECONDARY-SOURCE ONLY: research reports that Traitoris titans can reportedly be allied into a Chaos army (adding the TITANICUS TRAITORIS faction keyword), analogous to the loyalist Titanic Support single-model ally slot. This route must be verified against the pack PDF before being treated as fact.

### Disposition Fit (current meta verdict)
The disposition is forced by the inherited army rule — Take and Hold is not chosen.
Assessed under that constraint:

| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Forced by design; identical reasoning to loyalist titans — massive multi-wound OC blocks that cannot be shifted once planted. |
| Purge the Foe | Strong (unreachable) | Same weapon mass as loyalist datasheets; unreachable as a chosen disposition for a pure-titan force, but a single allied traitor titan delivers this value inside a CHAOS army's own plan. |
| Reconnaissance | Weak (by construction) | One-to-four models cannot contest wide boards regardless of alignment. |
| Priority Assets | Situational (by construction) | Survivability is intrinsic profile scale, not granted; no rule layer supports asset protection. |
| Disruption | Weak (by construction) | No denial mechanics on any of the four datasheets. |

### Detachment Assessments
<!-- none exist — by design -->

#### Detachments (none — by design)
- **Mechanics**: inherited Towering Example removes the Select Detachment Rules step; the substitution overlay adds no detachment layer. Research verdict: ZERO detachments is CORRECT — there is no separate Chaos titan rules product in 11e to carry detachments.
- **Rating**: Not applicable — no detachments exist to rate.
- **Synergies**: n/a at the detachment level. The practical synergy path (pending verification of the ally route) would be one traitor titan slotted into a CHAOS army — e.g. anchoring a World Eaters or Chaos Knights battle line with its datasheet weapons while the host army's detachments do the buffing. The allied titan gains no detachment rules either way.
- **Limits**: ⚠ the ally-into-Chaos route is flagged secondary-source-only in research — verify against the pack PDF before relying on it. Points values are the loyalist ones (research). No engine modifiers exist for this faction; any engine output showing detachment modifiers for chaos-titan-legions is wrong by definition.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/adeptus-titanicus/

### Enhancements & Stratagems Worth Taking
- None exist — the substitution overlay grants no enhancement or stratagem layer beyond what the Adeptus Titanicus pack provides (none). Titans fielded via the (unverified) Chaos ally route use the host army's enhancements/stratagems, which never affect the allied titan unless its own datasheet says so.

Overall army play pattern (interpretation): mechanically this faction is the loyalist Adeptus Titanicus entry wearing a different keyword set — every judgement from the titan-legions assessment carries over unchanged, including the forced Take and Hold disposition, the zero-detachment structure, and the practical reality that matched-play presence comes through single-model ally slots rather than pure-titan armies. The only genuinely distinct facts here are negative or unverified: there is no dedicated Chaos titan product, and the reported ability to slot a Traitoris titan into a CHAOS army remains secondary-sourced until checked against the pack itself.
