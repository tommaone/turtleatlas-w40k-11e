# Aeldari

## Faction Identity

- **Full name**: Aeldari (BSData catalogue: "Aeldari - Craftworlds"; library covers Craftworlds, Drukhari, Harlequins)
- **Faction keyword**: AELDARI
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Battle Focus token economy — tokens fuel manoeuvres such as Fade Back and Swift as the Wind (+2" Move), plus Agile Manoeuvre rolls (per detachment_research/aeldari.json references in Warhost/Spirit Conclave entries)
- **Keywords every unit should carry**: AELDARI
- **Sub-faction keywords** (per research corpus): ASURYANI, ANHRATHE (Harlequins), YNNARI, HARLEQUINS, plus unit-family keywords (ASPECT WARRIORS, GUARDIAN, WRAITH CONSTRUCT, RANGERS)

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/aeldari.json (2026-08-23, packs v1.1).

### Army Rule
- **Battle Focus**: token-based manoeuvre economy. Tokens enable moves such as Fade Back and Swift as the Wind (+2" Move) and Agile Manoeuvre rolls (research corpus references these by name in the Warhost, Spirit Conclave and Devoted of Ynnead entries; the corpus does NOT reproduce the full army-rule text — treat token generation/spend details as partially unverified here).
- **Play pattern** *(interpretation)*: token economy rewards constant repositioning — lists that spend tokens every turn on threat-range extension and objective dips. Detachments that add tokens (Warhost) or extend Battle Focus access to new units (Spirit Conclave) compound the economy.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Strong | Multiple objective-focused detachments (Guardian Battlehost +1 to Hit near objectives, Spirit Conclave wraith BATTLELINE); army-wide mobility supports objective rotation. |
| Purge the Foe | Moderate | Eldritch Raiders grants Advance-and-Charge army-wide (research: `advance_and_charge`); damage buffs elsewhere are unit-scoped. |
| Reconnaissance | Situational | Three recon-tagged detachments exist but their rules are detection-range/Assault interactions outside the engine vocabulary; value unproven. |
| Priority Assets | Situational | Corsair Coterie sticky-objective + MW punish and Seer Council Fate dice help, but nothing protects expensive glass units durably. |
| Disruption | Moderate | Four disruption detachments, largely Harlequin-keyword scoped (Stealth, charge-through-units, OC 2 Troupes) — strong if the list is Harlequin-heavy, else narrow. |

### Detachment Assessments
<!-- one block per detachment, ordered by DP -->

#### Armoured Warhost (1DP → RECONNAISSANCE)
- **Mechanics**: Skilled Crews — friendly AELDARI VEHICLE ranged weapons gain [ASSAULT] (shoot after Advance).
- **Rating**: Situational for Reconnaissance / Purge the Foe
- **Synergies**: any VEHICLE-heavy build; research names War Walkers and Vypers as vehicle-family units in the corpus.
- **Limits**: VEHICLE units only; [ASSAULT] is explicitly not modeled (no vocabulary key); no other buff in the detachment per corpus.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Fateful Performance (1DP → DISRUPTION)
- **Mechanics**: Acrobatic Onslaught — HARLEQUINS units can move through enemy models when making a Charge move.
- **Rating**: Situational for Disruption
- **Synergies**: Troupe, Skyweavers — charges that ignore body-blocking screens.
- **Limits**: HARLEQUINS units only; positioning benefit with no modifier equivalent; cheapest way into Harlequin play but adds nothing offensively.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Path Of The Outcast (1DP → RECONNAISSANCE)
- **Mechanics**: Far-Reaching Doom — while a friendly RANGERS or SHROUD RUNNERS unit is selected to shoot, enemy units add 6" to their detection range until it has shot.
- **Rating**: Weak for most dispositions; Situational for Disruption only if the 11e hidden/detection rules matter heavily in the matchup
- **Synergies**: Rangers, Shroud Runners (both present in data/config/aeldari/squads.json).
- **Limits**: two-unit-type scope; depends entirely on out-of-corpus detection rules; no modifier equivalent.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Twilight Flickers (1DP → TAKE AND HOLD)
- **Mechanics**: Dance of Distortion — friendly HARLEQUINS units have Stealth (-1 to be hit by ranged attacks).
- **Rating**: Situational for Take and Hold (Harlequin-heavy builds)
- **Synergies**: Troupe, Skyweavers holding mid-board objectives.
- **Limits**: corpus flags explicitly: HARLEQUINS units ONLY — must not be applied army-wide.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Aspect Host (3DP → DISRUPTION)
- **Mechanics**: Path of the Warrior — each time an ASPECT WARRIORS or AVATAR OF KHAINE unit shoots/fights, choose one for that phase: re-roll hit 1s or re-roll wound 1s.
- **Rating**: Moderate for Purge the Foe / Disruption
- **Synergies**: Dire Avengers, Howling Banshees, Fire Dragons, Dark Reapers, Avatar of Khaine (all in config).
- **Limits**: player chooses per activation — both rerolls never stack; unit-scope excludes Guardians/Craftworld core; 3DP consumes the entire typical budget.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Warhost (3DP → RECONNAISSANCE)
- **Mechanics**: Martial Grace — +1 additional Battle Focus token per battle round; Swift as the Wind becomes +3" total (+1 on army-rule +2"); +1 to D6-based Agile Manoeuvre results.
- **Rating**: Situational for Reconnaissance / Take and Hold
- **Synergies**: any mobile core — Windriders, Shroud Runners, Striking Spears (Shining Spears in config).
- **Limits**: benefits are token-spending-choice dependent; movement_bonus refers only to the token-gated manoeuvre, not raw Move; 3DP full-budget cost for a mobility dividend.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Corsair Coterie (2DP → PRIORITY ASSETS)
- **Mechanics**: Relentless Raiders — enemy units ending any move within range of an objective you control roll 2+, on success suffer D3 mortal wounds; ANHRATHE units get Void Thieves (sticky objective control); grants points-costed Corsair Enhancements to ANHRATHE units.
- **Rating**: Moderate for Priority Assets / Take and Hold
- **Synergies**: Corsair Voidreavers, Corsair Voidscarred, Corsair Skyreavers (in config); any cheap objective-sitter force.
- **Limits**: MW output is reactive and dice-dependent; Void Thieves and the Enhancement system have no modeled equivalents; Enhancements add points.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Devoted Of Ynnead (2DP → PRIORITY ASSETS)
- **Mechanics**: Strength from Death — three sub-rules: revenge move (D6+1") for nearby YNNARI Infantry/Mounted after a Ynnari unit dies in opponent's Shooting phase; Fade Back surges D6+1"; one YNNARI unit below starting strength gains Fights First at start of Fight phase. Requires Yvraine and/or The Yncarne as Warlord.
- **Rating**: Situational for Priority Assets
- **Synergies**: Yvraine, The Yncarne, plus any YNNARI-tagged core.
- **Limits**: hard army-construction gate (named Warlord requirement); all three effects reactive/conditional; none modeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Eldritch Raiders (2DP → PURGE THE FOE)
- **Mechanics**: Yriel's Own — AELDARI units may declare charges in a turn they Advanced; ANHRATHE/RANGERS/SHROUD RUNNERS re-roll Advance rolls; Veterans of the Void adds points-costed Corsair Enhancements for ANHRATHE units.
- **Rating**: Moderate for Purge the Foe (melee delivery), Situational otherwise
- **Synergies**: Howling Banshees, Striking Scorpions, Avatar of Khaine — Advance-and-Charge fixes melee delivery; Prince Yriel is the namesake carrier.
- **Limits**: Advance rerolls are unit-scoped; Enhancement effects (LANCE, ANTI-MONSTER/VEHICLE 5+) not modeled; charge declaration ≠ guaranteed charge distance.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Ghosts Of The Webway (2DP → DISRUPTION)
- **Mechanics**: Acrobatic Onslaught (charge through enemy models for HARLEQUINS) + Travelling Players: TROUPE units gain BATTLELINE, TROUPE models OC 2; max 3 each Death Jester/Shadowseer/Troupe Master.
- **Rating**: Situational for Disruption
- **Synergies**: Troupe spam with Troupe Master/Shadowseer support.
- **Limits**: OC 2 applies ONLY to TROUPE models (corpus assumption: base OC 1); charge-move rule has no modifier equivalent; Harlequin-only payoff.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Guardian Battlehost (2DP → TAKE AND HOLD)
- **Mechanics**: Defend at All Costs — DIRE AVENGER, GUARDIAN, SUPPORT WEAPON and WAR WALKER attacks get +1 to Hit if attacker and/or target is within range of an objective marker.
- **Rating**: Moderate for Take and Hold (the condition aligns with what this list does anyway)
- **Synergies**: Dire Avengers, Guardian Defenders, Storm Guardians, D-Cannon/Shadow Weaver/Vibro Cannon platforms, War Walkers.
- **Limits**: +1 to Hit is CONDITIONAL on objective-marker proximity (explicitly not modeled as always-on); four-unit-family scope.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Seer Council (2DP → PRIORITY ASSETS)
- **Mechanics**: Strands of Fate — Fate dice pool at battle start (3/6/9 D6 by battle size); once per phase substitute a Fate die for any single dice roll (Advance, charge, hit, wound, damage, save, battle-shock) for a unit with the Strands of Fate ability; discarding a die matching a stratagem-mapped value reduces that stratagem's CP cost by 1.
- **Rating**: Moderate for Priority Assets (utility across every phase)
- **Synergies**: Farseer, Eldrad Ulthran, Warlock-led units carrying the ability.
- **Limits**: stochastic resource — no fixed modifier value; pool size varies by battle size; CP-discount mapping is stratagem-specific and unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Serpent’S Brood (2DP → PURGE THE FOE)
- **Mechanics**: Boons of the Brood — weapons on HARLEQUINS MOUNTED and HARLEQUINS VEHICLE models gain Sustained Hits 1; HARLEQUINS units disembarking from a Transport also gain Sustained Hits 1 until end of turn; TROUPE gains BATTLELINE with OC 2.
- **Rating**: Situational for Purge the Foe (buff is real but narrowly scoped)
- **Synergies**: Skyweavers, Troupe on transports (disembark turn burst).
- **Limits**: always-on part covers MOUNTED/VEHICLE Harlequin models only; disembark bonus is turn-of-disembark only; BATTLELINE/OC grants unmodeled.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Spirit Conclave (2DP → TAKE AND HOLD)
- **Mechanics**: Shepherds of the Dead — enemy units that destroy an ASURYANI PSYKER gain a Vengeful Dead token; WRAITH CONSTRUCT attacks against tokened units get +1 to Hit and +1 to Wound; ASURYANI PSYKERs carry a 12" Spirit Guides aura granting Battle Focus to Wraithblades/Wraithguard/Wraithlord; Wraithblades/Wraithguard gain BATTLELINE.
- **Rating**: Situational for Take and Hold
- **Synergies**: Spiritseer-led Wraithblades/Wraithguard blocks.
- **Limits**: +1/+1 is double-conditional (enemy must already have killed your PSYKER AND target must be WRAITH CONSTRUCT) — explicitly not modeled; Battle Focus aura depends on the token economy.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

#### Windrider Host (2DP → DISRUPTION)
- **Mechanics**: Ride the Wind — in Declare Battle Formations, ASURYANI MOUNTED and VYPER units may deploy into Reserves arriving as Strategic Reserves one battle round earlier; at end of opponent's turn may voluntarily remove a limited number (1/2/3 by battle size) into Strategic Reserves; WINDRIDERS gain BATTLELINE.
- **Rating**: Situational for Disruption / Reconnaissance
- **Synergies**: Windriders, Vypers — repeated threat-angle resets.
- **Limits**: reserve/withdrawal tricks outside modifier vocabulary; withdrawal cap varies by battle size; payoff depends on opponent over-committing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/aeldari/

### Enhancements & Stratagems Worth Taking
*(interpretation — corpus documents enhancement SYSTEMS, not individual picks, for this faction)*
- Corsair Enhancements (Corsair Coterie / Eldritch Raiders): research names Infamy (OC debuff aura), Deep Strike, LANCE melee, and ANTI-MONSTER/VEHICLE 5+ ranged options — all points-costed and unmodeled; treat any specific pick as unverified until individually sourced.
- The corpus does NOT catalogue individual stratagem names for this faction — no recommendations offered rather than invented ones.

---

**Overall army play pattern** *(interpretation)*: The Aeldari assessment reduces to one question: how much of the plan rides on the Battle Focus token economy. The strongest grounded packages convert mobility into objective pressure — Guardian Battlehost makes objective-proximity a weapon rather than a liability, Eldritch Raiders solves melee delivery, and Corsair Coterie taxes anyone who contests your markers. The Harlequin-keyword detachments (Twilight Flickers, Ghosts of the Webway, Serpent's Brood, Fateful Performance) form a separate sub-game that only pays inside a Harlequin-dense list, and the corpus is careful to scope every one of those buffs to HARLEQUINS models. Expect fast, fragile boards where position beats durability, with Seer Council's Fate dice smoothing the variance that glass profiles otherwise suffer.
