# Expert: Leagues of Votann

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide Leagues of Votann-specific ground truth so Shredder can identify WRONG data.
> Scope: Faction Identity + Army Rules & Detachments Expert Assessment. Unit-by-unit cheat sheets not yet written.

## Faction Identity

- **Full name**: Leagues of Votann
- **Faction keyword**: `Faction: Leagues of Votann` (no `Imperium`/`Chaos` alignment)
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Yield Points (YP) resource economy plus the army rule's two modes — offensive **Hostile Acquisition** and defensive **Fortify Takeover** — with automatic switching at a 7+ YP threshold; some detachments modify generation or let you flip modes manually. Judging effects must never assume a specific mode is always-on.
- **Keywords every unit should carry**: `Faction: Leagues of Votann`, plus family keywords (`VOTANN`, `HERNKYN`, `CTHONIAN`, `KÂHL`, `ANATHEMA PSYKANA`-style scoped keywords used by detachment rules)
- **Sub-faction keywords**: Individual Leagues exist as flavour, not selectable sub-factions.

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/leagues-of-votann.json (2026-08-23, packs v1.1).

### Army Rule
- **Yield Points + mode switch**: The army accumulates Yield Points from game events; at a 7+ YP threshold it switches from Hostile Acquisition (offensive mode, objective-linked accuracy) to Fortify Takeover (defensive mode). Detachments add YP sources/spends or manual mode control.
- **Play pattern** *(interpretation)*: Votann lists plan around which mode they want active in which battle round — aggressive early pushes under Hostile Acquisition, then a defensive end-state under Fortify Takeover. YP-generating detachments accelerate that timeline; mode value is always conditional on game state, never assumed on.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Hostile Acquisition is inherently objective-linked and two detachments map here; Einhyr Hearthguard and Hearthkyn Warriors rank top of engine in Take and Hold natively. |
| Purge the Foe | Moderate | Dêlve Assault Shift deep-striking Beserks plus Needgaârd kill-fuelled YP; engine ranks Einhyr Hearthguard and Cthonian Beserks top of purge already. |
| Reconnaissance | Moderate | Farseekers buffs Hernkyn scouts (+1 to hit within 12") and Hernkyn Pioneers/Kapricus frames rank high in recon in engine. |
| Priority Assets | Moderate | Hearthband (3DP) is the faction's strongest detachment *for this army* because its closest-target condition matches the natural push-up play (see Overall Play Pattern), but it maps here alongside weaker elite-only options. |
| Disruption | Situational | Persecution Prospect pinning needs repeated multi-unit shooting into non-monster/non-vehicle targets; Armoured Trailblazers is deployment utility only. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Armoured Trailblazers (1DP → DISRUPTION)
- **Mechanics**: Sagitaur Spearhead — friendly SAGITAUR units gain Scouts 6" (pre-first-turn redeploy). Enhancements exist separately (e.g. Sagitaur IGNORES COVER) but are not part of the detachment rule.
- **Rating**: Situational for Disruption
- **Synergies:** Sagitaur-heavy transport screens grabbing early board position.
- **Limits**: Scouts is a pre-battle redeploy move, not a Move bonus; touches only Sagitaur units; no in-game stat change after turn 1.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Farseekers (1DP → RECONNAISSANCE)
- **Mechanics**: Eye of the Hunt — HERNKYN units' ranged attacks vs targets within 12" get +1 to hit.
- **Rating**: Situational for Reconnaissance
- **Synergies:** Hernkyn Yaegirs and Hernkyn Pioneers pushing into mid-range shooting lanes.
- **Limits**: HERNKYN units only, ranged only, targets within 12" only — multi-condition gate on a small unit family.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Hearthguard Covenant (1DP → PRIORITY ASSETS)
- **Mechanics**: Avatars of the Ancestors — KÂHL, EINHYR CHAMPION, EINHYR HEARTHGUARD and ÛTHAR THE DESTINED units re-roll wound rolls of 1 with ranged attacks targeting a unit within 9".
- **Rating**: Situational for Priority Assets
- **Synergies:** Einhyr Hearthguard gunlines (engine-ranked #1 across most dispositions by name presence) pushing to 9".
- **Limits**: Elite units only, ranged only, target within 9"; melee half of the army untouched; 3DP-tier detachments do the same job more broadly.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Brandfast Oathband (2DP → TAKE AND HOLD)
- **Mechanics**: Mobile Sensor Relays — each VOTANN TRANSPORT projects an aura: friendly VOTANN INFANTRY wholly within 6" have Sustained Hits 1 on ranged weapons.
- **Rating**: Moderate for Take and Hold
- **Synergies:** Hearthkyn Warriors riding Sagitaur/Hekaton Land Fortress transports and dismounting inside the aura.
- **Limits**: Infantry must be wholly within 6" of a transport — position-gated every phase; transport-dependent list shape; Sustained Hits value collapses vs single-model units.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Dêlve Assault Shift (2DP → PURGE THE FOE)
- **Mechanics**: Fury From The Dêlve — CTHONIAN BESERKS units gain Deep Strike and the BATTLELINE keyword. Stratagems granting rerolls/pile-in extension are CP-gated.
- **Rating**: Moderate for Purge the Foe
- **Synergies:** Cthonian Beserks (already engine-ranked in Purge the Foe) arriving turn 2+ directly into melee range; Battleline status fixes mission-slot pressure.
- **Limits**: Deployment mechanic, not a stat buff — no hit/wound improvement in the rule itself; key stratagem support costs CP; single-datasheet scope.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Mercenary Oathband (2DP → TAKE AND HOLD)
- **Mechanics**: Ruthless Reinvestment — replaces the army's automatic Hostile Acquisition/Fortify Takeover switching; units start with Hostile Acquisition, and at end of your Command phase you may spend 3 YP to manually flip between the two modes.
- **Rating**: Situational for Take and Hold
- **Synergies:** Lists that want Fortify Takeover active earlier (or Hostile Acquisition retained later) than the automatic 7+ YP threshold allows.
- **Limits**: Pure tempo-control tool — no stat effect of its own; underlying mode buffs belong to the shared army rule; 3 YP per flip competes with all other spends.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Needgaârd Oathband (2DP → PURGE THE FOE)
- **Mechanics**: Martial Leverage — gain 1 Yield Point each time an enemy unit is destroyed, accelerating progression toward the 7+ YP threshold that switches to Fortify Takeover and fuelling YP-spending rules.
- **Rating**: Moderate for Purge the Foe
- **Synergies:** Kill-heavy builds — Einhyr Hearthguard and Cthonian Beserks deleting units early to bank YP ahead of schedule.
- **Limits**: Indirect buff — value depends on how many kills happen and when; does nothing if the game runs clean early turns; economy effect has no modifier vocabulary equivalent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Persecution Prospect (2DP → DISRUPTION)
- **Mechanics**: Assailed From Every Angle — after a VOTANN unit shoots it may restrict its attacks to one non-monster/non-vehicle enemy unit and label it 'assailed'; hitting an already-assailed unit pins it: −2" Move and −2 to charge rolls until your next Shooting phase.
- **Rating**: Situational for Disruption
- **Synergies:** Massed small-arms volume (Hearthkyn Warriors, Hernkyn Yaegirs) tagging and pinning enemy infantry/mounted movers.
- **Limits**: Requires at least two shooting activations into the same target across turns; excludes Monster/Vehicle targets entirely; enemy-side debuffs have no modifier vocabulary equivalent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Hearthfyre Arsenal (2DP → PRIORITY ASSETS)
- **Mechanics**: Optimal Application — Iron-Masters/Memnyr Strategists holding non-home objectives generate Yield Points (max 2/turn); BRÔKHYR, IRONKIN STEELJACKS or ARKANYST EVALUATOR units may spend 1 YP when selected to shoot to re-roll hit rolls of 1 that phase.
- **Rating**: Situational for Priority Assets
- **Synergies:** Brôkhyr Thunderkyn and Ironkin Steeljacks shooting blocks fed by an objective-holding Iron-Master/Strategist pair.
- **Limits**: Shared contested YP economy with capped generation (max 2/turn); reroll requires spending 1 YP per unit per phase — never assume it on; requires specific HQs sitting on non-home objectives.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

#### Hearthband (3DP → PRIORITY ASSETS)
- **Mechanics**: Methodical Annihilation — all VOTANN models re-roll wound rolls of 1 when attacking the closest eligible target or any target within Engagement Range; KÂHL, EINHYR HEARTHGUARD and ÛTHAR THE DESTINED additionally improve AP by 1 on such attacks.
- **Rating**: Strong for Priority Assets
- **Synergies:** The whole push-up core — Einhyr Hearthguard, Hearthkyn Warriors and Ûthar The Destined advancing straight into the nearest foe matches both the rule's condition and the faction's natural play.
- **Limits**: Wound reroll and AP bonus require targeting closest eligible/in-Engagement-Range units — long-range target selection forfeits the buff; AP boost limited to three elite datasheets; 3DP cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/leagues-of-votann/

### Enhancements & Stratagems Worth Taking
*(interpretation — enhancement effect text is NOT yet captured in the research corpus except where noted; names verified against data/merged only. Verify effects against the faction pack before citing mechanics.)*
- **Hearthband** ships four enhancements (Bastion Shield, High Kâhl, Ironskein, Quake Multigenerator) on the detachment rated strongest for this army above — likely picks by placement alone.
- Armoured Trailblazers' research notes reference a Sagitaur IGNORES COVER enhancement among its options — existence noted, exact name/effect unverified.
- Dêlve Assault Shift stratagems include CP-gated rerolls and pile-in extension per the research corpus — exact names/costs unverified; do not assert specifics.

### Overall Play Pattern
*(interpretation)* Leagues of Votann plays as a mid-board attrition engine: durable short-range shooters advance under Hostile Acquisition, bank Yield Points, and transition to Fortify Takeover for the endgame. Hearthband is the clearest competitive expression because its condition (attack the nearest thing) is exactly what the army wants to do anyway; the YP-economy detachments are tempo levers whose value swings hard with game state, so they rate Situational rather than as defaults. Weaknesses are the faction's modest mobility outside scouts and detachment rules fragmented across keyword families — few rules touch the whole army at once.

Assumptions:
- opponent unknown (all-comers)
- no cover factored beyond what detachment rules state
- YP economy assumed contested (spends compete); mode assumed conditional, never always-on
- no CP economy modeling for stratagems beyond what the research corpus states
