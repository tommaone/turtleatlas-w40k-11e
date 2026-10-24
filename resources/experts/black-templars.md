# Expert File: Black Templars

## Faction Identity

- **Full name**: Black Templars (BSData catalogue: "Imperium - Adeptus Astartes - Black Templars")
- **Faction keyword**: `Faction: Adeptus Astartes`, `Faction: Black Templars`
- **Game edition**: 11th (10e-derived profiles)
- **Core mechanics**: Adeptus Astartes framework with two shared rules — **Combat Doctrines** (Assault / Devastator / Tactical) and **Templar Vows**. The Warhammer Community faction-pack line ("forget Oaths of Moment, swear a Templar Vow") still holds in 11e: the chapter layers a Vow on top of the doctrines rather than replacing them. The Vow is picked at the start of the first battle round and drives how the chapter fights. Sourced: BSData 9b8207c (rule `Templar Vows`, Astartes library); GW faction-pack article.
- **Sub-faction keywords**: `Faction: Black Templars`

## Army Rules & Detachments — Expert Assessment

> 🔴 STRATEGY TIER — interpretation layer. Ratings below are expert-player
> judgement grounded in the mechanics facts cited; they are NOT engine output.
> Engine numbers (DPP/tier scores) live in findings/ and are GENERALIST ONLY.
> No assumptions presented as facts: every factual claim traces to merged
> data, the research corpus, or engine output. Judgements are labeled.

**Research basis**: workspace/detachment_research/black-templars.json +
_space-marines-shared.json (2026-08-23, packs v1.1). 20 detachments total:
6 chapter-specific, 14 inherited from the shared Space Marines codex pack
(rated here in Black Templars context, not re-assessed).

### Army Rule
- **Army Rule Rating**: Weak — Black Templars use Templar Vows (hidden rule in the Astartes library) alongside the shared Astartes Combat Doctrines army rule; substantive August readings were poor (34.0% 10-Aug, 31.4% 17-Aug) on tiny samples. Sourced: BSData 9b8207c; warpfriends.wordpress.com 2026-08-12 (34.0%); listhammer.info/factions/black-templars 2026-09-05 (54.8%, N=8).
- **Templar Vows**: Black Templars pick one of four Templar Vows at the start of the first battle round (Adeptus Astartes armies only): a psyker-hunting vow (charge re-rolls + Precision vs Psykers), a low-strength vow (+1 wound on melee), a relentless-pursuit vow (charge after Fall-back + no consolidation constraint), and an honour vow (holds objectives, can perform Actions). Sourced: BSData 9b8207c (rule `Templar Vows`, Astartes library).
- **Play pattern** *(interpretation)*: the chapter-specific suite is built around Crusader Squad / Sword Brethren bodies pushing forward — advance/charge reliability, transport assault, and Chaplain-fuelled melee pressure — with Templar Vows deciding what the first battle round is for.

### Disposition Fit (current meta verdict)
| Disposition | Fit | Grounded reasoning |
|-------------|-----|--------------------|
| Take and Hold | Moderate | Fist Of The God-Emperor (Crusader Squad surge moves target the closest objective) anchors the chapter; the inherited bench (Assault Brethren, Gravis Linebreaker/Siege Force, Tacticus Attack Force) fills the gap, and Templar Vows (Uphold the Honour) can secure objectives outright. |
| Purge the Foe | Strong | Vow-Sworn Crusaders (Templar Vows — Accept Any Challenge gives +1 wound against tougher targets) and Devastator Brethren answer it; Sword Brethren mortal-wound charges supply the melee spike. |
| Reconnaissance | Moderate | Only inherited tools (Gauntlet Task Force, Stormlance Task Force) — no chapter-specific recon piece. |
| Priority Assets | Moderate | Marshal's Household (Sword Brethren +1A within objective range) is unit-locked; Ironclad Champions, Tactical Brethren, Terminator Storm Force and Tacticus Firestorm Force are the inherited generalists. |
| Disruption | Strong | Fist Of The God-Emperor's surge economy plus Phobos Shadow/Shock Force and Stormlance Task Force (mounted +2" M) carry the mobility games. |

### Detachment Assessments
<!-- Roster source: the 11e detachment roster is rendered from data/merged/<fid>.json (MFM 1.5, 11e);
     this file supplies the rating only, matched by detachment name AND by the disposition the
     rating was judged for ("Strong for Disruption" only applies if the 11e package still queues
     for Disruption). The blocks below are the 10e research record: a name that still exists in 11e
     keeps its rating only when that disposition still applies, and its prose still describes the
     10e rule. Detachments that no longer exist in 11e are dropped at render time. -->

### Chapter-Specific Detachments
<!-- ordered by DP -->

