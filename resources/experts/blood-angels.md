# Expert File: Blood Angels

## Faction Identity

- **Full name**: Blood Angels (BSData catalogue: "Imperium - Adeptus Astartes - Blood Angels")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Blood Angels`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Adeptus Astartes framework — the shared **Combat Doctrines** army rule (Assault / Devastator / Tactical, one per Command phase, one per battle, one active per unit), no separate chapter army rule. Chapter identity expresses through melee/jump-pack-oriented detachments whose rules reference the Red Thirst (Angelic Inheritors, Encarmine Speartip). Sourced: BSData 9b8207c; GW preview 2026-09-10.
- **Sub-faction keywords**: `Faction: Blood Angels`

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/blood-angels.json +
_space-marines-shared.json (2026-08-23, packs v1.1). 24 detachments total:
8 chapter-specific, 16 inherited from the shared Space Marines codex pack
(rated here in Blood Angels context, not re-assessed).

### Army Rule
- **Army Rule Rating**: Weak — Blood Angels use the Astartes Combat Doctrines army rule (one of three doctrines per Command phase, one per battle, one active per unit) with no separate chapter army rule; the chapter's punch comes from detachment tools.
- **Oath of Moment (RETIRED)**: was the Astartes army rule until Codex: Space Marines (2026-10-03) replaced it with Combat Doctrines. Survives in BSData only as a reference inside the Angels Ascendant character ability. Sourced: BSData 9b8207c; GW preview 2026-09-10.
- **Play pattern** *(interpretation)*: the detachment roster pushes hard toward melee tempo — jump-pack density (Sanguinary Guard, Death Company, Vanguard Veterans With Jump Packs) converts into doctrine-driven swings in the three chapter-specific detachments (Encarmine Speartip puts Sanguinary Guard on Tactical, Wrath of the Doomed puts Death Company on Assault).

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Encarmine Speartip and Wrath Of The Doomed convert the chapter's bodies into objective holders — Sanguinary Guard and Death Company ride a doctrine; the inherited bench (Assault Brethren, Gladius Task Force, Gravis Linebreaker/Siege Force, Tacticus Attack Force) adds depth. |
| Purge the Foe | Strong | Angelic Inheritors (3DP — chapter characters re-roll hits and wounds of 1) with Wrath Of The Doomed (assault doctrine active for Death Company) and Devastator Brethren give both a character-led and a mass-melee answer. |
| Reconnaissance | Moderate | Only inherited tools (Gauntlet Task Force, Stormlance Task Force); jump mobility reaches objectives but scoring actions are thin. |
| Priority Assets | Moderate | Angelic Inheritors is characters-only; Gladius Task Force, Ironclad Champions, Terminator Storm Force and Tacticus Firestorm Force (Rapid Fire at full range) are the inherited generalists. |
| Disruption | Strong | Encarmine Speartip (tactical doctrine active for Sanguinary Guard) plus Phobos Shadow/Shock Force and Deathwatch Support suit a jump-pack-heavy roster; Stormlance Task Force adds mounted reach. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->

### Chapter-Specific Detachments
<!-- ordered by DP -->

#### Encarmine Speartip (1DP → DISRUPTION)
- **Mechanics**: Wrath of Angels — SANGUINARY GUARD units stay eligible to shoot and charge in a turn they Fell Back; enhancements add melee Lethal/Sustained Hits or once-per-battle +1 Damage; stratagems add charge mortal wounds, reaction moves and Stealth.
- **Rating**: Situational for Disruption
- **Synergies**: Sanguinary Guard-led engagement grinding; the fall-back-and-recharge loop keeps the Guard locked on an objective.
- **Limits**: Eligibility restricted to SANGUINARY GUARD only; most payoff is enhancement/stratagem-gated; cheap 1DP add-on alongside a main detachment.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### Legacy Of Grace (1DP → PRIORITY ASSETS)
- **Mechanics**: Legacy of the Angel — BLOOD ANGELS CHARACTERS (except Dante) add 1 to Advance and Charge rolls. GRACE-tagged: cannot combine with other GRACE detachments.
- **Rating**: Situational for Priority Assets
- **Synergies**: Captain With Jump Pack / Chaplain With Jump Pack-led spearheads needing reliable charge distances.
- **Limits**: Roll modifier, not eligibility — does not enable advance-and-charge; characters only; mutually exclusive with Angelic Inheritors (GRACE tag).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### Wrath Of The Doomed (1DP → PURGE THE FOE)
- **Mechanics**: Fanatical Celerity — a DEATH COMPANY unit that Advances may take D3+1 mortal wounds to become eligible to charge that turn; stratagems mark killers (+1 to wound vs the marked unit), grant MOBILE to a Death Company Dreadnought, and surge-move after being shot.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Death Company Marines With Jump Packs trading wounds for extra charge turns; Lemartes keeping them alive longer.
- **Limits**: DOOMED tag; advance-and-charge is optional and self-damaging (mortal-wound cost unmodeled); Death Company-scope only.
- **_source**: https://www.tabletopbattles.com/40k-11th-edition-faction-pack-review-blood-angels

#### The Angelic Host (2DP → DISRUPTION)
- **Mechanics**: Upon Wings of Fire — at end of opponent's turn remove up to 1/2/3 (by battle size) JUMP PACK units from the battlefield into Strategic Reserves; they Deep Strike back next Movement phase. Gleaming Pinions enhancement deep strikes at 8" (errata'd).
- **Rating**: Moderate for Disruption
- **Synergies**: Assault Intercessors With Jump Packs and Vanguard Veteran Squad With Jump Packs hopping between threats; Sanguinary Guard escape-and-return loops.
- **Limits**: Cap scales with battle size; units must be outside Engagement Range to leave; tempo mechanic with no stat modifier.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### The Lost Brethren (2DP → PURGE THE FOE)
- **Mechanics**: A Noble Death in Combat — DEATH COMPANY re-roll melee wound rolls of 1 (full wound re-roll when Below Half-strength); DEATH COMPANY MARINES gain BATTLELINE.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Massed Death Company Marines (now scoring Battleline) led by Lemartes or a Death Company Captain; the Below-Half escalation rewards aggressive trades.
- **Limits**: Rerolls apply to DEATH COMPANY melee only; value collapses without a heavy Death Company investment; BATTLELINE grant affects secondary/scoring, unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### Angelic Inheritors (3DP → PRIORITY ASSETS)
- **Mechanics**: Legacy of the Angel — pick two of three army-battle abilities for all ADEPTUS ASTARTES CHARACTERS: fall-back-shoot-and-charge; re-roll hit/wound 1s; re-roll Advance and Charge rolls. GRACE tag.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Character-dense builds (Dante, Mephiston, multiple jump Captains) — the hit/wound-1s pick (Carmine Wrath) is the documented damage pick.
- **Limits**: Two of three picks only; CHARACTERS only — the rank-and-file never benefit; full 3DP spend for a character-layer buff; excludes Legacy Of Grace.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### Liberator Assault Group (3DP → TAKE AND HOLD)
- **Mechanics**: Red Thirst — each ADEPTUS ASTARTES unit that made a Charge move this turn gains +1 Attacks and +2 Strength on melee weapons until end of phase. Enhancements: once-per-battle Fights First, Sustained Hits 3 spike, Desperate Escape penalty aura.
- **Rating**: Strong for Take and Hold **on charge turns** (and Purge the Foe) — the buff requires your unit to have charged this turn, so holding an objective means charging onto it or counter-charging off it
- **Synergies**: Every melee threat in the book — Sanguinary Guard, Death Company, Vanguard Veterans With Jump Packs, Terminator Assault Squad — converts any successful charge into a stat swing.
- **Limits**: Buff strictly conditional on having charged that turn; nothing for shooting phases; full 3DP.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

#### Rage-Cursed Onslaught (3DP → PURGE THE FOE)
- **Mechanics**: Maddened Ferocity — every ADEPTUS ASTARTES model re-rolls melee wound rolls of 1; charging units gain +1 Attacks (+2 if Battle-shocked). Stratagems add +1S/+1AP on charge, Death Company FNP and fight-on-death. DOOMED tag.
- **Rating**: Strong for Purge the Foe
- **Synergies**: Broadest melee coverage in the chapter roster (even Tactical Squad power swords benefit); pairs with the voluntary-Battle-shock stratagem for +2 Attacks.
- **Limits**: Melee-only wound rerolls; DOOMED tag restricts combination; the +2 Attacks path requires accepting Battle-shock (OC/action risk).
- **_source**: https://wahapedia.ru/wh40k11ed/factions/space-marines/blood-angels

### Inherited From Space Marines Codex
<!-- shorter blocks; mechanics per _space-marines-shared.json, rated in BA context -->

#### Fulguris Task Force (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Skystrike — SPEEDER units ingress in Movement phase 1 (inherited from SM codex).
- **Rating**: Situational for Reconnaissance — no BA speeder emphasis; ⚠️ shared-codex delta flags official sources listing DISRUPTION.
- **_source**: inherited:_space-marines-shared.json

#### Subversion Assets (1DP → DISRUPTION) — *inherited*
- **Mechanics**: Nowhere to Hide — Scout/Phobos detection manipulation (inherited from SM codex).
- **Rating**: Situational for Disruption — Scout Squad support piece; ⚠️ shared-codex delta flags official sources listing RECONNAISSANCE.
- **_source**: inherited:_space-marines-shared.json

#### Librarius Conclave (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Rotating Psychic Disciplines for PSYKER units (inherited from SM codex).
- **Rating**: Situational for Reconnaissance — Mephiston/Chief Librarian-led psyker density dependent.
- **_source**: inherited:_space-marines-shared.json

#### Vengeful Hosts (1DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Imperator Unleashed — FLY INFANTRY re-roll hit 1s on ingress/charge turns (inherited from SM codex).
- **Rating**: Situational for Take and Hold — better fit here than most chapters given BA jump density. ⚠️ Research confidence LOW: objective/DP sourcing unconfirmed (later corroborated by the Wahapedia BA page per post-research note).
- **_source**: inherited:_space-marines-shared.json

#### 1st Company Task Force (2DP → PURGE THE FOE) — *inherited*
- **Mechanics (10e record)**: Once-per-battle wound re-rolls vs the Oath target (inherited from SM codex).
- **Rating**: Situational for Purge the Foe — single-target conditional tool; Terminator Assault Squad delivery.
- **_source**: inherited:_space-marines-shared.json

#### Anvil Siege Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: All ranged weapons gain HEAVY (+1 Wound stationary if already HEAVY) (inherited from SM codex).
- **Rating**: Weak for Take and Hold — anti-synergy with a melee-first chapter; Devastator/Desolation fire bases only.
- **_source**: inherited:_space-marines-shared.json

#### Bastion Task Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Battleline act after Advance/Fall Back + Auspex scan rerolls (inherited from SM codex).
- **Rating**: Situational for Take and Hold — Intercessor/Heavy Intercessor screen playstyle off-brand for BA.
- **_source**: inherited:_space-marines-shared.json

#### Firestorm Assault Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: ASSAULT on all ranged, +1 Strength within 12" (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — suits Aggressor Squad and Infernus Squad close-range packages; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Headhunter Task Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Tank Ace vehicles: flat 6" Advance, stationary damage re-rolls (inherited from SM codex).
- **Rating**: Situational for Priority Assets — Gladiator Lancer/Repulsor hulls only.
- **_source**: inherited:_space-marines-shared.json

#### Ironstorm Spearhead (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: One hit/wound/damage re-roll per unit per phase (inherited from SM codex).
- **Rating**: Weak for Take and Hold — single-die insurance, vehicle-themed, poor match; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Orbital Assault Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: 2-4 units gain Deep Strike + arrival-turn wound-1s rerolls (inherited from SM codex).
- **Rating**: Moderate for Take and Hold — Drop Pod-delivered Eradicator/Sternguard alpha complements jump reserves.
- **_source**: inherited:_space-marines-shared.json

#### Stormlance Task Force (2DP → DISRUPTION) — *inherited, chapter-discounted DP*
- **Mechanics**: Lightning Assault — all units charge after Advancing or Falling Back (inherited from SM codex).
- **Rating**: Strong for Disruption — army-wide advance-and-charge on a jump/melee roster at 2DP (vs 3DP shared cost; BA-specific price confirmed by Wahapedia and WarHammer-community faction pack table per research delta note) undercuts every other melee detachment.
- **Limits**: Eligibility ≠ auto-made charges; fall-back-charge unmodeled.
- **_source**: inherited:_space-marines-shared.json

#### Vanguard Spearhead (2DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Benefit of Cover vs ranged attacks from beyond 12" (inherited from SM codex).
- **Rating**: Moderate for Reconnaissance — best inherited defensive option for forward-deployed Scout Squads.
- **_source**: inherited:_space-marines-shared.json

#### Armoured Speartip (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Post-disembark follow-up moves from moved Transports (inherited from SM codex).
- **Rating**: Situational for Take and Hold — Land Raider Crusader assault-ramp delivery of Terminators.
- **_source**: inherited:_space-marines-shared.json

#### Ceramite Sentinels (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Terrain-based hit/wound-1s rerolls + Entrenched status (inherited from SM codex).
- **Rating**: Situational for Take and Hold — static gunline theme, off-brand.
- **_source**: inherited:_space-marines-shared.json

#### Gladius Task Force (3DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Rotating Combat Doctrines, each once per battle (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — workable generalist, but the Assault Doctrine turn duplicates what Liberator/Stormlance do permanently.
- **_source**: inherited:_space-marines-shared.json

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* In Liberator Assault Group, Speed of the Primarch (once-per-battle Fights First) is the named spike tool for a decisive charge turn. In Rage-Cursed Onslaught, the +1S/+1AP-on-charge stratagem (or both halves via voluntary Battle-shock) is the documented burst option. In The Angelic Host, Gleaming Pinions (8" deep strike after errata) tightens the return drop. Inherited Gladius tools (Storm of Fire ignore-cover, Honour the Chapter Lance) remain the CP sink when running doctrines. All CP-gated burst options, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Blood Angels play on two engines: the inherited Astartes chassis (Gladius Task Force, Ironstorm Spearhead, Tacticus x2, Gauntlet, Stormlance, Phobos x2) and three chapter packages — Angelic Inheritors (3DP, Priority Assets + Purge the Foe), Encarmine Speartip and Wrath Of The Doomed (both 1DP). The chapter identity is in the units and in the detachment rules that hand out a third doctrine (Angelic Inheritors) or point the Sanguinary Guard at a different doctrine (Encarmine Speartip), so the correct default is the 3DP melee package with a 1DP doctrine add-on rather than a gunline. Reconnaissance is the structural weak spot: no chapter package generates scoring actions, and the inherited tools for it (Gauntlet Task Force, Stormlance Task Force) are mobility, not scoring. Shooting detachments actively fight the army's strengths — the chapter has the melee and jump-pack density to convert movement into damage, and the doctrine framework lets it swing with a free doctrine pick.

### First-Army Fit
- **First-Army Fit**: Demanding — fast melee tempo on a fragile 2W core; staging and threat-timing punish early mistakes (same fragility class as World Eaters). Sourced: user domain call 2026-09-06.
