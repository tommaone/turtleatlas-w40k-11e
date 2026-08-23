# Expert: Astra Militarum

> Injected into Shredder's adversarial validation prompt.
> Purpose: provide Astra Militarum-specific ground truth so Shredder can identify WRONG data.
> Scope: Faction Identity + Army Rules & Detachments Expert Assessment. Unit-by-unit cheat sheets not yet written.

## Faction Identity

- **Full name**: Astra Militarum
- **Faction keyword**: `Faction: Astra Militarum` (all units also `Imperium`)
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Orders system — Officer characters issue Orders to infantry units; some detachments extend Orders to Squadron (vehicle) units. Army is split between `Regiment` (infantry) and `Squadron` (tank) keyword families, which detachments buff separately or together.
- **Keywords every unit should carry**: `Imperium`, `Faction: Astra Militarum`, plus `Regiment` (infantry) / `Squadron` (vehicles) family keywords
- **Sub-faction keywords**: Regimental identities (e.g. Cadian, Krieg, Tempestus) appear as unit names/keywords rather than selectable sub-factions

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/astra-militarum.json (2026-08-23, packs v1.1).

### Army Rule
- **Orders system**: Officers issue Orders that modify how infantry (and in some detachments vehicles) act — accuracy, run-and-shoot, reactive moves. Detachment rules consistently gate their buffs on a unit being "affected by an Order" (e.g. Grizzled Company's re-roll hit rolls of 1).
- **Play pattern**: *(interpretation)* The army lives and dies on Order economy: every Officer is an accuracy multiplier, so list construction pushes toward cheap Officers spread across many infantry blocks plus a vehicle wing. Units that can't receive Orders get proportionally less from the faction's best detachments.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Four detachments map to Take and Hold; engine-ranked bodies (Cadian Shock Troops, Death Korps Of Krieg, Bullgryn Squad) hold ground well, but only Grizzled Company adds meaningful accuracy on top. |
| Purge the Foe | Moderate | Hammer Of The Emperor / Steel Hammer enable tank pushes; engine top melee is thin (Attilan Rough Riders, Ogryn Squad), so purge output leans on shooting not assaults. |
| Reconnaissance | Moderate | Recon Element + Designation Force + Mechanised Assault; engine ranks Lord Solar Leontus, Attilan Rough Riders and Tempestus Aquilons highly here. |
| Priority Assets | Moderate | Bridgehead Strike (Scion drop accuracy) and Grizzled Company both target this; Kasrkin/Aquilons rank high in engine output. |
| Disruption | Situational | Only Siege Regiment maps here and all three of its modes are once-per-round choices with dice/range gates. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Abhuman Auxiliaries (1DP → TAKE AND HOLD)
- **Mechanics**: Ogryn, Bullgryn and Ratling units gain a faction keyword; Commissars gain an extra accuracy-boosting order and can each issue one order to an Abhuman unit. Cannot be paired with another detachment sharing its tag.
- **Rating**: Situational for Take and Hold
- **Synergies**: Bullgryn Squad (engine-ranked in Take and Hold) as ordered objective body; Ogryn Squad screen.
- **Limits**: Buff scope restricted to three Abhuman datasheets; Commissar BS boost is order-dependent, not always-on; tag exclusivity constrains list-building.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Bridgehead Strike (1DP → PRIORITY ASSETS)
- **Mechanics**: If the Warlord is a Militarum Tempestus Officer: Scions count as Battleline and gain +1 OC; any Tempestus unit set up this turn gets +1 to hit when selected to shoot.
- **Rating**: Situational for Priority Assets
- **Synergies**: Tempestus Aquilons and Scions drop turns; engine ranks Aquilons across multiple dispositions.
- **Limits**: Hard gate on Tempestus Warlord; +1 OC only for Scions; +1 to hit only on the deployment turn — nothing afterwards.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Designation Force (1DP → RECONNAISSANCE)
- **Mechanics**: Scout Sentinels and smoke-equipped infantry may mark one visible enemy within 12" in the Shooting phase; that enemy's detection range increases by 3" for the round, widening indirect-fire targeting.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Indirect-fire battery units (e.g. Basilisk); Scout Sentinel as designated marker.
- **Limits**: Requires spending a Shooting phase on marking; detection-range mechanic has no modifier equivalent and only matters while Hidden-style rules apply.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Armoured Infantry (2DP → TAKE AND HOLD)
- **Mechanics**: Officers can issue Orders to Squadron units as well as infantry; new reactive-move Order lets an armoured-skirmisher unit make a short normal move when an enemy ends a move within 8".
- **Rating**: Moderate for Take and Hold
- **Synergies**: Leman Russ squadron wings finally receiving Orders; Chimera/Taurox skirmishers for the reactive move.
- **Limits**: Reactive move triggers only on enemy moves within 8", once per turn per unit; excludes artillery and very high-wound vehicles.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Combined Arms (2DP → TAKE AND HOLD)
- **Mechanics**: Regiment ranged attacks get Lethal Hits; Squadron ranged attacks get Lethal Hits but only against Monster/Vehicle targets.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Massed lasgun infantry (Cadian Shock Troops, Death Korps Of Krieg) into infantry targets; Russ/Hydra shots into vehicles.
- **Limits**: Doubly target-type restricted — Regiment shooters lose Lethal Hits vs Monsters/Vehicles, Squadron shooters only have them vs Monsters/Vehicles; always-on modeling would misapply it.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Hammer Of The Emperor (2DP → PURGE THE FOE)
- **Mechanics**: Squadron units that Advance automatically add 6" (no roll) and may move through Engagement Range though not end there.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Russ/Leman-Russ-family squadrons repositioning full distance every turn; Hellhound-class fast tanks closing to torrent range.
- **Limits**: Fixed +6" replaces the random Advance roll (delta vs ~average Advance is smaller than it looks); crossing but not ending in Engagement Range.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Mechanised Assault (2DP → RECONNAISSANCE)
- **Mechanics**: All AM ranged attacks get +1 to Wound rolls in a turn in which the attacking model disembarked from a Transport.
- **Rating**: Situational for Reconnaissance
- **Synergies**: Chimera-borne infantry squads; Taurox-rushed Tempestus units disembarking into rapid-fire range.
- **Limits**: +1 to wound applies only on the disembark turn — one-turn bursts requiring transport investment.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Siege Regiment (2DP → DISRUPTION)
- **Mechanics**: Each battle round choose one mode: distant (>12") enemies may become Shaken (−2" Move, −2 charge) on 5+ rolls capped by battle size; distant enemies lose Benefit of Cover; or friendly units gain Stealth.
- **Rating**: Situational for Disruption
- **Synergies**: Artillery-heavy builds (Basilisk, Hydra batteries) benefiting from cover-strip on distant targets.
- **Limits**: One mode per round; Shaken is dice-gated (5+); cover-strip only affects enemies >12" away; Stealth choice forecloses the offensive modes that round.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Steel Hammer (2DP → PURGE THE FOE)
- **Mechanics**: Titanic and Squadron units shoot at enemies within Engagement Range without the close-range penalty (excludes Indirect Fire; only if no other friendly unit is engaged with that enemy). Titanic units can optionally gain CHARACTER.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Tank-line pushes where vehicles grind forward and shoot into combat; Baneblade-class Titanic hulls as enhancement/Warlord carriers.
- **Limits**: Void if another friendly unit is engaged with the target; no benefit for Indirect Fire; point-blank mechanic has no modifier vocabulary equivalent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Grizzled Company (3DP → PRIORITY ASSETS)
- **Mechanics**: Every Officer issues one additional Order per battle round; while an AM unit is affected by any Order, its models re-roll hit rolls of 1. Effectively an army-wide accuracy buff gated on the Order system.
- **Rating**: Strong for Priority Assets and Take and Hold
- **Synergies**: Any broad Officer suite — Lord Solar Leontus, Cadian Castellan, Commissar — multiplying into Kasrkin, Cadian Shock Troops, Death Korps Of Krieg and ordered vehicle wings.
- **Limits**: Re-roll applies only while the unit is affected by an Order; extra-order economy scales with number of Officers paid for; 3DP entry cost.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

#### Recon Element (3DP → RECONNAISSANCE)
- **Mechanics**: Walker or Regiment units permanently count as having Benefit of Cover; when such a unit gains cover from another source, its save improves by a further 1 (max 3+).
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Infantry horde bodies (Death Korps Of Krieg, Cadian Shock Troops) plus Sentinel walkers sitting in terrain; Rough Rider skirmish screens.
- **Limits**: Save improvement capped at 3+; cover-save mechanics not expressible in modifier vocabulary; 3DP cost for a purely defensive rule.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/astra-militarum/

### Enhancements & Stratagems Worth Taking
*(interpretation — enhancement effect text is NOT yet captured in the research corpus; names verified against data/merged only. Verify effects against the faction pack before citing mechanics.)*
- **Grizzled Company's four enhancements** (Abhuman Detail, Aquilan Eye, Laud Hailer, Spec Ops Veteran) sit on the faction's strongest detachment — likely picks by placement alone.
- Combined Arms' Grand Strategist also appears in Armoured Infantry, suggesting a shared command-economy enhancement design; verify wording before assuming identical effects.
- No stratagem effects were captured in the research corpus for this faction — do not assert any stratagem mechanics as fact.

### Overall Play Pattern
*(interpretation)* Astra Militarum plays as an Orders-economy army: cheap durable bodies and tank squadrons whose output is multiplied by spreading Officer Orders as widely as possible. Grizzled Company is the clearest expression of this identity and the default competitive shell; the rest of the detachment roster offers narrower tools (Scion drops, tank rushes, siege debuffs) that ask the opponent to answer a specific plan. The faction's weakness is that most non-Grizzled rules are conditional on positioning or turn timing, so off-plan lists fall back to baseline statlines quickly.

Assumptions:
- opponent unknown (all-comers)
- no cover factored beyond what detachment rules state
- Order availability assumes typical Officer counts, not maximum-saturation lists
- no CP economy modeling for stratagems