#### Marshal'S Household (1DP → PRIORITY ASSETS)
- **Mechanics**: Faith-fuelled Resolve — Sword Brethren Squads gain +1 OC; enhancements add +1 to charge rolls or Fights First; stratagems add +2 Strength vs Monsters/Vehicles, D6-per-model mortal wounds on the charge (max 6), and Desperate Escape punishment.
- **Rating**: Situational for Priority Assets
- **Synergies**: Sword Brethren Squad led by High Marshal Helbrecht or a Marshal as the army's scoring blade.
- **Limits**: OC buff restricted to Sword Brethren Squads; mortal-wound stratagem is CP-gated and capped; 1DP add-on scope.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### The Living Miracle (1DP → DISRUPTION)
- **Mechanics**: Anointed Champion — when the Emperor's Champion fights, re-roll one hit roll and one wound roll. Free Guiding Omens enhancement picks 3 of 6 abilities (incl. once-per-battle Devastating Wounds vs Characters, +2 Attacks). No stratagems.
- **Rating**: Situational for Disruption
- **Synergies**: Emperor'S Champion (or Anointed variant) duelling enemy characters.
- **Limits**: Single-model detachment — zero effect on the other ~90% of the army; ⚠️ merged objective DISRUPTION conflicts with official sources listing PURGE THE FOE.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Wrathful Procession (1DP → TAKE AND HOLD)
- **Mechanics**: Chant of Deathless Devotion — Chaplain units get a 5+ invulnerable save vs ranged attacks; enhancements add Devastating Wounds or Cleave/Precision choice to the Chaplain's melee; stratagems add 4+ FNP vs mortals, unit Precision, +1 Strength.
- **Rating**: Situational for Take and Hold
- **Synergies**: Chaplain Grimaldus holding an objective with Crusader Squad bodyguard.
- **Limits**: Chaplain-keyword-gated throughout; save is ranged-only; 1DP add-on scope.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Companions Of Vehemence (2DP → PURGE THE FOE)
- **Mechanics**: Righteous Fervour — ALL units re-roll Advance and Charge rolls. Stratagems give 6" pile-in/consolidate, reactive Surge toward enemies within 9", battle-shock punishment for chargers.
- **Rating**: Strong for Purge the Foe (and Disruption)
- **Synergies**: Any melee core — Crusader Squad blobs, Sword Brethren Squad, Assault Intercessors With Jump Packs — gets reliable charge math without spending eligibility rules.
- **Limits**: Rerolls are dice-reliability, not eligibility (cannot charge after Advance); most spike damage lives behind CP stratagems.
- **_source**: https://www.goonhammer.com/40k-11th-edition-faction-pack-review-black-templars

#### Godhammer Assault Force (2DP → PURGE THE FOE)
- **Mechanics**: Units get +1 to hit with melee if they disembarked from a Transport that turn; charged enemies take Battle-shock tests. Stratagems allow charging through models and disembarking from a Land Raider straight into Engagement Range.
- **Rating**: Situational for Purge the Foe
- **Synergies**: Land Raider-delivered Terminator Assault Squad / Sword Brethren alpha strikes.
- **Limits**: Everything keys off Transport disembarkation — dead transport rule, dead detachment; ⚠️ research confidence MEDIUM; ⚠️ merged objective PURGE THE FOE conflicts with official sources listing DISRUPTION.
- **_source**: https://www.warhammer-community.com/en-gb/articles/3nvcmema/black-templars-forget-oaths-of-moment-swear-a-templar-vow-today/

#### Vindication Task Force (2DP → PRIORITY ASSETS)
- **Mechanics**: Purge and Sanctify — attacks vs ANCIENT units near objectives subtract 1 from wound rolls when attacker S exceeds target T; Crusader Squad surge moves can route toward objectives. Stratagems revive a destroyed Ancient, add AP near objectives, ignore cover/hit modifiers.
- **Rating**: Situational for Take and Hold (objective-holding build despite PRIORITY ASSETS label)
- **Synergies**: Crusade Ancient / Ancient anchoring big Crusader Squads on mid-field markers.
- **Limits**: Defensive reduction dual-conditional (ANCIENT + objective + S>T); revival stratagem once-per-battle per model; research confidence MEDIUM.
- **_source**: https://www.40k.app/factions/black-templars/detachments/vindication-task-force

### Inherited From Space Marines Codex
<!-- shorter blocks; mechanics per _space-marines-shared.json, rated in BT context -->

#### Fulguris Task Force (1DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Skystrike — SPEEDER units ingress in Movement phase 1 (inherited from SM codex).
- **Rating**: Situational for Reconnaissance — thin speeder roster in config; ⚠️ shared-codex delta flags official sources listing DISRUPTION.
- **_source**: inherited:_space-marines-shared.json

#### Subversion Assets (1DP → DISRUPTION) — *inherited*
- **Mechanics**: Nowhere to Hide — Scout/Phobos detection manipulation (inherited from SM codex).
- **Rating**: Situational for Disruption — Scout Squad utility only; ⚠️ shared-codex delta flags official sources listing RECONNAISSANCE.
- **_source**: inherited:_space-marines-shared.json

#### Vengeful Hosts (1DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Imperator Unleashed — FLY INFANTRY re-roll hit 1s on ingress/charge turns (inherited from SM codex).
- **Rating**: Situational for Take and Hold. ⚠️ Research confidence LOW: objective/DP sourcing unconfirmed by fetched sources.
- **_source**: inherited:_space-marines-shared.json

#### Anvil Siege Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: All ranged weapons gain HEAVY (+1 Wound stationary if already HEAVY) (inherited from SM codex).
- **Rating**: Weak for Take and Hold — static gunline theme against a melee chapter identity.
- **_source**: inherited:_space-marines-shared.json

#### Firestorm Assault Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: ASSAULT on all ranged, +1 Strength within 12" (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — works with Aggressor Squad close-range packages; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Headhunter Task Force (2DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Tank Ace vehicles: flat 6" Advance, stationary damage re-rolls (inherited from SM codex).
- **Rating**: Situational for Priority Assets — very thin vehicle roster in config (Drop Pod only), limiting value.
- **_source**: inherited:_space-marines-shared.json

#### Ironstorm Spearhead (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: One hit/wound/damage re-roll per unit per phase (inherited from SM codex).
- **Rating**: Weak for Take and Hold — single-die insurance, vehicle-themed mismatch; ⚠️ shared-codex delta flags official sources listing PURGE THE FOE.
- **_source**: inherited:_space-marines-shared.json

#### Orbital Assault Force (2DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: 2-4 units gain Deep Strike + arrival-turn wound-1s rerolls (inherited from SM codex).
- **Rating**: Moderate for Take and Hold — Drop Pod delivery suits the Crusader push.
- **_source**: inherited:_space-marines-shared.json


#### Vanguard Spearhead (2DP → RECONNAISSANCE) — *inherited*
- **Mechanics**: Benefit of Cover vs ranged attacks from beyond 12" (inherited from SM codex).
- **Rating**: Moderate for Reconnaissance — best inherited defensive core for a footslogging Crusader army.
- **_source**: inherited:_space-marines-shared.json

#### Bastion Task Force (3DP → TAKE AND HOLD) — *inherited, premium DP*
- **Mechanics**: Battleline act after Advance/Fall Back + Auspex scan rerolls (inherited from SM codex; BT pay 3DP vs 2DP shared cost — confirmed by research note).
- **Rating**: Weak for Take and Hold — paying above shared-codex price for an off-brand Battleline flood playstyle.
- **_source**: inherited:_space-marines-shared.json

#### Armoured Speartip (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Post-disembark follow-up moves from moved Transports (inherited from SM codex).
- **Rating**: Situational for Take and Hold — overlaps Godhammer's transport-assault niche at higher DP.
- **_source**: inherited:_space-marines-shared.json

#### Ceramite Sentinels (3DP → TAKE AND HOLD) — *inherited*
- **Mechanics**: Terrain-based hit/wound-1s rerolls + Entrenched status (inherited from SM codex).
- **Rating**: Situational for Take and Hold — static gunline theme, off-brand.
- **_source**: inherited:_space-marines-shared.json

#### Gladius Task Force (3DP → PRIORITY ASSETS) — *inherited*
- **Mechanics**: Rotating Combat Doctrines, each once per battle (inherited from SM codex).
- **Rating**: Moderate for Priority Assets — serviceable generalist; Assault Doctrine duplicates what Companions/Stormlance do permanently.
- **_source**: inherited:_space-marines-shared.json


#### Assault Brethren (1DP → TAKE AND HOLD)
- **Mechanics**: Assault Mastery — select the Assault Doctrine one additional time per battle.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Assault doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Deathwatch Support (1DP → DISRUPTION)
- **Mechanics**: Inherited cross-chapter package.
- **Rating**: Situational for Disruption
- **Synergies**: Niche.
- **Limits**: Minimal bespoke rules.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Devastator Brethren (1DP → PURGE THE FOE)
- **Mechanics**: Devastator Mastery — select the Devastator Doctrine one additional time per battle.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Firepower doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Fist Of The God-Emperor (1DP → TAKE AND HOLD)
- **Mechanics**: Inherited/alternate package for Templar play (context-dependent).
- **Rating**: Moderate for Take and Hold
- **Synergies**: Melee-focused objective play.
- **Limits**: Package effect details vary; treat as conditional.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Gauntlet Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Combined Deployment — transport shoots marks target assailed; disembarked ADEPTUS ASTARTES get [Sustained Hits 1] vs it.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Transport delivery.
- **Limits**: Conditional timing.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Gravis Linebreaker Force (1DP → TAKE AND HOLD)
- **Mechanics**: Walking Fortress — Gravis moved Normal: ranged lose [Heavy] and get +1 to hit.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Aggressive Gravis.
- **Limits**: Gravis-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Gravis Siege Force (1DP → TAKE AND HOLD)
- **Mechanics**: Indomitable Defence — while in range of objective, attacks with S>T vs Gravis have -1 to wound.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Gravis anchoring.
- **Limits**: Objective-range, S>T only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Ironclad Champions (1DP → PRIORITY ASSETS)
- **Mechanics**: Enduring Vengeance — Dreadnoughts re-roll hit rolls of 1.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Dreadnought lists.
- **Limits**: Dreadnought-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Phobos Shadow Force (1DP → DISRUPTION)
- **Mechanics**: Shadow Masters — Phobos/Scout shoot then don't prevent hidden or make D6" move (no charge until end).
- **Rating**: Moderate for Disruption
- **Synergies**: Phobos recon.
- **Limits**: Scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Phobos Shock Force (1DP → DISRUPTION)
- **Mechanics**: Vanguard Ambushers — end of Movement if hidden, Phobos attacks re-roll wound rolls of 1 until end of turn.
- **Rating**: Moderate for Disruption
- **Synergies**: Hidden Phobos.
- **Limits**: Requires hidden.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Stormlance Task Force (1DP → RECONNAISSANCE)
- **Mechanics**: Lightning-Fast Strike — Mounted/Speeder have +2" Move.
- **Rating**: Moderate for Reconnaissance
- **Synergies**: Bike/Speeders.
- **Limits**: Mounted/Speeder only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Tactical Brethren (1DP → PRIORITY ASSETS)
- **Mechanics**: Tactical Mastery — select Tactical Doctrine one additional time per battle.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Doctrine cycling.
- **Limits**: Doctrine-gated.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Tacticus Attack Force (1DP → TAKE AND HOLD)
- **Mechanics**: Wrath of the Chapter — Tacticus units can re-roll advance rolls.
- **Rating**: Moderate for Take and Hold
- **Synergies**: Tacticus advancing.
- **Limits**: Tacticus-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Tacticus Firestorm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Codex Fire-Patterns — Tacticus [Rapid Fire] at max range count as Rapid Fire.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Tacticus rapid fire.
- **Limits**: Tacticus/RF only.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Terminator Storm Force (1DP → PRIORITY ASSETS)
- **Mechanics**: Death Blow — Terminator units have +1 to charge rolls.
- **Rating**: Moderate for Priority Assets
- **Synergies**: Terminator assaults.
- **Limits**: Terminator-scoped.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

#### Vow-Sworn Crusaders (2DP → PURGE THE FOE)
- **Mechanics**: Templar vows-focused package enhancing crusader melee.
- **Rating**: Moderate for Purge the Foe
- **Synergies**: Crusader Squads in melee-focused lists.
- **Limits**: Vow-dependent, melee-focused.
- **_source**: https://wahapedia.ru/wh40k11ed/factions/black-templars/

### Enhancements & Stratagems Worth Taking
- *(Interpretation, restricted to what the research files document)* The Living Miracle's free Guiding Omens pick-3-of-6 does not count against the army enhancement limit — the only documented zero-cost enhancement in the chapter pack, making Emperor's Champion builds efficient. Marshal's Household's Blade of Detestation (D6-per-model mortal wounds on the charge, max 6) is the named burst CP tool for Sword Brethren. Companions Of Vehemence's pile-in/consolidate 6" stratagem extends engagement grinding. All CP/enhancement-gated, not plan-of-record.

### Overall Army Play Pattern
*(interpretation)* Black Templars are an Adeptus Astartes army with a vow layer on top: Combat Doctrines for the framework, Templar Vows for the chapter's engine (a Vow is picked at the start of the first battle round and shapes how the army fights). The 11e roster is three chapter packages — Fist Of The God-Emperor (1DP, Take and Hold), Marshal's Household (1DP, Priority Assets), Vow-Sworn Crusaders (2DP, Purge the Foe) — plus fifteen inherited Astartes packages, so the chapter's identity is narrower than the 10e corpus suggested. The correct default is Vow-Sworn Crusaders for the melee trade with a 1DP take-and-hold or asset package layered on, and the army's massed Crusader Squad / Sword Brethren bodies do the scoring and the trading. Weak spots: Reconnaissance is inherited only (Stormlance, Gauntlet), the army has no doctrine-granting package of its own, and any claim about a specific Vow's numbers is unsupported in the corpus — treat vow effects as unverified until the rules text is read.